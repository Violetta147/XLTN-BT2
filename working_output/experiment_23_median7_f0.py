"""Compare median5 and median7 F0 smoothing in training-only four-fold LOFO."""

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
from experiment_05_median_f0 import median_f0_within_runs
from experiment_07_acf_amdf_25ms import AMDF


def fit_pitch_threshold(files):
    voiced = np.concatenate([x['scores'][x['labels'] == 'v'] for x in files])
    unvoiced = np.concatenate([x['scores'][x['labels'] == 'uv'] for x in files])
    return float(AMDF['gaussian_threshold'](voiced, unvoiced))


def smooth7(item, prediction):
    f0 = np.full(len(prediction), np.nan)
    f0[prediction] = item['fs'] / item['lags'][prediction]
    edges = np.diff(np.r_[False, prediction, False].astype(int))
    starts, stops = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    for start, stop in zip(starts, stops):
        if stop - start >= 7:
            raw = f0[start:stop].copy()
            windows = np.stack([raw[i:len(raw) - 6 + i] for i in range(7)])
            f0[start + 3:stop - 3] = np.median(windows, axis=0)
    return f0


def mae_pair(item, prediction, smoother):
    values = smoother(item, prediction)
    values = values[np.isfinite(values) & (values > 0)]
    assert len(values) == int(prediction.sum())
    stats = item['stats']
    return (abs(float(values.mean()) - stats['F0mean']),
            abs(float(values.std()) - stats['F0std']))


def score(item, pitch, energy):
    pred = (item['scores'] < pitch) & (item['relative_rms'] >= energy)
    base = median_f0_within_runs(item, pred)
    base = base[np.isfinite(base) & (base > 0)]
    cand = smooth7(item, pred)
    cand = cand[np.isfinite(cand) & (cand > 0)]
    assert len(base) == len(cand) == int(pred.sum())
    labels = item['labels']
    v, uv = labels == 'v', labels == 'uv'
    tp, tn = int((v & pred).sum()), int((uv & ~pred).sum())
    fp, fn = int((uv & pred).sum()), int((v & ~pred).sum())
    f1v = 2 * tp / (2 * tp + fp + fn)
    f1uv = 2 * tn / (2 * tn + fp + fn)
    return {
        'prediction': pred,
        'median5_F0mean_MAE_hz': abs(float(base.mean()) - item['stats']['F0mean']),
        'median7_F0mean_MAE_hz': abs(float(cand.mean()) - item['stats']['F0mean']),
        'median5_F0std_MAE_hz': abs(float(base.std()) - item['stats']['F0std']),
        'median7_F0std_MAE_hz': abs(float(cand.std()) - item['stats']['F0std']),
        'macro_f1': (f1v + f1uv) / 2,
        'balanced_accuracy': (tp / (tp + fn) + tn / (tn + fp)) / 2,
        'recall_V': tp / (tp + fn), 'recall_UV': tn / (tn + fp),
        'NumF0': int(pred.sum()),
        'FP_SIL': int(((labels == 'sil') & pred).sum()),
    }


def main():
    files = [load_with_energy(p) for p in FILES]
    rows = []
    for held in files:
        train = [x for x in files if x is not held]
        pitch, energy = fit_pitch_threshold(train), fit_energy_threshold(train)
        result = score(held, pitch, energy)
        rows.append({
            'held_out_file': held['name'],
            'training_files': '|'.join(x['name'] for x in train),
            'pitch_threshold': pitch, 'energy_threshold': energy,
            **{k: v for k, v in result.items() if k != 'prediction'},
        })
    df = pd.DataFrame(rows)
    f0mean_delta = float((df.median7_F0mean_MAE_hz - df.median5_F0mean_MAE_hz).mean())
    f0std_gain = float((df.median5_F0std_MAE_hz - df.median7_F0std_MAE_hz).mean())
    max_file_worsening = float(max(
        (df.median7_F0mean_MAE_hz - df.median5_F0mean_MAE_hz).max(),
        (df.median7_F0std_MAE_hz - df.median5_F0std_MAE_hz).max(),
    ))
    summary = {
        'training_only': True, 'test_used': False,
        'cv': 'four-fold outer leave-one-training-file-out',
        'frame_ms': 25, 'hop_ms': 10,
        'hypothesis': 'median7 improves mean F0std MAE >=0.25 Hz; F0mean MAE worsens <=0.10 Hz',
        'mean_median5_F0mean_MAE_hz': float(df.median5_F0mean_MAE_hz.mean()),
        'mean_median7_F0mean_MAE_hz': float(df.median7_F0mean_MAE_hz.mean()),
        'mean_F0mean_MAE_worsening_hz': f0mean_delta,
        'mean_median5_F0std_MAE_hz': float(df.median5_F0std_MAE_hz.mean()),
        'mean_median7_F0std_MAE_hz': float(df.median7_F0std_MAE_hz.mean()),
        'mean_F0std_MAE_improvement_hz': f0std_gain,
        'max_single_file_MAE_worsening_hz': max_file_worsening,
        'mean_macro_f1': float(df.macro_f1.mean()),
        'mean_balanced_accuracy': float(df.balanced_accuracy.mean()),
        'mean_recall_V': float(df.recall_V.mean()),
        'mean_recall_UV': float(df.recall_UV.mean()),
        'NumF0_total': int(df.NumF0.sum()), 'FP_SIL_total': int(df.FP_SIL.sum()),
        'keep_candidate': bool(f0std_gain >= 0.25 and f0mean_delta <= 0.10
                               and max_file_worsening <= 1.0),
        'python': platform.python_version(), 'numpy': np.__version__,
        'pandas': pd.__version__, 'scikit_learn': sklearn.__version__,
    }
    df.to_csv(ROOT / 'working_output' / 'experiment_23_lofo.csv',
              index=False, float_format='%.10g')
    (ROOT / 'working_output' / 'experiment_23_summary.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8')
    print(df.to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
