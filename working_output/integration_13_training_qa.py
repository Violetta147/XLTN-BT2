from pathlib import Path
import hashlib, json, platform, sys

import numpy as np
import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / 'BT2_AMDF_implement_executed_original - Copy.ipynb'
nb = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
ns = {'__name__': '__main__', 'display': lambda *a, **k: None}
for index in (1, 3, 5, 7, 9, 10, 14, 19):
    exec(compile(''.join(nb['cells'][index]['source']),
                 f'{NOTEBOOK.name}:cell{index}', 'exec'), ns)
    if index == 1:
        assert ns['TRAIN_DIR'].resolve() == (ROOT / 'TinHieuHuanLuyen').resolve()
        ns['FRAME_MS_CANDIDATES'] = (25,)
        ns['TEST_DIR'] = ROOT / '_disabled_test_for_training_qa'

assert len(ns['train_pairs']) == 4
assert ns['FINAL_FRAME_MS'] == 25 and ns['HOP_MS'] == 10
assert ns['FINAL_THRESHOLD_METHOD'] == 'Gaussian'
assert np.isclose(ns['FINAL_THRESHOLD'], 0.41249330632749887, atol=1e-9)
assert np.isclose(ns['FINAL_ENERGY_THRESHOLD'], 0.061544615883604575, atol=1e-9)

baseline = pd.read_csv(ROOT / 'working_output' / 'integration_12_training_after.csv').set_index('file')
rows = []
for wav_path, lab_path in ns['train_pairs']:
    result = ns['process_file_amdf'](wav_path, lab_path)
    labels = np.asarray([ns['label_at_time'](t, result['segments'])
                         for t in result['center_times']], dtype=object)
    pred = result['predicted_voiced']
    mask = np.isin(labels, ('v', 'uv'))
    truth, p = labels[mask] == 'v', pred[mask]
    tp = int((truth & p).sum())
    tn = int((~truth & ~p).sum())
    fp = int((~truth & p).sum())
    fn = int((truth & ~p).sum())
    f1v = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0
    f1uv = 2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else 0
    used = np.asarray(result['f0_contour'])
    valid = used[np.isfinite(used)]
    rows.append({
        'file': wav_path.name, 'frames': len(labels), 'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn,
        'macro_f1': (f1v + f1uv) / 2,
        'recall_V': tp / (tp + fn), 'recall_UV': tn / (tn + fp),
        'balanced_accuracy': (tp / (tp + fn) + tn / (tn + fp)) / 2,
        'NumF0': len(valid), 'FP_SIL': int(((labels == 'sil') & pred).sum()),
        'median5_F0mean_MAE_hz': abs(float(valid.mean()) - result['gt_f0_mean']),
        'median5_F0std_MAE_hz': abs(float(valid.std()) - result['gt_f0_std']),
        'prediction_sha256': hashlib.sha256(pred.astype(np.uint8).tobytes()).hexdigest(),
    })

frame = pd.DataFrame(rows).set_index('file').sort_index()
base = baseline.sort_index()
for column in ('TP', 'TN', 'FP', 'FN', 'NumF0', 'FP_SIL', 'prediction_sha256'):
    assert np.array_equal(frame[column].to_numpy(), base[column].to_numpy()), column
for column in ('macro_f1', 'recall_V', 'recall_UV', 'balanced_accuracy'):
    assert np.allclose(frame[column], base[column], rtol=0, atol=1e-12), column

summary = {
    'data': 'TinHieuHuanLuyen only', 'files': len(frame), 'frame_ms': ns['FINAL_FRAME_MS'],
    'hop_ms': ns['HOP_MS'], 'T_pitch': float(ns['FINAL_THRESHOLD']),
    'T_energy': float(ns['FINAL_ENERGY_THRESHOLD']),
    'macro_f1_mean': float(frame.macro_f1.mean()),
    'BA_mean': float(frame.balanced_accuracy.mean()),
    'recall_V_mean': float(frame.recall_V.mean()),
    'recall_UV_mean': float(frame.recall_UV.mean()),
    'F0mean_MAE_median3': float(base.used_F0mean_MAE_hz.mean()),
    'F0mean_MAE_median5': float(frame.median5_F0mean_MAE_hz.mean()),
    'F0std_MAE_median3': float(base.used_F0std_MAE_hz.mean()),
    'F0std_MAE_median5': float(frame.median5_F0std_MAE_hz.mean()),
    'NumF0_total': int(frame.NumF0.sum()), 'FP_SIL_total': int(frame.FP_SIL.sum()),
    'classification_and_prediction_hashes_unchanged': True,
    'prediction_hashes': dict(zip(frame.index, frame.prediction_sha256)),
    'python': platform.python_version(), 'numpy': np.__version__,
    'pandas': pd.__version__, 'scikit_learn': sklearn.__version__,
}
assert summary['F0mean_MAE_median5'] < summary['F0mean_MAE_median3']
assert summary['F0std_MAE_median5'] < summary['F0std_MAE_median3']

out = ROOT / 'working_output'
frame.reset_index().to_csv(out / 'integration_13_training_after.csv', index=False,
                           float_format='%.10g')
(out / 'integration_13_training_after.json').write_text(
    json.dumps(summary, indent=2), encoding='utf-8')
print(frame.to_string())
print(json.dumps(summary, indent=2))
