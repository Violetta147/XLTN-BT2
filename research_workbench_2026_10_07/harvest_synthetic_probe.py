import hashlib
import json
from pathlib import Path

import numpy as np
import pyworld

HERE = Path(__file__).resolve().parent
rows = []
for fs in (16000, 44100):
    times = np.arange(fs) / fs
    for harmonics in (2, 12):
        for noise in (0., .003):
            signal = sum(np.sin(2 * np.pi * 173 * k * times) / k for k in range(1, harmonics + 1))
            signal += np.random.default_rng(20261007).normal(0, noise, len(signal))
            f0, native_times = pyworld.harvest(signal.astype(np.float64), fs,
                                              f0_floor=70, f0_ceil=400, frame_period=10)
            center = (native_times >= .1) & (native_times <= .9)
            valid = (f0 > 0) & center
            rows.append({'fs': fs, 'harmonics': harmonics, 'white_noise_std': noise, 'seed': 20261007,
                         'true_f0_hz': 173, 'center_voiced_frames': int(valid.sum()),
                         'center_native_frames': int(center.sum()),
                         'median_error_hz': float(np.median(abs(f0[valid] - 173))) if valid.any() else None,
                         'max_error_hz': float(np.max(abs(f0[valid] - 173))) if valid.any() else None})
proof = {'purpose': 'Synthetic transfer diagnostic before BT2 WAV; fixed grid; no tuning on real files',
         'signal': '1s; sum_{k=1..K} sin(2*pi*173*k*t)/k plus Gaussian noise; t=arange(fs)/fs',
         'rows': rows, 'pure_harmonic_failure_retained': True, 'real_wav_read': False,
         'pyworld': pyworld.__version__, 'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(HERE / 'results/Harvest_synthetic_probe.json').write_text(json.dumps(proof, indent=2) + '\n')
for row in rows:
    print(row)
