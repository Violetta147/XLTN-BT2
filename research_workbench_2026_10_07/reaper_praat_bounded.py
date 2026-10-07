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
import reaper_adapter as reaper_api
from estimator_experiment import eligibility

audit.HERE = HERE
audit.RESULTS = HERE / 'results'
audit.FIGURES = HERE / 'figures'
audit.RESULTS.mkdir(exist_ok=True)
audit.FIGURES.mkdir(exist_ok=True)



def registry(family):
    assert family=='H38'
    common={'frame_ms':3000/70,'hop_ms':10,'pitch_frame_ms':None,'unvoiced_cost':.9,'gate_voicing_threshold':.3}
    return [{'id':'praat7_filtered_v0.3','frame_ms':3000/70,'hop_ms':10,'pitch_frame_ms':3000/70,
             'method':'control','voicing_threshold':.3},
            {'id':'praat_gate_reaper_c0.9',**common,'method':'raw'}]+[
        {'id':f'praat_reaper_b{band}_a{alpha:g}',**common,'method':'bounded',
         'agreement_cents':band,'reaper_weight':alpha}
        for band in (100,200) for alpha in (.5,1.)]


SOURCE_CACHE = {}


def fuse(gate_times,gate_frequency,reaper_times,reaper_frequency,fs,option):
    right=np.minimum(np.searchsorted(reaper_times,gate_times),len(reaper_times)-1)
    left=np.maximum(right-1,0)
    indices=np.where(abs(reaper_times[left]-gate_times)<=abs(reaper_times[right]-gate_times),left,right)
    support=abs(reaper_times[indices]-gate_times)<=.005+1/fs
    gate=(gate_frequency>=70)&(gate_frequency<=400)
    available=support&(reaper_frequency[indices]>=70)&(reaper_frequency[indices]<=400)
    delta=np.full(len(gate_times),np.nan)
    valid=gate&available
    delta[valid]=1200*np.log2(reaper_frequency[indices[valid]]/gate_frequency[valid])
    use=valid.copy()
    replacement=reaper_frequency[indices].copy()
    if option['method']=='bounded':
        use &= abs(delta)<=option['agreement_cents']+1e-9
        alpha=option['reaper_weight']
        if alpha!=1:
            replacement[use]=np.exp((1-alpha)*np.log(gate_frequency[use])+alpha*np.log(replacement[use]))
        replacement_tag='reaper_agree' if alpha==1 else 'blend_agree'
    else:
        replacement_tag='reaper'
    frequency=np.where(gate,np.where(use,replacement,gate_frequency),0.)
    source=np.where(~gate,'unvoiced',np.where(use,replacement_tag,np.where(available,'praat_disagreement','praat_missing')))
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
        reaper_key=(f"reaper_c{option['unvoiced_cost']:g}",item['file'])
        if reaper_key not in SOURCE_CACHE:
            SOURCE_CACHE[reaper_key]=reaper_api.pitch(audio,item['fs'],option['unvoiced_cost'])
        st,sf,_=SOURCE_CACHE[reaper_key]
        frequency,_,source,_,_=fuse(times,gate_frequency,st,sf,item['fs'],option)
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
    audit.csv_write('H38_raw_native_frames.csv',native_rows)
    audit.csv_write('H38_source_native_frames.csv',[{'source_id':identity,'file':file,'time_s':float(t),'raw_f0_hz':float(f)} for (identity,file),(times,frequency,log) in SOURCE_CACHE.items() for t,f in zip(times,frequency)])
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
            valid = bool(np.isfinite(table.average_mape).all()
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
    audit.csv_write('H38_fixed_lofo.csv', [{'option_id': option['id'], **score(option, [n for n in names if n != held], held)[0]}
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
             'code_sha256': {str(p.relative_to(REPO)): audit.digest(p) for p in (Path(__file__), HERE / 'amdf_dual_window.py', HERE / 'praat_native_adapter.py', HERE / 'sptk_adapter.py', HERE / 'reaper_adapter.py', HERE / 'results/reaper_synthetic_probe.json', HERE / 'results/reaper_author_source_discovery.json', HERE / 'praat_extract_native.praat', HERE / 'results/sptk_native_provenance.json', HERE / 'results/reaper_adapter_probe.json', HERE / 'results/praat_native_7002_provenance.json', HERE / 'results/praat_native_command_source.json', Path(core.__file__), Path(audit.__file__), core.BASELINES / 'AMDF.ipynb', core.RESULTS / 'frozen_config.json', REPO / 'research_workbench_2026_10_06/estimator_experiment.py')},
             'data_sha256': {n: audit.digest(core.TRAIN / n) for n in names},
             'wall_time_s': time.perf_counter() - started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
             'selection_objective': 'minimize worst-file Average MAPE, then mean, then id', 'goal_all_nested_files_le_2': bool((table[(table.split=='nested')&(table.model=='candidate')].average_mape<=2).all()), 'train_only': True, 'baseline_reproduced': True, 'poisoned_gt_inference_invariant': True,
             'environment': {'python': sys.version, 'platform': platform.platform(), 'numpy': np.__version__, 'scipy': scipy.__version__, 'sklearn': sklearn.__version__, 'praat':native_proof['version_stdout'], 'native_exe_sha256':native_proof['exe_sha256'],'sptk':sptk_api.metadata()['version'],'sptk_exe_sha256':sptk_api.metadata()['exe_sha256'],'sptk_source_root':sptk_api.metadata()['source_root'],'sptk_key_source_sha256':json.loads((HERE/'results/reaper_synthetic_probe.json').read_text())['source_sha256']}}
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
    fixed=pd.read_csv(HERE/'results/H38_fixed_lofo.csv')
    p_fixed=HERE/'results/H38_fixed_lofo.csv'
    for name,metric,title in [('H38_fixed_mape','average_mape','Average MAPE (%)'),('H38_fixed_std','F0std_mape','Std MAPE (%)')]:
        fig,axes=audit.plt.subplots(2,2,figsize=(14,9))
        for ax,file in zip(axes.flat,names):
            group=fixed[fixed.file==file]
            ax.barh(group.option_id,group[metric],color=['gray','coral']+['steelblue']*4)
            ax.invert_yaxis()
            ax.set(title=file,xlabel=title)
            ax.axvline(2,color='black',ls='--',lw=.8)
        fig.tight_layout()
        audit.save_figure(name,fig,[p_fixed],f'{title} của đủ sáu cấu hình fixed; line2 là mốc tham khảo.',
                          'Fixed results không thay nested; std riêng≤2% không phải mục tiêu Average MAPE. LAB không có F0 chuẩn từng khung.')
    usage=[]
    for (identity,file),value in features.items():
        if identity=='praat7_filtered_v0.3':
            continue
        tags=value['hybrid_source']
        used=np.isin(tags,['reaper','reaper_agree','blend_agree'])
        usage.append({'option_id':identity,'file':file,'native_voiced':int(value['native_pred'].sum()),
                      'reaper_used':int(used.sum()),'praat_disagreement':int((tags=='praat_disagreement').sum()),
                      'praat_missing':int((tags=='praat_missing').sum())})
    p_usage=audit.csv_write('H38_reaper_usage.csv',usage)
    for figure in audit.ARTIFACTS:
        figure.update(generator='reaper_praat_bounded.py', generator_sha256=audit.digest(__file__), command=f'python research_workbench_2026_10_07/reaper_praat_bounded.py {family}')
    audit.json_write(HERE / f'results/{family}_figure_manifest.json', {'figures': audit.ARTIFACTS})
    report=['# H38 — Kết hợp cao độ trong vùng đồng thuận Praat–REAPER', '',audit.markdown_table(summary), '',
      'Cents đo tỷ số cao độ: 1200 cents là một octave (tần số gấp đôi), 100 cents là một bán âm. Praat filtered .30 là nguồn neo ứng viên và giữ mask V/UV. REAPER .9 là nguồn thứ hai. Chỉ khi hai nguồn có support và nằm70–400Hz, chênh lệch≤100 hoặc200cents, thay bằng REAPER (weight1) hoặc trung bình hình học (weight.5). Nếu ngoài band hoặc thiếu REAPER, giữ Praat. Không nhân/chia tần số theo octave, không chỉnh theo file-stat ground truth.', '',
      'Control H31fixed.30; raw gated REAPER .9 là ablation H37. Cùng một grid6options cho toàn bộ file, không chọn theo tên/giới/device/held-stat. Hai nearest-time projections giữ H37, V/UV/count/support bằng control. Eight native source calls, no model fit. Native PCM, hashes và source tags giữ đầy đủ.', '',
      '## Gate', '', '~~~json',json.dumps(decision,indent=2),'~~~', '',
      '## Selections', '',audit.markdown_table(pd.DataFrame([{'outer_held':x['outer_held'],**x['option']} for x in selections])), '',
      '## Mọi cấu hình fixed LOFO', '',audit.markdown_table(fixed[['option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','macro_f1','recall_v','false_voiced_sil','projection_coverage']]), '',
      '## Nested per file', '',audit.markdown_table(table[(table.split=='nested')][['model','file','average_mape','F0std_mape','F0num_mape','recall_v','false_voiced_sil','projection_coverage']]), '',
      'Mục tiêu mỗi file≤2% riêng; không nhầm với mean≤2%. No actualfit; inner minimax/mean/ID chỉ chọnband/weight. Outerheld khôngselection; lịch sửn4 làmnestedexploratory. LAB chỉfile-stat/nhãnđoạn, khôngF0chuẩntừngkhung. Đồng thuận hai ứng viên không chứng minh pitch đúng; fallback có thể giữ lỗi Praat. Khôngpromote/test/Drive/deeplearning/PDF/retryJev. Failedoptions giữ nguyên.', '',
      '![Nested](figures/H38_nested.png)', '', '![Fixed Average MAPE](figures/H38_fixed_mape.png)', '', '![Fixed std](figures/H38_fixed_std.png)', '',
      'Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/reaper_praat_bounded.py H38']
    (HERE / f'{family}_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps(decision, indent=2), flush=True)
    print(summary[['model', 'split', 'average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil']].to_string(index=False), flush=True)


def check():
    import amdf_dual_window
    amdf_dual_window.check()
    proof=sptk_api.metadata()
    probe=json.loads((HERE/'results/reaper_adapter_probe.json').read_text())
    assert probe['adapter_sha256']==audit.digest(HERE/'reaper_adapter.py')
    assert probe['sptk_adapter_sha256']==audit.digest(HERE/'sptk_adapter.py')
    assert len(probe['rows'])==8 and not probe['real_wav_read']
    assert probe['native_provenance_sha256']==audit.digest(HERE/'results/sptk_native_provenance.json')
    raw=json.loads((HERE/'results/reaper_synthetic_probe.json').read_text())
    assert probe['raw_probe_sha256']==audit.digest(HERE/'results/reaper_synthetic_probe.json')
    for relative,expected in raw['source_sha256'].items():
        assert audit.digest(Path(proof['source_root'])/relative)==expected
    assert proof['version']=='4.4'
    native_api.metadata()
    raw_option=registry('H38')[1]
    gate_times=np.array([.01,.02,.03,.04,.10])
    gate_frequency=np.array([173.,0.,180.,190.,200.])
    reaper_times=np.array([0.,.01,.02,.03,.04,.05])
    reaper_frequency=np.array([175.,174.,176.,0.,500.,180.])
    result=fuse(gate_times,gate_frequency,reaper_times,reaper_frequency,16000,raw_option)
    assert np.array_equal(result[0],[174.,0.,180.,190.,200.])
    assert list(result[2])==['reaper','unvoiced','praat_missing','praat_missing','praat_missing']
    assert not result[4][-1]
    tied=fuse(np.array([.015]),np.array([180.]),np.array([.01,.02]),np.array([170.,190.]),16000,raw_option)
    assert tied[0][0]==170. and tied[3][0]==0
    tests=[]
    for option in registry('H38')[2:]:
        t=np.arange(6)*.01
        g=np.array([200.,200.,0.,200.,200.,200.])
        r=np.array([100.,200*2**(option['agreement_cents']/1200),220.,500.,0.,200*2**((option['agreement_cents']+.01)/1200)])
        frequency,use,tags,_,_=fuse(t,g,t,r,16000,option)
        assert np.array_equal(use,[False,True,False,False,False,False])
        assert np.array_equal(frequency[[0,2,3,4,5]],[200.,0.,200.,200.,200.])
        assert np.isclose(frequency[1],200**(1-option['reaper_weight'])*r[1]**option['reaper_weight'],atol=1e-10)
        assert tags[0]=='praat_disagreement' and tags[5]=='praat_disagreement'
        assert np.array_equal(frequency>0,g>0)
        tests.append(option['id'])
    audit.json_write(HERE/'results/H38_precheck.json',{'family':'H38','bounded_rule_options_checked':tests,
        'runner_sha256':audit.digest(__file__),'uv_missing_range_unsupported_tie_band_boundary_blend_checked':True,
        'native_identity_and_historical_amdf_parity_checked':True,'new_H38_BT2_measured':False})
    print('PASS H38 native identity, UV/missing/range/time/tie/band boundary/blend tests; no new H38 BT2 measured.',flush=True)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'check', 'H38'])
    action = parser.parse_args().action
    if action == 'register':
        path = HERE / 'H38_REGISTRY.json'
        assert not path.exists(), 'Do not overwrite registered registry'
        audit.json_write(path, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                               'baseline_commit': 'cd23e9c', 'original_baseline_commit':'009fd2c', 'rollback_repository_commit': 'cd23e9c',
                               'family': 'H38', 'algorithm': 'Bounded log-frequency fusion of REAPER .9 with fixed Praat filtered .30 gate' , 'options': registry('H38')})
    elif action == 'check':
        check()
    else:
        run('H38')
