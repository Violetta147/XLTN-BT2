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
    assert family == 'H28'
    return [{'id':'amdf_control','frame_ms':25,'hop_ms':10,'pitch_frame_ms':40,'method':'control'}]+[
        {'id':f'harvest_h{hop}','frame_ms':None,'hop_ms':hop,'pitch_frame_ms':None,'method':'harvest'}
        for hop in (5,10,20)]


def feature_key(option):
    return option['id']


def extract(item, audio, option):
    if option['method']=='control':
        import amdf_dual_window
        return amdf_dual_window.extract(item,audio,dict(option,pitch_frame_ms=40))
    frequency,times=pyworld.harvest(np.ascontiguousarray(audio,dtype=np.float64),item['fs'],
        f0_floor=70,f0_ceil=400,frame_period=option['hop_ms'])
    pred=frequency>0
    assert np.isfinite(frequency).all() and len(times)==len(frequency)
    assert np.all((frequency==0)|((frequency>=70)&(frequency<=400)))
    return dict(item,times=times,preprocess=option['id'],native_pred=pred,
                native_f0=np.where(pred,frequency,np.nan))


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
                {'requires_fit':False,'actual_fit_files':[],'method':'WORLD Harvest','frame_period_ms':option['hop_ms']},None)
    fitted=core.fit(training,config)
    return (*core.infer(native,config,fitted),fitted,None)


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
    audit.csv_write('H28_fixed_lofo.csv', [{'option_id': option['id'], **score(option, [n for n in names if n != held], held)[0]}
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
        figure.update(generator='harvest_reference.py', generator_sha256=audit.digest(__file__), command=f'python research_workbench_2026_10_07/harvest_reference.py {family}')
    audit.json_write(HERE / f'results/{family}_figure_manifest.json', {'figures': audit.ARTIFACTS})
    report=['# H28 — pipeline tham chiếu WORLD Harvest', '',audit.markdown_table(summary), '',
      'So sánh toàn bộ pipeline với AMDF H24. Harvest lấy nhiều ứng viên từ filterbank, refine/score, loại ứng viên không tin cậy, nối/sửa contour và làm mượt. Dùng PyWORLD 0.3.5, F0 70–400 Hz, frame_period 5/10/20 ms; không thêm noise, cổng năng lượng AMDF hoặc StoneMask. Cửa sổ phân tích do thuật toán quản lý; frame_period là bước đầu ra, không phải độ dài cửa sổ.', '',
      'Ghép tâm native gần nhất vào lưới chấm 25/10 ms trong nửa hop cộng một mẫu; khi hòa chọn tâm sớm hơn. Không padding hoặc điều chỉnh count theo GT. Harvest không fit; traces fit_files ghi tập danh nghĩa để chọn cấu hình. Inner chọn worst-file MAPE rồi mean và ID. Giữ mọi gate đã đăng ký; nested vẫn exploratory do lịch sử nghiên cứu bốn file.', '',
      'Synthetic trước đo giữ cả failure: tín hiệu chỉ hai harmonic không noise bị gọi UV gần toàn bộ; 12 harmonic hoặc noise yếu nhận 81/81 khung trung tâm với lỗi tối đa dưới 0.03 Hz. Không thêm noise vào WAV thật. Nguồn sdist PyWORLD 0.3.5 harvest.cpp có hash giống source tác giả pin d625e7; wheel metadata không tự chứng minh native binary đã được build chính xác từ từng dòng source. Lưu cả native module hash và source provenance.', '',
      '## Gate', '', '~~~json',json.dumps(decision,indent=2),'~~~', '',
      '## Selections', '',audit.markdown_table(pd.DataFrame([{'outer_held':x['outer_held'],**x['option']} for x in selections])), '',
      '## Per file', '',audit.markdown_table(table[['split','model','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','recall_v','false_voiced_sil','projection_coverage']]), '',
      'Mục tiêu mỗi file Average MAPE ≤2% báo riêng. Giữ baseline gốc và failure; không tự promote. LAB có thống kê file và nhãn đoạn, không F0 chuẩn từng khung. Chỉ train local; không test/Drive/deep learning/PDF extraction.', '',
      '![Nested](figures/H28_nested.png)', '', 'Primary abstract: https://www.isca-archive.org/interspeech_2017/morise17b_interspeech.html', '',
      'Source implementation: https://github.com/mmorise/World/blob/d625e7608ca23a870018f01e7c562ac683d9847f/src/harvest.cpp', '',
      'Lệnh: ../.venv-bt2-world/Scripts/python.exe research_workbench_2026_10_07/harvest_reference.py H28']
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
    print('PASS original AMDF parity/native module provenance/12-harmonic173Hz/silence; earlier 2-harmonic failure retained. No BT2 Harvest WAV benchmark measured.',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'check', 'H28'])
    action = parser.parse_args().action
    if action == 'register':
        path = HERE / 'H28_REGISTRY.json'
        assert not path.exists(), 'Do not overwrite registered registry'
        audit.json_write(path, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                               'baseline_commit': '877eef9', 'original_baseline_commit':'009fd2c', 'rollback_repository_commit': '877eef9',
                               'family': 'H28', 'algorithm': 'WORLD Harvest versus AMDF control', 'options': registry('H28')})
    elif action == 'check':
        check()
    else:
        run('H28')
