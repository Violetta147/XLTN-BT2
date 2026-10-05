import json
import os

os.environ['MPLBACKEND'] = 'Agg'
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from core import HERE, TRAIN, RESULTS, load_audio, load_training, fit, infer, evaluate, lofo, summarize
from events import record


CONFIGS = {
    'ACF': {'algorithm': 'ACF', 'frame_ms': 25},
    'AMDF': {'algorithm': 'AMDF', 'frame_ms': 25},
    'AMDF_energy': {'algorithm': 'AMDF', 'frame_ms': 25, 'energy': True},
    'GMM_ACF': {'algorithm': 'ACF', 'frame_ms': 20, 'threshold_method': 'gmm'},
    'GMM_AMDF': {'algorithm': 'AMDF', 'frame_ms': 25, 'threshold_method': 'gmm'},
}


def main():
    data = {frame: load_training(frame) for frame in (20, 25, 30)}
    all_rows, cv_rows, decomposition, frame_rows, oracle, fits = [], [], [], [], [], {}
    for model, config in CONFIGS.items():
        items = data[config['frame_ms']]
        fitted = fit(items, config)
        fits[model] = fitted
        rows = evaluate(items, config, fitted)
        cv = lofo(items, config)
        rows['model'], cv['model'] = model, model
        all_rows.append(rows)
        cv_rows.append(cv)
        for item in items:
            pred, f0 = infer(item, config, fitted)
            finite = np.isfinite(f0)
            mean = f0[finite].mean()
            n = finite.sum()
            contributions = []
            for label in ('v', 'uv', 'sil', 'unknown'):
                values = f0[finite & (item['labels'] == label)]
                if len(values):
                    contribution = len(values) / n * (values.var() + (values.mean() - mean) ** 2)
                    contributions.append(contribution)
                    decomposition.append({'model': model, 'file': item['file'], 'label': label,
                                          'count': len(values), 'mean': values.mean(), 'std': values.std(),
                                          'variance_contribution': contribution,
                                          'variance_share': contribution / f0[finite].var()})
            assert np.isclose(sum(contributions), f0[finite].var())
            for kind, mask in [('all_predictions', finite), ('oracle_v_only', finite & (item['labels'] == 'v')),
                               ('oracle_v_interior', finite & (item['labels'] == 'v') & ~item['boundary'])]:
                values = f0[mask]
                std = float(values.std())
                oracle.append({'model': model, 'file': item['file'], 'diagnostic_only': kind,
                               'num': len(values), 'mean': values.mean(), 'std': std,
                               'std_mape': 100 * abs(std - item['stats']['F0std']) / item['stats']['F0std']})
            if model in ('ACF', 'AMDF_energy'):
                algorithm = config['algorithm']
                for index in range(len(f0)):
                    candidates = item[algorithm + '_candidate_f0'][index]
                    strength = item[algorithm + '_candidate_strength'][index]
                    finite_c = np.isfinite(candidates)
                    double = finite_c & (np.abs(np.log2(candidates / f0[index]) - 1) < .08) if finite[index] else np.zeros(12, bool)
                    frame_rows.append({'model': model, 'file': item['file'], 'time_s': item['times'][index],
                                       'label': item['labels'][index], 'boundary': item['boundary'][index],
                                       'relative_rms': item['relative_rms'][index], 'score': item[algorithm + '_score'][index],
                                       'f0': f0[index], 'candidate_count': int(finite_c.sum()),
                                       'double_f0_candidate': float(candidates[double][0]) if double.any() else np.nan,
                                       'double_candidate_score_gap': float(strength.max() - strength[double].max()) if double.any() else np.nan})
    full, cv = pd.concat(all_rows, ignore_index=True), pd.concat(cv_rows, ignore_index=True)
    full.to_csv(RESULTS / 'baseline_train.csv', index=False)
    cv.to_csv(RESULTS / 'baseline_lofo.csv', index=False)
    pd.DataFrame(decomposition).to_csv(RESULTS / 'variance_decomposition.csv', index=False)
    pd.DataFrame(frame_rows).to_csv(RESULTS / 'baseline_training_frames.csv', index=False)
    pd.DataFrame(oracle).to_csv(RESULTS / 'oracle_diagnostics_not_deployable.csv', index=False)
    summary = {model: {'full_train': summarize(full[full.model == model]),
                       'lofo': summarize(cv[cv.model == model]), 'fit': fits[model], 'config': CONFIGS[model]}
               for model in CONFIGS}
    assert np.isclose(summary['ACF']['full_train']['average_mape'], 29.83471057738782, atol=1e-8)
    assert np.isclose(fits['ACF']['pitch_threshold'], .6840817762403983, atol=1e-10)
    assert np.isclose(fits['AMDF_energy']['energy_threshold'], .061544615883604575)
    (RESULTS / 'baseline_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    metadata = []
    for item in data[25]:
        fs, signal = load_audio(TRAIN / item['file'])
        spectrum = abs(np.fft.rfft(signal)) ** 2
        frequencies = np.fft.rfftfreq(len(signal), 1 / fs)
        rows = {'file': item['file'], 'fs': fs, 'duration_s': item['duration_s'],
                'samples': len(signal), 'peak_amplitude': abs(signal).max(),
                'clipped_fraction': (abs(signal) > .999).mean(),
                'dc_mean': signal.mean(), 'band_above_1000_fraction': spectrum[frequencies > 1000].sum() / spectrum.sum(),
                'GT_mean': item['stats']['F0mean'], 'GT_std': item['stats']['F0std'], 'GT_num': item['stats']['F0num'],
                'boundary_fraction': item['boundary'].mean(),
                'GT_cycles_per_frame_at_mean': .025 * item['stats']['F0mean']}
        for label in ('v', 'uv', 'sil'):
            mask = item['labels'] == label
            rows[label + '_frames'] = int(mask.sum())
            rows[label + '_rms_median'] = np.median(item['rms'][mask])
        rows['V_to_SIL_rms_ratio_dB_proxy_not_SNR'] = 20 * np.log10(rows['v_rms_median'] / rows['sil_rms_median'])
        metadata.append(rows)
    pd.DataFrame(metadata).to_csv(RESULTS / 'training_dataset_profile.csv', index=False)
    fig, axes = plt.subplots(4, 1, figsize=(12, 11), constrained_layout=True)
    for ax, item in zip(axes, data[25]):
        pred, f0 = infer(item, CONFIGS['ACF'], fits['ACF'])
        for label, color in [('v', '#1976d2'), ('uv', '#ef6c00'), ('sil', '#c62828')]:
            mask = item['labels'] == label
            ax.scatter(item['times'][mask], f0[mask], s=12, c=color, label=label)
        ax.axhline(item['stats']['F0mean'], color='black', ls='--', label='LAB mean')
        ax.axhspan(item['stats']['F0mean'] - item['stats']['F0std'], item['stats']['F0mean'] + item['stats']['F0std'], alpha=.10)
        ax.set(title=item['file'] + ' — baseline ACF', ylim=(60, 410), ylabel='F0 (Hz)', xlabel='Time (s)')
        ax.legend(ncol=4, fontsize=8)
        ax.grid(alpha=.2)
    fig.savefig(HERE / 'figures' / 'baseline_train_contours.png', dpi=160)
    plt.close(fig)
    brief = '; '.join(f'{model} {summary[model]["full_train"]["average_mape"]:.2f}% (LOFO {summary[model]["lofo"]["average_mape"]:.2f}%)' for model in CONFIGS)
    record('H0: tái lập baseline và cách tính ba MAPE trên train', brief,
           'ACF khớp 29.8347105774% và ngưỡng gốc; không phát hiện lỗi ghép file/công thức. Chuyển sang chẩn đoán F0std.')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
