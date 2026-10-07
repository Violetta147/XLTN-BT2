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
import praat_native_adapter as native_api
from estimator_experiment import eligibility

audit.HERE = HERE
audit.RESULTS = HERE / 'results'
audit.FIGURES = HERE / 'figures'
audit.RESULTS.mkdir(exist_ok=True)
audit.FIGURES.mkdir(exist_ok=True)



def registry(family):
    assert family=='H31'
    return [{'id':f'praat7_filtered_v{threshold:g}','frame_ms':3000/70,'hop_ms':10,'pitch_frame_ms':3000/70,
             'method':'filtered','voicing_threshold':threshold} for threshold in (.25,.30,.35,.40,.45)]


def feature_key(option):
    return option['id']


def extract(item,audio,option):
    if option['method']=='control':
        import amdf_dual_window
        return amdf_dual_window.extract(item,audio,dict(option,pitch_frame_ms=40))
    times,frequency,log=native_api.pitch(core.TRAIN/item['file'],option['method'],option['voicing_threshold'])
    pred=(frequency>=70)&(frequency<=400)
    return dict(item,times=times,preprocess=option['id'],native_pred=pred,native_f0=np.where(pred,frequency,np.nan),
                raw_native_frequency=frequency,native_call=log,range_rejected_frames=int(((frequency>0)&~pred).sum()))


def project(native, canonical, pred, f0, hop_ms):
    times = native['times']
    right = np.minimum(np.searchsorted(times, canonical['times']), len(times) - 1)
    left = np.maximum(right - 1, 0)
    choose_left = abs(times[left] - canonical['times']) <= abs(times[right] - canonical['times'])
    indices = np.where(choose_left, left, right)
    support = abs(times[indices] - canonical['times']) <= hop_ms / 2000 + 1 / native['fs']
    return pred[indices] & support, np.where(support, f0[indices], np.nan), support


def infer(native, training, option, config):
    if option['method']!='control':
        return (native['native_pred'].copy(),native['native_f0'].copy(),
                {'requires_fit':False,'actual_fit_files':[],'method':'Praat 7.0.02 '+option['method'],'voicing_threshold':option['voicing_threshold']},None)
    fitted=core.fit(training,config)
    return (*core.infer(native,config,fitted),fitted,None)


def run(family):
    assert not (HERE / f'results/{family}_experiment.json').exists(), 'Preserve completed experiment'
    started = time.perf_counter()
    native_proof=native_api.metadata()
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
    native_rows=[]
    for (identity,file),value in features.items():
        if 'raw_native_frequency' in value:
            native_rows += [{'option_id':identity,'file':file,'time_s':float(t),'raw_f0_hz':float(f)}
                            for t,f in zip(value['times'],value['raw_native_frequency'])]
    audit.csv_write('H31_raw_native_frames.csv',native_rows)
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

    baseline = next(x for x in options if x['id'] == 'praat7_filtered_v0.45')
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
    saved = core.summarize(pd.read_csv(HERE/'results/H30_fixed_lofo.csv').query("option_id == 'praat7_filtered_v0.45'"))
    actual_base = core.summarize(base_metrics)
    for metric in ('average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil'):
        assert np.isclose(actual_base[metric], saved[metric], atol=1e-8), metric
    audit.csv_write('H31_fixed_lofo.csv', [{'option_id': option['id'], **score(option, [n for n in names if n != held], held)[0]}
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
             'native_calls': {key[0]+'|'+key[1]:value['native_call'] for key,value in features.items() if 'native_call' in value},
             'range_rejected_frames': {key[0]+'|'+key[1]:value['range_rejected_frames'] for key,value in features.items() if 'range_rejected_frames' in value},
             'long_window_fallback_counts': {key[1]: int(value.get('long_window_fallback', np.zeros(1)).sum()) for key, value in features.items() if key[0] == 'amdf_control'},
             'registry_sha256': audit.digest(HERE / f'{family}_REGISTRY.json'),
             'code_sha256': {str(p.relative_to(REPO)): audit.digest(p) for p in (Path(__file__), HERE / 'amdf_dual_window.py', HERE / 'praat_native_adapter.py', HERE / 'praat_extract_native.praat', HERE / 'results/praat_native_7002_provenance.json', HERE / 'results/praat_native_command_source.json', Path(core.__file__), Path(audit.__file__), core.BASELINES / 'AMDF.ipynb', core.RESULTS / 'frozen_config.json', REPO / 'research_workbench_2026_10_06/estimator_experiment.py')},
             'data_sha256': {n: audit.digest(core.TRAIN / n) for n in names},
             'wall_time_s': time.perf_counter() - started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
             'selection_objective': 'minimize worst-file Average MAPE, then mean, then id', 'goal_all_nested_files_le_2': bool((table[(table.split=='nested')&(table.model=='candidate')].average_mape<=2).all()), 'train_only': True, 'baseline_reproduced': True, 'poisoned_gt_inference_invariant': True,
             'environment': {'python': sys.version, 'platform': platform.platform(), 'numpy': np.__version__, 'scipy': scipy.__version__, 'sklearn': sklearn.__version__, 'praat':native_proof['version_stdout'], 'native_exe_sha256':native_proof['exe_sha256']}}
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
        figure.update(generator='praat_voicing_threshold.py', generator_sha256=audit.digest(__file__), command=f'python research_workbench_2026_10_07/praat_voicing_threshold.py {family}')
    audit.json_write(HERE / f'results/{family}_figure_manifest.json', {'figures': audit.ARTIFACTS})
    fixed=pd.read_csv(HERE/'results/H31_fixed_lofo.csv')
    report=['# H31 — ngưỡng hữu thanh của Praat filtered', '',audit.markdown_table(summary), '',
      'Một tham số được thay: voicing threshold .25/.30/.35/.40/.45. Control H30 native filtered.45. Giữ Praat7.0.02, floor70/top800/attenuation.03, silence.09, octave.055, jump.35,VUV.14, max15, veryaccuratefalse, step10ms và range output70–400. Không thêm gate/filter/median/noise hoặc đổi window/range/metric.', '',
      'Top800 là giới hạn candidate và điểm Gaussian attenuation; native selectedF0 ngoài output range70–400 nhậnUV/NaN. Lưu raw native frames và số range rejected. Ghép nearest native center vào canonical25/10 trong halfhop+một mẫu, hòa sớm hơn, không padding/fallback/GT-count trim. Praat không fit; inner chọn worst-file MAPE rồi mean/ID. Outer held không chọn cấu hình. Nested exploratory vì lịch sử nghiên cứu bốn file.', '',
      'Baseline thí nghiệm này là H30 fixed0.45 đã qua8gate, không ghi đè originalAMDF/frozen_config. Native calls/binary/script/adapter/source/WAV hashes được giữ; probe đã qua trước đo.', '',
      '## Gate', '', '~~~json',json.dumps(decision,indent=2),'~~~', '',
      '## Selections', '',audit.markdown_table(pd.DataFrame([{'outer_held':x['outer_held'],**x['option']} for x in selections])), '',
      '## Mọi cấu hình fixed LOFO', '',audit.markdown_table(fixed[['option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','macro_f1','recall_v','false_voiced_sil']]), '',
      '## Nested per file', '',audit.markdown_table(table[(table.split=='nested')][['model','file','average_mape','F0std_mape','F0num_mape','recall_v','false_voiced_sil','projection_coverage']]), '',
      'Mục tiêu mỗi file Average MAPE≤2% báo riêng. Không auto-promote; chỉ local train, không test/Drive/deep learning/PDF extraction. LAB chưa có F0 chuẩn từng khung.', '',
      '![Nested](figures/H31_nested.png)', '',
      'Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/praat_voicing_threshold.py H31']
    (HERE / f'{family}_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps(decision, indent=2), flush=True)
    print(summary[['model', 'split', 'average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil']].to_string(index=False), flush=True)


def check():
    import amdf_dual_window
    amdf_dual_window.check()
    proof=native_api.metadata()
    probe=json.loads((HERE/'results/praat_native_synthetic_probe.json').read_text())
    assert probe['adapter_sha256']==audit.digest(HERE/'praat_native_adapter.py')
    assert probe['script_sha256']==audit.digest(HERE/'praat_extract_native.praat')
    assert len(probe['rows'])==8 and all(x['call']['returncode']==0 for x in probe['rows'])
    assert proof['version_stdout']=='7.0.02'
    print('PASS original AMDF parity/native7 binary and eight synthetic probes; no new H31 threshold benchmark measured by check; H30 preserved.',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'check', 'H31'])
    action = parser.parse_args().action
    if action == 'register':
        path = HERE / 'H31_REGISTRY.json'
        assert not path.exists(), 'Do not overwrite registered registry'
        audit.json_write(path, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                               'baseline_commit': '7432dd6', 'original_baseline_commit':'009fd2c', 'rollback_repository_commit': '7432dd6',
                               'family': 'H31', 'algorithm': 'Praat7 filtered voicing threshold', 'options': registry('H31')})
    elif action == 'check':
        check()
    else:
        run('H31')
