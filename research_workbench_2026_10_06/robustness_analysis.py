import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import audit
import core
import hysteresis_experiment as hysteresis
from audio_features import acf_features

HERE = Path(__file__).resolve().parent
CSV = HERE / 'results/robustness_cases.csv'
PROGRESS = HERE / 'results/robustness_progress.json'
DEADLINE = datetime.fromisoformat('2026-10-06T21:00:00+00:00')


def registry(items):
    rows = []
    for item in items:
        for kind in ('white', 'pink', 'brown'):
            for level in (30., 25., 20., 15., 10., 5., 0.):
                for seed in range(20):
                    rows.append({'file': item['file'], 'kind': kind, 'level': level, 'seed': seed})
        for level in (.1, .25, .5, 2., 4.):
            rows.append({'file': item['file'], 'kind': 'gain', 'level': level, 'seed': 0})
        for kind in ('dc_rms', 'clip_peak'):
            for level in ((.25, 1., 2.) if kind == 'dc_rms' else (.8, .5, .25)):
                rows.append({'file': item['file'], 'kind': kind, 'level': level, 'seed': 0})
        for seed in range(5):
            rows.append({'file': item['file'], 'kind': 'impulse_rms', 'level': 10., 'seed': seed})
    for row in rows:
        row['case_id'] = '|'.join(str(row[x]) for x in ('file', 'kind', 'level', 'seed'))
    return rows


def perturb(audio, condition):
    kind, level = condition['kind'], condition['level']
    seed_material = condition['file'] + '|' + kind + '|' + str(condition['seed'])
    seed = 20261006 + int(hashlib.sha256(seed_material.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    rms = np.sqrt(np.mean(audio ** 2))
    achieved = np.nan
    if kind in ('white', 'pink', 'brown'):
        noise = rng.normal(size=len(audio))
        if kind != 'white':
            exponent = .5 if kind == 'pink' else 1.
            spectrum = np.fft.rfft(noise)
            spectrum /= np.maximum(np.arange(len(spectrum)), 1) ** exponent
            spectrum[0] = 0.
            noise = np.fft.irfft(spectrum, n=len(audio))
        noise -= noise.mean()
        noise *= rms / np.sqrt(np.mean(noise ** 2)) * 10 ** (-level / 20)
        achieved = float(10 * np.log10(np.mean(audio ** 2) / np.mean(noise ** 2)))
        assert abs(achieved - level) < 1e-8
        result = audio + noise
    elif kind == 'gain':
        result = audio * level
    elif kind == 'dc_rms':
        result = audio + rms * level
    elif kind == 'clip_peak':
        threshold = max(abs(audio)) * level
        result = np.clip(audio, -threshold, threshold)
    elif kind == 'impulse_rms':
        result = audio.copy()
        indices = rng.choice(len(audio), max(1, round(len(audio) * .001)), replace=False)
        result[indices] += rng.choice([-1., 1.], len(indices)) * level * rms
    else:
        raise ValueError(kind)
    return result, seed, achieved


def write_progress(rows, total, metadata, state):
    tmp = CSV.with_suffix('.tmp')
    pd.DataFrame(rows).to_csv(tmp, index=False)
    tmp.replace(CSV)
    audit.json_write(PROGRESS, {'status': state, 'completed_cases': len(rows) // 2, 'registered_cases': total,
                     'updated_at_utc': datetime.now(timezone.utc).isoformat(), **metadata})


def figures_and_report(frame, metadata, completed, total):
    noise = frame[frame.kind.isin(['white', 'pink', 'brown'])]
    group_keys = ['kind', 'level', 'model', 'file']
    by_file = noise.groupby(group_keys).agg(recall_v=('recall_v', 'mean'), macro_f1=('macro_f1', 'mean'),
                                          false_voiced_sil=('false_voiced_sil', 'mean'), average_mape=('average_mape', 'mean'),
                                          realizations=('case_id', 'size'), finite_stat_cases=('average_mape', 'count')).reset_index()
    p_groups = audit.csv_write('robustness_noise_per_file.csv', by_file)
    aggregate = by_file.groupby(['kind', 'level', 'model']).agg(recall_v=('recall_v', 'mean'), macro_f1=('macro_f1', 'mean'),
                              false_voiced_sil=('false_voiced_sil', 'sum'), conditional_average_mape=('average_mape', 'mean'),
                              files=('file', 'size'), cases=('realizations', 'sum'), finite_stat_cases=('finite_stat_cases', 'sum')).reset_index()
    aggregate['stat_coverage'] = aggregate.finite_stat_cases / aggregate.cases
    p_aggregate = audit.csv_write('robustness_noise_summary.csv', aggregate)
    if len(noise):
        fig, axes = audit.plt.subplots(3, 4, figsize=(15, 10))
        for row, kind in enumerate(('white', 'pink', 'brown')):
            for col, metric in enumerate(('recall_v', 'macro_f1', 'false_voiced_sil', 'conditional_average_mape')):
                ax = axes[row, col]
                for model in ('accepted', 'hysteresis_nested'):
                    data = aggregate[(aggregate.kind == kind) & (aggregate.model == model)].sort_values('level')
                    ax.plot(data.level, data[metric], 'o-', label=model)
                ax.set(title=kind + ' — ' + metric, xlabel='Injected full-file SNR (dB)')
                if metric in ('recall_v', 'macro_f1'):
                    ax.set_ylim(0, 1)
        axes[0, 0].legend(fontsize=7)
        audit.save_figure('robustness_noise_curves', fig, [p_aggregate, p_groups], 'Sensitivity hai cấu hình cố định theo simulatednoise/SNR.', '4file,20noise realizations/cell; AvgMAPE conditional khi cóF0, phải đọc coverage. Không chứng minh pitch đúng từng khung.')
        fig, axes = audit.plt.subplots(1, 3, figsize=(12, 4))
        for ax, kind in zip(axes, ('white', 'pink', 'brown')):
            for model in ('accepted', 'hysteresis_nested'):
                data = aggregate[(aggregate.kind == kind) & (aggregate.model == model)].sort_values('level')
                ax.plot(data.level, data.stat_coverage, 'o-', label=model)
            ax.set(title=kind + ': finite file-stat metrics', xlabel='Injected SNR (dB)', ylabel='Fraction of realizations', ylim=(0, 1.05))
        axes[0].legend(fontsize=7)
        audit.save_figure('robustness_stat_coverage', fig, [p_aggregate], 'Tỷ lệ cases có đủ mean/std/AvgMAPE để so sánh.', 'Empty-F0 mean/std undefined, không bị tính nhưerror0; coverage phải đi cùngconditional error.')
    other = frame[~frame.kind.isin(['white', 'pink', 'brown'])]
    p_other = audit.csv_write('robustness_gain_dc_clip_impulse.csv', other)
    if len(other):
        fig, axes = audit.plt.subplots(2, 4, figsize=(15, 7))
        for col, kind in enumerate(('gain', 'dc_rms', 'clip_peak', 'impulse_rms')):
            for model in ('accepted', 'hysteresis_nested'):
                data = other[(other.kind == kind) & (other.model == model)].groupby('level').agg(macro_f1=('macro_f1','mean'), false_voiced_sil=('false_voiced_sil','mean')).reset_index()
                axes[0,col].plot(data.level, data.macro_f1, 'o-', label=model)
                axes[1,col].plot(data.level, data.false_voiced_sil, 'o-', label=model)
            axes[0,col].set(title=kind, ylabel='Mean file macro F1')
            axes[1,col].set(xlabel='Registered level (see protocol)', ylabel='Mean file SIL false voiced')
        axes[0,0].legend(fontsize=7)
        audit.save_figure('robustness_other_conditions', fig, [p_other], 'Gain/DC/clipping/impulses riêng từng condition.', 'Gain là float lý tưởng không quantize; DC theofileRMS, clipping theopeak; không chồngperturbations.')
    for figure in audit.ARTIFACTS:
        figure['generator'] = 'robustness_analysis.py'
        figure['generator_sha256'] = audit.digest(__file__)
        figure['command'] = 'python research_workbench_2026_10_06/robustness_analysis.py'
    audit.json_write(HERE / 'results/robustness_figure_manifest.json', {'figures': audit.ARTIFACTS})
    report = ['# H15 — robustness có kiểm soát, fixed clean-trained models', '',
              f'Hoàn thành {completed}/{total} registered cases; mỗi case có2model. Raw train-only, không đọc/test/tune từ stress curves.', '',
              'Hysteresis dùng margin của nestedfold chỉ other3 đã chọn. Thresholds fit cleanother3; noise tidak được dùng để fit lại. SNR toàn file gồmSIL; injectednoise synthetic PSD0/-1/-2, không noise corpus thật.', '',
              '## Noise summary', '', audit.markdown_table(aggregate), '',
              'AvgMAPE conditional khi có estimate; statcoverage báo riêng, undefined không fill0. Các seed không là thêm speakers: chỉ4file gốc. Group trước theofile, average seed trongfile, rồi average4file; SILsum là tổng expectation theo4file.', '',
              '## Gain/DC/clip/impulse', '', audit.markdown_table(other.groupby(['kind','level','model']).agg(macro_f1=('macro_f1','mean'), recall_v=('recall_v','mean'), false_voiced_sil=('false_voiced_sil','mean')).reset_index()) if len(other) else 'Chưa chạy các cases này.', '',
              '## Reproduction metadata', '', '~~~json', json.dumps(metadata, indent=2), '~~~', '',
              '## Figures', '', '![Noise](figures/robustness_noise_curves.png)', '', '![Coverage](figures/robustness_stat_coverage.png)', '',
              '![Other](figures/robustness_other_conditions.png)', '',
              '~~~powershell', 'python research_workbench_2026_10_06/robustness_analysis.py', '~~~']
    (HERE / 'ROBUSTNESS_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report-only', action='store_true')
    args = parser.parse_args()
    started = time.perf_counter()
    items = core.load_training()
    conditions = registry(items)
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['ACF']['config']
    selections = pd.read_csv(HERE / 'results/hysteresis_outer_selections.csv')
    metadata = {'registry_sha256': hashlib.sha256(json.dumps(conditions,sort_keys=True).encode()).hexdigest(),
                'code_sha256': {name:audit.digest(HERE/name) for name in ('audio_features.py','robustness_analysis.py','hysteresis_experiment.py')},
                'raw_wav_sha256': {item['file']:audit.digest(core.TRAIN/item['file']) for item in items},
                'test_read': False, 'deadline_utc': DEADLINE.isoformat(), 'selection_tuned_from_noise': False}
    audit.json_write(HERE / 'results/robustness_registry.json', {'conditions': conditions, **metadata})
    rows = pd.read_csv(CSV).to_dict('records') if CSV.exists() else []
    if rows:
        previous = json.loads(PROGRESS.read_text(encoding='utf-8'))
        assert previous['registry_sha256'] == metadata['registry_sha256'] and previous['code_sha256'] == metadata['code_sha256'], 'Resume needs unchanged source/registry'
    if args.report_only:
        figures_and_report(pd.DataFrame(rows), metadata, len(rows)//2, len(conditions))
        return
    completed = {row['case_id'] for row in rows}
    source = {}
    for item in items:
        fs, audio = core.load_audio(core.TRAIN/item['file'])
        raw = acf_features(audio, fs)
        for key in raw:
            assert np.allclose(raw[key], item[key], atol=1e-8, equal_nan=True), 'Raw extraction mismatch: '+key
        fitted = core.fit([x for x in items if x is not item],config)
        selected = selections[(selections.split=='nested')&(selections.held_file==item['file'])].iloc[0]
        assert item['file'] not in selected.selection_files.split('|')
        source[item['file']] = item, audio, fitted, float(selected.margin)
    metadata['raw_extractor_reproduced'] = True
    for number, condition in enumerate(conditions,1):
        if condition['case_id'] in completed:
            continue
        if datetime.now(timezone.utc) >= DEADLINE:
            write_progress(rows,len(conditions),metadata,'deadline_partial')
            break
        item,audio,fitted,margin = source[condition['file']]
        perturbed,seed,achieved = perturb(audio,condition)
        transformed = dict(item,**acf_features(perturbed,item['fs']))
        assert np.allclose(transformed['times'],item['times'],atol=1e-12)
        for model in ('accepted','hysteresis_nested'):
            pred,f0 = core.infer(transformed,config,fitted) if model=='accepted' else hysteresis.infer(transformed,config,fitted,margin)
            rows.append({**condition,'model':model,'actual_rng_seed':seed,'achieved_snr_db':achieved,'margin':0. if model=='accepted' else margin,
                         'pitch_threshold':fitted['pitch_threshold'],'energy_threshold':fitted['energy_threshold'],
                         **core.score_file(item,pred,f0)})
        write_progress(rows,len(conditions),metadata,'running')
        if number % 100 == 0:
            print(f'{number}/{len(conditions)} cases, elapsed {time.perf_counter()-started:.1f}s',flush=True)
    status = 'complete' if len(rows)//2==len(conditions) else 'deadline_partial'
    metadata['wall_time_s'] = time.perf_counter()-started
    write_progress(rows,len(conditions),metadata,status)
    figures_and_report(pd.DataFrame(rows),metadata,len(rows)//2,len(conditions))
    print(json.dumps({'status':status,'completed_cases':len(rows)//2,'registered_cases':len(conditions),'wall_time_s':metadata['wall_time_s']},indent=2),flush=True)


if __name__ == '__main__':
    main()
