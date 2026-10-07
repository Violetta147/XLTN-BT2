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
import sptk_adapter as sptk_api
from estimator_experiment import eligibility

audit.HERE = HERE
audit.RESULTS = HERE / 'results'
audit.FIGURES = HERE / 'figures'
audit.RESULTS.mkdir(exist_ok=True)
audit.FIGURES.mkdir(exist_ok=True)



def registry(family):
    assert family=='H35'
    return [{'id':'praat7_filtered_v0.3','frame_ms':3000/70,'hop_ms':10,'pitch_frame_ms':3000/70,
             'method':'control','voicing_threshold':.3}]+[
        {'id':f'praat_gate_swipe_t{threshold:g}','frame_ms':3000/70,'hop_ms':10,'pitch_frame_ms':None,
         'method':'hybrid','voicing_threshold':threshold,'gate_voicing_threshold':.3}
        for threshold in (.2,.3)]


SOURCE_CACHE = {}


def fuse(gate_times,gate_frequency,swipe_times,swipe_frequency,fs):
    right=np.minimum(np.searchsorted(swipe_times,gate_times),len(swipe_times)-1)
    left=np.maximum(right-1,0)
    indices=np.where(abs(swipe_times[left]-gate_times)<=abs(swipe_times[right]-gate_times),left,right)
    support=abs(swipe_times[indices]-gate_times)<=.005+1/fs
    gate=(gate_frequency>=70)&(gate_frequency<=400)
    available=support&(swipe_frequency[indices]>=70)&(swipe_frequency[indices]<=400)
    use=gate&available
    frequency=np.where(gate,np.where(use,swipe_frequency[indices],gate_frequency),0.)
    source=np.where(~gate,'unvoiced',np.where(use,'swipe','praat_fallback'))
    return frequency,use,source,indices,support


def feature_key(option):
    return option['id']


def extract(item,audio,option):
    gate_key=('praat7_filtered_v0.3',item['file'])
    if gate_key not in SOURCE_CACHE:
        SOURCE_CACHE[gate_key]=native_api.pitch(core.TRAIN/item['file'],'filtered',.3)
    times,gate_frequency,gate_log=SOURCE_CACHE[gate_key]
    if option['method']=='control':
        frequency=gate_frequency.copy()
        source=np.full(len(times),'praat_control')
    else:
        swipe_key=(f"swipe_t{option['voicing_threshold']:g}",item['file'])
        if swipe_key not in SOURCE_CACHE:
            SOURCE_CACHE[swipe_key]=sptk_api.pitch(audio,item['fs'],'swipe',option['voicing_threshold'])
        st,sf,_=SOURCE_CACHE[swipe_key]
        frequency,_,source,_,_=fuse(times,gate_frequency,st,sf,item['fs'])
    pred=(frequency>=70)&(frequency<=400)
    return dict(item,times=times,preprocess=option['id'],native_pred=pred,native_f0=np.where(pred,frequency,np.nan),
                raw_native_frequency=frequency,raw_native_voiced=frequency>0,hybrid_source=source,
                range_rejected_frames=int(((frequency>0)&~pred).sum()))


def project(native, canonical, pred, f0, hop_ms):
    times = native['times']
    right = np.minimum(np.searchsorted(times, canonical['times']), len(times) - 1)
    left = np.maximum(right - 1, 0)
    choose_left = abs(times[left] - canonical['times']) <= abs(times[right] - canonical['times'])
    indices = np.where(choose_left, left, right)
    support = abs(times[indices] - canonical['times']) <= hop_ms / 2000 + 1 / native['fs']
    return pred[indices] & support, np.where(support, f0[indices], np.nan), support


def infer(native, training, option, config):
    return native['native_pred'].copy(),native['native_f0'].copy(),{
        'requires_fit':False,'actual_fit_files':[],'method':option['method']},None


def run(family):
    assert not (HERE / f'results/{family}_experiment.json').exists(), 'Preserve completed experiment'
    SOURCE_CACHE.clear()
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
            native_rows += [{'option_id':identity,'file':file,'time_s':float(t),'raw_f0_hz':float(f),'raw_voiced':bool(v),'hybrid_source':str(src)}
                            for t,f,v,src in zip(value['times'],value['raw_native_frequency'],value['raw_native_voiced'],value['hybrid_source'])]
    audit.csv_write('H35_raw_native_frames.csv',native_rows)
    audit.csv_write('H35_source_native_frames.csv',[{'source_id':identity,'file':file,'time_s':float(t),'raw_f0_hz':float(f)} for (identity,file),(times,frequency,log) in SOURCE_CACHE.items() for t,f in zip(times,frequency)])
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
                           projection_coverage=float(support.mean()), effective_median_span_ms=0)
            prediction_cache[key] = (metrics, pp, ff, support)
            fit_log.append({'option_id': option['id'], 'fit_files': sorted(fit_names), 'held_file': held,
                            'fitted': fitted, 'classifier': classifier})
        return prediction_cache[key]

    baseline = next(x for x in options if x['id'] == 'praat7_filtered_v0.3')
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
    saved = core.summarize(pd.read_csv(HERE/'results/H31_fixed_lofo.csv').query("option_id == 'praat7_filtered_v0.3'"))
    actual_base = core.summarize(base_metrics)
    for metric in ('average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil'):
        assert np.isclose(actual_base[metric], saved[metric], atol=1e-8), metric
    audit.csv_write('H35_fixed_lofo.csv', [{'option_id': option['id'], **score(option, [n for n in names if n != held], held)[0]}
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
             'source_calls': {key[0]+'|'+key[1]:value[2] for key,value in SOURCE_CACHE.items()},
             'range_rejected_frames': {key[0]+'|'+key[1]:value['range_rejected_frames'] for key,value in features.items() if 'range_rejected_frames' in value},
             'long_window_fallback_counts': {key[1]: int(value.get('long_window_fallback', np.zeros(1)).sum()) for key, value in features.items() if key[0] == 'amdf_control'},
             'registry_sha256': audit.digest(HERE / f'{family}_REGISTRY.json'),
             'code_sha256': {str(p.relative_to(REPO)): audit.digest(p) for p in (Path(__file__), HERE / 'amdf_dual_window.py', HERE / 'praat_native_adapter.py', HERE / 'sptk_adapter.py', HERE / 'praat_extract_native.praat', HERE / 'results/sptk_native_provenance.json', HERE / 'results/swipe_synthetic_probe.json', HERE / 'results/praat_native_7002_provenance.json', HERE / 'results/praat_native_command_source.json', Path(core.__file__), Path(audit.__file__), core.BASELINES / 'AMDF.ipynb', core.RESULTS / 'frozen_config.json', REPO / 'research_workbench_2026_10_06/estimator_experiment.py')},
             'data_sha256': {n: audit.digest(core.TRAIN / n) for n in names},
             'wall_time_s': time.perf_counter() - started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
             'selection_objective': 'minimize worst-file Average MAPE, then mean, then id', 'goal_all_nested_files_le_2': bool((table[(table.split=='nested')&(table.model=='candidate')].average_mape<=2).all()), 'train_only': True, 'baseline_reproduced': True, 'poisoned_gt_inference_invariant': True,
             'environment': {'python': sys.version, 'platform': platform.platform(), 'numpy': np.__version__, 'scipy': scipy.__version__, 'sklearn': sklearn.__version__, 'praat':native_proof['version_stdout'], 'native_exe_sha256':native_proof['exe_sha256'],'sptk':sptk_api.metadata()['version'],'sptk_exe_sha256':sptk_api.metadata()['exe_sha256'],'sptk_source_root':sptk_api.metadata()['source_root'],'sptk_key_source_sha256':sptk_api.metadata()['key_source_sha256']}}
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
        figure.update(generator='swipe_praat_hybrid.py', generator_sha256=audit.digest(__file__), command=f'python research_workbench_2026_10_07/swipe_praat_hybrid.py {family}')
    audit.json_write(HERE / f'results/{family}_figure_manifest.json', {'figures': audit.ARTIFACTS})
    fixed=pd.read_csv(HERE/'results/H35_fixed_lofo.csv')
    report=['# H35 — SWIPE pitch with Praat voicing gate', '',audit.markdown_table(summary), '',
      'Praat filtered .30 quyết định V/UV; SWIPE native strength .2/.3 chỉ thay F0 tại khung được Praat nhận hữu thanh và SWIPE có support/range hợp lệ. Nếu thiếu SWIPE, giữ F0 Praat (fallback), không thêm/bớt khung V. Control H31fixed.30. Cùng một gate cho toàn bộ file, không metadata/GTcount/held-stat routing.', '',
      'SWIPE input restorePCM×32768 và output0-origin giữ H34. Hai lần nearest-time: SWIPE→nativePraatgrid, rồi hybrid→canonical; nửa hop+một mẫu, tiesearlier. Lưu raw hai nguồn, hybrid frequencies/source tags, commands/hashes. Không đổi V/UV, dùng probability/GT, trimcount, smooth hoặc chỉnh phân phối theo held-stat.', '',
      '## Gate', '', '~~~json',json.dumps(decision,indent=2),'~~~', '',
      '## Selections', '',audit.markdown_table(pd.DataFrame([{'outer_held':x['outer_held'],**x['option']} for x in selections])), '',
      '## Mọi cấu hình fixed LOFO', '',audit.markdown_table(fixed[['option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','macro_f1','recall_v','false_voiced_sil','projection_coverage']]), '',
      '## Nested per file', '',audit.markdown_table(table[(table.split=='nested')][['model','file','average_mape','F0std_mape','F0num_mape','recall_v','false_voiced_sil','projection_coverage']]), '',
      'Mục tiêu mỗi file≤2% riêng. No actualfit; inner minmax/mean/ID chỉ chọnthreshold. Outerheld khôngselection; lịch sửn4 làmnestedexploratory. LAB chỉfile-stat/nhãnđoạn, khôngF0từngkhung. Đây là wholepipeline comparison, không claim đãđọcfullpaper. Khôngpromote/test/Drive/deeplearning/PDF hoặcretryJev.', '',
      '![Nested](figures/H35_nested.png)', '',
      'Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/swipe_praat_hybrid.py H35']
    (HERE / f'{family}_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps(decision, indent=2), flush=True)
    print(summary[['model', 'split', 'average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil']].to_string(index=False), flush=True)


def check():
    import amdf_dual_window
    amdf_dual_window.check()
    proof=sptk_api.metadata()
    probe=json.loads((HERE/'results/swipe_synthetic_probe.json').read_text())
    assert probe['adapter_sha256']==audit.digest(HERE/'sptk_adapter.py')
    assert len(probe['rows'])==8 and not probe['real_wav_read']
    assert probe['provenance_sha256']==audit.digest(HERE/'results/sptk_native_provenance.json')
    assert proof['version']=='4.4'
    native_api.metadata()
    gate_times=np.array([.01,.02,.03,.04,.10])
    gate_frequency=np.array([173.,0.,180.,190.,200.])
    swipe_times=np.array([0.,.01,.02,.03,.04,.05])
    swipe_frequency=np.array([175.,174.,176.,0.,500.,180.])
    frequency,use,source,indices,support=fuse(gate_times,gate_frequency,swipe_times,swipe_frequency,16000)
    assert np.array_equal(frequency,[174.,0.,180.,190.,200.])
    assert np.array_equal(use,[True,False,False,False,False])
    assert list(source)==['swipe','unvoiced','praat_fallback','praat_fallback','praat_fallback']
    assert np.array_equal(frequency>0,gate_frequency>0)
    assert not support[-1]
    tied=fuse(np.array([.015]),np.array([180.]),np.array([.01,.02]),np.array([170.,190.]),16000)
    assert tied[0][0]==170. and tied[3][0]==0
    print('PASS AMDF original parity/SPTK4.4 source+binary/eight SWIPE synthetic probes/Praat control; no new H35 hybrid BT2 measured.',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'check', 'H35'])
    action = parser.parse_args().action
    if action == 'register':
        path = HERE / 'H35_REGISTRY.json'
        assert not path.exists(), 'Do not overwrite registered registry'
        audit.json_write(path, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                               'baseline_commit': '1261f77', 'original_baseline_commit':'009fd2c', 'rollback_repository_commit': '1261f77',
                               'family': 'H35', 'algorithm': 'SWIPE pitch with fixed Praat filtered .30 voicing gate' , 'options': registry('H35')})
    elif action == 'check':
        check()
    else:
        run('H35')
