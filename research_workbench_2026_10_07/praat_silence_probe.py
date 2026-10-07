import json
from pathlib import Path

import numpy as np
from scipy.io import wavfile

import praat_silence_adapter as native

HERE = Path(__file__).resolve().parent
folder = Path(native.metadata()['exe']).parent / 'probe'
folder.mkdir(exist_ok=True)
rows = []
for fs in (16000, 44100):
    times = np.arange(fs) / fs
    for name, signal in [('tone', np.sin(2 * np.pi * 173 * times) + .4 * np.sin(2 * np.pi * 346 * times)),
                         ('silence', np.zeros(fs))]:
        path = folder / f'silence_ablation_{name}_{fs}.wav'
        wavfile.write(path, fs, signal.astype(np.float32))
        for threshold in (.09, .15):
            native_times, f0, log = native.pitch(path, threshold)
            valid = f0[f0 > 0]
            if name == 'tone':
                assert len(valid) > 80 and np.max(abs(valid - 173)) < 1
            else:
                assert not len(valid)
            rows.append({'fs': fs, 'signal': name, 'silence_threshold': threshold, 'frames': len(f0),
                         'voiced_frames': len(valid), 'max_error_hz': float(np.max(abs(valid - 173))) if len(valid) else None,
                         'call': log})
proof = {'rows': rows, 'real_wav_read': False, 'generator_sha256': native.digest(__file__),
         'adapter_sha256': native.digest(HERE / 'praat_silence_adapter.py'),
         'script_sha256': native.digest(HERE / 'praat_extract_silence.praat')}
(HERE / 'results/praat_silence_synthetic_probe.json').write_text(json.dumps(proof, indent=2) + '\n')
print('PASS silence .09/.15: synthetic 173Hz and silence at16k/44.1k; eight native calls, no real WAV.')
