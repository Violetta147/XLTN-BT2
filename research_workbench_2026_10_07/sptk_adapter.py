import hashlib
import json
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def metadata():
    proof = json.loads((HERE/'results/sptk_native_provenance.json').read_text())
    assert proof['commit']=='0ebff5a9b1fb5851709130efa1d3efb186ef702a'
    assert digest(proof['exe'])==proof['exe_sha256']
    for path,expected in proof['key_source_sha256'].items():
        assert digest(Path(proof['source_root'])/path)==expected,path
    return proof


def pitch(audio, fs, algorithm, threshold):
    assert algorithm in ('swipe','reaper') and len(audio)>0 and 6000<fs<=98000
    assert np.isfinite(audio).all() and np.max(abs(audio))<=1
    proof = metadata()
    code = {'swipe':1,'reaper':2}[algorithm]
    hop = round(fs*.01)
    command = [proof['exe'],'-a',str(code),'-p',str(hop),'-s',str(fs/1000),
               '-L','70','-H','400',f'-t{code}',str(threshold),'-o','1']
    encoded = np.ascontiguousarray(np.asarray(audio)*32768,dtype='<f8').tobytes()
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    result = subprocess.run(command,input=encoded,capture_output=True,timeout=120,startupinfo=startup,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    stderr = result.stderr.decode('utf-8',errors='replace')
    if result.returncode:
        raise RuntimeError(f'SPTK {algorithm} returncode={result.returncode}: {stderr}')
    assert len(result.stdout)%8==0
    frequency = np.frombuffer(result.stdout,dtype='<f8').copy()
    assert len(frequency)==int(np.ceil(len(audio)/hop))
    assert np.isfinite(frequency).all() and (frequency>=0).all()
    times = np.arange(len(frequency))*hop/fs
    log = {'command':command,'returncode':result.returncode,'stderr':stderr,'input_samples':len(audio),
           'input_sha256':hashlib.sha256(encoded).hexdigest(),'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),
           'transport':'binary little-endian float64 PCM-scale stdin/output; frequency Hz, UV=0',
           'normalised_audio_scale':32768,'hop_samples':hop,'time_origin_s':0,'native_frames':len(frequency),
           'exe_sha256':proof['exe_sha256'],'source_commit':proof['commit'],'adapter_sha256':digest(__file__)}
    return times,frequency,log
