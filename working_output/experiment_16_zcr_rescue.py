"""Training-only LOFO evaluation of a ZCR gate for low-energy AMDF rescue."""

from pathlib import Path
import json
import platform
import sys

import numpy as np
import pandas as pd
import sklearn
from numpy.lib.stride_tricks import sliding_window_view

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_01_hysteresis import FILES
from experiment_04_energy_gate import fit_energy_threshold, load_with_energy
from experiment_07_acf_amdf_25ms import fit_selector
from experiment_14_nested_median_f0 import median5 as median5_contour
from validate_saved_results import load_wav


def attach_zcr(item, path):
    fs, signal = load_wav(path)
    length, hop = round(fs * .025), round(fs * .010)
    frames = sliding_window_view(signal, length)[::hop]
    centered = frames - frames.mean(axis=1, keepdims=True)
    item['zcr'] = np.not_equal(centered[:, 1:] < 0, centered[:, :-1] < 0).mean(axis=1)
    assert len(item['zcr']) == len(item['scores'])
    return item


def fit_zcr_threshold(training, pitch, energy):
    zcr_parts, label_parts = [], []
    for item in training:
        mask = ((item['relative_rms'] < energy) & (item['scores'] < pitch)
                & np.isin(item['labels'], ('v', 'uv', 'sil')))
        zcr_parts.append(item['zcr'][mask])
        label_parts.append(item['labels'][mask])
    zcr, labels = np.concatenate(zcr_parts), np.concatenate(label_parts)
    positive, negative = labels == 'v', labels != 'v'
    if not positive.any() or not negative.any():
        return float(np.nextafter(np.min(zcr), -np.inf))
    unique = np.unique(zcr)
    candidates = np.r_[np.nextafter(unique[0], -np.inf),
                       (unique[:-1] + unique[1:]) / 2,
                       np.nextafter(unique[-1], np.inf)]

    def objective(threshold):
        pred = zcr <= threshold
        sensitivity = float(pred[positive].mean())
        specificity = float((~pred[negative]).mean())
        return (sensitivity + specificity) / 2, -float(threshold)

    return float(max(candidates, key=objective))


def evaluate(item, prediction):
    labels = item['labels']
    valid = np.isin(labels, ('v', 'uv'))
    truth_v, pred_v = labels[valid] == 'v', prediction[valid]
    tp, tn = int((truth_v & pred_v).sum()), int((~truth_v & ~pred_v).sum())
    fp, fn = int((~truth_v & pred_v).sum()), int((truth_v & ~pred_v).sum())
    f1v = 2 * tp / (2 * tp + fp + fn)
    f1uv = 2 * tn / (2 * tn + fp + fn)
    f0 = median5_contour(item, prediction)
    f0 = f0[np.isfinite(f0) & (f0 > 0)]
    return {
        'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn,
        'macro_f1': (f1v + f1uv) / 2,
        'balanced_accuracy': ((tp / (tp + fn)) + (tn / (tn + fp))) / 2,
        'recall_V': tp / (tp + fn), 'recall_UV': tn / (tn + fp),
        'F0mean_MAE_hz': abs(float(f0.mean()) - item['stats']['F0mean']),
        'F0std_MAE_hz': abs(float(f0.std()) - item['stats']['F0std']),
        'NumF0': int(len(f0)),
        'FP_SIL': int(((labels == 'sil') & prediction).sum()),
    }


def main():
    files = [attach_zcr(load_with_energy(path), path) for path in FILES]
    rows = []
    for held in files:
        training = [item for item in files if item is not held]
        method, pitch, _ = fit_selector(training, 'AMDF')
        assert method == 'Gaussian'
        energy = fit_energy_threshold(training)
        zcr_threshold = fit_zcr_threshold(training, pitch, energy)
        base = ((held['scores'] < pitch) & (held['relative_rms'] >= energy))
        rescued = ((held['scores'] < pitch) & (held['relative_rms'] < energy)
                  & (held['zcr'] <= zcr_threshold))
        candidate = base | rescued
        for name, prediction in (('energy + median5', base),
                                 ('energy + ZCR rescue + median5', candidate)):
            rows.append({
                'file': held['name'], 'method': name, 'T_pitch': pitch,
                'T_energy': energy, 'T_zcr': zcr_threshold,
                'rescued_frames': int(rescued.sum()) if 'ZCR rescue' in name else 0,
                **evaluate(held, prediction),
            })
    frame = pd.DataFrame(rows)
    base = frame[frame.method == 'energy + median5'].set_index('file')
    candidate = frame[frame.method == 'energy + ZCR rescue + median5'].set_index('file')
    summary = {
        'training_only': True, 'frame_ms': 25, 'hop_ms': 10,
        'cv': 'four-fold leave-one-file-out; thresholds fit on the other three files',
        'zcr_definition': 'mean sign changes after subtracting each frame mean, divided by frame length minus one',
        'zcr_threshold_fit': 'maximize V-vs-(UV or SIL) balanced accuracy among low-energy, pitch-eligible training frames; ties choose lower threshold',
        'baseline_mean_macro_f1': float(base.macro_f1.mean()),
        'candidate_mean_macro_f1': float(candidate.macro_f1.mean()),
        'baseline_mean_balanced_accuracy': float(base.balanced_accuracy.mean()),
        'candidate_mean_balanced_accuracy': float(candidate.balanced_accuracy.mean()),
        'baseline_mean_recall_V': float(base.recall_V.mean()),
        'candidate_mean_recall_V': float(candidate.recall_V.mean()),
        'baseline_mean_recall_UV': float(base.recall_UV.mean()),
        'candidate_mean_recall_UV': float(candidate.recall_UV.mean()),
        'baseline_mean_F0mean_MAE_hz': float(base.F0mean_MAE_hz.mean()),
        'candidate_mean_F0mean_MAE_hz': float(candidate.F0mean_MAE_hz.mean()),
        'baseline_mean_F0std_MAE_hz': float(base.F0std_MAE_hz.mean()),
        'candidate_mean_F0std_MAE_hz': float(candidate.F0std_MAE_hz.mean()),
        'baseline_NumF0_total': int(base.NumF0.sum()),
        'candidate_NumF0_total': int(candidate.NumF0.sum()),
        'baseline_FP_SIL_total': int(base.FP_SIL.sum()),
        'candidate_FP_SIL_total': int(candidate.FP_SIL.sum()),
        'rescued_frames_total': int(candidate.rescued_frames.sum()),
        'keep_by_preregistered_rule': bool(
            candidate.recall_V.mean() - base.recall_V.mean() >= .02
            and candidate.macro_f1.mean() - base.macro_f1.mean() >= -.01
            and candidate.balanced_accuracy.mean() - base.balanced_accuracy.mean() >= -.01
            and candidate.F0mean_MAE_hz.mean() - base.F0mean_MAE_hz.mean() <= .25
            and candidate.F0std_MAE_hz.mean() - base.F0std_MAE_hz.mean() <= .25
            and candidate.FP_SIL.sum() <= 3
        ),
        'python': platform.python_version(), 'numpy': np.__version__,
        'pandas': pd.__version__, 'scikit_learn': sklearn.__version__,
    }
    out = ROOT / 'working_output'
    frame.to_csv(out / 'experiment_16_lofo.csv', index=False, float_format='%.10g')
    (out / 'experiment_16_summary.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8')
    print(frame.to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
