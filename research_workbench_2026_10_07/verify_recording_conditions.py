import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import wavfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE / 'results'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


receipt = json.loads((OUT / 'recording_conditions_receipt.json').read_text(encoding='utf-8'))
for relative, expected in receipt['input_sha256'].items():
    path = Path(relative)
    path = path if path.is_absolute() else REPO / path
    assert digest(path) == expected, path
for relative, expected in receipt['output_sha256'].items():
    assert digest(OUT / relative) == expected, relative
frames = pd.read_csv(OUT / 'recording_conditions_frames.csv')
features = pd.read_csv(OUT / 'recording_conditions_features.csv')
energy = pd.read_csv(OUT / 'recording_conditions_energy.csv')
metrics = pd.read_csv(OUT / 'recording_conditions_saved_metrics.csv')
groups = pd.read_csv(OUT / 'recording_conditions_groups.csv')
assert set(frames.file) == {'phone_F1.wav', 'phone_M1.wav', 'studio_F1.wav', 'studio_M1.wav'}
assert set(frames['mode']) == {'native', 'common_16k'}
assert len(frames) == receipt['frames'] and len(features) == receipt['feature_rows']
assert not frames.duplicated(['file', 'mode', 'start_s']).any()
assert np.isfinite(frames.select_dtypes('number')).all().all()
assert np.allclose(features.filter(like='fraction_').sum(axis=1), 1, atol=1e-12)
assert ((features.filter(like='fraction_') >= 0) & (features.filter(like='fraction_') <= 1)).all().all()
assert np.allclose(frames.filter(regex=r'^power_').sum(axis=1), frames.spectral_power_0_8000, rtol=1e-12)
assert set(frames.loc[frames['mode'] == 'common_16k', 'fs']) == {16000}
for name, data in frames.groupby('file'):
    segments = []
    for line in (REPO / 'TinHieuHuanLuyen' / Path(name).with_suffix('.lab')).read_text(encoding='utf-8-sig').splitlines():
        words = line.split()
        if len(words) == 3:
            segments.append((float(words[0]), float(words[1]), words[2]))
    for row in data.itertuples():
        assert any(label == row.label and row.start_s >= a + .020 - 1e-10 and row.end_s <= b - .020 + 1e-10 for a, b, label in segments)
checked = 0
for name, data in frames[frames['mode'] == 'native'].groupby('file'):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', wavfile.WavFileWarning)
        fs, pcm = wavfile.read(REPO / 'TinHieuHuanLuyen' / name)
    for row in data.itertuples():
        start = round(row.start_s * fs)
        x = pcm[start:start + row.samples].astype(np.float64) / 32768
        expected = np.linalg.norm(x) ** 2 / len(x)
        assert np.isclose(expected, row.mean_square, rtol=1e-10, atol=1e-16)
        checked += 1
for row in features.itertuples():
    data = frames[(frames.file == row.file) & (frames['mode'] == row.mode) & (frames.label == row.label)]
    assert len(data) == row.frames
    assert np.isclose(row.rms ** 2, data.mean_square.mean(), rtol=1e-10, atol=1e-16)
for row in energy.itertuples():
    data = features[(features.file == row.file) & (features['mode'] == row.mode)].set_index('label')
    assert np.isclose(row.v_sil_rms_ratio_db, 20 * np.log10(data.loc['v', 'rms'] / data.loc['sil', 'rms']), atol=1e-10)
for row in groups.itertuples():
    data = metrics[(metrics.protocol == row.protocol) & (metrics.device_name == row.device_name)]
    assert len(data) == row.files == 2
    assert np.isclose(row.average_mape, data.average_mape.mean(), atol=1e-12)
assert len(metrics) == receipt['metric_rows'] == 28
validation = dict(passed=True, input_hashes_checked=len(receipt['input_sha256']), output_hashes_checked=len(receipt['output_sha256']),
                  native_frame_energy_checks=checked, no_test_audio=True, group_rows=len(groups),
                  receipt_sha256=digest(OUT / 'recording_conditions_receipt.json'), verifier_sha256=digest(Path(__file__).resolve()),
                  limit='Checks hashes, native RMS, aggregates, fractions and scope; does not certify speaker identity, causal recording effects or pitch correctness')
(OUT / 'recording_conditions_validation.json').write_text(json.dumps(validation, indent=2) + '\n', encoding='utf-8')
print(json.dumps(validation, indent=2))
