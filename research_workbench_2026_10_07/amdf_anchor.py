import hashlib
from pathlib import Path

import numpy as np
import amdf_dual_window as dual

HERE=Path(__file__).resolve().parent
core,audit=dual.core,dual.audit
SOURCE_CACHE={}
CURVE_CACHE={}
OUTPUT_PREFIX='H41'


def candidates(lags,curve,fs):
    if not np.isfinite(curve).all() or np.ptp(curve)<=1e-12:
        return np.array([]),np.array([]),np.array([],dtype=int)
    indices=np.flatnonzero((curve[1:-1]<=curve[:-2])&(curve[1:-1]<=curve[2:]))+1
    if not len(indices):
        indices=np.array([int(np.argmin(curve))])
    refined=np.array([core.refine_lag(curve,index,float(lags[index])) for index in indices])
    frequency=fs/refined
    keep=np.isfinite(frequency)&(frequency>=70)&(frequency<=400)
    return frequency[keep],curve[indices[keep]],indices[keep]


def choose(gate,frequency,dips,band):
    if not 70<=gate<=400 or not len(frequency):
        return gate,'praat_no_candidate',-1
    delta=abs(1200*np.log2(frequency/gate))
    valid=np.flatnonzero(delta<=band+1e-9)
    if not len(valid):
        return gate,'praat_disagreement',-1
    chosen=min(valid,key=lambda j:(float(dips[j]),float(delta[j]),float(frequency[j])))
    return float(frequency[chosen]),'amdf_dip',int(chosen)


def curves(item,audio,times,gate,window):
    key=(window,item['file'])
    if key in CURVE_CACHE:
        return CURVE_CACHE[key]
    core.init_functions()
    fs=item['fs']
    length=round(fs*window/1000)
    lags,_=core.AMDF['normalized_amdf'](np.zeros(length),fs)
    values=np.full((len(times),len(lags)),np.nan)
    starts=np.array([round(t*fs-length/2) for t in times])
    hashes=np.full(len(times),'',dtype='<U64')
    for i in np.flatnonzero((gate>=70)&(gate<=400)):
        start=starts[i]
        if start<0 or start+length>len(audio):
            continue
        frame=np.ascontiguousarray(audio[start:start+length],dtype=np.float64)
        frame_lags,values[i]=core.AMDF['normalized_amdf'](frame,fs)
        assert np.array_equal(frame_lags,lags)
        hashes[i]=hashlib.sha256(frame.tobytes()).hexdigest()
    path=HERE/f'results/{OUTPUT_PREFIX}_curves_w{window}_{Path(item["file"]).stem}.npz'
    assert not path.exists(),'Preserve completed features'
    np.savez_compressed(path,times=times,gate_frequency=gate,lags=lags,curve=values,starts=starts,frame_sha256=hashes,
                        frame_samples=length,fs=fs,input_samples=len(audio),audio_sha256=hashlib.sha256(np.ascontiguousarray(audio,dtype=np.float64).tobytes()).hexdigest())
    value={'times':times,'lags':lags,'curves':values,'starts':starts,'frame_samples':length,
           'path':str(path.relative_to(HERE)),'sha256':audit.digest(path),'input_samples':len(audio),
           'window_ms':window,'processed_frames':int(np.isfinite(values).all(axis=1).sum()),
           'source_sha256':audit.digest(__file__),'frozen_notebook_sha256':audit.digest(core.BASELINES/'AMDF.ipynb')}
    CURVE_CACHE[key]=value
    return value
