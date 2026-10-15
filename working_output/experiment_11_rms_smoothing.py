from pathlib import Path
import sys, json, platform
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_04_energy_gate import FILES, load_with_energy

saved = pd.read_csv(ROOT / 'working_output' / 'experiment_08_lofo.csv')
saved = saved[saved.method == 'Gaussian + energy'].set_index('file')
rows = []
for path in FILES:
    item = load_with_energy(path)
    ref = saved.loc[path.name]
    pitch = item['scores'] < float(ref.threshold)
    gate = float(ref.energy_threshold)
    original = pitch & (item['relative_rms'] >= gate)
    padded = np.pad(item['relative_rms'], (1, 1), mode='edge')
    smooth = np.median(np.lib.stride_tricks.sliding_window_view(padded, 3), axis=1)
    candidate = pitch & (smooth >= gate)
    changed = int(np.count_nonzero(candidate != original))
    labels = item['labels']
    mask = np.isin(labels, ('v', 'uv'))
    truth = labels[mask] == 'v'
    pred = candidate[mask]
    tp = int((truth & pred).sum()); tn = int((~truth & ~pred).sum())
    fp = int((~truth & pred).sum()); fn = int((truth & ~pred).sum())
    f1v = 2 * tp / (2 * tp + fp + fn)
    f1uv = 2 * tn / (2 * tn + fp + fn)
    f0 = item['fs'] / item['lags'][candidate]
    f0 = f0[np.isfinite(f0) & (f0 > 0)]
    stats = item['stats']
    rows.append({'file': path.name, 'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn,
        'macro_f1': (f1v + f1uv) / 2, 'recall_V': tp / (tp + fn),
        'recall_UV': tn / (tn + fp),
        'balanced_accuracy': (tp / (tp + fn) + tn / (tn + fp)) / 2,
        'F0mean_abs_error_hz': abs(float(f0.mean()) - stats['F0mean']),
        'F0std_abs_error_hz': abs(float(f0.std()) - stats['F0std']),
        'NumF0': int(len(f0)), 'FP_SIL': int(((labels == 'sil') & candidate).sum()),
        'original_gate_NumF0': int(ref.NumF0),
        'restored_LAB_V': int((candidate & ~original & pitch & (labels == 'v')).sum()),
        'restored_LAB_SIL': int((candidate & ~original & pitch & (labels == 'sil')).sum()),
        'restored_LAB_UV': int((candidate & ~original & pitch & (labels == 'uv')).sum()),
        'changed_voiced_decisions': changed})
frame = pd.DataFrame(rows)
frame.to_csv(ROOT / 'working_output' / 'experiment_11_lofo.csv', index=False, float_format='%.10g')
base = pd.read_csv(ROOT / 'working_output' / 'experiment_08_lofo.csv')
base = base[base.method == 'Gaussian + energy']
metrics = ['macro_f1','balanced_accuracy','recall_V','recall_UV','F0mean_abs_error_hz','F0std_abs_error_hz']
summary = {'training_only': True, 'frame_ms': 25, 'hop_ms': 10,
           'cv': 'four fold leave one file out; fixed thresholds from experiment 08',
           'median_window_frames': 3, 'files': len(rows),
           'baseline_mean': {k: float(base[k].mean()) for k in metrics if k in base},
           'candidate_mean': {k: float(frame[k].mean()) for k in metrics},
           'baseline_NumF0': int(base.NumF0.sum()), 'candidate_NumF0': int(frame.NumF0.sum()),
           'baseline_FP_SIL': int(base.FP_SIL.sum()), 'candidate_FP_SIL': int(frame.FP_SIL.sum()),
           'restored_LAB_V': int(frame.restored_LAB_V.sum()),
           'restored_LAB_SIL': int(frame.restored_LAB_SIL.sum()),
           'restored_LAB_UV': int(frame.restored_LAB_UV.sum()),
           'changed_voiced_decisions': int(frame.changed_voiced_decisions.sum()),
           'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__}
summary['keep_by_preregistered_rule'] = bool(
    summary['restored_LAB_V'] >= 3 and
    summary['candidate_mean']['macro_f1'] >= summary['baseline_mean']['macro_f1'] - .01 and
    summary['candidate_mean']['balanced_accuracy'] >= summary['baseline_mean']['balanced_accuracy'] - .01 and
    summary['candidate_FP_SIL'] <= summary['baseline_FP_SIL'] + 3 and
    summary['candidate_mean']['F0mean_abs_error_hz'] <= summary['baseline_mean']['F0mean_abs_error_hz'] + .5 and
    summary['candidate_mean']['F0std_abs_error_hz'] <= summary['baseline_mean']['F0std_abs_error_hz'] + 2)
(ROOT / 'working_output' / 'experiment_11_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(frame.to_string(index=False))
print(json.dumps(summary, indent=2))
