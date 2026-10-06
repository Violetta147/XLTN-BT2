import argparse
import importlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import audit
import core
import pitch_estimators

HERE = Path(__file__).resolve().parent


def method_function(method):
    return pitch_estimators.yin if method == 'yin' else importlib.import_module(method + '_estimator').estimate


def synthetic_signals():
    rng = np.random.default_rng(20261006)
    for fs in (16000, 44100):
        t = np.arange(round(fs * .025)) / fs
        for pitch in (70., 80., 100., 120., 160., 200., 240., 300., 380., 400.):
            for seed in range(5):
                phase = rng.uniform(0, 2 * np.pi)
                fundamental = 2 * np.pi * pitch * t + phase
                for kind, amplitudes in [('sine', [1.]), ('harmonic', [1., .5, 1/3, .25]),
                                         ('weak_fundamental', [.1, 1., .4]), ('missing_fundamental', [0., 1., .7])]:
                    clean = sum(a * np.sin((j + 1) * fundamental) for j, a in enumerate(amplitudes))
                    for snr in (np.inf, 20., 10., 0.):
                        noise = rng.normal(size=len(clean))
                        scale = 0. if np.isinf(snr) else np.sqrt(np.mean(clean ** 2) / np.mean(noise ** 2)) * 10 ** (-snr / 20)
                        yield fs, pitch, seed, kind, snr, clean + noise * scale


def synthetic_evaluate(method):
    estimator = method_function(method)
    rows = []
    for fs, truth, seed, kind, snr, frame in synthetic_signals():
        estimate, strength = estimator(frame, fs)
        assert np.isfinite(estimate) and 70 <= estimate <= 400
        rows.append({'method': method, 'fs': fs, 'truth_hz': truth, 'phase_seed': seed, 'signal_kind': kind,
                     'snr_db': snr, 'estimate_hz': estimate, 'strength': strength,
                     'absolute_cents': abs(1200 * np.log2(estimate / truth)),
                     'absolute_relative_error_percent': 100 * abs(estimate - truth) / truth})
    frame = pd.DataFrame(rows)
    checks = {'silence_returns_nan': bool(np.isnan(estimator(np.zeros(400), 16000)[0])),
              'constant_returns_nan': bool(np.isnan(estimator(np.ones(400), 16000)[0]))}
    t = np.arange(400) / 16000
    signal = np.sin(2 * np.pi * 173 * t) + .4 * np.sin(2 * np.pi * 346 * t)
    ref = estimator(signal, 16000)[0]
    checks['gain_invariance'] = bool(np.isclose(ref, estimator(signal * .031, 16000)[0], atol=1e-8))
    checks['dc_invariance'] = bool(np.isclose(ref, estimator(signal + .7, 16000)[0], atol=1e-8))
    if method == 'yin':
        _, difference, support = pitch_estimators.yin_curve(signal, 16000)
        direct = np.array([np.sum((signal[:support] - signal[k:k + support]) ** 2) for k in range(len(difference))])
        checks['fft_direct_difference_max_error'] = float(abs(difference - direct).max())
        assert checks['fft_direct_difference_max_error'] < 1e-10
    clean = frame[(frame.signal_kind.isin(['sine', 'harmonic'])) & np.isinf(frame.snr_db) & frame.truth_hz.between(80, 380)]
    checks['clean_interior_median_cents'] = float(clean.absolute_cents.median())
    checks['clean_interior_p95_cents'] = float(clean.absolute_cents.quantile(.95))
    assert all(checks[k] for k in ('silence_returns_nan', 'constant_returns_nan', 'gain_invariance', 'dc_invariance'))
    assert checks['clean_interior_median_cents'] < 5 and checks['clean_interior_p95_cents'] < 15
    return frame, checks


def method_features(item, method):
    fs, audio = core.load_audio(core.TRAIN / item['file'])
    frames = np.lib.stride_tricks.sliding_window_view(audio, round(fs * .025))[::round(fs * .010)]
    estimates, strengths = zip(*(method_function(method)(frame, fs) for frame in frames))
    return {'f0': np.array(estimates), 'strength': np.array(strengths)}


def infer_estimator(item, features, config, fitted):
    pred, _ = core.infer(item, dict(config, candidate='best', median=1), fitted)
    f0 = np.where(pred, features['f0'], np.nan)
    for start, stop in core.voiced_runs(pred):
        if stop - start >= 3:
            original = f0[start:stop].copy()
            f0[start + 1:stop - 1] = np.median(np.lib.stride_tricks.sliding_window_view(original, 3), axis=1)
    return pred, f0


def eligibility(per_file, summaries):
    champion, candidate = summaries['accepted'], summaries['candidate']
    original = per_file[(per_file.model == 'accepted') & (per_file.split == 'lofo')].set_index('file')
    new = per_file[(per_file.model == 'candidate') & (per_file.split == 'lofo')].set_index('file')
    checks = {'train_mape_relative_10_percent': candidate['train']['average_mape'] <= .9 * champion['train']['average_mape'],
              'lofo_mape_relative_5_percent': candidate['lofo']['average_mape'] <= .95 * champion['lofo']['average_mape'],
              'lofo_f1_drop_at_most_01': candidate['lofo']['macro_f1'] >= champion['lofo']['macro_f1'] - .01,
              'lofo_recall_v_drop_at_most_01': candidate['lofo']['recall_v'] >= champion['lofo']['recall_v'] - .01,
              'lofo_sil_increase_at_most_1': candidate['lofo']['false_voiced_sil'] <= champion['lofo']['false_voiced_sil'] + 1,
              'lofo_no_file_mape_worse_by_over_2pp': bool(((new.average_mape - original.average_mape) <= 2).all()),
              'lofo_phone_f1_std_not_worse': bool(new.loc['phone_F1.wav', 'F0std_mape'] <= original.loc['phone_F1.wav', 'F0std_mape'])}
    return {'checks': {k: bool(v) for k, v in checks.items()}, 'eligible': bool(all(checks.values())),
            'nested_status': 'No newly tuned parameter: fixed candidate evaluated by LOFO; no distinct inner selection estimate.',
            'champion_promoted': False}


def run(method):
    started = time.perf_counter()
    synthetic, checks = synthetic_evaluate(method)
    p_synthetic = audit.csv_write(method + '_synthetic.csv', synthetic)
    audit.json_write(HERE / 'results' / (method + '_synthetic_validation.json'), checks)
    items = core.load_training()
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['ACF']['config']
    features = {item['file']: method_features(item, method) for item in items}
    rows, fit_rows, contours = [], [], []
    for split in ('train', 'lofo'):
        for item in items:
            training = items if split == 'train' else [other for other in items if other is not item]
            fitted = core.fit(training, config)
            fit_rows.append({'split': split, 'held_file': item['file'], 'fit_files': '|'.join(x['file'] for x in training), **fitted})
            for model in ('accepted', 'acf_single_peak_control', 'candidate'):
                if model == 'candidate':
                    pred, f0 = infer_estimator(item, features[item['file']], config, fitted)
                else:
                    selected_config = config if model == 'accepted' else dict(config, candidate='best', clip_range=True)
                    pred, f0 = core.infer(item, selected_config, fitted)
                rows.append({'method': method, 'split': split, 'model': model, **core.score_file(item, pred, f0)})
                if split == 'lofo':
                    for i in range(len(f0)):
                        contours.append({'file': item['file'], 'time_s': item['times'][i], 'label': item['labels'][i],
                                         'model': model, 'pred_voiced': bool(pred[i]), 'estimate_hz': f0[i]})
    per_file = pd.DataFrame(rows)
    p_metrics = audit.csv_write(method + '_metrics_per_file.csv', per_file)
    p_fits = audit.csv_write(method + '_fold_fits.csv', fit_rows)
    p_contours = audit.csv_write(method + '_lofo_contours.csv', contours)
    for row in fit_rows:
        if row['split'] == 'lofo':
            assert row['held_file'] not in row['fit_files'].split('|')
    summaries = {model: {split: core.summarize(per_file[(per_file.model == model) & (per_file.split == split)]) for split in ('train', 'lofo')} for model in per_file.model.unique()}
    decision = eligibility(per_file, summaries)
    poison = dict(items[0], labels=np.full(len(items[0]['labels']), 'unknown'), stats={'F0mean': -1, 'F0std': -1, 'F0num': -1})
    expected = infer_estimator(items[0], features[items[0]['file']], config, core.fit(items, config))
    actual = infer_estimator(poison, features[items[0]['file']], config, core.fit(items, config))
    assert np.array_equal(expected[0], actual[0]) and np.allclose(expected[1], actual[1], equal_nan=True)
    audit.json_write(HERE / 'results' / (method + '_experiment.json'), {'method': method, 'summaries': summaries,
                     'decision': decision, 'synthetic_validation': checks, 'wall_time_s': time.perf_counter() - started,
                     'train_only': True, 'poisoned_gt_inference_invariant': True,
                     'code_sha256': {p: audit.digest(HERE / p) for p in (('pitch_estimators.py' if method == 'yin' else method + '_estimator.py'), 'estimator_experiment.py')},
                     'data_sha256': {item['file']: audit.digest(core.TRAIN / item['file']) for item in items}})
    fig, axes = audit.plt.subplots(1, 2, figsize=(11, 4))
    for kind, group in synthetic.groupby('signal_kind'):
        plot = group[np.isinf(group.snr_db)].groupby('truth_hz').absolute_cents.median()
        axes[0].plot(plot.index, plot, 'o-', label=kind)
    axes[0].set(xlabel='Known synthetic F0 (Hz)', ylabel='Median absolute cents', title=method.upper() + ': clean synthetic')
    axes[0].legend(fontsize=8)
    for kind, group in synthetic[~np.isinf(synthetic.snr_db)].groupby('signal_kind'):
        plot = group.groupby('snr_db').absolute_cents.median()
        axes[1].plot(plot.index, plot, 'o-', label=kind)
    axes[1].set(xlabel='Injected SNR (dB)', ylabel='Median absolute cents', title='Noise stress: simulated, not natural speech')
    audit.save_figure(method + '_synthetic_accuracy', fig, [p_synthetic], 'Pitch error trên tín hiệu tổng hợp có F0 biết trước.', 'Không thay thế kết quả trên WAV thật; đây là kiểm tra thuật toán trong25ms.')
    fig, axes = audit.plt.subplots(1, 3, figsize=(12, 4))
    lofo = per_file[per_file.split == 'lofo']
    for ax, component in zip(axes, ('F0mean_mape', 'F0std_mape', 'F0num_mape')):
        table = lofo.pivot(index='file', columns='model', values=component)
        x = np.arange(len(table))
        for j, model in enumerate(table.columns):
            ax.bar(x + (j - 1) * .25, table[model], width=.25, label=model)
        ax.set_xticks(x, table.index.str.replace('.wav', '', regex=False), rotation=35, ha='right')
        ax.set(ylabel='File statistic MAPE (%)', title=component)
    axes[0].legend(fontsize=7)
    audit.save_figure(method + '_lofo_metrics', fig, [p_metrics], 'Các thành phần MAPE LOFO: accepted ACF/path, ACF single peak, estimator mới.', 'Cùng voiced mask/RMS/median3. Chỉ bốn file; không có pitch GT từng khung.')
    fig, axes = audit.plt.subplots(4, 1, figsize=(11, 9))
    contours_df = pd.DataFrame(contours)
    for ax, item in zip(axes, items):
        for model in ('accepted', 'candidate'):
            plot = contours_df[(contours_df.file == item['file']) & (contours_df.model == model)]
            ax.plot(plot.time_s, plot.estimate_hz, '.', ms=3, label=model)
        ax.set(title=item['file'], ylabel='Estimated F0 (Hz)', ylim=(50, 430))
    axes[0].legend(fontsize=8)
    axes[-1].set_xlabel('Time (s)')
    audit.save_figure(method + '_lofo_contours', fig, [p_contours], 'F0 ước lượng theo thời gian ở held file.', 'Không phải đường truth, không kết luận contour mượt là đúng.')
    for figure in audit.ARTIFACTS:
        figure['generator'] = 'estimator_experiment.py'
        figure['generator_sha256'] = audit.digest(__file__)
        figure['command'] = f'python research_workbench_2026_10_06/estimator_experiment.py {method}'
    audit.json_write(HERE / 'results' / (method + '_figure_manifest.json'), {'figures': audit.ARTIFACTS, 'fold_fit_csv': str(p_fits.relative_to(HERE))})
    summary_table = pd.DataFrame([{'model': model, 'split': split, **value} for model, parts in summaries.items() for split, value in parts.items()])
    report = ['# ' + method.upper() + ' — thí nghiệm pitch estimator', '',
              'Train-only; same frame25/hop10, ACF mask/RMS fold fit, median3. Fixed parameter, không tune/test. Accepted champion giữ nguyên.', '',
              '## Số đo', '', audit.markdown_table(summary_table), '',
              '## Validation synthetic', '', '~~~json', json.dumps(checks, indent=2), '~~~', '',
              '## Gate đăng ký trước', '', '~~~json', json.dumps(decision, indent=2), '~~~', '',
              'Không có bước chọn tham số bên trong cho model fixed này, nên LOFO là đánh giá held-file; không tạo thêm nested score bằng việc chạy lại giống nhau. Với model tune tiếp theo, phải nested selection thật. Dữ liệu train đã dùng chọn champion trước đây, n=4 nên kết quả thăm dò.', '',
              '## Tái lập', '', '~~~powershell', f'python research_workbench_2026_10_06/estimator_experiment.py {method}', '~~~', '',
              '## Figures', '']
    for figure in audit.ARTIFACTS:
        report += [f'![{figure["name"]}]({figure["png"]})', '', figure['limits_vi'], '']
    (HERE / (method.upper() + '_EXPERIMENT_REPORT.md')).write_text('\n'.join(report).rstrip() + '\n', encoding='utf-8')
    print(json.dumps({'method': method, 'decision': decision, 'summaries': summaries, 'checks': checks}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('method', choices=['yin', 'mpm'])
    run(parser.parse_args().method)
