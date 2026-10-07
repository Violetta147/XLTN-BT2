import argparse
import itertools
import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / 'research_workbench_2026_10_06'))
import audit
import core
import numpy as np
import pandas as pd
import scipy
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from estimator_experiment import eligibility

audit.HERE = HERE
audit.RESULTS = HERE / 'results'
audit.FIGURES = HERE / 'figures'
audit.RESULTS.mkdir(exist_ok=True)
audit.FIGURES.mkdir(exist_ok=True)
FIT_LOG = []
CLASSIFIERS = {}


def registry(family):
    assert family == 'H22'
    return [{'id': identity, 'kind': 'raw', 'low_hz': 0, 'high_hz': 0,
             'frame_ms': 25, 'hop_ms': 10, 'C': c, 'use_zcr': zcr}
            for identity, c, zcr in [('raw_0_0_f25_h10', None, False),
                                      ('raw_lr1_2d', 1., False), ('raw_lr1_3d_zcr', 1., True)]]


def zero_crossing_rate(frames, fs):
    centered = frames - frames.mean(axis=1, keepdims=True)
    signs = np.signbit(centered)
    return np.mean(signs[:, 1:] != signs[:, :-1], axis=1) * fs


def feature_key(option):
    return '|'.join(str(option[x]) for x in ('kind', 'low_hz', 'high_hz', 'frame_ms', 'hop_ms'))


def extract(item, audio, option):
    core.init_functions()
    fs = item['fs']
    signal = audio
    length, hop = round(fs * option['frame_ms'] / 1000), round(fs * option['hop_ms'] / 1000)
    frames = np.lib.stride_tricks.sliding_window_view(signal, length)[::hop]
    raw = np.lib.stride_tricks.sliding_window_view(audio, length)[::hop]
    times = (np.arange(len(frames)) * hop + length / 2) / fs
    labels = np.array([next((lab for a, b, lab in item['segments'] if a <= t < b), 'unknown') for t in times])
    rms = np.sqrt(np.mean(raw ** 2, axis=1))
    scores, lags, frequencies, strengths = [], [], [], []
    for frame in frames:
        score, lag, curve = core.ACF['detect_pitch_acf'](frame, fs)
        lo, hi = max(1, math.ceil(fs / 400)), min(len(frame) - 2, math.floor(fs / 70))
        indices = np.arange(lo, hi + 1)
        peaks = indices[(curve[indices] >= curve[indices - 1]) & (curve[indices] >= curve[indices + 1])]
        values = curve[peaks]
        refined = np.array([core.refine_lag(curve, idx, float(idx)) for idx in peaks])
        if not len(peaks):
            refined, values = np.array([lag]), np.array([score])
        f0 = fs / refined
        valid = np.isfinite(f0) & (f0 >= 70) & (f0 <= 400)
        f0, values = f0[valid], values[valid]
        order = np.argsort(values)[::-1][:12]
        f, s = np.full(12, np.nan), np.full(12, -np.inf)
        f[:len(order)], s[:len(order)] = f0[order], values[order]
        scores.append(score)
        lags.append(lag)
        frequencies.append(f)
        strengths.append(s)
    return dict(item, frame_ms=option['frame_ms'], preprocess=feature_key(option), times=times, labels=labels,
                zcr=zero_crossing_rate(raw, fs), rms=rms, relative_rms=rms / max(np.quantile(rms, .95), core.EPS),
                ACF_score=np.array(scores), ACF_lag=np.array(lags),
                ACF_candidate_f0=np.array(frequencies), ACF_candidate_strength=np.array(strengths))


def project(native, canonical, pred, f0, hop_ms):
    times = native['times']
    right = np.minimum(np.searchsorted(times, canonical['times']), len(times) - 1)
    left = np.maximum(right - 1, 0)
    choose_left = abs(times[left] - canonical['times']) <= abs(times[right] - canonical['times'])
    indices = np.where(choose_left, left, right)
    support = abs(times[indices] - canonical['times']) <= hop_ms / 2000 + 1 / native['fs']
    return pred[indices] & support, np.where(support, f0[indices], np.nan), support


def design(item, use_zcr):
    columns = [item['ACF_score'], item['relative_rms']]
    if use_zcr:
        columns.append(item['zcr'])
    return np.column_stack(columns)


def fit_logistic(items, c, use_zcr):
    key = (items[0]['preprocess'], c, use_zcr, tuple(sorted(x['file'] for x in items)))
    if key in CLASSIFIERS:
        return CLASSIFIERS[key]
    total = sum(np.isin(x['labels'], ['v', 'uv']).sum() for x in items)
    xx, yy, ww = [], [], []
    for item in items:
        mask = np.isin(item['labels'], ['v', 'uv'])
        target = (item['labels'][mask] == 'v').astype(int)
        weights = np.array([total / (2 * len(items) * max((target == value).sum(), 1)) for value in target])
        xx.append(design(item, use_zcr)[mask])
        yy.append(target)
        ww.append(weights)
    x, y, w = np.vstack(xx), np.concatenate(yy), np.concatenate(ww)
    scaler = StandardScaler().fit(x, sample_weight=w)
    model = LogisticRegression(C=c, max_iter=500).fit(scaler.transform(x), y, sample_weight=w)
    assert model.n_iter_[0] < 500
    value = {'feature_names': ['ACF_score', 'relative_rms'] + (['zcr_crossings_per_s'] if use_zcr else []), 'fit_files': sorted(i['file'] for i in items), 'C': c,
             'mean': scaler.mean_.tolist(), 'scale': scaler.scale_.tolist(),
             'coefficient': model.coef_[0].tolist(), 'intercept': float(model.intercept_[0])}
    assert np.allclose(expit(scaler.transform(x) @ model.coef_[0] + model.intercept_[0]), model.predict_proba(scaler.transform(x))[:, 1], atol=1e-12)
    CLASSIFIERS[key] = value
    return value


def infer(native, training, option, config):
    fitted = core.fit(training, config)
    if option['C'] is None:
        return (*core.infer(native, config, fitted), fitted, None)
    classifier = fit_logistic(training, option['C'], option['use_zcr'])
    x = design(native, option['use_zcr'])
    score = expit(((x - classifier['mean']) / classifier['scale']) @ np.array(classifier['coefficient']) + classifier['intercept'])
    mask = (score >= .5) & (native['relative_rms'] >= fitted['energy_threshold'])
    adapted = dict(native, ACF_score=np.where(mask, 1., -1.))
    pred, f0 = core.infer(adapted, config, dict(fitted, pitch_threshold=.5))
    assert np.array_equal(mask, pred)
    return pred, f0, fitted, classifier


def run(family):
    started = time.perf_counter()
    options = json.loads((HERE / f'{family}_REGISTRY.json').read_text(encoding='utf-8'))['options']
    assert options == registry(family)
    items = core.load_training()
    by_name = {x['file']: x for x in items}
    names = sorted(by_name)
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['ACF']['config']
    features = {}
    for item in items:
        _, audio = core.load_audio(core.TRAIN / item['file'])
        for option in options:
            key = (feature_key(option), item['file'])
            if key not in features:
                features[key] = extract(item, audio, option)
        print(f'{family}: features ready {item["file"]}', flush=True)
    prediction_cache = {}
    fit_log = []

    def score(option, fit_names, held):
        key = (option['id'], tuple(sorted(fit_names)), held)
        if key not in prediction_cache:
            native = features[(feature_key(option), held)]
            training = [features[(feature_key(option), n)] for n in sorted(fit_names)]
            pred, f0, fitted, classifier = infer(native, training, option, config)
            pp, ff, support = project(native, by_name[held], pred, f0, option['hop_ms'])
            metrics = core.score_file(by_name[held], pp, ff)
            metrics.update(native_frames=len(pred), native_f0_count=int(np.isfinite(f0).sum()),
                           projection_coverage=float(support.mean()), effective_median_span_ms=2 * option['hop_ms'])
            prediction_cache[key] = (metrics, pp, ff, support)
            fit_log.append({'option_id': option['id'], 'fit_files': sorted(fit_names), 'held_file': held,
                            'fitted': fitted, 'classifier': classifier})
        return prediction_cache[key]

    baseline = next(x for x in options if x['id'] == 'raw_0_0_f25_h10')
    traces, selections = [], []

    def choose(pool, outer):
        candidates = []
        for option in options:
            rows, reference = [], []
            for held in pool:
                fit_names = [n for n in pool if n != held]
                measured = score(option, fit_names, held)[0]
                rows.append(measured)
                reference.append(score(baseline, fit_names, held)[0])
                traces.append({'outer_held': outer, 'option_id': option['id'], 'inner_held': held,
                               'fit_files': '|'.join(fit_names), **measured})
            table, control = pd.DataFrame(rows), pd.DataFrame(reference)
            summary, ref = core.summarize(table), core.summarize(control)
            valid = bool(table.average_mape.notna().all()
                         and summary['macro_f1'] >= ref['macro_f1'] - .01
                         and summary['recall_v'] >= ref['recall_v'] - .01
                         and summary['false_voiced_sil'] <= ref['false_voiced_sil'] + 1)
            candidates.append((not valid, summary['average_mape'] if valid else math.inf, option['id'], option))
        selected = min(candidates, key=lambda v: v[:3])[3]
        selections.append({'outer_held': outer, 'selection_files': pool, 'option': selected})
        print(f'{family}: selected {outer}: {selected["id"]}', flush=True)
        return selected

    final = choose(names, 'final')
    outer_options = {held: choose([n for n in names if n != held], held) for held in names}
    rows, contours = [], []
    for split in ('train', 'lofo', 'nested'):
        for held in names:
            fit_names = names if split == 'train' else [n for n in names if n != held]
            for model, option in [('accepted', baseline), ('candidate', outer_options[held] if split == 'nested' else final)]:
                metrics, pred, f0, support = score(option, fit_names, held)
                rows.append({'split': split, 'model': model, 'option_id': option['id'], **metrics})
                if split == 'nested':
                    for i, t in enumerate(by_name[held]['times']):
                        contours.append({'model': model, 'file': held, 'time_s': t,
                                         'label': by_name[held]['labels'][i], 'boundary': bool(by_name[held]['boundary'][i]),
                                         'pred_voiced': bool(pred[i]), 'f0_hz': f0[i], 'support': bool(support[i])})
    table = pd.DataFrame(rows)
    summaries = {model: {split: core.summarize(table[(table.model == model) & (table.split == split)])
                        for split in ('train', 'lofo', 'nested')} for model in ('accepted', 'candidate')}
    nested_table = table[table.split.isin(['train', 'nested'])].copy()
    nested_table['split'] = nested_table.split.replace({'nested': 'lofo'})
    nested_summaries = {m: {'train': summaries[m]['train'], 'lofo': summaries[m]['nested']} for m in summaries}
    decision = eligibility(nested_table, nested_summaries)
    decision['checks']['selected_lofo_mape_relative_5_percent'] = summaries['candidate']['lofo']['average_mape'] <= .95 * summaries['accepted']['lofo']['average_mape']
    decision['eligible'] = all(decision['checks'].values())
    decision['nested_status'] = 'Outer file excluded from every inner fit and selection; selected LOFO is separate.'
    for entry in fit_log:
        if entry['held_file'] not in entry['fit_files']:
            assert entry['classifier'] is None or entry['held_file'] not in entry['classifier']['fit_files']
    for entry in selections:
        assert entry['outer_held'] == 'final' or entry['outer_held'] not in entry['selection_files']
    base_metrics = table[(table.model == 'accepted') & (table.split == 'lofo')]
    recorded = pd.read_csv(REPO / 'research_workbench_2026_10_06/results/logistic_voicing_metrics.csv')
    recorded = recorded[(recorded.model == 'accepted') & (recorded.split == 'lofo')]
    assert np.allclose(base_metrics.sort_values('file').average_mape, recorded.sort_values('file').average_mape, atol=1e-8)
    native = features[(feature_key(final), names[0])]
    training = [features[(feature_key(final), n)] for n in names]
    poison = dict(native, labels=np.full(len(native['labels']), 'unknown'), stats={'F0mean': -1, 'F0std': -1, 'F0num': -1})
    expected, actual = infer(native, training, final, config), infer(poison, training, final, config)
    assert np.array_equal(expected[0], actual[0]) and np.allclose(expected[1], actual[1], equal_nan=True)
    fixed_controls(names, options, score)
    p_metrics = audit.csv_write(f'{family}_metrics.csv', table)
    audit.csv_write(f'{family}_inner_traces.csv', traces)
    p_contours = audit.csv_write(f'{family}_nested_contours.csv', contours)
    audit.json_write(HERE / f'results/{family}_fits.json', {'fits': fit_log})
    value = {'family': family, 'decision': decision, 'summaries': summaries, 'selections': selections,
             'registry_sha256': audit.digest(HERE / f'{family}_REGISTRY.json'),
             'code_sha256': {str(p.relative_to(REPO)): audit.digest(p) for p in (Path(__file__), Path(core.__file__), Path(audit.__file__), REPO / 'research_workbench_2026_10_06/estimator_experiment.py')},
             'data_sha256': {n: audit.digest(core.TRAIN / n) for n in names},
             'wall_time_s': time.perf_counter() - started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
             'train_only': True, 'baseline_reproduced': True, 'poisoned_gt_inference_invariant': True,
             'environment': {'python': sys.version, 'platform': platform.platform(), 'numpy': np.__version__, 'scipy': scipy.__version__}}
    audit.json_write(HERE / f'results/{family}_experiment.json', value)
    summary = pd.DataFrame([{'model': m, 'split': s, **v} for m, parts in summaries.items() for s, v in parts.items()])
    fig, axes = audit.plt.subplots(1, 3, figsize=(13, 4))
    for ax, metric in zip(axes, ('average_mape', 'macro_f1', 'false_voiced_sil')):
        for model in ('accepted', 'candidate'):
            part = table[(table.split == 'nested') & (table.model == model)]
            ax.plot(part.file.str.replace('.wav', '', regex=False), part[metric], 'o-', label=model)
        ax.set(title=metric)
        ax.tick_params(axis='x', rotation=30)
    axes[0].legend(fontsize=8)
    audit.save_figure(f'{family}_nested', fig, [p_metrics], 'Kết quả từng outer file; lựa chọn chỉ dùng các file train còn lại.', 'Chỉ bốn file; MAPE là thống kê cả file trên lưới chấm chung, không xác minh F0 từng thời điểm.')
    for figure in audit.ARTIFACTS:
        figure.update(generator='zcr_logistic.py', generator_sha256=audit.digest(__file__), command=f'python research_workbench_2026_10_07/zcr_logistic.py {family}')
    audit.json_write(HERE / f'results/{family}_figure_manifest.json', {'figures': audit.ARTIFACTS})
    report = ['# ' + family + ' — thêm ZCR vào logistic', '', audit.markdown_table(summary), '',
              '## Tiêu chí đã đăng ký', '', '~~~json', json.dumps(decision, indent=2), '~~~', '',
              '## Lựa chọn theo fold', '', audit.markdown_table(pd.DataFrame([{'outer_held': x['outer_held'], **x['option']} for x in selections])), '',
              'Giữ champion; các kết quả không đạt cũng được lưu. Selected LOFO có ảnh hưởng lựa chọn, đọc nested để đánh giá quy trình. Registry được đề xuất sau lịch sử đã xem bốn file nên nested vẫn là thăm dò.', '',
              'Giữ frame25/hop10 và raw ACF. ZCR là số lần đổi dấu sau trừ mean khung chia thời lượng giữa các mẫu (crossings/s), không là F0. Registry gồm accepted, logistic2D C1 và logistic3D C1+ZCR; không tune C hoặc thêm filter trong vòng này.', '',
              'StandardScaler/coefficients/class weights chỉ fit subset train. Tỉ lệ class/file, C1, threshold0.5, energy gate, path và median giống control2D. Mọi khung nhãn V/UV dùng để fit; SIL không là negative training class ở thiết kế này. ZCR normalization theo fs tránh dùng fraction phụ thuộc sampling rate làm cùng đơn vị giữa phone/studio.', '',
              f'![Nested](figures/{family}_nested.png)', '',
              'Lệnh: `python research_workbench_2026_10_07/zcr_logistic.py ' + family + '`', '',
              'Nguồn API: [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html). H22_REGISTRATION.md xác định câu hỏi, controls và giới hạn trước đo.']
    (HERE / f'{family}_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps(decision, indent=2), flush=True)
    print(summary[['model', 'split', 'average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil']].to_string(index=False), flush=True)


def fixed_controls(names, options, score):
    rows = []
    for option in options:
        for held in names:
            metrics = score(option, [n for n in names if n != held], held)[0]
            rows.append({'option_id': option['id'], **metrics})
    table = pd.DataFrame(rows)
    source = audit.csv_write('H22_fixed_lofo_metrics.csv', table)
    control = table[table.option_id == 'raw_lr1_2d'].sort_values('file')
    earlier = pd.read_csv(REPO / 'research_workbench_2026_10_06/results/logistic_voicing_metrics.csv')
    earlier = earlier[(earlier.model == 'candidate') & (earlier.split == 'lofo')].sort_values('file')
    for key in ('average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil'):
        assert np.allclose(control[key], earlier[key], atol=1e-8), key
    summary = pd.DataFrame([{'option_id': opt['id'], **core.summarize(table[table.option_id == opt['id']])} for opt in options])
    audit.csv_write('H22_fixed_lofo_summary.csv', summary)
    fig, axes = audit.plt.subplots(1, 3, figsize=(13, 4))
    for ax, metric in zip(axes, ('average_mape', 'macro_f1', 'recall_v')):
        for option in options:
            part = table[table.option_id == option['id']]
            ax.plot(part.file.str.replace('.wav', '', regex=False), part[metric], 'o-', label=option['id'])
        ax.set(title=metric)
        ax.tick_params(axis='x', rotation=30)
    axes[0].legend(fontsize=7)
    audit.save_figure('H22_fixed_feature_control', fig, [source], 'Fixed LOFO3D so2D: chỉ thêm ZCR, giữ C1 và cách fit/score.', 'Bốn file đã xem nhiều lần; không phải held-out corpus mới. Không dùng fixed-control scores để mở grid sau đo.')
    print('Fixed controls (2D reproduced H16):', flush=True)
    print(summary[['option_id','average_mape','macro_f1','recall_v','false_voiced_sil']].to_string(index=False), flush=True)


def check():
    frames = np.array([[1.,-1.,1.,-1.], [0.,0.,0.,0.], [-1.,-1.,1.,1.]])
    assert np.allclose(zero_crossing_rate(frames, 12), [12.,0.,4.])
    assert np.allclose(zero_crossing_rate(frames*.1+7, 12), zero_crossing_rate(frames,12))
    items = core.load_training()
    option = registry('H22')[0]
    for item in items:
        _, audio = core.load_audio(core.TRAIN / item['file'])
        native = extract(item, audio, option)
        for name in ('times','rms','relative_rms','ACF_score','ACF_lag','ACF_candidate_f0','ACF_candidate_strength'):
            assert np.allclose(native[name], item[name], atol=1e-10, equal_nan=True), (item['file'],name)
        assert np.isfinite(native['zcr']).all() and ((native['zcr']>=0)&(native['zcr']<=item['fs'])).all()
    print('PASS: ZCR known crossings/DC/gain and raw baseline feature identity on all 4 train files.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register','check','H22'])
    action = parser.parse_args().action
    if action == 'register':
        path=HERE/'H22_REGISTRY.json'
        assert not path.exists(), 'Do not overwrite registered registry'
        audit.json_write(path, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                               'baseline_commit':'009fd2c','rollback_repository_commit':'dc87b79',
                               'family':'H22','options':registry('H22')})
    elif action == 'check':
        check()
    else:
        run('H22')
