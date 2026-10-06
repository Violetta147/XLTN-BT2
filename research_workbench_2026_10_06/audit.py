import hashlib
import itertools
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PREVIOUS = REPO / 'research_3gt_2026_10_05'
os.environ['MPLBACKEND'] = 'Agg'
os.environ['MPLCONFIGDIR'] = str(HERE / '.mplconfig')
sys.path.insert(0, str(PREVIOUS))

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.io import wavfile
from scipy.signal import spectrogram
from sklearn.metrics import auc, precision_recall_curve, roc_curve

import core

RESULTS = HERE / 'results'
FIGURES = HERE / 'figures'
RESULTS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)
PALETTE = {'v': '#178f72', 'uv': '#c97014', 'sil': '#697785', 'unknown': '#bd213b'}
plt.rcParams.update({'font.size': 10, 'figure.dpi': 110, 'savefig.dpi': 240,
                     'axes.spines.top': False, 'axes.spines.right': False, 'legend.loc': 'upper right'})
ARTIFACTS = []


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def save_figure(name, figure, sources, caption, limits):
    figure.tight_layout()
    for suffix in ('png', 'svg'):
        path = FIGURES / f'{name}.{suffix}'
        figure.savefig(path, bbox_inches='tight')
    ARTIFACTS.append({'name': name, 'png': f'figures/{name}.png', 'svg': f'figures/{name}.svg',
                      'sources': [{'path': str(p.relative_to(HERE)), 'sha256': digest(p)} for p in sources],
                      'caption_vi': caption, 'limits_vi': limits,
                      'generator': 'audit.py', 'generator_sha256': digest(__file__),
                      'command': 'python research_workbench_2026_10_06/audit.py'})
    plt.close(figure)


def csv_write(name, rows):
    path = RESULTS / name
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    frame.to_csv(path, index=False)
    return path


def markdown_table(frame):
    def cell(value):
        return f'{value:.6g}' if isinstance(value, (float, np.floating)) else str(value).replace('|', '\\|')
    rows = ['| ' + ' | '.join(map(str, frame.columns)) + ' |',
            '| ' + ' | '.join(['---'] * len(frame.columns)) + ' |']
    rows.extend('| ' + ' | '.join(cell(value) for value in row) + ' |' for row in frame.itertuples(index=False, name=None))
    return '\n'.join(rows)


def audio_profile(path, item):
    fs, native = wavfile.read(path)
    channels = 1 if native.ndim == 1 else native.shape[1]
    _, audio = core.load_audio(path)
    segments = item['segments']
    gaps = sum(max(0, segments[i + 1][0] - segments[i][1]) for i in range(len(segments) - 1))
    overlaps = sum(max(0, segments[i][1] - segments[i + 1][0]) for i in range(len(segments) - 1))
    native_clips = int(((native == np.iinfo(native.dtype).min) | (native == np.iinfo(native.dtype).max)).sum()) if np.issubdtype(native.dtype, np.integer) else int((np.abs(native) >= 1).sum())
    out = {'file': path.name, 'fs': int(fs), 'channels': channels, 'dtype': str(native.dtype),
           'samples': len(native), 'duration_s': len(native) / fs, 'finite_audio': bool(np.isfinite(audio).all()),
           'native_clip_samples': native_clips, 'dc_mean': float(audio.mean()),
           'rms': float(np.sqrt(np.mean(audio ** 2))), 'exact_zero_fraction': float((audio == 0).mean()),
           'lab_gaps_s': gaps, 'lab_overlaps_s': overlaps, 'lab_end_minus_audio_s': segments[-1][1] - len(audio) / fs,
           'frame_count': len(item['times']), 'boundary_frames': int(item['boundary'].sum()),
           'gt_mean': item['stats']['F0mean'], 'gt_std': item['stats']['F0std'], 'gt_count': item['stats']['F0num'],
           'wav_sha256': digest(path), 'segment_lab_sha256': digest(path.with_suffix('.lab')),
           'stats_lab_sha256': digest(PREVIOUS / 'train_3gt' / path.with_suffix('.lab').name)}
    for label in PALETTE:
        out[label + '_frames'] = int((item['labels'] == label).sum())
        out[label + '_seconds'] = float(sum(b - a for a, b, lab in segments if lab == label))
    centers = (np.arange(len(item['times'])) * round(fs * .01) + round(fs * .025) / 2) / fs
    actual_labels = np.array([next((lab for a, b, lab in segments if a <= t < b), 'unknown') for t in centers])
    out['cache_times_match'] = bool(np.allclose(centers, item['times'], atol=1e-12))
    out['cache_labels_match'] = bool(np.array_equal(actual_labels, item['labels']))
    assert out['cache_times_match'] and out['cache_labels_match'], 'Stale cache labels/times'
    assert out['finite_audio'] and overlaps < 1e-9
    assert np.array_equal(item['times'], core.frame_features(path, 25)['times'])
    return out, audio


def frame_feature_table(item, audio):
    fs = item['fs']
    frames = np.lib.stride_tricks.sliding_window_view(audio, round(fs * .025))[::round(fs * .01)]
    centered = frames - frames.mean(axis=1, keepdims=True)
    power = np.abs(np.fft.rfft(centered * np.hanning(centered.shape[1]), axis=1)) ** 2
    power = np.maximum(power, 1e-20)
    frequencies = np.fft.rfftfreq(centered.shape[1], 1 / fs)
    flatness = np.exp(np.log(power).mean(axis=1)) / power.mean(axis=1)
    centroid = (power * frequencies).sum(axis=1) / power.sum(axis=1)
    zcr = (np.signbit(centered[:, 1:]) != np.signbit(centered[:, :-1])).mean(axis=1)
    return pd.DataFrame({'file': item['file'], 'time_s': item['times'], 'label': item['labels'],
                         'boundary': item['boundary'], 'relative_rms': item['relative_rms'],
                         'acf_score': item['ACF_score'], 'amdf_score': item['AMDF_score'],
                         'zcr': zcr, 'spectral_flatness': flatness, 'spectral_centroid_hz': centroid})


def main():
    started = time.perf_counter()
    begin = datetime.now(timezone.utc).isoformat()
    notebooks_before = {str(p.relative_to(REPO)): digest(p) for p in REPO.rglob('*.ipynb')}
    frozen = json.loads((PREVIOUS / 'results/frozen_config.json').read_text(encoding='utf-8'))
    items = core.load_training(25)
    profile, audio_by_file, features = [], {}, []
    for item in items:
        path = REPO / 'TinHieuHuanLuyen' / item['file']
        row, audio = audio_profile(path, item)
        profile.append(row)
        audio_by_file[item['file']] = audio
        features.append(frame_feature_table(item, audio))
    profile = pd.DataFrame(profile)
    p_profile = csv_write('training_data_profile.csv', profile)
    p_features = csv_write('training_features.csv', pd.concat(features, ignore_index=True))
    original = {'algorithm': 'ACF', 'frame_ms': 25}
    accepted = frozen['models']['ACF']['config']
    baseline_metrics, predictions, summaries = [], {}, []
    saved = pd.read_csv(PREVIOUS / 'results/final_train_test_per_file.csv')
    for version, config in [('baseline', original), ('improved', accepted)]:
        fitted = core.fit(items, config)
        full = core.evaluate(items, config, fitted)
        cv = core.lofo(items, config)
        for kind, frame in [('train', full), ('lofo', cv)]:
            frame = frame.copy()
            frame['version'], frame['kind'] = version, kind
            baseline_metrics.append(frame)
            summaries.append({'version': version, 'kind': kind, **core.summarize(frame)})
        reference = saved[(saved.model == 'ACF') & (saved.split == 'train') & (saved.version == version)].set_index('file')
        for _, row in full.iterrows():
            for key in ('F0mean', 'F0std', 'F0num', 'average_mape', 'TP', 'TN', 'FP', 'FN', 'false_voiced_sil'):
                assert np.isclose(row[key], reference.loc[row.file, key], rtol=0, atol=1e-8), (version, row.file, key, row[key], reference.loc[row.file, key])
        predictions[version] = {item['file']: core.infer(item, config, fitted) for item in items}
    p_metrics = csv_write('baseline_reproduction_per_file.csv', pd.concat(baseline_metrics, ignore_index=True))
    p_summary = csv_write('baseline_reproduction_summary.csv', summaries)
    frame_rows, decomposition, oracle, stratified, ambiguity = [], [], [], [], []
    for version in predictions:
        for item in items:
            pred, f0 = predictions[version][item['file']]
            labels = item['labels']
            finite = np.isfinite(f0)
            values = f0[finite]
            mean, variance = values.mean(), values.var()
            contribution_sum = 0
            for label in PALETTE:
                subset = f0[finite & (labels == label)]
                if len(subset):
                    within = len(subset) / len(values) * subset.var()
                    between = len(subset) / len(values) * (subset.mean() - mean) ** 2
                    contribution_sum += within + between
                    decomposition.append({'version': version, 'file': item['file'], 'label': label,
                                          'count': len(subset), 'mean': subset.mean(), 'std': subset.std(),
                                          'within_contribution_hz2': within, 'between_contribution_hz2': between,
                                          'variance_share': (within + between) / variance if variance else 0})
            assert np.isclose(contribution_sum, variance, atol=1e-8)
            for name, mask in [('all', finite), ('oracle_no_sil', finite & (labels != 'sil')),
                               ('oracle_v', finite & (labels == 'v')),
                               ('oracle_v_interior', finite & (labels == 'v') & ~item['boundary'])]:
                subset = f0[mask]
                oracle.append({'version': version, 'file': item['file'], 'diagnostic': name,
                               'count': len(subset), 'mean': subset.mean() if len(subset) else np.nan,
                               'std': subset.std() if len(subset) else np.nan,
                               'std_mape': 100 * abs(subset.std() - item['stats']['F0std']) / item['stats']['F0std'] if len(subset) else np.nan,
                               'deployable': name == 'all'})
            for label in ('v', 'uv', 'sil'):
                for boundary in (False, True):
                    mask = (labels == label) & (item['boundary'] == boundary)
                    errors = ~pred[mask] if label == 'v' else pred[mask]
                    stratified.append({'version': version, 'file': item['file'], 'label': label,
                                       'boundary': boundary, 'n': int(mask.sum()), 'error_count': int(errors.sum()),
                                       'error_rate': float(errors.mean()) if len(errors) else np.nan})
            for i, t in enumerate(item['times']):
                error = 'FN_V' if labels[i] == 'v' and not pred[i] else 'FP_UV' if labels[i] == 'uv' and pred[i] else 'FP_SIL' if labels[i] == 'sil' and pred[i] else 'correct_class'
                frame_rows.append({'version': version, 'file': item['file'], 'time_s': t,
                                   'label': labels[i], 'boundary': bool(item['boundary'][i]),
                                   'relative_rms': item['relative_rms'][i], 'acf_score': item['ACF_score'][i],
                                   'pred_voiced': bool(pred[i]), 'finite_f0': bool(finite[i]), 'f0_hz': f0[i],
                                   'error': error, 'pred_without_finite_f0': bool(pred[i] and not finite[i]),
                                   'f0_outside_range': bool(finite[i] and not 70 <= f0[i] <= 400)})
                if finite[i]:
                    candidate = item['ACF_candidate_f0'][i]
                    strength = item['ACF_candidate_strength'][i]
                    valid = np.isfinite(candidate)
                    for multiple in (2, 3):
                        match = valid & (np.abs(np.log2(candidate / f0[i]) - np.log2(multiple)) < .07)
                        ambiguity.append({'version': version, 'file': item['file'], 'time_s': t, 'label': labels[i],
                                          'multiple': multiple, 'alternative_exists': bool(match.any()),
                                          'nearest_score_gap': float(strength[valid].max() - strength[match].max()) if match.any() else np.nan,
                                          'is_proven_pitch_error': False})
    p_frames = csv_write('frame_errors.csv', frame_rows)
    p_variance = csv_write('variance_decomposition.csv', decomposition)
    p_oracle = csv_write('oracle_diagnostics.csv', oracle)
    p_strata = csv_write('boundary_errors.csv', stratified)
    p_ambiguity = csv_write('candidate_ambiguity.csv', ambiguity)
    thresholds = []
    energy_threshold = core.fit(items, accepted)['energy_threshold']
    for threshold in np.linspace(0, 1, 201):
        for with_energy in (False, True):
            rows = []
            for item in items:
                pred = item['ACF_score'] >= threshold
                if with_energy:
                    pred &= item['relative_rms'] >= energy_threshold
                rows.append(core.classification(item['labels'], pred))
            df = pd.DataFrame(rows)
            thresholds.append({'threshold': threshold, 'energy': with_energy,
                               'macro_file_balanced_accuracy': df.balanced_accuracy.mean(),
                               'macro_file_recall_v': df.recall_v.mean(), 'false_voiced_sil': df.false_voiced_sil.sum()})
    p_threshold = csv_write('threshold_diagnostic.csv', thresholds)
    metrics = pd.read_csv(p_metrics)
    diffs = metrics[metrics.kind == 'lofo'].pivot(index='file', columns='version', values='average_mape')
    delta = (diffs.improved - diffs.baseline).to_numpy()
    rng = np.random.default_rng(20261006)
    bootstrap = delta[rng.integers(0, len(delta), size=(10000, len(delta)))].mean(axis=1)
    sign_flips = np.array([np.mean(delta * signs) for signs in itertools.product((-1, 1), repeat=len(delta))])
    stats = {'n_independent_units': 4, 'unit': 'file', 'paired_mean_delta_pp': float(delta.mean()),
             'descriptive_file_bootstrap_95_interval_pp': [float(x) for x in np.quantile(bootstrap, [.025, .975])],
             'exploratory_exact_two_sided_sign_flip_p': float((np.abs(sign_flips) >= abs(delta.mean()) - 1e-12).mean()),
             'warning': 'Only 4 files; earlier selected accepted configuration and exploratory repeated analyses. Not a confirmatory hypothesis test or population confidence guarantee.'}
    json_write(RESULTS / 'paired_file_stability.json', stats)
    p_bootstrap = csv_write('paired_file_bootstrap.csv', {'delta_pp': bootstrap})
    cycles = pd.DataFrame([{'f0_hz': f, 'frame_ms': w, 'cycles': f * w / 1000} for w in (20, 25, 30) for f in range(70, 401)])
    p_cycles = csv_write('frame_cycle_support.csv', cycles)

    fig, ax = plt.subplots(figsize=(9, 4))
    bottom = np.zeros(len(profile))
    for label in ('v', 'uv', 'sil', 'unknown'):
        values = profile[label + '_frames'].to_numpy()
        ax.bar(profile.file.str.replace('.wav', '', regex=False), values, bottom=bottom, label=label.upper(), color=PALETTE[label])
        bottom += values
    ax.set(ylabel='Frame count (25 ms / 10 ms)', title='Training label support — center labels')
    ax.legend(ncol=4)
    save_figure('01_label_support', fig, [p_profile], 'Số khung theo nhãn thật của bốn file train.', 'Khung chồng nhau; không phải mẫu độc lập.')

    frames_df = pd.read_csv(p_frames)
    for item in items:
        stem = Path(item['file']).stem
        audio = audio_by_file[item['file']]
        fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
        axis_time = np.arange(len(audio)) / item['fs']
        axes[0].plot(axis_time, audio, linewidth=.45, color='#344b69')
        for a, b, label in item['segments']:
            axes[0].axvspan(a, b, alpha=.12, color=PALETTE[label])
        axes[0].set(ylabel='Normalized waveform', title=stem + ': waveform, labels and F0 estimates')
        for version, color in [('baseline', '#c95847'), ('improved', '#178f72')]:
            _, f0 = predictions[version][item['file']]
            axes[1].plot(item['times'], f0, '.', markersize=3, label=version, color=color)
        axes[1].axhline(item['stats']['F0mean'], ls='--', color='black', label='file GT mean (not frame reference)')
        axes[1].set(xlabel='Time (s)', ylabel='F0 (Hz)', ylim=(50, 430))
        axes[1].legend(fontsize=8)
        save_figure('02_contour_' + stem, fig, [p_frames, p_profile], 'Waveform, nhãn đoạn và F0 trước/sau của ' + stem + '.', 'Đường GT mean chỉ là chuẩn cả file, không phải contour chuẩn từng khung.')
        window_samples = round(item['fs'] * .025)
        nfft = 2 ** int(np.ceil(np.log2(window_samples)))
        frequencies, tt, spectrum = spectrogram(audio, item['fs'], nperseg=window_samples, noverlap=round(item['fs'] * .015), nfft=nfft)
        plotted_band = frequencies <= 2000
        frequencies, spectrum = frequencies[plotted_band], spectrum[plotted_band]
        spec_csv = csv_write('spectrogram_' + stem + '.csv', pd.DataFrame({'time_s': np.tile(tt, len(frequencies)), 'frequency_hz': np.repeat(frequencies, len(tt)), 'power_db': 10 * np.log10(spectrum.ravel() + 1e-20)}))
        fig, ax = plt.subplots(figsize=(11, 4))
        image = ax.pcolormesh(tt, frequencies, 10 * np.log10(spectrum + 1e-20), shading='auto', cmap='magma')
        fig.colorbar(image, ax=ax, label='PSD (dB relative to 1 signal-unit²/Hz)')
        ax.plot(item['times'], predictions['improved'][item['file']][1], '.', color='#28dbb4', ms=2, label='accepted F0 estimate')
        ax.set(ylim=(0, 2000), xlabel='Time (s)', ylabel='Frequency (Hz)', title=stem + ': spectrum and estimated F0')
        ax.legend()
        save_figure('03_spectrogram_' + stem, fig, [spec_csv, p_frames], 'Phổ thời gian và F0 ước lượng của ' + stem + '.', 'Không phải xác nhận mọi khung F0 bằng ground truth; đồ thị phổ là chẩn đoán.')

    feature_df = pd.read_csv(p_features)
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    for ax, feature in zip(axes.flat, ('relative_rms', 'acf_score', 'amdf_score', 'zcr', 'spectral_flatness', 'spectral_centroid_hz')):
        for label in ('v', 'uv', 'sil'):
            values = feature_df.loc[feature_df.label == label, feature]
            ax.hist(values, bins=35, density=True, histtype='step', lw=1.4, color=PALETTE[label], label=label.upper())
        ax.set(title=feature, ylabel='Density')
    axes.flat[0].legend()
    save_figure('04_feature_distributions', fig, [p_features], 'Phân bố đặc trưng theo V/UV/SIL.', 'Dữ liệu train gộp; histogram không chứng minh khả năng tổng quát hay feature importance nhân quả.')

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    roc_rows = []
    for item in items:
        mask = np.isin(item['labels'], ('v', 'uv'))
        y, score = item['labels'][mask] == 'v', item['ACF_score'][mask]
        fpr, tpr, cutoffs = roc_curve(y, score)
        precision, recall, _ = precision_recall_curve(y, score)
        axes[0].plot(fpr, tpr, label=Path(item['file']).stem + f' AUC={auc(fpr, tpr):.3f}')
        axes[1].plot(recall, precision, label=Path(item['file']).stem)
        roc_rows.extend({'file': item['file'], 'fpr': a, 'tpr': b, 'cutoff': c} for a, b, c in zip(fpr, tpr, cutoffs))
    p_roc = csv_write('roc_training.csv', roc_rows)
    axes[0].set(xlabel='False positive rate (UV)', ylabel='True positive rate (V)', title='ACF score ROC: training diagnostic')
    axes[1].set(xlabel='Recall V', ylabel='Precision V', title='Training precision–recall')
    for ax in axes:
        ax.legend(fontsize=7)
    save_figure('05_roc_pr', fig, [p_roc, p_features], 'ROC và precision–recall của ACF score theo từng file.', 'SIL không thuộc ROC này. Chưa hiệu chỉnh score thành xác suất. Các khung tương quan.')

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    train_metrics = metrics[metrics.kind == 'train']
    for ax, key in zip(axes, ('F0mean_mape', 'F0std_mape', 'F0num_mape')):
        table = train_metrics.pivot(index='file', columns='version', values=key)
        x = np.arange(len(table))
        for off, version, color in [(-.18, 'baseline', '#c95847'), (.18, 'improved', '#178f72')]:
            ax.bar(x + off, table[version], width=.36, color=color, label=version)
        ax.set_xticks(x, table.index.str.replace('.wav', '', regex=False), rotation=35, ha='right')
        ax.set(title=key.replace('_mape', ''), ylabel='File-level MAPE (%)')
    axes[0].legend(fontsize=8)
    save_figure('06_component_mape', fig, [p_metrics], 'Ba thành phần MAPE của ACF trước/sau trên train.', 'Mean/std/count là thống kê cả file; không phải MAPE F0 từng khung.')

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, version in zip(axes[:2], ('baseline', 'improved')):
        sums = train_metrics[train_metrics.version == version][['TP', 'TN', 'FP', 'FN']].sum()
        matrix = np.array([[sums.TP, sums.FN], [sums.FP, sums.TN]])
        ax.imshow(matrix, cmap='Blues')
        for (i, j), value in np.ndenumerate(matrix):
            ax.text(j, i, int(value), ha='center', va='center', color='white' if value > matrix.max() / 2 else 'black')
        ax.set(xticks=[0, 1], xticklabels=['pred V', 'pred UV'], yticks=[0, 1], yticklabels=['true V', 'true UV'], title=version)
    table = train_metrics.pivot(index='file', columns='version', values='false_voiced_sil')
    x = np.arange(len(table))
    axes[2].bar(x - .18, table.baseline, .36, label='baseline', color='#c95847')
    axes[2].bar(x + .18, table.improved, .36, label='improved', color='#178f72')
    axes[2].set_xticks(x, table.index.str.replace('.wav', '', regex=False), rotation=35, ha='right')
    axes[2].set(title='SIL → predicted voiced (reported separately)', ylabel='Frame count')
    axes[2].legend(fontsize=7)
    save_figure('07_classification_tradeoff', fig, [p_metrics], 'Ma trận V/UV và số khung SIL bị gán hữu thanh.', 'SIL được báo riêng; giảm SIL vẫn có thể làm tăng FN V.')

    fig, axes = plt.subplots(4, 1, figsize=(11, 8))
    error_colors = {'FN_V': '#c95847', 'FP_UV': '#dd9c22', 'FP_SIL': '#435ec0'}
    for ax, item in zip(axes, items):
        frame = frames_df[frames_df.file == item['file']]
        for y, version in enumerate(('baseline', 'improved')):
            for error, color in error_colors.items():
                subset = frame[(frame.version == version) & (frame.error == error)]
                ax.scatter(subset.time_s, np.full(len(subset), y), s=15, marker='|', color=color, label=error if y == 0 else None)
        ax.set(yticks=[0, 1], yticklabels=['baseline', 'improved'], title=item['file'], xlabel='Time (s)', ylim=(-.5, 1.5))
    axes[0].legend(ncol=3, fontsize=7)
    save_figure('08_error_timeline', fig, [p_frames], 'Vị trí lỗi V/UV/SIL trước/sau theo thời gian.', 'Đây là lỗi lớp theo nhãn đoạn; không chấm độ đúng cao độ của từng khung.')

    variance_df = pd.read_csv(p_variance)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, version in zip(axes, ('baseline', 'improved')):
        group = variance_df[variance_df.version == version].copy()
        group['contribution'] = group.within_contribution_hz2 + group.between_contribution_hz2
        table = group.pivot(index='file', columns='label', values='contribution').fillna(0)
        bottom = np.zeros(len(table))
        for label in ('v', 'uv', 'sil'):
            values = table[label] if label in table else np.zeros(len(table))
            ax.bar(table.index.str.replace('.wav', '', regex=False), values, bottom=bottom, label=label.upper(), color=PALETTE[label])
            bottom += values
        ax.set(title=version, ylabel='Variance contribution (Hz²)')
        ax.tick_params(axis='x', rotation=30)
    axes[0].legend()
    save_figure('09_variance_by_label', fig, [p_variance], 'Phân rã phương sai F0 theo nhãn: within và between cộng đúng tổng phương sai.', 'Tỷ lệ đóng góp phương sai không phải tỷ lệ gây MAPE; oracle nhãn chỉ chẩn đoán.')

    fig, axes = plt.subplots(1, 3, figsize=(11, 4))
    strata_df = pd.read_csv(p_strata)
    for ax, label in zip(axes, ('v', 'uv', 'sil')):
        for version, color in [('baseline', '#c95847'), ('improved', '#178f72')]:
            group = strata_df[(strata_df.label == label) & (strata_df.version == version)].groupby('boundary')[['n', 'error_count']].sum()
            ax.plot(group.index.astype(int), group.error_count / group.n, 'o-', label=version, color=color)
        ax.set(xticks=[0, 1], xticklabels=['interior', 'boundary'], title=label.upper(), ylabel='Observed class error rate')
    axes[0].legend()
    save_figure('10_boundary_error_rates', fig, [p_strata], 'Lỗi lớp ở khung sát ranh giới và khung bên trong.', 'So sánh mô tả, không coi các khung chồng nhau là quan sát độc lập.')

    threshold_df = pd.read_csv(p_threshold)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for energy, color in [(False, '#c95847'), (True, '#178f72')]:
        group = threshold_df[threshold_df.energy == energy]
        for ax, key in zip(axes, ('macro_file_balanced_accuracy', 'macro_file_recall_v', 'false_voiced_sil')):
            ax.plot(group.threshold, group[key], color=color, label='RMS gate' if energy else 'no RMS')
            ax.set(title=key, xlabel='ACF score threshold')
            ax.axvline(frozen['models']['ACF']['fitted']['pitch_threshold'], color='gray', ls='--')
    axes[0].legend(fontsize=8)
    save_figure('11_threshold_sensitivity', fig, [p_threshold], 'Độ nhạy ngưỡng ACF: balanced accuracy, recall V và lỗi SIL.', 'Dùng train đã biết để chẩn đoán; không chọn threshold mới từ đồ thị này hay từ test.')

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(diffs.index.str.replace('.wav', '', regex=False), delta, color='#178f72')
    axes[0].axhline(0, color='gray', lw=.7)
    axes[0].set(ylabel='Accepted − original LOFO MAPE (pp)', title='Paired file differences')
    axes[0].tick_params(axis='x', rotation=30)
    axes[1].hist(bootstrap, bins=45, color='#344b69', alpha=.8)
    axes[1].axvline(0, color='gray', ls='--')
    axes[1].set(xlabel='Mean paired delta (pp)', ylabel='Bootstrap draws', title='File bootstrap: descriptive, n=4')
    save_figure('12_file_stability', fig, [p_metrics, p_bootstrap], 'Chênh lệch LOFO theo file và bootstrap lấy file làm đơn vị.', 'Chỉ n=4 và cấu hình từng được chọn trên train; không phải kiểm định xác nhận.')

    fig, ax = plt.subplots(figsize=(9, 4))
    for width, group in cycles.groupby('frame_ms'):
        ax.plot(group.f0_hz, group.cycles, label=str(width) + ' ms')
    ax.axhline(2, color='gray', ls='--', label='2 cycles (reference guide only)')
    ax.set(xlabel='F0 (Hz)', ylabel='Cycles within one frame', title='Finite window support: low pitch has few cycles')
    ax.legend()
    save_figure('13_frame_support', fig, [p_cycles], 'Số chu kỳ nằm trong cửa sổ 20/25/30 ms theo F0.', 'Công thức hình học F0×duration, không phải phép đo pitch accuracy.')

    selected_features = ['relative_rms', 'acf_score', 'amdf_score', 'zcr', 'spectral_flatness', 'spectral_centroid_hz']
    corr = feature_df[selected_features].corr()
    p_corr = csv_write('feature_correlation.csv', corr.reset_index())
    fig, ax = plt.subplots(figsize=(8, 6))
    image = ax.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)), corr.columns, rotation=45, ha='right')
    ax.set_yticks(range(len(corr)), corr.index)
    fig.colorbar(image, ax=ax, label='Pearson r (descriptive)')
    for (i, j), value in np.ndenumerate(corr.to_numpy()):
        ax.text(j, i, f'{value:.2f}', ha='center', va='center', fontsize=8)
    ax.set_title('Feature dependence across training frames')
    save_figure('14_feature_correlation', fig, [p_corr, p_features], 'Tương quan đặc trưng để nhận ra thông tin trùng lặp.', 'Pooled frames tương quan thời gian; không suy diễn nhân quả hay p-value độc lập.')

    environment = {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
                   'numpy': np.__version__, 'scipy': scipy.__version__, 'pandas': pd.__version__,
                   'matplotlib': matplotlib.__version__, 'sklearn': sklearn.__version__}
    json_write(RESULTS / 'environment.json', environment)
    json_write(RESULTS / 'figure_manifest.json', {'created_at_utc': begin, 'figures': ARTIFACTS})
    notebooks_after = {str(p.relative_to(REPO)): digest(p) for p in REPO.rglob('*.ipynb')}
    assert notebooks_before == notebooks_after, 'Notebook changed during audit'
    for item in items:
        poisoned = dict(item, stats={'F0mean': -999., 'F0std': 999999., 'F0num': -1}, labels=np.full(len(item['labels']), 'unknown'))
        expected = predictions['improved'][item['file']]
        actual = core.infer(poisoned, accepted, frozen['models']['ACF']['fitted'])
        assert np.array_equal(expected[0], actual[0]) and np.allclose(expected[1], actual[1], equal_nan=True), 'Inference depends on scoring GT'
    validation = {'baseline_reproduced': True, 'cache_labels_times_match': True,
                  'notebook_hashes_unchanged': True, 'notebook_count': len(notebooks_before),
                  'poisoned_gt_inference_invariant': True, 'variance_identity_verified': True,
                  'raw_training_manifest': profile[['file', 'wav_sha256', 'segment_lab_sha256', 'stats_lab_sha256']].to_dict('records'),
                  'figure_count': len(ARTIFACTS), 'test_files_read_in_this_audit': False,
                  'started_at_utc': begin, 'wall_time_s': time.perf_counter() - started}
    json_write(RESULTS / 'audit_validation.json', validation)
    report = ['# H00 — audit sâu và tái lập baseline', '',
              'Chạy local, train-only, không đổi thuật toán hoặc notebook đã giao.', '',
              '## Kiểm tra thực tế', '',
              '- Tái lập ACF original và accepted khớp saved CSV, tolerance 1e-8; số nguyên khớp.',
              '- Cache times/labels khớp chia khung và nhãn đọc độc lập.',
              '- Poison GT trong input inference không làm thay đổi pred/F0; fit vẫn cần nhãn training.',
              '- Đẳng thức phân rã phương sai within/between theo nhãn được kiểm tra bằng code.',
              f'- {len(notebooks_before)} notebook giữ nguyên hash; xuất {len(ARTIFACTS)} figure PNG/SVG.', '',
              '## Các số đo chính', '', markdown_table(pd.DataFrame(summaries)), '',
              '## Dữ liệu', '', markdown_table(profile[['file', 'fs', 'duration_s', 'frame_count', 'v_frames', 'uv_frames', 'sil_frames', 'gt_count', 'native_clip_samples', 'lab_end_minus_audio_s']]), '',
              '## Độ ổn định theo file', '', json.dumps(stats, indent=2, ensure_ascii=False), '',
              '## Giới hạn cần giữ', '',
              'GT mean/std/count không xác minh pitch từng thời điểm. Count hữu hạn không đồng nhất số nhãn V.',
              'Frame windows chồng nhau; n độc lập không bằng số hàng của CSV. F/M và phone/studio chỉ là phân nhóm tên file.',
              'ROC/PR và threshold curves là train diagnostic, không phải test độc lập hoặc calibrated probability.',
              'Ứng viên gần tỉ lệ 2/3 là dấu hiệu ambiguity, không phải octave-error rate đã biết truth.',
              'Bootstrap/sign-flip với 4 file là thăm dò mô tả; không chứng minh thuật toán tổng quát tốt hơn.', '',
              '## Tái lập', '', '~~~powershell', 'python research_workbench_2026_10_06/audit.py', '~~~', '',
              '## Figures', '']
    for artifact in ARTIFACTS:
        report.extend([f'### {artifact["name"]}', '', artifact['caption_vi'], '', f'![{artifact["name"]}]({artifact["png"]})', '', artifact['limits_vi'], ''])
    (HERE / 'H00_AUDIT_REPORT.md').write_text('\n'.join(report).rstrip() + '\n', encoding='utf-8')
    print(json.dumps(validation, indent=2), flush=True)


if __name__ == '__main__':
    main()
