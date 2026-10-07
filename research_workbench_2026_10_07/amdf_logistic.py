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
import sklearn
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from estimator_experiment import eligibility

audit.HERE = HERE
audit.RESULTS = HERE / 'results'
audit.FIGURES = HERE / 'figures'
audit.RESULTS.mkdir(exist_ok=True)
audit.FIGURES.mkdir(exist_ok=True)


CLASSIFIERS = {}


def registry(family):
    assert family == 'H25'
    return [{'id': 'amdf_control' if c is None else f'amdf_lr{c:g}',
             'frame_ms': 25, 'hop_ms': 10, 'pitch_frame_ms': 40, 'C': c}
            for c in (None, .1, 1., 10.)]


def feature_key(option):
    return 'amdf_control'


def long_candidates(frame, fs):
    dip, _, refined, lag_grid, curve = core.AMDF['deepest_local_dip'](frame, fs)
    peaks = np.where((curve[1:-1] <= curve[:-2]) & (curve[1:-1] <= curve[2:]))[0] + 1
    values = 1 - curve[peaks]
    lags = np.array([core.refine_lag(curve, i, float(lag_grid[i])) for i in peaks])
    if not len(peaks):
        lags, values = np.array([refined]), np.array([1-dip])
    f0 = fs/lags
    valid = np.isfinite(f0) & (f0>=70) & (f0<=400)
    f0, values = f0[valid], values[valid]
    order = np.argsort(values)[::-1][:12]
    frequencies, strengths = np.full(12,np.nan), np.full(12,-np.inf)
    frequencies[:len(order)], strengths[:len(order)] = f0[order], values[order]
    return frequencies, strengths


def extract(item, audio, option):
    if option['pitch_frame_ms'] == 25:
        return item
    core.init_functions()
    fs = item['fs']
    length = round(fs*option['pitch_frame_ms']/1000)
    frequency = item['AMDF_candidate_f0'].copy()
    strength = item['AMDF_candidate_strength'].copy()
    fallback = np.zeros(len(item['times']), dtype=bool)
    for i, center in enumerate(item['times']):
        start = round(center*fs - length/2)
        if start<0 or start+length>len(audio):
            fallback[i] = True
        else:
            frequency[i], strength[i] = long_candidates(audio[start:start+length],fs)
    return dict(item, preprocess='amdf_control', AMDF_candidate_f0=frequency,
                AMDF_candidate_strength=strength, long_window_fallback=fallback)


def project(native, canonical, pred, f0, hop_ms):
    times = native['times']
    right = np.minimum(np.searchsorted(times, canonical['times']), len(times) - 1)
    left = np.maximum(right - 1, 0)
    choose_left = abs(times[left] - canonical['times']) <= abs(times[right] - canonical['times'])
    indices = np.where(choose_left, left, right)
    support = abs(times[indices] - canonical['times']) <= hop_ms / 2000 + 1 / native['fs']
    return pred[indices] & support, np.where(support, f0[indices], np.nan), support


def design(item):
    return np.column_stack([item['AMDF_score'], item['relative_rms']])


def fit_logistic(items, c):
    key = (c, tuple(sorted(x['file'] for x in items)))
    if key in CLASSIFIERS:
        return CLASSIFIERS[key]
    total = sum(np.isin(x['labels'], ['v','uv']).sum() for x in items)
    xx, yy, ww = [], [], []
    for item in items:
        mask = np.isin(item['labels'], ['v','uv'])
        y = (item['labels'][mask]=='v').astype(int)
        w = np.array([total/(2*len(items)*max((y==v).sum(),1)) for v in y])
        xx.append(design(item)[mask]); yy.append(y); ww.append(w)
    x,y,w = np.vstack(xx), np.concatenate(yy), np.concatenate(ww)
    scaler = StandardScaler().fit(x,sample_weight=w)
    model = LogisticRegression(C=c,max_iter=500).fit(scaler.transform(x),y,sample_weight=w)
    assert model.n_iter_[0]<500
    assert np.allclose(expit(scaler.transform(x)@model.coef_[0]+model.intercept_[0]),
                       model.predict_proba(scaler.transform(x))[:,1],atol=1e-12)
    value = {'feature_names':['AMDF_score','relative_rms'], 'fit_files':sorted(i['file'] for i in items),
             'C':c, 'mean':scaler.mean_.tolist(), 'scale':scaler.scale_.tolist(),
             'coefficient':model.coef_[0].tolist(), 'intercept':float(model.intercept_[0])}
    CLASSIFIERS[key]=value
    return value


def infer(native, training, option, config):
    fitted = core.fit(training,config)
    if option['C'] is None:
        return (*core.infer(native,config,fitted),fitted,None)
    classifier = fit_logistic(training,option['C'])
    x = design(native)
    score = expit(((x-classifier['mean'])/classifier['scale'])@np.array(classifier['coefficient'])+classifier['intercept'])
    mask = (score>=.5)&(native['relative_rms']>=fitted['energy_threshold'])
    adapted = dict(native,AMDF_score=np.where(mask,0.,1.))
    pred,f0 = core.infer(adapted,config,dict(fitted,pitch_threshold=.5))
    assert np.array_equal(pred,mask)
    return pred,f0,fitted,classifier


def run(family):
    assert not (HERE / f'results/{family}_experiment.json').exists(), 'Preserve completed experiment'
    started = time.perf_counter()
    options = json.loads((HERE / f'{family}_REGISTRY.json').read_text(encoding='utf-8'))['options']
    assert options == registry(family)
    items = core.load_training()
    by_name = {x['file']: x for x in items}
    names = sorted(by_name)
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['AMDF_energy']['config']
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
                           projection_coverage=float(support.mean()), effective_median_span_ms=(config.get('median', 1) - 1) * option['hop_ms'])
            prediction_cache[key] = (metrics, pp, ff, support)
            fit_log.append({'option_id': option['id'], 'fit_files': sorted(fit_names), 'held_file': held,
                            'fitted': fitted, 'classifier': classifier})
        return prediction_cache[key]

    baseline = next(x for x in options if x['id'] == 'amdf_control')
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
            candidates.append((not valid, float(table.average_mape.max()) if valid else math.inf, summary['average_mape'] if valid else math.inf, option['id'], option))
        selected = min(candidates, key=lambda v: v[:4])[4]
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
    saved = core.summarize(pd.read_csv(HERE/'results/H24_fixed_lofo.csv').query("option_id == 'amdf_gate25_pitch40'"))
    actual_base = core.summarize(base_metrics)
    for metric in ('average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil'):
        assert np.isclose(actual_base[metric], saved[metric], atol=1e-8), metric
    audit.csv_write('H25_fixed_lofo.csv', [{'option_id': option['id'], **score(option, [n for n in names if n != held], held)[0]}
                                                for option in options for held in names])
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
             'long_window_fallback_counts': {key[1]: int(value.get('long_window_fallback', np.zeros(1)).sum()) for key, value in features.items() if key[0] == 'amdf_control'},
             'registry_sha256': audit.digest(HERE / f'{family}_REGISTRY.json'),
             'code_sha256': {str(p.relative_to(REPO)): audit.digest(p) for p in (Path(__file__), Path(core.__file__), Path(audit.__file__), core.BASELINES / 'AMDF.ipynb', core.RESULTS / 'frozen_config.json', REPO / 'research_workbench_2026_10_06/estimator_experiment.py')},
             'data_sha256': {n: audit.digest(core.TRAIN / n) for n in names},
             'wall_time_s': time.perf_counter() - started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
             'selection_objective': 'minimize worst-file Average MAPE, then mean, then id', 'goal_all_nested_files_le_2': bool((table[(table.split=='nested')&(table.model=='candidate')].average_mape<=2).all()), 'train_only': True, 'baseline_reproduced': True, 'poisoned_gt_inference_invariant': True,
             'environment': {'python': sys.version, 'platform': platform.platform(), 'numpy': np.__version__, 'scipy': scipy.__version__, 'sklearn': sklearn.__version__}}
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
        figure.update(generator='amdf_logistic.py', generator_sha256=audit.digest(__file__), command=f'python research_workbench_2026_10_07/amdf_logistic.py {family}')
    audit.json_write(HERE / f'results/{family}_figure_manifest.json', {'figures': audit.ARTIFACTS})
    report = ['# H25 — Logistic Regression cho quyết định V/UV AMDF', '', audit.markdown_table(summary), '',
              'Mục tiêu người dùng: từng file Average MAPE <=2%. Inner rank worst-file, sau đó mean và ID. Nested vẫn thăm dò vì registry được định hướng sau lịch sử bốn file.', '',
              'Control cố định H24 gate25/pitch40; không phải selection nested H24. Chỉ thay classifier, C0.1/1/10; giữ energy gate, pathjump.35, median1, range70–400, cùng candidates40ms và fallback25. Không ZCR/filter/range/median tuning.', '',
              'Fit scaler/LR chỉ V/UV các file fit, trọng số cân bằng file và class; SIL xử lý bằng energy gate fit từ pool đó. Threshold probability0.5 chốt trước chạy. Không dùng countGT của held để chỉnh output.', '',
              '## Gate đăng ký', '', '~~~json',json.dumps(decision,indent=2),'~~~', '',
              '## Lựa chọn', '',audit.markdown_table(pd.DataFrame([{'outer_held':x['outer_held'],**x['option']} for x in selections])), '',
              '## Metric từng file', '',audit.markdown_table(table[['split','model','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','recall_v','false_voiced_sil']]), '',
              'Chưa auto-promote; không sửa frozen_config gốc. GT chỉ thống kê file và loại đoạn, không F0 từng khung.', '',
              '![Nested](figures/H25_nested.png)', '', 'Lệnh: python research_workbench_2026_10_07/amdf_logistic.py H25']
    (HERE / f'{family}_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps(decision, indent=2), flush=True)
    print(summary[['model', 'split', 'average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil']].to_string(index=False), flush=True)


def check():
    import amdf_dual_window
    amdf_dual_window.check()
    items=core.load_training()
    config=json.loads((core.RESULTS/'frozen_config.json').read_text())['models']['AMDF_energy']['config']
    featured=[]
    option=registry('H25')[0]
    for item in items:
        _,audio=core.load_audio(core.TRAIN/item['file'])
        featured.append(extract(item,audio,option))
    rows=[]
    for held in featured:
        train=[x for x in featured if x['file']!=held['file']]
        pred,f0,_,_=infer(held,train,option,config)
        rows.append(core.score_file(held,pred,f0))
    new=pd.DataFrame(rows).sort_values('file')
    old=pd.read_csv(HERE/'results/H24_fixed_lofo.csv').query("option_id == 'amdf_gate25_pitch40'").sort_values('file')
    columns=['F0mean','F0std','F0num','average_mape','macro_f1','false_voiced_sil']
    assert np.allclose(new[columns],old[columns],atol=1e-8)
    print('PASS: fixed H24 control reproduced before H25 measurements.',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'check', 'H25'])
    action = parser.parse_args().action
    if action == 'register':
        path = HERE / 'H25_REGISTRY.json'
        assert not path.exists(), 'Do not overwrite registered registry'
        audit.json_write(path, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                               'baseline_commit': '9456632', 'original_baseline_commit':'009fd2c', 'rollback_repository_commit': '9456632',
                               'family': 'H25', 'algorithm': 'AMDF', 'options': registry('H25')})
    elif action == 'check':
        check()
    else:
        run('H25')
