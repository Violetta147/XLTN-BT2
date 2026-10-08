import argparse
import json
import platform
import subprocess
import time
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
import voicing_recovery as common

HERE, REPO, OUT = common.HERE, common.REPO, common.OUT
core, audit = common.core, common.audit
OPTIONS = [dict(id='hard170',alpha=None,transition=0.)]+[
    dict(id=f'cep_a{int(alpha*100):03d}_t{int(transition*100):03d}',alpha=alpha,transition=transition)
    for alpha in (0.,.5,1.) for transition in (0.,.15,.5)]
BY_ID = {r['id']:r for r in OPTIONS}


def git(*args):
    return subprocess.check_output(['git','-c','safe.directory='+str(REPO).replace('\\','/'),'-C',str(REPO),*args],text=True).strip()


def refine(curve,k):
    a,b,c=curve[k-1:k+2]
    delta=.5*(a-c)/(a-2*b+c) if abs(a-2*b+c)>1e-12 else 0.
    return k+np.clip(delta,-.5,.5)


def design(audio,fs,times,baseline):
    length=round(fs*.04)
    nfft=1 << (4*length-1).bit_length()
    lags=np.arange(int(np.ceil(fs/400))-1,int(np.floor(fs/70))+2)
    cep_curves=np.zeros((len(times),len(lags)))
    acf_curves=np.zeros_like(cep_curves)
    candidates=np.full((len(times),9),np.nan)
    acf_score=np.zeros_like(candidates);cep_score=np.zeros_like(candidates)
    starts=np.round(times*fs-length/2).astype(int)
    for i in np.flatnonzero(baseline['pred']):
        start=starts[i]
        x=np.zeros(length)
        left,right=max(0,start),min(len(audio),start+length)
        x[left-start:right-start]=audio[left:right]
        x-=x.mean()
        spectrum=abs(np.fft.rfft(x*np.hanning(length),nfft))
        floor=max(np.max(spectrum)*1e-8,1e-20)
        cepstrum=np.fft.irfft(np.log(np.maximum(spectrum,floor)),nfft)
        cep_curves[i]=cepstrum[lags]
        for j,lag in enumerate(lags):
            a,b=x[:-lag],x[lag:]
            acf_curves[i,j]=np.dot(a,b)/max(np.linalg.norm(a)*np.linalg.norm(b),1e-20)
        values=[float(baseline['f0'][i])]
        for curve in (acf_curves[i],cep_curves[i]):
            peaks=[k for k in range(1,len(lags)-1) if curve[k]>0 and curve[k]>=curve[k-1] and curve[k]>=curve[k+1]]
            peaks=sorted(peaks,key=lambda k:(-curve[k],k))
            accepted=[]
            for k in peaks:
                pitch=fs/(lags[0]+refine(curve,k))
                if 70<=pitch<=400 and abs(1200*np.log2(pitch/baseline['f0'][i]))<=200:
                    accepted.append(pitch)
                if len(accepted)==4:break
            values+=accepted
        candidates[i,:len(values)]=values
        normalization=max(float(np.max(cep_curves[i,1:-1])),1e-20)
        for j,pitch in enumerate(values):
            lag=fs/pitch
            acf_score[i,j]=np.clip(np.interp(lag,lags,acf_curves[i]),0.,1.)
            cep_score[i,j]=np.clip(np.interp(lag,lags,cep_curves[i])/normalization,0.,1.)
    return dict(times=times,base_pred=baseline['pred'],base_f0=baseline['f0'],candidates=candidates,
                acf_score=acf_score,cep_score=cep_score,acf_curves=acf_curves,cep_curves=cep_curves,
                lags=lags,starts=starts,frame_samples=length,nfft=nfft,fs=fs)


def infer(proof,option):
    pred,f0=proof['base_pred'].copy(),proof['base_f0'].copy()
    if option['alpha'] is None:return pred,f0
    cand=proof['candidates'];valid=np.isfinite(cand)
    cents=np.zeros_like(cand)
    for i in np.flatnonzero(pred):
        cents[i,valid[i]]=abs(1200*np.log2(cand[i,valid[i]]/proof['base_f0'][i]))
    cost=1-((1-option['alpha'])*proof['acf_score']+option['alpha']*proof['cep_score'])+.15*cents/200
    cost[~valid]=np.inf
    indices=np.flatnonzero(pred)
    runs=np.split(indices,np.where(np.diff(indices)>1)[0]+1)
    for run in runs:
        if not len(run):continue
        back=np.zeros((len(run),9),dtype=int)
        accumulated=cost[run[0]].copy()
        for t,i in enumerate(run[1:],1):
            a,b=cand[i-1],cand[i]
            distance=np.full((9,9),np.inf)
            supported=valid[i-1][:,None]&valid[i][None,:]
            difference=np.zeros((9,9))
            np.divide(b[None,:],a[:,None],out=difference,where=supported)
            distance[supported]=np.minimum(abs(1200*np.log2(difference[supported]))/200,3)
            transition=option['transition']*np.where(supported,distance,0.)
            matrix=accumulated[:,None]+transition
            matrix[~supported]=np.inf
            back[t]=np.argmin(matrix,axis=0)
            accumulated=matrix[back[t],np.arange(9)]+cost[i]
        state=int(np.argmin(accumulated))
        for t in range(len(run)-1,-1,-1):
            f0[run[t]]=cand[run[t],state]
            state=int(back[t,state])
    assert np.array_equal(pred,np.isfinite(f0))
    return pred,f0


def choose(rows):
    frame=pd.DataFrame(rows);base=frame[frame.option_id=='hard170'];rank=[]
    for option in OPTIONS:
        group=frame[frame.option_id==option['id']]
        eligible=bool(np.isfinite(group.average_mape).all() and group.macro_f1.mean()>=base.macro_f1.mean()-.01
            and group.recall_v.mean()>=base.recall_v.mean()-.01 and group.false_voiced_sil.sum()<=base.false_voiced_sil.sum()+1)
        rank.append((not eligible,group.average_mape.max() if eligible else np.inf,
                     group.average_mape.mean() if eligible else np.inf,option['id']))
    return min(rank)[-1]


def register():
    assert not (HERE/'H53_REGISTRY.json').exists()
    paths=[Path(__file__),HERE/'verify_cepstral_path.py',HERE/'verify_yaapt_extension_v2.py',HERE/'yaapt_extension.py',
        HERE/'H53_REGISTRATION.md',Path(core.__file__),Path(common.__file__),
        OUT/'H47_nested_contours.csv',OUT/'H48_test_contours.csv',core.RESULTS/'frozen_config.json']
    for directory in (core.TRAIN,REPO/'TinHieuKiemThu',core.TRAIN_GT,core.HERE/'test_3gt'):
        paths+=list(directory.glob('*.wav'))+list(directory.glob('*.lab'))
    audit.json_write(HERE/'H53_REGISTRY.json',dict(options=OPTIONS,rollback_commit=git('rev-parse','HEAD'),
        hashes={str(p.relative_to(REPO)):audit.digest(p) for p in paths},seed=None,actual_fit_files=[]))


def check_registry():
    registry=json.loads((HERE/'H53_REGISTRY.json').read_text());assert registry['options']==OPTIONS
    for path,digest in registry['hashes'].items():assert audit.digest(REPO/path)==digest,path


def precheck():
    rows=[]
    for fs in (16000,44100):
        t=np.arange(round(fs*.6))/fs
        for pitch in (100.,173.,200.,300.):
            audio=.2*(np.sin(2*np.pi*pitch*t)+.5*np.sin(4*np.pi*pitch*t)+.3*np.sin(6*np.pi*pitch*t))
            times=np.arange(.1,.5,.01)
            baseline=dict(pred=np.ones(len(times),bool),f0=np.full(len(times),pitch*1.015))
            proof=design(audio,fs,times,baseline)
            shifted=design(audio*.5+.2,fs,times,baseline)
            assert np.allclose(proof['acf_curves'],shifted['acf_curves'],atol=1e-10)
            assert np.allclose(proof['cep_curves'],shifted['cep_curves'],atol=1e-8)
            for option in OPTIONS[1:]:
                pred,f0=infer(proof,option)
                assert pred.all() and np.isfinite(f0).all()
                error=float(np.median(abs(f0-pitch)))
                rows.append(dict(fs=fs,pitch=pitch,option_id=option['id'],median_error_hz=error,passed=error<5))
    audit.json_write(OUT/'H53_precheck.json',dict(passed=all(r['passed'] for r in rows),cases=rows,
        scope='8 synthetic harmonic signals x9 deterministic configurations; gain/DC invariance; 1.5percent biased anchors'))
    assert all(r['passed'] for r in rows)
    print('PASS H53 synthetic harmonic accuracy, finite output and gain/DC invariance')


def measure(stage):
    check_registry()
    assert not (OUT/f'H53_{stage}_experiment.json').exists()
    if stage=='test':
        assert json.loads((OUT/'H53_train_verification.json').read_text())['passed']
        freeze=json.loads((OUT/'H53_FROZEN_SELECTION.json').read_text())
        options=[BY_ID[identity] for identity in freeze['external_options']]
    else:
        assert json.loads((OUT/'H53_precheck.json').read_text())['passed']
        options=OPTIONS
    directory=core.TRAIN if stage=='train' else REPO/'TinHieuKiemThu'
    old=pd.read_csv(OUT/('H47_nested_contours.csv' if stage=='train' else 'H48_test_contours.csv'),float_precision='round_trip')
    rows,outputs=[],[];started=time.perf_counter()
    for path in sorted(directory.glob('*.wav')):
        fs,audio=core.load_audio(path)
        group=old[(old.file==path.name)&(old.model=='candidate')]
        baseline=dict(pred=group.pred_voiced.to_numpy(bool),f0=group.f0_hz.to_numpy())
        times=group.time_s.to_numpy()
        proof=design(audio,fs,times,baseline)
        proof_path=OUT/f'H53_{stage}_design_{path.stem}.npz';assert not proof_path.exists()
        np.savez_compressed(proof_path,**proof);outputs.append(proof_path)
        item=core.frame_features(path,split=stage)
        assert np.allclose(times,item['times'],atol=1e-12)
        estimates=[]
        for option in options:
            pred,f0=infer(proof,option)
            row=dict(option_id=option['id'],changed_pitch_frames=int(np.sum(pred & (f0!=baseline['f0']))),**core.score_file(item,pred,f0))
            rows.append(row);estimates.append(f0)
        output=OUT/f'H53_{stage}_predictions_{path.stem}.npz';assert not output.exists()
        np.savez_compressed(output,option_id=np.array([r['id'] for r in options]),f0=np.array(estimates),pred=baseline['pred'],times=times)
        outputs.append(output);print('H53 measured',stage,path.name,flush=True)
    path=OUT/f'H53_{stage}_fixed.csv';pd.DataFrame(rows).to_csv(path,index=False);outputs.append(path)
    result=dict(measured_commit=git('rev-parse','HEAD'),actual_fit_files=[],seed=None,new_native_calls=0,
        historical_test_exposure=True,test_tuning=False,wall_time_s=time.perf_counter()-started,
        runtime=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__))
    if stage=='train':
        names=sorted({r['file'] for r in rows});selections=[];traces=[]
        for outer in ['final']+names:
            pool=[name for name in names if name!=outer]
            records=[dict(outer_held=outer,inner_held=r['file'],actual_fit_files='',**r) for r in rows if r['file'] in pool]
            traces+=records;selections.append(dict(outer_held=outer,selection_files=pool,option_id=choose(records)))
        selected={r['outer_held']:r['option_id'] for r in selections};metrics=[]
        for split in ('train','lofo','nested'):
            for name in names:
                for model,identity in [('accepted','hard170'),('candidate',selected[name] if split=='nested' else selected['final'])]:
                    row=next(r for r in rows if r['file']==name and r['option_id']==identity)
                    metrics.append(dict(split=split,model=model,**row))
        summaries,gates=common.gates(pd.DataFrame(metrics));result.update(selections=selections,summaries=summaries,decision=gates)
        for filename,value in [('H53_metrics.csv',metrics),('H53_inner_traces.csv',traces)]:
            path=OUT/filename;pd.DataFrame(value).to_csv(path,index=False);outputs.append(path)
        path=OUT/'H53_FROZEN_SELECTION.json'
        audit.json_write(path,dict(option=BY_ID[selected['final']],external_options=list(dict.fromkeys(['hard170',selected['final'],'cep_a050_t015'])),
            actual_fit_files=[],seed=None,no_test_selection=True));outputs.append(path)
        print(json.dumps(dict(selections=selections,decision=gates),indent=2))
    else:result['freeze_sha256']=audit.digest(OUT/'H53_FROZEN_SELECTION.json')
    result['artifacts']={str(path.relative_to(REPO)):audit.digest(path) for path in outputs}
    audit.json_write(OUT/f'H53_{stage}_experiment.json',result)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['precheck','register','train','test']);args=parser.parse_args()
    {'precheck':precheck,'register':register,'train':lambda:measure('train'),'test':lambda:measure('test')}[args.action]()
