"""Training-only LOFO test of rescuing strong AMDF dips below the energy gate."""

from pathlib import Path
import json
import platform
import sys

import numpy as np
import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_01_hysteresis import FILES
from experiment_04_energy_gate import fit_energy_threshold, load_with_energy
from experiment_05_median_f0 import median_f0_within_runs
from experiment_07_acf_amdf_25ms import fit_selector


def fit_rescue_threshold(training_files, pitch, energy):
    scores, labels = [], []
    for item in training_files:
        mask = ((item['relative_rms'] < energy) & (item['scores'] < pitch)
                & np.isin(item['labels'], ('v', 'uv', 'sil')))
        scores.append(item['scores'][mask])
        labels.append(item['labels'][mask])
    scores = np.concatenate(scores)
    labels = np.concatenate(labels)
    if not np.any(labels == 'v') or not np.any(labels != 'v'):
        return float(np.nextafter(np.min(scores), -np.inf))

    unique = np.unique(scores)
    candidates = np.r_[np.nextafter(unique[0], -np.inf),
                       (unique[:-1] + unique[1:]) / 2,
                       np.nextafter(unique[-1], np.inf)]
    candidates = candidates[candidates <= pitch]
    if len(candidates) == 0:
        return float(np.nextafter(np.min(scores), -np.inf))

    positive, negative = labels == 'v', labels != 'v'

    def objective(threshold):
        pred = scores < threshold
        sensitivity = float(pred[positive].mean())
        specificity = float((~pred[negative]).mean())
        return (sensitivity + specificity) / 2, -float(threshold)

    return float(max(candidates, key=objective))


def median5_contour(item, prediction):
    f0 = np.full(len(prediction), np.nan)
    f0[prediction] = item['fs'] / item['lags'][prediction]
    edges = np.diff(np.r_[False, prediction, False].astype(int))
    for start, stop in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        if stop - start >= 5:
            raw = f0[start:stop].copy()
            windows = np.stack((raw[:-4], raw[1:-3], raw[2:-2], raw[3:-1], raw[4:]))
            f0[start + 2:stop - 2] = np.median(windows, axis=0)
    return f0


def evaluate(item, prediction):
    labels = item['labels']
    valid_labels = np.isin(labels, ('v', 'uv'))
    truth_v = labels[valid_labels] == 'v'
    pred_v = prediction[valid_labels]
    tp = int((truth_v & pred_v).sum())
    tn = int((~truth_v & ~pred_v).sum())
    fp = int((~truth_v & pred_v).sum())
    fn = int((truth_v & ~pred_v).sum())
    f1_v = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    f1_uv = 2 * tn / (2 * tn + fp + fn) if (2 * tn + fp + fn) else 0.0
    f0 = median5_contour(item, prediction)
    f0 = f0[np.isfinite(f0) & (f0 > 0)]
    return {
        'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn,
        'macro_f1': (f1_v + f1_uv) / 2,
        'balanced_accuracy': ((tp / (tp + fn)) + (tn / (tn + fp))) / 2,
        'recall_V': tp / (tp + fn), 'recall_UV': tn / (tn + fp),
        'F0mean_MAE_hz': abs(float(f0.mean()) - item['stats']['F0mean']),
        'F0std_MAE_hz': abs(float(f0.std()) - item['stats']['F0std']),
        'NumF0': int(len(f0)),
        'FP_SIL': int(((labels == 'sil') & prediction).sum()),
    }


def main():
    files = [load_with_energy(path) for path in FILES]
    rows = []
    for held in files:
        training = [item for item in files if item is not held]
        method, pitch, _ = fit_selector(training, 'AMDF')
        assert method == 'Gaussian'
        energy = fit_energy_threshold(training)
        rescue = fit_rescue_threshold(training, pitch, energy)
        baseline = ((held['scores'] < pitch) & (held['relative_rms'] >= energy))
        recovered = ((held['scores'] < rescue) & (held['relative_rms'] < energy))
        candidate = baseline | recovered
        for name, prediction in (('energy + median5', baseline),
                                 ('energy + rescue + median5', candidate)):
            rows.append({
                'file': held['name'], 'method': name,
                'T_pitch': pitch, 'T_energy': energy, 'T_rescue': rescue,
                'rescued_frames': int(recovered.sum()) if 'rescue' in name else 0,
                **evaluate(held, prediction),
            })

    frame = pd.DataFrame(rows)
    base = frame[frame.method == 'energy + median5'].set_index('file')
    cand = frame[frame.method == 'energy + rescue + median5'].set_index('file')
    summary = {
        'training_only': True, 'frame_ms': 25, 'hop_ms': 10,
        'cv': 'four-fold leave-one-file-out; all thresholds fit on other three files',
        'rescue_fit': 'maximize V-vs-(UV or SIL) balanced accuracy among low-energy, pitch-eligible training frames; ties choose lower threshold',
        'baseline_mean_macro_f1': float(base.macro_f1.mean()),
        'candidate_mean_macro_f1': float(cand.macro_f1.mean()),
        'baseline_mean_balanced_accuracy': float(base.balanced_accuracy.mean()),
        'candidate_mean_balanced_accuracy': float(cand.balanced_accuracy.mean()),
        'baseline_mean_recall_V': float(base.recall_V.mean()),
        'candidate_mean_recall_V': float(cand.recall_V.mean()),
        'baseline_mean_recall_UV': float(base.recall_UV.mean()),
        'candidate_mean_recall_UV': float(cand.recall_UV.mean()),
        'baseline_mean_F0mean_MAE_hz': float(base.F0mean_MAE_hz.mean()),
        'candidate_mean_F0mean_MAE_hz': float(cand.F0mean_MAE_hz.mean()),
        'baseline_mean_F0std_MAE_hz': float(base.F0std_MAE_hz.mean()),
        'candidate_mean_F0std_MAE_hz': float(cand.F0std_MAE_hz.mean()),
        'baseline_NumF0_total': int(base.NumF0.sum()),
        'candidate_NumF0_total': int(cand.NumF0.sum()),
        'baseline_FP_SIL_total': int(base.FP_SIL.sum()),
        'candidate_FP_SIL_total': int(cand.FP_SIL.sum()),
        'rescued_frames_total': int(cand.rescued_frames.sum()),
        'keep_by_preregistered_rule': bool(
            cand.recall_V.mean() - base.recall_V.mean() >= 0.02
            and cand.macro_f1.mean() - base.macro_f1.mean() >= -0.01
            and cand.balanced_accuracy.mean() - base.balanced_accuracy.mean() >= -0.01
            and cand.F0mean_MAE_hz.mean() - base.F0mean_MAE_hz.mean() <= 0.25
            and cand.F0std_MAE_hz.mean() - base.F0std_MAE_hz.mean() <= 0.25
            and cand.FP_SIL.sum() <= 3
        ),
        'python': platform.python_version(), 'numpy': np.__version__,
        'pandas': pd.__version__, 'scikit_learn': sklearn.__version__,
    }
    out = ROOT / 'working_output'
    frame.to_csv(out / 'experiment_15_lofo.csv', index=False, float_format='%.10g')
    (out / 'experiment_15_summary.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8')
    print(frame.to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
