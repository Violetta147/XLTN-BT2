"""Exact pinned VOICEBOX PEFAC through Octave, plus explicit projection."""
import hashlib, subprocess, tempfile
from pathlib import Path
import numpy as np
from scipy.io import savemat,loadmat
HERE=Path(__file__).resolve().parent
EXE=Path('C:/Users/LAPTOP T&T/AppData/Local/Programs/GNU Octave/Octave-11.3.0/mingw64/bin/octave-cli.exe')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mquote(s):return "'"+str(s).replace('\\','/').replace("'","''")+"'"
def native(audio,fs):
    with tempfile.TemporaryDirectory(prefix='bt2-pefac-') as directory:
        input_path=Path(directory)/'input.mat';output_path=Path(directory)/'output.mat'
        savemat(input_path,dict(audio=np.asarray(audio).reshape(-1,1),fs=float(fs)))
        expression=f'addpath({mquote(HERE)}); pefac_bridge({mquote(input_path)},{mquote(output_path)});'
        command=[str(EXE),'--no-gui','--quiet','--eval',expression]
        result=subprocess.run(command,capture_output=True,text=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:raise RuntimeError(f'Octave PEFAC exit{result.returncode}: {result.stderr}')
        data=loadmat(output_path,squeeze_me=True,struct_as_record=False);fv=data['fv']
        proof=dict(raw_f0=np.asarray(data['fx']).reshape(-1),native_times=np.asarray(data['tx']).reshape(-1),pv=np.asarray(data['pv']).reshape(-1),vuvfea=fv.vuvfea,best=np.asarray(fv.best).reshape(-1).astype(int),ff=fv.ff,amp=fv.amp,medfx=np.asarray(fv.medfx).reshape(-1),w=np.asarray(fv.w).reshape(-1),dffact=np.asarray(fv.dffact),hist=fv.hist,native_fs=np.asarray(fs))
        assert len(proof['raw_f0'])>1 and np.isfinite(proof['raw_f0']).all() and np.isfinite(proof['pv']).all()
        assert np.all((proof['pv']>=0)&(proof['pv']<=1)) and np.allclose(np.diff(proof['native_times']),.01,atol=1e-12)
        log=dict(exe=str(EXE),exe_sha256=digest(EXE),runtime=str(data['runtime']),image_filter=str(data['image_filter']),image_filter_sha256=digest(str(data['image_filter'])),image_pad=str(data['image_pad']),image_pad_sha256=digest(str(data['image_pad'])),source=str(data['source']),source_sha256=digest(str(data['source'])),bridge_sha256=digest(HERE/'pefac_bridge.m'),returncode=result.returncode,stderr=result.stderr,stdout=result.stdout,input_pcm_sha256=hashlib.sha256(np.asarray(audio).tobytes()).hexdigest(),native_frames=len(proof['raw_f0']),native_first_center=float(proof['native_times'][0]),parameters=dict(tinc=.01,flim=[70,400],other_parameters='upstream defaults: fres20Hz; native analysis window; supplied GMM and DP weights'),transport='temporary MAT direct local subprocess; no Drive')
        return proof,log
def project(proof,times,fs,option,base_pred,base_f0):
    pred=np.zeros(len(times),bool);f0=np.full(len(times),np.nan)
    for i,t in enumerate(times):
        k=int(np.argmin(abs(proof['native_times']-t)))
        f=proof['raw_f0'][k];valid=abs(proof['native_times'][k]-t)<=.005+1/fs and 70<=f<=400
        if valid and (option['mode']=='pitch_only' or proof['pv'][k]>option['threshold']):pred[i]=True;f0[i]=f
    if option['mode']=='pitch_only':
        f0=np.where(base_pred&np.isfinite(f0),f0,base_f0);pred=base_pred.copy()
    assert np.array_equal(pred,np.isfinite(f0))
    return pred,f0
