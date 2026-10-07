import hashlib
import json
import warnings
from pathlib import Path

import librosa
import numpy as np

HERE = Path(__file__).resolve().parent
PARAMETERS = {'fmin':70,'fmax':400,'n_thresholds':100,'beta_parameters':(2,18),'boltzmann_parameter':2,
              'resolution':.1,'max_transition_rate':35.92,'switch_prob':.01,'no_trough_prob':.01,
              'fill_na':np.nan,'center':False,'pad_mode':'constant'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def metadata():
    proof = json.loads((HERE/'results/librosa_011_provenance.json').read_text())
    assert librosa.__version__==proof['librosa']=='0.11.0'
    for path, expected in proof['runtime_source_sha256'].items():
        assert digest(path)==expected,path
    return proof


def pitch(audio, fs, frame_ms):
    metadata()
    frame_length, hop_length = round(fs*frame_ms/1000),round(fs*.01)
    assert frame_ms in (40,60,80) and len(audio)>=frame_length and frame_length>=2*fs/70
    parameters = dict(PARAMETERS,sr=fs,frame_length=frame_length,hop_length=hop_length)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        f0, voiced, probability = librosa.pyin(np.ascontiguousarray(audio,dtype=np.float64),**parameters)
    times = (np.arange(len(f0))*hop_length+frame_length/2)/fs
    assert len(f0)==1+(len(audio)-frame_length)//hop_length
    assert np.array_equal(np.isfinite(f0),voiced)
    assert np.isfinite(probability).all() and ((probability>=0)&(probability<=1)).all()
    assert ((f0[voiced]>=70)&(f0[voiced]<=400)).all()
    saved_parameters = dict(parameters,beta_parameters=list(parameters['beta_parameters']),fill_na='NaN')
    return times,f0,voiced,probability,{'librosa':'0.11.0','parameters':saved_parameters,
        'warnings':[str(x.message) for x in caught],'input_samples':len(audio),'native_frames':len(f0),
        'center_alignment':'(frame_index*hop_length+frame_length/2)/fs; center=False; no padding',
        'adapter_sha256':digest(__file__)}
