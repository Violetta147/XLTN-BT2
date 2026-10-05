import json
import os

os.environ['MPLBACKEND'] = 'Agg'
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import core
from baseline_audit import CONFIGS
from events import record


def main():
    frames = pd.read_csv(core.RESULTS / 'baseline_training_frames.csv')
    variance = pd.read_csv(core.RESULTS / 'variance_decomposition.csv')
    oracle = pd.read_csv(core.RESULTS / 'oracle_diagnostics_not_deployable.csv')
    data = core.load_training(25)
    phone = next(x for x in data if x['file'] == 'phone_F1.wav')
    fitted = core.fit(data, CONFIGS['ACF'])
    pred, f0 = core.infer(phone, CONFIGS['ACF'], fitted)
    low = np.isfinite(f0) & (f0 < .6 * phone['stats']['F0mean'])
    evidence = []
    for index in np.flatnonzero(low):
        candidates, strengths = phone['ACF_candidate_f0'][index], phone['ACF_candidate_strength'][index]
        double = np.isfinite(candidates) & (np.abs(np.log2(candidates / f0[index]) - 1) < .08)
        evidence.append({'time_s': phone['times'][index], 'label': phone['labels'][index],
                         'boundary': bool(phone['boundary'][index]), 'f0_selected': f0[index],
                         'alternative_near_double': float(candidates[double][0]) if double.any() else None,
                         'score_loss_to_double': float(strengths.max() - strengths[double].max()) if double.any() else None})
    contributions = variance[(variance.model == 'ACF') & (variance.file == 'phone_F1.wav')].to_dict('records')
    stats = {'phone_F1_low_F0_frames': len(evidence),
             'phone_F1_low_frames_in_v': int((low & (phone['labels'] == 'v')).sum()),
             'phone_F1_low_frames_at_boundary': int((low & phone['boundary']).sum()),
             'phone_F1_double_candidate_within_0_02': sum(x['score_loss_to_double'] is not None and x['score_loss_to_double'] < .02 for x in evidence),
             'phone_F1_double_candidate_within_0_05': sum(x['score_loss_to_double'] is not None and x['score_loss_to_double'] < .05 for x in evidence),
             'phone_F1_variance_by_label': contributions,
             'phone_F1_low_F0_evidence': evidence,
             'population_vs_sample_std_max_relative_pct_at_n82': 100 * (np.sqrt(82 / 81) - 1)}
    (core.RESULTS / 'hypothesis_diagnosis.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
    fs, signal = core.load_audio(core.TRAIN / phone['file'])
    chosen = [index for index in np.flatnonzero(low & (phone['labels'] == 'v') & ~phone['boundary'])][:2]
    if len(chosen) < 2:
        chosen = list(np.flatnonzero(low)[:2])
    fig, axes = plt.subplots(len(chosen), 2, figsize=(12, 4 * len(chosen)), constrained_layout=True)
    for row, index in enumerate(chosen):
        start = round(index * fs * .010)
        values = signal[start:start + round(fs * .025)]
        curve = core.ACF['normalized_acf'](values)
        time_ms = np.arange(len(values)) / fs * 1000
        axes[row, 0].plot(time_ms, values, lw=1)
        axes[row, 0].set(title=f'phone_F1 t={phone["times"][index]:.3f}s, label={phone["labels"][index]}', xlabel='Frame time (ms)', ylabel='Amplitude')
        lo, hi = int(np.ceil(fs / 400)), int(np.floor(fs / 70))
        lags = np.arange(lo, hi + 1)
        axes[row, 1].plot(lags / fs * 1000, curve[lags])
        axes[row, 1].axvline(1000 / f0[index], color='#c62828', label=f'Selected {f0[index]:.1f} Hz')
        candidates, strengths = phone['ACF_candidate_f0'][index], phone['ACF_candidate_strength'][index]
        valid = np.isfinite(candidates)
        axes[row, 1].scatter(1000 / candidates[valid], strengths[valid], s=25)
        axes[row, 1].set(title='Normalized ACF: competing local peaks', xlabel='Lag (ms)', ylabel='Correlation')
        axes[row, 1].legend()
    fig.savefig(core.HERE / 'figures' / 'phone_F1_competing_periods.png', dpi=170)
    plt.close(fig)
    phone_rows = oracle[(oracle.model == 'ACF') & (oracle.file == 'phone_F1.wav')]
    studio_rows = oracle[(oracle.model == 'ACF') & (oracle.file == 'studio_M1.wav')]
    phone_v = phone_rows.loc[phone_rows.diagnostic_only == 'oracle_v_only', 'std'].iloc[0]
    studio_v = studio_rows.loc[studio_rows.diagnostic_only == 'oracle_v_only', 'std'].iloc[0]
    record('H1: phân rã phương sai, lọc theo nhãn thật chỉ để chẩn đoán',
           f'phone_F1 chỉ giữ V vẫn std={phone_v:.2f} Hz (GT20.6); studio_M1 chỉ giữ V std={studio_v:.2f} (GT26.4). ddof chỉ khoảng 0.62%.',
           'SIL giải thích studio_M1; phone_F1 còn sai ứng viên trong vùng V. Không dùng oracle trong cải tiến.')
    record('H2: kiểm tra bội chu kỳ ở phone_F1',
           f'{len(evidence)} F0 thấp; {stats["phone_F1_low_frames_in_v"]} nằm trong V; {stats["phone_F1_double_candidate_within_0_05"]} có ứng viên gần gấp đôi chỉ kém score <0.05.',
           'Bằng chứng phù hợp nhầm bội chu kỳ; thiếu GT F0 từng khung nên không khẳng định mọi F0 thấp đều sai.')
    print(json.dumps(stats, indent=2), flush=True)


if __name__ == '__main__':
    main()
