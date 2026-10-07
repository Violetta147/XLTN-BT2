import hashlib
import io
import json
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def metadata():
    proof = json.loads((HERE / 'results/praat_native_7002_provenance.json').read_text())
    assert proof['version_stdout'] == '7.0.02'
    assert digest(proof['exe']) == proof['exe_sha256']
    return proof


def decode(data):
    return data.decode('utf-16-le') if b'\x00' in data else data.decode('utf-8-sig')


def pitch(path, method, voicing_threshold):
    assert method in ('raw', 'filtered') and 0 < voicing_threshold < 1
    proof = metadata()
    command = [proof['exe'], '--run', str(HERE / 'praat_extract_native.praat'),
               str(Path(path).resolve()), method, str(voicing_threshold)]
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    result = subprocess.run(command, capture_output=True, timeout=60, startupinfo=startup,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    stdout, stderr = decode(result.stdout), decode(result.stderr)
    if result.returncode:
        raise RuntimeError(f'Praat CLI returncode={result.returncode}: {stderr}')
    assert stdout.splitlines()[0] == '# Praat 7.0.02'
    table = pd.read_csv(io.StringIO(stdout), comment='#')
    assert list(table.columns) == ['time_s', 'f0_hz'] and len(table)
    assert np.isfinite(table.to_numpy()).all() and (table.f0_hz >= 0).all()
    assert np.allclose(np.diff(table.time_s), .01, atol=1e-12)
    log = {'command': command, 'returncode': result.returncode, 'stderr': stderr,
           'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(), 'native_frames': len(table),
           'transport': 'stdout; UTF-16LE detected when needed; no FULL-TRUST',
           'exe_sha256': proof['exe_sha256'], 'script_sha256': digest(HERE / 'praat_extract_native.praat')}
    return table.time_s.to_numpy(), table.f0_hz.to_numpy(), log
