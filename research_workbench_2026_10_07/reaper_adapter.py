import hashlib
from pathlib import Path

import numpy as np

import sptk_adapter as native


def pitch(audio,fs,unvoiced_cost):
    assert len(audio)>fs*.05 and 6000<fs<=98000
    assert -.5<=unvoiced_cost<=1.6 and np.isfinite(audio).all()
    assert np.max(audio*32768)<=32767 and np.min(audio*32768)>=-32768
    if np.count_nonzero(audio)==0:
        proof=native.metadata()
        hop=round(fs*.01)
        frames=int(np.ceil(len(audio)/hop))
        times=np.arange(frames)*hop/fs
        f0=np.zeros(frames)
        call={'native_called':False,'status':'exact_whole_input_zero','command':None,'returncode':None,
              'input_samples':len(audio),'input_sha256':hashlib.sha256(np.ascontiguousarray(audio*32768,dtype='<f8').tobytes()).hexdigest(),
              'stdout_sha256':None,'native_frames':frames,'hop_samples':hop,'time_origin_s':0,
              'exe_sha256':proof['exe_sha256'],'source_commit':proof['commit'],
              'policy':'Only all-zero complete input bypasses native; no segment gate or failure-to-zero conversion'}
    else:
        times,f0,call=native.pitch(audio,fs,'reaper',unvoiced_cost)
        call=dict(call,native_called=True,status='native_success')
    call['reaper_adapter_sha256']=native.digest(Path(__file__))
    return times,f0,call
