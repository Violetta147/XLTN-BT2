import hashlib
import inspect
import json
import platform
import sys
import urllib.request
from pathlib import Path

import librosa
import llvmlite
import numba
import numpy as np
import scipy

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


install = json.loads((HERE/'results/librosa_011_install_report.json').read_text())
wheel = next(x for x in install['install'] if x['metadata']['name']=='librosa')
assert wheel['metadata']['version']=='0.11.0'
root = Path(librosa.__file__).parent
pitch_source = Path(inspect.getsourcefile(librosa.pyin))
url = 'https://raw.githubusercontent.com/librosa/librosa/0.11.0/librosa/core/pitch.py'
with urllib.request.urlopen(url,timeout=30) as response:
    official = response.read()
assert hashlib.sha256(official).hexdigest()==digest(pitch_source)
paths = [pitch_source,root/'sequence.py',root/'util/utils.py',root/'util/decorators.py']
native_paths = list(Path(numba.__file__).parent.glob('*.pyd')) + list(Path(llvmlite.__file__).parent.rglob('*.dll'))
proof = {'python':sys.version,'interpreter':sys.executable,'platform':platform.platform(),'librosa':librosa.__version__,
         'numpy':np.__version__,'scipy':scipy.__version__,'numba':numba.__version__,'llvmlite':llvmlite.__version__,
         'wheel':wheel['download_info'],'runtime_source_sha256':{str(p):digest(p) for p in paths+native_paths},
         'official_pitch_source_url':url,'official_pitch_source_sha256':hashlib.sha256(official).hexdigest(),
         'installed_pitch_source_identical_to_official_tag':True,'real_wav_read':False,'generator_sha256':digest(__file__)}
(HERE/'results/librosa_011_provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
import pyin_adapter
rows = []
for fs in (16000,44100):
    time = np.arange(fs)/fs
    for name,audio in [('tone',np.sin(2*np.pi*173*time)+.4*np.sin(2*np.pi*346*time)),('silence',np.zeros(fs))]:
        for frame_ms in (40,80):
            times,f0,voiced,probability,log = pyin_adapter.pitch(audio,fs,frame_ms)
            valid = f0[voiced]
            if name=='tone':
                assert len(valid)>80 and np.max(abs(valid-173))<1.5
            else:
                assert not len(valid)
            rows.append({'fs':fs,'signal':name,'frame_ms':frame_ms,'native_frames':len(f0),'voiced_frames':len(valid),
                         'max_error_hz':float(np.max(abs(valid-173))) if len(valid) else None,'call':log})
probe = {'rows':rows,'real_wav_read':False,'adapter_sha256':digest(HERE/'pyin_adapter.py'),
         'generator_sha256':digest(__file__),'provenance_sha256':digest(HERE/'results/librosa_011_provenance.json')}
(HERE/'results/pyin_synthetic_probe.json').write_text(json.dumps(probe,indent=2)+'\n')
print('PASS librosa0.11.0 official pitch source match; eight synthetic pYIN tone/silence probes, no BT2 WAV.')
