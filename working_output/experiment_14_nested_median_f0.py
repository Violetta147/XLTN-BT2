"""Nested training-only LOFO assessment of median3 versus median5 F0 smoothing."""

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


def fit_gaussian_pitch(files):
    voiced = np.concatenate([item['scores'][item['labels'] == 'v'] for item in files])
    unvoiced = np.concatenate([item['scores'][item['labels'] == 'uv'] for item in files])
    return float(AMDF['gaussian_threshold'](voiced, unvoiced))


def median5(item, prediction):
    f0 = np.full(len(prediction), np.nan)
    f0[prediction] = item['fs'] / item['lags'][prediction]
    edges = np.diff(np.r_[False, prediction, False].astype(int))
    for start, stop in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        if stop - start >= 5:
            raw = f0[start:stop].copy()
            windows = np.stack((raw[:-4], raw[1:-3], raw[2:-2], raw[3:-1], raw[4:]))
            f0[start + 2:stop - 2] = np.median(windows, axis=0)
    return f0


def f0_maes(item, prediction):
    f0_3 = median_f0_within_runs(item, prediction)
    f0_5 = median5(item, prediction)
    valid3 = f0_3[np.isfinite(f0_3) & (f0_3 > 0)]
    valid5 = f0_5[np.isfinite(f0_5) & (f0_5 > 0)]
    assert len(valid3) == len(valid5) == int(prediction.sum())
    stats = item['stats']
    return {
        'median3_F0mean_MAE_hz': abs(float(valid3.mean()) - stats['F0mean']),
        'median5_F0mean_MAE_hz': abs(float(valid5.mean()) - stats['F0mean']),
        'median3_F0std_MAE_hz': abs(float(valid3.std()) - stats['F0std']),
        'median5_F0std_MAE_hz': abs(float(valid5.std()) - stats['F0std']),
    }


def evaluate(item, pitch, energy):
    prediction = ((item['scores'] < pitch) & (item['relative_rms'] >= energy))
    maes = f0_maes(item, prediction)
    labels = item['labels']
    v, uv = labels == 'v', labels == 'uv'
    tp = int((v & prediction).sum())
    tn = int((uv & ~prediction).sum())
    fp = int((uv & prediction).sum())
    fn = int((v & ~prediction).sum())
    return {
        'prediction': prediction,
        'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn,
        'macro_f1': (2 * tp / (2 * tp + fp + fn) + 2 * tn / (2 * tn + fp + fn)) / 2,
        'balanced_accuracy': ((tp / (tp + fn)) + (tn / (tn + fp))) / 2,
        'recall_V': tp / (tp + fn), 'recall_UV': tn / (tn + fp),
        'NumF0': int(prediction.sum()),
        'FP_SIL': int(((labels == 'sil') & prediction).sum()), **maes,
    }


def choose_window(inner_metrics):
    f0mean3 = np.mean([r['median3_F0mean_MAE_hz'] for r in inner_metrics])
    f0mean5 = np.mean([r['median5_F0mean_MAE_hz'] for r in inner_metrics])
    f0std3 = np.mean([r['median3_F0std_MAE_hz'] for r in inner_metrics])
    f0std5 = np.mean([r['median5_F0std_MAE_hz'] for r in inner_metrics])
    choose5 = (f0mean5 <= f0mean3 and f0std5 <= f0std3
               and (f0mean5 < f0mean3 or f0std5 < f0std3))
    return (5 if choose5 else 3), {
        'inner_mean_median3_F0mean_MAE_hz': float(f0mean3),
        'inner_mean_median5_F0mean_MAE_hz': float(f0mean5),
        'inner_mean_median3_F0std_MAE_hz': float(f0std3),
        'inner_mean_median5_F0std_MAE_hz': float(f0std5),
    }


def main():
    files = [load_with_energy(p) for p in FILES]
    outer_rows = []
    inner_rows = []
    for outer in files:
        outer_train = [item for item in files if item is not outer]
        inner_metrics = []
        for inner in outer_train:
            inner_train = [item for item in outer_train if item is not inner]
            pitch = fit_gaussian_pitch(inner_train)
            energy = fit_energy_threshold(inner_train)
            result = evaluate(inner, pitch, energy)
            inner_metrics.append(result)
            inner_rows.append({
                'outer_file': outer['name'], 'inner_held_file': inner['name'],
                'inner_train_files': '|'.join(x['name'] for x in inner_train),
                'T_pitch': pitch, 'T_energy': energy,
                **{k: v for k, v in result.items() if k != 'prediction'},
            })

        selected, inner_summary = choose_window(inner_metrics)
        pitch = fit_gaussian_pitch(outer_train)
        energy = fit_energy_threshold(outer_train)
        result = evaluate(outer, pitch, energy)
        outer_rows.append({
            'outer_held_file': outer['name'], 'selected_window': selected,
            'outer_train_files': '|'.join(x['name'] for x in outer_train),
            'T_pitch': pitch, 'T_energy': energy,
            **inner_summary,
            **{k: v for k, v in result.items() if k != 'prediction'},
        })

    outer = pd.DataFrame(outer_rows)
    inner = pd.DataFrame(inner_rows)
    selected = outer.apply(
        lambda r: r['median5_F0mean_MAE_hz'] if r.selected_window == 5
        else r['median3_F0mean_MAE_hz'], axis=1)
    selected_std = outer.apply(
        lambda r: r['median5_F0std_MAE_hz'] if r.selected_window == 5
        else r['median3_F0std_MAE_hz'], axis=1)
    n_selected5 = int((outer.selected_window == 5).sum())
    mean_selected = float(selected.mean())
    mean_selected_std = float(selected_std.mean())
    mean_fixed3 = float(outer.median3_F0mean_MAE_hz.mean())
    mean_fixed3_std = float(outer.median3_F0std_MAE_hz.mean())
    summary = {
        'training_only': True, 'frame_ms': 25, 'hop_ms': 10,
        'cv': 'nested four-fold outer LOFO; three-fold inner LOFO in each outer training set',
        'pitch_threshold': 'Gaussian fit using only each corresponding training fold V/UV scores',
        'energy_threshold': 'fit using only each corresponding training fold V/SIL labels',
        'outer_folds_selecting_median5': n_selected5,
        'outer_folds_selecting_median3': 4 - n_selected5,
        'nested_selected_mean_F0mean_MAE_hz': mean_selected,
        'fixed_median3_mean_F0mean_MAE_hz': mean_fixed3,
        'nested_selected_mean_F0std_MAE_hz': mean_selected_std,
        'fixed_median3_mean_F0std_MAE_hz': mean_fixed3_std,
        'mean_macro_f1': float(outer.macro_f1.mean()),
        'mean_balanced_accuracy': float(outer.balanced_accuracy.mean()),
        'mean_recall_V': float(outer.recall_V.mean()),
        'mean_recall_UV': float(outer.recall_UV.mean()),
        'NumF0_total': int(outer.NumF0.sum()), 'FP_SIL_total': int(outer.FP_SIL.sum()),
        'keep_median5_by_preregistered_rule': bool(
            n_selected5 >= 3 and mean_selected < mean_fixed3
            and mean_selected_std < mean_fixed3_std
        ),
        'python': platform.python_version(), 'numpy': np.__version__,
        'pandas': pd.__version__, 'scikit_learn': sklearn.__version__,
    }
    outer.to_csv(ROOT / 'working_output' / 'experiment_14_outer_lofo.csv',
                 index=False, float_format='%.10g')
    inner.to_csv(ROOT / 'working_output' / 'experiment_14_inner_lofo.csv',
                 index=False, float_format='%.10g')
    (ROOT / 'working_output' / 'experiment_14_summary.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8')
    print(outer.to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
