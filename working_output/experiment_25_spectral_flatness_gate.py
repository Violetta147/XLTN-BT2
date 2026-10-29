"""Nested training-only LOFO experiment for a spectral-flatness UV gate."""

from pathlib import Path
import json
import platform
import sys

import numpy as np
import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_04_energy_gate import FILES, fit_energy_threshold, load_with_energy
from experiment_24_amdf_confidence_gate import fit_pitch_threshold, median5_f0
from validate_saved_results import load_wav

QUANTILES = (0.50, 0.60, 0.70, 0.80, 0.90, 0.95)


def add_flatness(item, path):
    fs, signal = load_wav(path)
    length, hop = round(fs * 0.025), round(fs * 0.010)
    window = np.hanning(length)
    values = []
    for start in range(0, len(signal) - length + 1, hop):
        power = np.abs(np.fft.rfft(signal[start:start + length] * window)) ** 2
        flatness = np.exp(np.log(power + 1e-12).mean()) / (power.mean() + 1e-12)
        values.append(float(flatness))
    item['spectral_flatness'] = np.asarray(values)
    assert len(values) == len(item['scores'])
    return item


def baseline_prediction(item, pitch, energy):
    return (item['scores'] < pitch) & (item['relative_rms'] >= energy)


def fit_flatness_cutoff(files, pitch, energy, quantile):
    values = []
    for item in files:
        predicted = baseline_prediction(item, pitch, energy)
        selected = item['spectral_flatness'][predicted]
        if len(selected):
            values.append(selected)
    if not values:
        return None
    return float(np.quantile(np.concatenate(values), quantile))


def score(item, pitch, energy, cutoff=None):
    baseline = baseline_prediction(item, pitch, energy)
    pred = baseline.copy()
    if cutoff is not None:
        pred[baseline & (item['spectral_flatness'] >= cutoff)] = False
    labels = item['labels']
    scored = np.isin(labels, ('v', 'uv'))
    truth_v, pred_v = labels[scored] == 'v', pred[scored]
    tp = int((truth_v & pred_v).sum())
    tn = int((~truth_v & ~pred_v).sum())
    fp = int((~truth_v & pred_v).sum())
    fn = int((truth_v & ~pred_v).sum())
    f1_v = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    f1_uv = 2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else 0.0
    recall_v = tp / (tp + fn) if tp + fn else 0.0
    recall_uv = tn / (tn + fp) if tn + fp else 0.0
    f0 = median5_f0(item, pred)
    f0 = f0[np.isfinite(f0) & (f0 > 0)]
    f0mean_mae = abs(float(f0.mean()) - item['stats']['F0mean']) if len(f0) else float('inf')
    f0std_mae = abs(float(f0.std()) - item['stats']['F0std']) if len(f0) else float('inf')
    return {
        'prediction': pred,
        'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn,
        'macro_f1': (f1_v + f1_uv) / 2,
        'balanced_accuracy': (recall_v + recall_uv) / 2,
        'recall_V': recall_v, 'recall_UV': recall_uv,
        'NumF0': int(len(f0)),
        'FP_SIL': int(((labels == 'sil') & pred).sum()),
        'rejected_voiced': int((baseline & ~pred).sum()),
        'F0mean_MAE_hz': f0mean_mae, 'F0std_MAE_hz': f0std_mae,
    }


def select_quantile(outer_train):
    rows = []
    choices = [('none', None)] + [(f'q{q:.2f}', q) for q in QUANTILES]
    for held in outer_train:
        inner_train = [item for item in outer_train if item is not held]
        pitch = fit_pitch_threshold(inner_train)
        energy = fit_energy_threshold(inner_train)
        for config, q in choices:
            cutoff = None if q is None else fit_flatness_cutoff(inner_train, pitch, energy, q)
            result = score(held, pitch, energy, cutoff)
            rows.append({'file': held['name'], 'config': config, 'q': q,
                         'q_order': -1.0 if q is None else q,
                         **{key: val for key, val in result.items() if key != 'prediction'}})
    detail = pd.DataFrame(rows)
    summary = detail.groupby(['config', 'q', 'q_order'], dropna=False).agg(
        macro_f1=('macro_f1', 'mean'), balanced_accuracy=('balanced_accuracy', 'mean'),
        recall_V=('recall_V', 'mean'), rejected=('rejected_voiced', 'mean'),
    ).reset_index()
    best = summary.sort_values(
        ['macro_f1', 'balanced_accuracy', 'recall_V', 'rejected', 'q_order'],
        ascending=[False, False, False, True, True], kind='mergesort'
    ).iloc[0]
    return (None if pd.isna(best.q) else float(best.q)), detail


def main():
    files = [add_flatness(load_with_energy(path), path) for path in FILES]
    rows, inner_rows = [], []
    for held in files:
        train = [item for item in files if item is not held]
        q, inner = select_quantile(train)
        inner.insert(0, 'outer_file', held['name'])
        inner_rows.append(inner)
        pitch, energy = fit_pitch_threshold(train), fit_energy_threshold(train)
        cutoff = None if q is None else fit_flatness_cutoff(train, pitch, energy, q)
        if q is not None and cutoff is None:
            raise RuntimeError(f'No training flatness values for {held["name"]}')
        baseline = score(held, pitch, energy)
        candidate = score(held, pitch, energy, cutoff)
        row = {'held_out_file': held['name'],
               'training_files': '|'.join(x['name'] for x in train),
               'selected_quantile': q, 'flatness_cutoff': cutoff}
        row.update({f'baseline_{key}': val for key, val in baseline.items() if key != 'prediction'})
        row.update({f'candidate_{key}': val for key, val in candidate.items() if key != 'prediction'})
        rows.append(row)

    outer = pd.DataFrame(rows)
    inner = pd.concat(inner_rows, ignore_index=True)
    reference = pd.read_csv(ROOT / 'working_output' / 'experiment_24_outer_lofo.csv').set_index('held_out_file')
    for _, row in outer.iterrows():
        ref = reference.loc[row['held_out_file']]
        pairs = (
            ('baseline_macro_f1', 'baseline_macro_f1'),
            ('baseline_balanced_accuracy', 'baseline_balanced_accuracy'),
            ('baseline_recall_V', 'baseline_recall_V'),
            ('baseline_recall_UV', 'baseline_recall_UV'),
            ('baseline_NumF0', 'baseline_NumF0'),
            ('baseline_FP_SIL', 'baseline_FP_SIL'),
            ('baseline_F0mean_MAE_hz', 'baseline_F0mean_MAE_hz'),
            ('baseline_F0std_MAE_hz', 'baseline_F0std_MAE_hz'),
        )
        for ref_key, actual_key in pairs:
            assert np.isclose(float(row[actual_key]), float(ref[ref_key]), atol=1e-8, rtol=1e-8), (
                f'EXP24 baseline parity failed: {row["held_out_file"]} {ref_key}'
            )

    metric_keys = ('F0mean_MAE_hz', 'F0std_MAE_hz', 'macro_f1',
                   'balanced_accuracy', 'recall_V', 'recall_UV')
    deltas = {key: float((outer[f'candidate_{key}'] - outer[f'baseline_{key}']).mean())
              for key in metric_keys}
    std_improvement = -deltas['F0std_MAE_hz']
    max_file_worsening = max(
        float((outer.candidate_F0mean_MAE_hz - outer.baseline_F0mean_MAE_hz).max()),
        float((outer.candidate_F0std_MAE_hz - outer.baseline_F0std_MAE_hz).max()),
    )
    baseline_numf0, candidate_numf0 = int(outer.baseline_NumF0.sum()), int(outer.candidate_NumF0.sum())
    summary = {
        'training_only': True, 'test_used': False,
        'cv': 'nested four-fold outer LOFO; three-fold inner LOFO per outer fold',
        'frame_ms': 25, 'hop_ms': 10, 'baseline_parity_with_experiment_24': True,
        'mean_baseline_F0mean_MAE_hz': float(outer.baseline_F0mean_MAE_hz.mean()),
        'mean_candidate_F0mean_MAE_hz': float(outer.candidate_F0mean_MAE_hz.mean()),
        'mean_F0mean_MAE_change_hz': deltas['F0mean_MAE_hz'],
        'mean_baseline_F0std_MAE_hz': float(outer.baseline_F0std_MAE_hz.mean()),
        'mean_candidate_F0std_MAE_hz': float(outer.candidate_F0std_MAE_hz.mean()),
        'mean_F0std_MAE_improvement_hz': std_improvement,
        'mean_macro_f1_change': deltas['macro_f1'],
        'mean_balanced_accuracy_change': deltas['balanced_accuracy'],
        'mean_recall_V_change': deltas['recall_V'],
        'mean_recall_UV_change': deltas['recall_UV'],
        'baseline_NumF0_total': baseline_numf0,
        'candidate_NumF0_total': candidate_numf0,
        'candidate_FP_SIL_total': int(outer.candidate_FP_SIL.sum()),
        'max_single_file_F0_MAE_worsening_hz': max_file_worsening,
        'selected_quantiles_by_outer_fold': outer.selected_quantile.tolist(),
        'keep_candidate': bool(
            deltas['macro_f1'] >= -0.005 and deltas['balanced_accuracy'] >= -0.005
            and deltas['recall_V'] >= -0.01 and deltas['F0mean_MAE_hz'] <= 0.10
            and std_improvement >= 0.25 and candidate_numf0 >= 0.98 * baseline_numf0
            and int(outer.candidate_FP_SIL.sum()) <= 3 and max_file_worsening <= 1.0
        ),
        'python': platform.python_version(), 'numpy': np.__version__,
        'pandas': pd.__version__, 'scikit_learn': sklearn.__version__,
    }
    outer.to_csv(ROOT / 'working_output' / 'experiment_25_outer_lofo.csv', index=False,
                 float_format='%.10g')
    inner.to_csv(ROOT / 'working_output' / 'experiment_25_inner_selection.csv', index=False,
                 float_format='%.10g')
    (ROOT / 'working_output' / 'experiment_25_summary.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8')
    print(outer.to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
