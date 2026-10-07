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
from estimator_experiment import eligibility

audit.HERE = HERE
audit.RESULTS = HERE / 'results'
audit.FIGURES = HERE / 'figures'
audit.RESULTS.mkdir(exist_ok=True)
audit.FIGURES.mkdir(exist_ok=True)


def registry(family):
    assert family == 'H21'
    return [{'id': 'raw_0_0_f25_h10' if ratio == 0 else f'center_{ratio:g}_f25_h10',
             'kind': 'raw', 'low_hz': 0, 'high_hz': 0, 'frame_ms': 25, 'hop_ms': 10,
             'C': None, 'center_ratio': ratio} for ratio in (0., .3, .5)]


def center_clip(frame, ratio):
    if ratio == 0:
        return frame.copy()
    level = ratio * np.max(np.abs(frame))
    return np.sign(frame) * np.maximum(np.abs(frame) - level, 0.)


def feature_key(option):
    return f"center_{option['center_ratio']:g}_f25_h10"


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
    for raw_frame in frames:
        frame = center_clip(raw_frame, option['center_ratio'])
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
                rms=rms, relative_rms=rms / max(np.quantile(rms, .95), core.EPS),
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


def infer(native, training, option, config):
    fitted = core.fit(training, config)
    return (*core.infer(native, config, fitted), fitted, None)


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
    feature_diagnostics(items, options)
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
        figure.update(generator='center_clipping.py', generator_sha256=audit.digest(__file__), command=f'python research_workbench_2026_10_07/center_clipping.py {family}')
    audit.json_write(HERE / f'results/{family}_figure_manifest.json', {'figures': audit.ARTIFACTS})
    report = ['# ' + family + ' — center clipping có vòng chọn bên trong', '', audit.markdown_table(summary), '',
              '## Tiêu chí đã đăng ký', '', '~~~json', json.dumps(decision, indent=2), '~~~', '',
              '## Lựa chọn theo fold', '', audit.markdown_table(pd.DataFrame([{'outer_held': x['outer_held'], **x['option']} for x in selections])), '',
              'Giữ champion; các kết quả không đạt cũng được lưu. Selected LOFO có ảnh hưởng lựa chọn, đọc nested để đánh giá quy trình. Registry được đề xuất sau lịch sử đã xem bốn file nên nested vẫn là thăm dò.', '',
              'Vòng này giữ frame25/hop10 để cô lập center clipping; H18/H19 trước đã cho phép thay geometry. Grid native trùng grid chấm, không thêm/cắt F0 để khớp GT. GT chỉ thống kê cả file và nhãn đoạn; không có pitch reference từng khung.', '',
              'Center clipping đối xứng y=sign(x) max(abs(x)-r max(abs(frame)),0), trước mean-removal/Hamming của ACF hiện có. r thuộc0/.3/.5, threshold học lại trong fold. RMS luôn từ raw. Đây không phải hard clipping cắt đỉnh của H20; không giả định tự loại được brown noise. Giữ path/median/range/energy rule.', '',
              f'![Nested](figures/{family}_nested.png)', '',
              'Lệnh: `python research_workbench_2026_10_07/center_clipping.py ' + family + '`', '',
              'Tham khảo cơ chế: [Columbia autocorrelation demonstration](https://www.ee.columbia.edu/~dpwe/classes/e6820-2001-01/matlab/MAD/auto/auto.htm). Hàm đối xứng và thứ tự xử lý cụ thể đã đăng ký tại H21_REGISTRATION.md; không tuyên bố sao chép trọn pipeline Sondhi.']
    (HERE / f'{family}_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps(decision, indent=2), flush=True)
    print(summary[['model', 'split', 'average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil']].to_string(index=False), flush=True)


def feature_diagnostics(items, options):
    rows = []
    for item in items:
        _, audio = core.load_audio(core.TRAIN / item['file'])
        length, hop = round(item['fs'] * .025), round(item['fs'] * .010)
        frames = np.lib.stride_tricks.sliding_window_view(audio, length)[::hop]
        for option in options:
            for i, frame in enumerate(frames):
                transformed = center_clip(frame, option['center_ratio'])
                rows.append({'file': item['file'], 'time_s': item['times'][i],
                             'label': item['labels'][i], 'ratio': option['center_ratio'],
                             'zero_fraction': float(np.mean(transformed == 0)),
                             'energy_retained': float(np.sum(transformed**2) / max(np.sum(frame**2), core.EPS))})
    source = audit.csv_write('H21_center_features.csv', rows)
    data = pd.DataFrame(rows)
    fig, axes = audit.plt.subplots(1, 2, figsize=(11, 4))
    for label in ('v', 'uv', 'sil'):
        part = data[data.label == label].groupby(['ratio', 'file']).agg(
            zero_fraction=('zero_fraction', 'mean'), energy_retained=('energy_retained', 'mean')).groupby('ratio').mean()
        for ax, metric in zip(axes, ('zero_fraction', 'energy_retained')):
            ax.plot(part.index, part[metric], 'o-', label=label)
            ax.set(xlabel='Center clipping ratio', ylabel=metric)
    axes[0].legend()
    audit.save_figure('H21_center_effect', fig, [source], 'Biên độ nhỏ bị đưa về0; năng lượng giữ lại theo nhãn, trung bình trong file rồi qua file.', 'Chẩn đoán train gộp; không chứng minh khả năng phân lớp hoặc hiệu quả với noise.')
    item = next(x for x in items if x['file'] == 'phone_F1.wav')
    _, audio = core.load_audio(core.TRAIN / item['file'])
    length, hop = round(item['fs'] * .025), round(item['fs'] * .010)
    mask = (item['labels'] == 'v') & ~item['boundary']
    i = np.flatnonzero(mask)[np.argmax(item['rms'][mask])]
    frame = audio[i*hop:i*hop+length]
    waveform = pd.DataFrame({'time_ms': np.arange(length)*1000/item['fs'], 'raw': frame,
                             'center_03': center_clip(frame, .3), 'center_05': center_clip(frame, .5),
                             'hard_025': np.clip(frame, -.25*np.max(abs(frame)), .25*np.max(abs(frame)))})
    source = audit.csv_write('H21_transform_waveform.csv', waveform)
    fig, axes = audit.plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    for column in ('raw', 'center_03', 'center_05'):
        axes[0].plot(waveform.time_ms, waveform[column], label=column)
    for column in ('raw', 'hard_025'):
        axes[1].plot(waveform.time_ms, waveform[column], label=column)
    for ax in axes:
        ax.legend(loc='upper right'); ax.set(ylabel='Amplitude')
    axes[1].set(xlabel='Time within frame (ms)')
    audit.save_figure('H21_transform_waveform', fig, [source], f'phone_F1: raw V-frame nội bộ có RMS lớn nhất, center={item["times"][i]:.4f}s; không chọn theo điểm thuật toán.', 'Hình so cơ chế, không là pitch ground truth; hard025 chỉ minh họa, không ứng viên H21.')


def check():
    frame = np.array([-2., -1., -.5, 0., .5, 1., 2.])
    assert np.array_equal(center_clip(frame, 0), frame)
    assert np.array_equal(center_clip(frame, .5), np.array([-1., 0., 0., 0., 0., 0., 1.]))
    for ratio in (.3, .5):
        assert np.array_equal(center_clip(-frame, ratio), -center_clip(frame, ratio))
        assert np.allclose(center_clip(frame*.031, ratio), center_clip(frame, ratio)*.031)
        assert np.array_equal(center_clip(np.zeros(400), ratio), np.zeros(400))
    items = core.load_training()
    option = registry('H21')[0]
    for item in items:
        _, audio = core.load_audio(core.TRAIN / item['file'])
        native = extract(item, audio, option)
        for name in ('times', 'rms', 'relative_rms', 'ACF_score', 'ACF_lag', 'ACF_candidate_f0', 'ACF_candidate_strength'):
            assert np.allclose(native[name], item[name], atol=1e-10, equal_nan=True), (item['file'], name)
    print('PASS: center clipping formula, sign/gain/zero invariants and raw ACF feature identity on all 4 train files.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'check', 'H21'])
    action = parser.parse_args().action
    if action == 'register':
        path = HERE / 'H21_REGISTRY.json'
        assert not path.exists(), 'Do not overwrite registered registry'
        audit.json_write(path, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                               'baseline_commit': '009fd2c', 'rollback_repository_commit': '35ba151',
                               'family': 'H21', 'options': registry('H21')})
    elif action == 'check':
        check()
    else:
        run('H21')
