from pathlib import Path
import sys, json, platform
import numpy as np
import pandas as pd
import sklearn
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_04_energy_gate import FILES, load_with_energy
from experiment_05_median_f0 import median_f0_within_runs

def _runs(mask):
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))

saved = pd.read_csv(ROOT / 'working_output' / 'experiment_08_lofo.csv')
saved = saved[saved.method == 'Gaussian + energy'].set_index('file')
rows = []
for path in FILES:
    item = load_with_energy(path)
    ref = saved.loc[path.name]
    pred = ((item['scores'] < float(ref.threshold)) &
            (item['relative_rms'] >= float(ref.energy_threshold)))
    f0_raw = item['fs'] / item['lags'][pred]
    f0_smooth = median_f0_within_runs(item, pred)[pred]
    valid_raw = f0_raw[np.isfinite(f0_raw) & (f0_raw > 0)]
    valid_smooth = f0_smooth[np.isfinite(f0_smooth) & (f0_smooth > 0)]
    assert len(valid_raw) == len(valid_smooth) == int(ref.NumF0)
    stats = item['stats']
    rows.append({'file': path.name, 'NumF0': len(valid_raw),
      'raw_F0mean_MAE_hz': abs(float(valid_raw.mean()) - stats['F0mean']),
      'median3_F0mean_MAE_hz': abs(float(valid_smooth.mean()) - stats['F0mean']),
      'raw_F0std_MAE_hz': abs(float(valid_raw.std()) - stats['F0std']),
      'median3_F0std_MAE_hz': abs(float(valid_smooth.std()) - stats['F0std']),
      'macro_f1': float(ref.macro_f1), 'balanced_accuracy': float(ref.balanced_accuracy),
      'recall_V': float(ref.recall_V), 'recall_UV': float(ref.recall_UV),
      'FP_SIL': int(ref.FP_SIL),
      'interior_frames_smoothed': int(max((end-start-2) for start,end in _runs(pred)))})
frame = pd.DataFrame(rows)
frame.to_csv(ROOT / 'working_output' / 'experiment_12_lofo.csv', index=False, float_format='%.10g')
summary = {'training_only': True, 'frame_ms':25, 'hop_ms':10,
 'cv':'four fold leave one file out; thresholds from experiment 08', 'files':len(rows),
 'mean_raw_F0mean_MAE_hz':float(frame.raw_F0mean_MAE_hz.mean()),
 'mean_median3_F0mean_MAE_hz':float(frame.median3_F0mean_MAE_hz.mean()),
 'mean_raw_F0std_MAE_hz':float(frame.raw_F0std_MAE_hz.mean()),
 'mean_median3_F0std_MAE_hz':float(frame.median3_F0std_MAE_hz.mean()),
 'NumF0_total':int(frame.NumF0.sum()), 'FP_SIL_total':int(frame.FP_SIL.sum()),
 'keep_by_preregistered_rule':bool(
   frame.median3_F0mean_MAE_hz.mean() <= frame.raw_F0mean_MAE_hz.mean() and
   frame.median3_F0std_MAE_hz.mean() <= frame.raw_F0std_MAE_hz.mean() and
   (frame.raw_F0mean_MAE_hz.mean()-frame.median3_F0mean_MAE_hz.mean() >= .25 or
    frame.raw_F0std_MAE_hz.mean()-frame.median3_F0std_MAE_hz.mean() >= .25)),
 'python':platform.python_version(), 'numpy':np.__version__, 'pandas':pd.__version__, 'scikit_learn':sklearn.__version__}
assert frame.NumF0.sum() == int(saved.NumF0.sum())
assert frame.FP_SIL.sum() == int(saved.FP_SIL.sum())
(ROOT / 'working_output' / 'experiment_12_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(frame.to_string(index=False))
print(json.dumps(summary, indent=2))
