"""Nested LOFO experiment for an AMDF competing-minimum confidence gate."""

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
from experiment_07_acf_amdf_25ms import AMDF
from validate_saved_results import amdf_score, load_wav

QUANTILES = (0.0, 0.10, 0.20, 0.30, 0.40, 0.50)


def frame_margin(frame, fs, reference_score):
    """Return best-vs-second local-minimum gap, parity-checking the baseline."""
    x = frame - frame.mean()
    n = len(x)
    lo = max(1, int(np.floor(fs / 400.0)))
    hi = min(n - 1, int(np.ceil(fs / 70.0)))
    lags = np.arange(lo, hi + 1)
    if np.mean(np.abs(x)) < 1e-8:
        scores = np.ones(len(lags))
    else:
        sample_index = np.arange(n - lo)[None, :]
        lag_matrix = lags[:, None]
        valid = sample_index < n - lag_matrix
        shifted_index = np.minimum(sample_index + lag_matrix, n - 1)
        left = np.broadcast_to(x[:n - lo][None, :], shifted_index.shape)
        right = x[shifted_index]
        count = valid.sum(axis=1)
        diff = (np.abs(left - right) * valid).sum(axis=1) / count
        left_abs = (np.abs(left) * valid).sum(axis=1) / count
        right_abs = (np.abs(right) * valid).sum(axis=1) / count
        scores = diff / (left_abs + right_abs + 1e-12)
    local = np.flatnonzero(
        (scores[1:-1] <= scores[:-2]) & (scores[1:-1] <= scores[2:])
    ) + 1
    if len(local) < 2:
        best = int(local[np.argmin(scores[local])]) if len(local) else int(np.argmin(scores))
        best_score = float(scores[best])
        assert np.isclose(best_score, reference_score, atol=1e-12, rtol=1e-10)
        return np.nan
    minima = np.sort(scores[local])
    assert np.isclose(float(minima[0]), reference_score, atol=1e-12, rtol=1e-10)
    return float(minima[1] - minima[0])


def add_margins(item, path):
    fs, signal = load_wav(path)
    length, hop = round(fs * 0.025), round(fs * 0.010)
    margins = []
    for index, start in enumerate(range(0, len(signal) - length + 1, hop)):
        margins.append(frame_margin(signal[start:start + length], fs, item['scores'][index]))
    assert len(margins) == len(item['scores'])
    item['margin'] = np.asarray(margins)
    return item


def fit_pitch_threshold(files):
    voiced = np.concatenate([x['scores'][x['labels'] == 'v'] for x in files])
    unvoiced = np.concatenate([x['scores'][x['labels'] == 'uv'] for x in files])
    return float(AMDF['gaussian_threshold'](voiced, unvoiced))


def base_prediction(item, pitch, energy):
    return (item['scores'] < pitch) & (item['relative_rms'] >= energy)


def median5_f0(item, prediction):
    f0 = np.full(len(prediction), np.nan)
    f0[prediction] = item['fs'] / item['lags'][prediction]
    edges = np.diff(np.r_[False, prediction, False].astype(int))
    for start, stop in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        if stop - start >= 5:
            raw = f0[start:stop].copy()
            windows = np.stack((raw[:-4], raw[1:-3], raw[2:-2], raw[3:-1], raw[4:]))
            f0[start + 2:stop - 2] = np.median(windows, axis=0)
    return f0


def training_cutoff(files, pitch, energy, quantile):
    margins = []
    for item in files:
        pred = base_prediction(item, pitch, energy)
        selected = item['margin'][pred & np.isfinite(item['margin'])]
        if len(selected):
            margins.append(selected)
    values = np.concatenate(margins) if margins else np.array([], dtype=float)
    if not len(values):
        return None
    return float(np.quantile(values, quantile))


def evaluate(item, pitch, energy, cutoff=None):
    baseline = base_prediction(item, pitch, energy)
    pred = baseline.copy()
    if cutoff is not None:
        reject = baseline & np.isfinite(item['margin']) & (item['margin'] <= cutoff)
        pred[reject] = False
    labels = item['labels']
    scored = np.isin(labels, ('v', 'uv'))
    truth_v, pred_v = labels[scored] == 'v', pred[scored]
    tp = int((truth_v & pred_v).sum())
    tn = int((~truth_v & ~pred_v).sum())
    fp = int((~truth_v & pred_v).sum())
    fn = int((truth_v & ~pred_v).sum())
    f1_v = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    f1_uv = 2 * tn / (2 * tn + fp + fn) if (2 * tn + fp + fn) else 0.0
    recall_v = tp / (tp + fn) if tp + fn else 0.0
    recall_uv = tn / (tn + fp) if tn + fp else 0.0
    f0 = median5_f0(item, pred)
    f0 = f0[np.isfinite(f0) & (f0 > 0)]
    return {
        'prediction': pred,
        'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn,
        'macro_f1': (f1_v + f1_uv) / 2,
        'balanced_accuracy': (recall_v + recall_uv) / 2,
        'recall_V': recall_v, 'recall_UV': recall_uv,
        'NumF0': int(len(f0)),
        'FP_SIL': int(((labels == 'sil') & pred).sum()),
        'rejected_voiced': int((baseline & ~pred).sum()),
        'F0mean_MAE_hz': abs(float(f0.mean()) - item['stats']['F0mean']),
        'F0std_MAE_hz': abs(float(f0.std()) - item['stats']['F0std']),
    }


def select_quantile(outer_train):
    rows = []
    choices = [('none', None)] + [(f'q{q:.2f}', q) for q in QUANTILES]
    for held in outer_train:
        inner_train = [x for x in outer_train if x is not held]
        pitch, energy = fit_pitch_threshold(inner_train), fit_energy_threshold(inner_train)
        for config, q in choices:
            cutoff = None if q is None else training_cutoff(inner_train, pitch, energy, q)
            score = evaluate(held, pitch, energy, cutoff)
            rows.append({'file': held['name'], 'config': config, 'q': q,
                         'q_order': -1.0 if q is None else q, **score})
    frame = pd.DataFrame(rows)
    summary = frame.groupby(['config', 'q', 'q_order'], dropna=False).agg(
        mean_macro_f1=('macro_f1', 'mean'),
        mean_balanced_accuracy=('balanced_accuracy', 'mean'),
        mean_recall_V=('recall_V', 'mean'),
        mean_rejected=('rejected_voiced', 'mean'),
    ).reset_index()
    best = summary.sort_values(
        ['mean_macro_f1', 'mean_balanced_accuracy', 'mean_recall_V', 'mean_rejected', 'q_order'],
        ascending=[False, False, False, True, True], kind='mergesort'
    ).iloc[0]
    return (None if pd.isna(best.q) else float(best.q)), frame, summary


def main():
    files = [add_margins(load_with_energy(path), path) for path in FILES]
    outer_rows, inner_rows = [], []
    for held in files:
        train = [x for x in files if x is not held]
        q, inner, q_summary = select_quantile(train)
        inner.insert(0, 'outer_file', held['name'])
        inner_rows.append(inner)
        pitch, energy = fit_pitch_threshold(train), fit_energy_threshold(train)
        cutoff = None if q is None else training_cutoff(train, pitch, energy, q)
        if q is not None and cutoff is None:
            raise RuntimeError(f'No training margin available for outer fold {held["name"]}')
        baseline = evaluate(held, pitch, energy)
        candidate = evaluate(held, pitch, energy, cutoff)
        row = {
            'held_out_file': held['name'],
            'training_files': '|'.join(x['name'] for x in train),
            'selected_quantile': q, 'margin_cutoff': cutoff,
        }
        row.update({f'baseline_{k}': v for k, v in baseline.items() if k != 'prediction'})
        row.update({f'candidate_{k}': v for k, v in candidate.items() if k != 'prediction'})
        # Strict parity: applying no margin gate must reproduce the accepted EXP14 baseline.
        row['baseline_prediction_hash'] = __import__('hashlib').sha256(
            baseline['prediction'].tobytes()).hexdigest()
        outer_rows.append(row)

    outer = pd.DataFrame(outer_rows)
    inner = pd.concat(inner_rows, ignore_index=True)
    reference = pd.read_csv(ROOT / 'working_output' / 'experiment_14_outer_lofo.csv').set_index('outer_held_file')
    for _, row in outer.iterrows():
        ref = reference.loc[row['held_out_file']]
        for key, column in (
            ('macro_f1', 'baseline_macro_f1'),
            ('balanced_accuracy', 'baseline_balanced_accuracy'),
            ('recall_V', 'baseline_recall_V'), ('recall_UV', 'baseline_recall_UV'),
            ('NumF0', 'baseline_NumF0'), ('FP_SIL', 'baseline_FP_SIL'),
            ('median5_F0mean_MAE_hz', 'baseline_F0mean_MAE_hz'),
            ('median5_F0std_MAE_hz', 'baseline_F0std_MAE_hz'),
        ):
            ref_key = key if key in ref.index else key
            ref_value = ref[ref_key]
            assert np.isclose(float(row[column]), float(ref_value), atol=1e-8, rtol=1e-8), (
                f'Baseline parity failed: {row["held_out_file"]} {key}: '
                f'{row[column]} != {ref_value}'
            )

    delta = {}
    metric_map = {
        'F0mean_MAE_hz': 'F0mean_MAE_hz', 'F0std_MAE_hz': 'F0std_MAE_hz',
        'macro_f1': 'macro_f1', 'balanced_accuracy': 'balanced_accuracy',
        'recall_V': 'recall_V', 'recall_UV': 'recall_UV',
    }
    for metric, suffix in metric_map.items():
        delta[metric] = float((outer[f'candidate_{suffix}'] - outer[f'baseline_{suffix}']).mean())
    std_improvement = -delta['F0std_MAE_hz']
    max_file_worsening = max(
        float((outer.candidate_F0mean_MAE_hz - outer.baseline_F0mean_MAE_hz).max()),
        float((outer.candidate_F0std_MAE_hz - outer.baseline_F0std_MAE_hz).max()),
    )
    baseline_numf0 = int(outer.baseline_NumF0.sum())
    candidate_numf0 = int(outer.candidate_NumF0.sum())
    summary = {
        'training_only': True, 'test_used': False,
        'cv': 'nested four-fold outer LOFO; three-fold inner LOFO per outer fold',
        'frame_ms': 25, 'hop_ms': 10,
        'baseline_parity_with_experiment_14': True,
        'mean_baseline_F0mean_MAE_hz': float(outer.baseline_F0mean_MAE_hz.mean()),
        'mean_candidate_F0mean_MAE_hz': float(outer.candidate_F0mean_MAE_hz.mean()),
        'mean_F0mean_MAE_change_hz': delta['F0mean_MAE_hz'],
        'mean_baseline_F0std_MAE_hz': float(outer.baseline_F0std_MAE_hz.mean()),
        'mean_candidate_F0std_MAE_hz': float(outer.candidate_F0std_MAE_hz.mean()),
        'mean_F0std_MAE_improvement_hz': std_improvement,
        'mean_macro_f1_change': delta['macro_f1'],
        'mean_balanced_accuracy_change': delta['balanced_accuracy'],
        'mean_recall_V_change': delta['recall_V'],
        'mean_recall_UV_change': delta['recall_UV'],
        'baseline_NumF0_total': baseline_numf0,
        'candidate_NumF0_total': candidate_numf0,
        'FP_SIL_total': int(outer.candidate_FP_SIL.sum()),
        'max_single_file_F0_MAE_worsening_hz': max_file_worsening,
        'selected_quantiles_by_outer_fold': outer.selected_quantile.tolist(),
        'keep_candidate': bool(
            std_improvement >= 0.25
            and delta['F0mean_MAE_hz'] <= 0.10
            and delta['macro_f1'] >= -0.005
            and delta['balanced_accuracy'] >= -0.005
            and delta['recall_V'] >= -0.01
            and candidate_numf0 >= 0.98 * baseline_numf0
            and int(outer.candidate_FP_SIL.sum()) <= 3
            and max_file_worsening <= 1.0
        ),
        'python': platform.python_version(), 'numpy': np.__version__,
        'pandas': pd.__version__, 'scikit_learn': sklearn.__version__,
    }
    outer.to_csv(ROOT / 'working_output' / 'experiment_24_outer_lofo.csv',
                 index=False, float_format='%.10g')
    inner.to_csv(ROOT / 'working_output' / 'experiment_24_inner_selection.csv',
                 index=False, float_format='%.10g')
    (ROOT / 'working_output' / 'experiment_24_summary.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8')
    print(outer.to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
