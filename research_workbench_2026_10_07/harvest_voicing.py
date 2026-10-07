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
import pyworld
from estimator_experiment import eligibility

audit.HERE = HERE
audit.RESULTS = HERE / 'results'
audit.FIGURES = HERE / 'figures'
audit.RESULTS.mkdir(exist_ok=True)
audit.FIGURES.mkdir(exist_ok=True)



def registry(family):
    assert family == 'H29'
    return [{'id':identity,'frame_ms':25,'hop_ms':10,'pitch_frame_ms':40 if gate=='control' else None,'gate':gate}
            for identity,gate in [('amdf_control','control'),('harvest_raw','none'),
                                 ('harvest_energy','energy'),('harvest_amdf','amdf')]]


def feature_key(option):
    return 'amdf_control' if option['gate']=='control' else 'harvest10canonical'


def extract(item,audio,option):
    if option['gate']=='control':
        import amdf_dual_window
        return amdf_dual_window.extract(item,audio,dict(option,pitch_frame_ms=40))
    frequency,times=pyworld.harvest(np.ascontiguousarray(audio,dtype=np.float64),item['fs'],
        f0_floor=70,f0_ceil=400,frame_period=10)
    right=np.minimum(np.searchsorted(times,item['times']),len(times)-1)
    left=np.maximum(right-1,0)
    index=np.where(abs(times[left]-item['times'])<=abs(times[right]-item['times']),left,right)
    support=abs(times[index]-item['times'])<=.005+1/item['fs']
    f0=np.where(support&(frequency[index]>0),frequency[index],np.nan)
    return dict(item,preprocess='harvest10canonical',harvest_f0=f0,harvest_support=support,
                harvest_native_frames=len(frequency),harvest_native_voiced=int((frequency>0).sum()))


def project(native,canonical,pred,f0,hop_ms):
    assert np.allclose(native['times'],canonical['times'])
    support=native.get('harvest_support',np.ones(len(pred),dtype=bool))
    return pred&support,np.where(support,f0,np.nan),support


def infer(native,training,option,config):
    gate=option['gate']
    names=sorted(x['file'] for x in training)
    if gate=='control':
        fitted=core.fit(training,config)
        pred,f0=core.infer(native,config,fitted)
        return pred,f0,dict(fitted,requires_fit=True,actual_fit_files=names,gate=gate),None
    f0=native['harvest_f0'].copy()
    pred=np.isfinite(f0)
    fitted={'requires_fit':False,'actual_fit_files':[],'gate':gate}
    if gate=='energy':
        energy=core.fit_energy(training)
        pred &= native['relative_rms']>=energy
        fitted.update(requires_fit=True,actual_fit_files=names,energy_threshold=energy)
    elif gate=='amdf':
        thresholds=core.fit(training,config)
        pred &= (native['relative_rms']>=thresholds['energy_threshold'])&(native['AMDF_score']<thresholds['pitch_threshold'])
        fitted.update(thresholds,requires_fit=True,actual_fit_files=names)
    elif gate!='none':
        raise ValueError(gate)
    return pred,np.where(pred,f0,np.nan),fitted,None


def run(family):
    assert not (HERE / f'results/{family}_experiment.json').exists(), 'Preserve completed experiment'
    started = time.perf_counter()
    compatibility=json.loads((HERE/'results/pyworld_035_compatibility.json').read_text())
    assert pyworld.__version__ == compatibility['version'] == '0.3.5'
    native_module=next(Path(pyworld.__file__).parent.glob('*.pyd'))
    assert audit.digest(native_module)==compatibility['native_module_sha256']
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
            metrics.update(native_frames=native.get('harvest_native_frames',len(pred)), native_f0_count=native.get('harvest_native_voiced',int(np.isfinite(f0).sum())), output_frames=len(pred),
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
    audit.csv_write('H29_fixed_lofo.csv', [{'option_id': option['id'], **score(option, [n for n in names if n != held], held)[0]}
                                                for option in options for held in names])
    previous_raw = pd.read_csv(HERE / 'results/H28_fixed_lofo.csv').query("option_id == 'harvest_h10'").set_index('file')
    raw_option = next(option for option in options if option['id'] == 'harvest_raw')
    for held in names:
        actual_raw = score(raw_option, [n for n in names if n != held], held)[0]
        for metric in ('F0mean','F0std','F0num','average_mape','macro_f1','recall_v','false_voiced_sil'):
            assert np.isclose(actual_raw[metric], previous_raw.loc[held, metric], atol=1e-8), (held,metric)
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
             'code_sha256': {str(p.relative_to(REPO)): audit.digest(p) for p in (Path(__file__), HERE / 'amdf_dual_window.py', HERE / 'results/pyworld_035_compatibility.json', Path(core.__file__), Path(audit.__file__), core.BASELINES / 'AMDF.ipynb', core.RESULTS / 'frozen_config.json', REPO / 'research_workbench_2026_10_06/estimator_experiment.py')},
             'data_sha256': {n: audit.digest(core.TRAIN / n) for n in names},
             'wall_time_s': time.perf_counter() - started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
             'selection_objective': 'minimize worst-file Average MAPE, then mean, then id', 'goal_all_nested_files_le_2': bool((table[(table.split=='nested')&(table.model=='candidate')].average_mape<=2).all()), 'train_only': True, 'baseline_reproduced': True, 'poisoned_gt_inference_invariant': True,
             'environment': {'python': sys.version, 'platform': platform.platform(), 'numpy': np.__version__, 'scipy': scipy.__version__, 'sklearn': sklearn.__version__, 'pyworld':pyworld.__version__, 'native_module_sha256':audit.digest(native_module)}}
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
        figure.update(generator='harvest_voicing.py', generator_sha256=audit.digest(__file__), command=f'python research_workbench_2026_10_07/harvest_voicing.py {family}')
    audit.json_write(HERE / f'results/{family}_figure_manifest.json', {'figures': audit.ARTIFACTS})
    fixed=pd.read_csv(HERE/'results/H29_fixed_lofo.csv')
    report=['# H29 — cổng V/UV cho cao độ Harvest', '',audit.markdown_table(summary), '',
      'Một thay đổi: gate của pipeline Harvest, giữ pitch Harvest raw 70–400 Hz/bước10ms. Bốn lựa chọn: AMDF H24 control; Harvest không gate; Harvest + energy; Harvest + cổng energy và AMDF_score25ms đang dùng ở control. Energy fit V/SIL bằng balanced accuracy; AMDF pitch threshold fit V/UV như baseline. Không thêm noise/filter/StoneMask/median hoặc thay candidate Harvest.', '',
      'Harvest raw được ghép vào lưới chấm canonical25/10 trước gate; tâm gần nhất trong nửa hop + một mẫu, hòa chọn sớm hơn. Không dùng nhãn/GT của held file để gate, không điều chỉnh count theo GT và không fallback khi Harvest UV. native_frames/native_f0_count là output Harvest trước gate; F0num là số khung còn lại trên lưới chấm. Inner chọn worst-file MAPE rồi mean/ID; outer held bị loại khỏi fit và selection. Kết quả vẫn exploratory do lịch sử nghiên cứu bốn file.', '',
      '## Gate', '', '~~~json',json.dumps(decision,indent=2),'~~~', '',
      '## Selections', '',audit.markdown_table(pd.DataFrame([{'outer_held':x['outer_held'],**x['option']} for x in selections])), '',
      '## Mọi cấu hình fixed LOFO', '',audit.markdown_table(fixed[['option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','macro_f1','recall_v','false_voiced_sil']]), '',
      '## Nested per file', '',audit.markdown_table(table[(table.split=='nested')][['model','file','average_mape','F0std_mape','F0num_mape','recall_v','false_voiced_sil','projection_coverage']]), '',
      'Mục tiêu mỗi file Average MAPE≤2% báo riêng. Không thay baseline gốc/frozen_config hoặc tự promote. Chỉ train local; không test/Drive/deep learning/PDF extraction. Ground truth là file-stat và loại đoạn, chưa có F0 chuẩn từng khung.', '',
      '![Nested](figures/H29_nested.png)', '',
      'Lệnh: ../.venv-bt2-world/Scripts/python.exe research_workbench_2026_10_07/harvest_voicing.py H29']
    (HERE / f'{family}_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps(decision, indent=2), flush=True)
    print(summary[['model', 'split', 'average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil']].to_string(index=False), flush=True)


def check():
    import amdf_dual_window
    amdf_dual_window.check()
    proof=json.loads((HERE/'results/pyworld_035_compatibility.json').read_text())
    assert pyworld.__version__ == proof['version'] == '0.3.5'
    assert audit.digest(next(Path(pyworld.__file__).parent.glob('*.pyd'))) == proof['native_module_sha256']
    for fs in (16000,44100):
        silent,times=pyworld.harvest(np.zeros(fs,dtype=np.float64),fs,f0_floor=70,f0_ceil=400,frame_period=10)
        assert not np.any(silent>0) and np.allclose(np.diff(times),.01)
        t=np.arange(fs)/fs
        sound=sum(np.sin(2*np.pi*173*k*t)/k for k in range(1,13)).astype(np.float64)
        f0,times=pyworld.harvest(sound,fs,f0_floor=70,f0_ceil=400,frame_period=10)
        center=(times>=.1)&(times<=.9)
        assert np.all(f0[center]>0) and np.max(abs(f0[center]-173))<.1
    print('PASS original AMDF parity/native module provenance/12-harmonic173Hz/silence; earlier 2-harmonic failure retained. Check measured no new gated H29 BT2 result; H28 preserved.',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'check', 'H29'])
    action = parser.parse_args().action
    if action == 'register':
        path = HERE / 'H29_REGISTRY.json'
        assert not path.exists(), 'Do not overwrite registered registry'
        audit.json_write(path, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                               'baseline_commit': '4b29af2', 'original_baseline_commit':'009fd2c', 'rollback_repository_commit': '4b29af2',
                               'family': 'H29', 'algorithm': 'Harvest voicing gate versus AMDF control', 'options': registry('H29')})
    elif action == 'check':
        check()
    else:
        run('H29')
