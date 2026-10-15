from pathlib import Path
import sys, json, platform
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_04_energy_gate import FILES, load_with_energy

folds = pd.read_csv(ROOT / 'working_output' / 'experiment_08_lofo.csv')
rows = []
for path in FILES:
    print('scoring ' + path.name, flush=True)
    item = load_with_energy(path)
    pitch_row = folds[(folds.file == path.name) & (folds.method == 'Gaussian')].iloc[0]
    gate_row = folds[(folds.file == path.name) & (folds.method == 'Gaussian + energy')].iloc[0]
    base = item['scores'] < float(pitch_row.threshold)
    gated = base & (item['relative_rms'] >= float(gate_row.energy_threshold))
    removed = base & ~gated
    labels = item['labels']
    rr = item['relative_rms']
    counts = {lab: int((removed & (labels == lab)).sum()) for lab in ('v','uv','sil')}
    row = {'file': path.name, 'pitch_only_voiced': int(base.sum()),
           'after_energy_voiced': int(gated.sum()), 'removed_total': int(removed.sum()),
           'removed_LAB_V': counts['v'], 'removed_LAB_UV': counts['uv'],
           'removed_LAB_SIL': counts['sil'],
           'energy_threshold': float(gate_row.energy_threshold)}
    for lab, mask in [('V', labels == 'v'), ('UV', labels == 'uv'), ('SIL', labels == 'sil')]:
        vals = rr[removed & mask]
        row[f'removed_{lab}_relative_RMS_median'] = float(np.median(vals)) if len(vals) else None
        row[f'removed_{lab}_relative_RMS_min'] = float(np.min(vals)) if len(vals) else None
        row[f'removed_{lab}_relative_RMS_max'] = float(np.max(vals)) if len(vals) else None
    assert row['after_energy_voiced'] == int(gate_row.NumF0)
    assert row['removed_total'] == row['removed_LAB_V'] + row['removed_LAB_UV'] + row['removed_LAB_SIL']
    rows.append(row)
out = pd.DataFrame(rows)
out.to_csv(ROOT / 'working_output' / 'energy_gate_removed_frames.csv', index=False, float_format='%.10g')
summary = {'training_only': True, 'files': len(rows),
           'pitch_only_voiced': int(out.pitch_only_voiced.sum()),
           'after_energy_voiced': int(out.after_energy_voiced.sum()),
           'removed_total': int(out.removed_total.sum()),
           'removed_LAB_V': int(out.removed_LAB_V.sum()),
           'removed_LAB_UV': int(out.removed_LAB_UV.sum()),
           'removed_LAB_SIL': int(out.removed_LAB_SIL.sum()),
           'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__}
assert summary['removed_total'] == summary['removed_LAB_V'] + summary['removed_LAB_UV'] + summary['removed_LAB_SIL']
assert summary['pitch_only_voiced'] - summary['after_energy_voiced'] == summary['removed_total']
(ROOT / 'working_output' / 'energy_gate_removed_frames_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(out.to_string(index=False))
print(json.dumps(summary, indent=2))

