import ast
import contextlib
import hashlib
import io
import json
import sys
import time
import warnings
from functools import lru_cache
from pathlib import Path

import numpy as np
import scipy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'sources/yaapt'))
import amfm_decompy.basic_tools as basic
import amfm_decompy.pYAAPT as api


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def metadata():
    proof=json.loads((HERE/'results/yaapt_source_discovery.json').read_text())
    for name in ('amfm_decompy/pYAAPT.py','amfm_decompy/basic_tools.py','LICENSE','pyproject.toml'):
        assert digest(HERE/'sources/yaapt'/name)==proof['sources'][name]['sha256']
    assert Path(api.__file__).resolve()==(HERE/'sources/yaapt/amfm_decompy/pYAAPT.py').resolve()
    assert Path(basic.__file__).resolve()==(HERE/'sources/yaapt/amfm_decompy/basic_tools.py').resolve()
    defaults={}
    for node in ast.walk(ast.parse(Path(api.__file__).read_text(encoding='utf-8'))):
        if isinstance(node,ast.Assign) and len(node.targets)==1:
            target=node.targets[0]
            if isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='parameters' and isinstance(node.value,ast.Call):
                key=ast.literal_eval(target.slice)
                defaults[key]=ast.literal_eval(node.value.args[1])
    assert len(defaults)==34 and defaults['frame_length']==35. and defaults['tda_frame_length']==35., 'Pinned port has 34 defaults'
    assert api.PitchObj.PITCH_HALF==0 and api.PitchObj.PITCH_DOUBLE==0
    return {'package_version':proof['package_version'],'python_port_commit':proof['github_commit'],
            'defaults':defaults,'source_sha256':{str(Path(x).relative_to(HERE.parent)):digest(x) for x in (api.__file__,basic.__file__)},
            'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__}


def pitch(audio,fs,frame_ms):
    assert fs>3000 and len(audio)>fs*.1 and np.isfinite(audio).all() and max(abs(audio))<=1
    proof=metadata()
    params=dict(proof['defaults'],frame_length=float(frame_ms),f0_min=70.,f0_max=400.,frame_space=10.)
    source=np.ascontiguousarray(audio,dtype=np.float64).copy()
    input_hash=hashlib.sha256(source.tobytes()).hexdigest()
    stdout=io.StringIO()
    started=time.perf_counter()
    with warnings.catch_warnings(record=True) as caught,contextlib.redirect_stdout(stdout):
        warnings.simplefilter('always')
        signal=basic.SignalObj(source,fs)
        output=api.yaapt(signal,**params)
    assert hashlib.sha256(source.tobytes()).hexdigest()==input_hash
    times=np.asarray(output.frames_pos)/fs
    frequency=np.asarray(output.samp_values,dtype=np.float64).copy()
    assert len(times)==len(frequency)>0 and np.isfinite(frequency).all() and (frequency>=0).all()
    assert np.allclose(np.diff(times),int(10*fs/1000)/fs,atol=1e-12)
    log={'parameters':params,'frame_size_samples':int(output.frame_size),'hop_samples':int(output.frame_jump),
         'time_origin_s':float(times[0]),'native_frames':len(frequency),'input_samples':len(source),'input_sha256':input_hash,
         'stdout':stdout.getvalue(),'warnings':[{'category':x.category.__name__,'message':str(x.message)} for x in caught],
         'f0_sha256':hashlib.sha256(frequency.tobytes()).hexdigest(),'frame_positions_samples':output.frames_pos.tolist(),
         'output_attribute':'samp_values (UV0), not samp_interp/upsampled values','backend_called':True,
         'input_unchanged':True,'half_double_flags':[api.PitchObj.PITCH_HALF,api.PitchObj.PITCH_DOUBLE],
         'source_sha256':proof['source_sha256'],'python_port_commit':proof['python_port_commit'],
         'adapter_sha256':digest(__file__),'wall_time_s':time.perf_counter()-started}
    return times,frequency,log
