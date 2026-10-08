"""pYIN with actual 25ms frames, no padding; separate from completed H33."""
import warnings,hashlib
from pathlib import Path
import numpy as np
import librosa
from pyin_adapter import PARAMETERS,metadata
def pitch(audio,fs,beta):
    provenance=metadata();length,hop=round(.025*fs),round(.01*fs)
    parameters=dict(PARAMETERS,sr=fs,frame_length=length,hop_length=hop,beta_parameters=tuple(beta))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        f0,voiced,probability=librosa.pyin(np.ascontiguousarray(audio,dtype=np.float64),**parameters)
    assert len(f0)==1+(len(audio)-length)//hop
    assert np.array_equal(np.isfinite(f0),voiced)
    assert np.isfinite(probability).all() and np.all((probability>=0)&(probability<=1))
    assert np.all((f0[voiced]>=70)&(f0[voiced]<=400))
    times=(np.arange(len(f0))*hop+length/2)/fs
    log=dict(librosa=librosa.__version__,frame_samples=length,hop_samples=hop,fs=fs,actual_frame_ms=1000*length/fs,actual_hop_ms=1000*hop/fs,rounding='Python round, nearest ties-to-even',beta_parameters=list(beta),center=False,audio_padding=False,other_parameters=dict(PARAMETERS,beta_parameters=list(beta),fill_na='NaN'),warnings=[str(w.message) for w in caught],source_hashes=provenance['runtime_source_sha256'],PCM_sha256=hashlib.sha256(np.ascontiguousarray(audio,dtype=np.float64).tobytes()).hexdigest(),frame_count=len(f0),limitation='70Hz has fewer than two periods in 25ms; quality warning retained, not concealed or circumvented with longer windows.')
    return dict(raw_f0=f0,native_times=times,voiced=voiced,probability=probability,native_fs=np.asarray(fs),frame_samples=np.asarray(length),hop_samples=np.asarray(hop)),log
