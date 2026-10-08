import argparse
import itertools
import json
import platform
import time
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.special import logsumexp
from threadpoolctl import threadpool_limits
import voicing_matrix as matrix

HERE,OUT,REPO,core,audit=matrix.HERE,matrix.OUT,matrix.REPO,matrix.core,matrix.audit
SEEDS=[11,29,47]
OPTIONS=[dict(id='hard170',width=0),dict(id='recovery_acf',width=0)]+[dict(id=f'recovery_bound_{w}',width=w) for w in (100,200,400)]
BY_ID={o['id']:o for o in OPTIONS}
RECIPE=matrix.BY_ID['gmm_PEZS']


def response(x,model):
    z=(x[:,RECIPE['columns']]-np.array(model['mean']))/np.array(model['scale'])
    centers=np.array(model['centers']);variance=np.array(model['variance'])
    logp=np.log(model['weights'])-.5*(np.sum(np.log(2*np.pi*variance),axis=1)[None,:]+np.sum((z[:,None,:]-centers[None,:,:])**2/variance[None,:,:],axis=2))
    return np.exp(logp-logsumexp(logp,axis=1,keepdims=True))[:,model['component']]


def serialize(model,names,seed):
    g=model['estimator'];scaler=model['scaler']
    return dict(fit_files=sorted(names),seed=seed,mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist(),
        weights=g.weights_.tolist(),centers=g.means_.tolist(),variance=g.covariances_.tolist(),component=model['component'])


def pitches(feature,fs,width):
    output=feature['pitch'].copy();anchor=np.full(len(output),np.nan);changed=np.zeros(len(output),bool)
    if not width:return output,anchor,changed
    voiced=np.flatnonzero(feature['base_pred']);curves=feature['curves'];lags=feature['lags']
    for i in range(len(output)):
        if not len(voiced):break
        k=voiced[np.argmin(abs(feature['times'][voiced]-feature['times'][i]))]
        if abs(feature['times'][k]-feature['times'][i])>.05+1/fs:continue
        anchor[i]=feature['base_f0'][k]
        row=curves[i];peaks=np.flatnonzero((row[1:-1]>=row[:-2])&(row[1:-1]>=row[2:])&(row[1:-1]>=.6))+1
        candidates=[]
        for j in peaks:
            denominator=row[j-1]-2*row[j]+row[j+1]
            delta=.5*(row[j-1]-row[j+1])/denominator if abs(denominator)>1e-12 else 0.
            f=float(np.clip(fs/(lags[j]+np.clip(delta,-.5,.5)),70,400))
            if abs(1200*np.log2(f/anchor[i]))<=width:candidates.append((float(row[j]),int(j),f))
        if candidates:
            best=min(candidates,key=lambda r:(-r[0],r[1]));output[i]=best[2];changed[i]=output[i]!=feature['pitch'][i]
    return output,anchor,changed


def infer(feature,prob,pitch,identity):
    pred=feature['base_pred'].copy();f0=feature['base_f0'].copy()
    recover=(~pred)&(prob>=.5)&(feature['x'][:,0]>=.6)&(feature['x'][:,1]>=np.log(.01))&np.isfinite(feature['pitch'])
    if identity=='hard170':recover[:]=False
    pred[recover]=True;f0[recover]=pitch[recover]
    assert np.array_equal(f0[feature['base_pred']],feature['base_f0'][feature['base_pred']])
    assert np.array_equal(pred,np.isfinite(f0))
    return pred,f0,recover


def choose(rows):
    control=[r for r in rows if r['option_id']=='hard170'];rank=[]
    for identity in BY_ID:
        group=[r for r in rows if r['option_id']==identity];valid=True
        for seed in SEEDS:
            g=[r for r in group if r['seed']==seed];b=[r for r in control if r['seed']==seed]
            valid &= all(np.isfinite(r['average_mape']) for r in g)
            for key in ('macro_f1','recall_v'):valid &= np.mean([r[key] for r in g])>=np.mean([r[key] for r in b])-.01
            valid &= sum(r['false_voiced_sil'] for r in g)<=sum(r['false_voiced_sil'] for r in b)+1
        rank.append((not valid,max(r['average_mape'] for r in group) if valid else np.inf,np.mean([r['average_mape'] for r in group]) if valid else np.inf,identity))
    return min(rank)[-1]


def precheck():
    assert not (OUT/'H56_precheck.json').exists()
    from verify_recovery_pitch import scalar_pitches
    checks=[]
    for fs in (16000,44100):
        for frequency in (100.,173.,300.):
            t=np.arange(round(.3*fs))/fs;x=np.sin(2*np.pi*frequency*t)
            feature=matrix.base.design(x,fs);n=len(feature['pitch'])
            feature.update(base_pred=np.arange(n)%3==0,base_f0=np.where(np.arange(n)%3==0,frequency*1.015,np.nan))
            for width in (100,200,400):
                pitch,anchor,changed=pitches(feature,fs,width);p,a,c=scalar_pitches(feature,fs,width)
                assert np.allclose(p,pitch,equal_nan=True,atol=1e-10) and np.allclose(a,anchor,equal_nan=True) and np.array_equal(c,changed)
                pred,f0,recover=infer(feature,np.ones(n),pitch,'recovery_bound_'+str(width))
                reference,_,_=infer(feature,np.ones(n),feature['pitch'],'recovery_acf')
                assert np.array_equal(pred,reference) and np.max(abs(pitch-frequency))<1
                assert np.array_equal(f0[feature['base_pred']],feature['base_f0'][feature['base_pred']])
                checks.append(dict(fs=fs,frequency=frequency,width=width,passed=True))
    feature['base_pred'][:]=False;feature['base_f0'][:]=np.nan
    pitch,anchor,_=pitches(feature,fs,200);assert np.array_equal(pitch,feature['pitch']) and np.isnan(anchor).all()
    audit.json_write(OUT/'H56_precheck.json',dict(passed=True,cases=checks,same_mask_across_pitch_ablations=True,unsupported_anchor_fallback=True,scope='Periodic synthetic with near-truth anchors, not BT2 frame F0 truth'))
    print('PASS H56: 18 synthetic scalar selectors, same masks, old pitch preservation, no-anchor fallback')


def register():
    assert not (HERE/'H56_REGISTRY.json').exists()
    paths=[Path(__file__),HERE/'verify_recovery_pitch.py',HERE/'H56_REGISTRATION.md',OUT/'H56_precheck.json',Path(matrix.__file__),Path(matrix.base.__file__),Path(core.__file__),HERE/'verify_srh.py',HERE/'verify_yaapt_extension_v2.py',HERE/'yaapt_extension.py',OUT/'H50_verification.json',OUT/'H51_train_verification.json',OUT/'H51_external_verification.json',core.RESULTS/'frozen_config.json']
    paths+=list(OUT.glob('H50_design_*.npz'))+list(OUT.glob('H51_predictions_*.npz'))+list(OUT.glob('H51_test_*.npz'))
    for folder in (core.TRAIN,REPO/'TinHieuKiemThu',core.TRAIN_GT,core.HERE/'test_3gt'):paths+=list(folder.glob('*.wav'))+list(folder.glob('*.lab'))
    audit.json_write(HERE/'H56_REGISTRY.json',dict(rollback_commit=matrix.commit_id(),recipe=RECIPE,seeds=SEEDS,options=OPTIONS,
        hashes={str(p.relative_to(REPO)):audit.digest(p) for p in paths}))


def check_registry():
    registry=json.loads((HERE/'H56_REGISTRY.json').read_text());assert registry['options']==OPTIONS and registry['seeds']==SEEDS and registry['recipe']==RECIPE
    for path,digest in registry['hashes'].items():assert audit.digest(REPO/path)==digest,path


def bank_train():
    bank=matrix.load_bank()
    for name in bank:bank[name]['fs']=core.load_audio(core.TRAIN/name)[0]
    return bank


def run(stage):
    check_registry();assert not (OUT/f'H56_{stage}_experiment.json').exists()
    assert json.loads((OUT/'H56_precheck.json').read_text())['passed']
    bank=bank_train();names=sorted(bank);models=[];proofs=[];rows=[];outputs=[];started=time.perf_counter()
    if stage=='train':
        pools=[pool for size in (2,3,4) for pool in itertools.combinations(names,size)]
        target=bank;options=OPTIONS
    else:
        assert json.loads((OUT/'H56_train_verification.json').read_text())['passed']
        freeze=json.loads((OUT/'H56_FROZEN_SELECTION.json').read_text());options=[BY_ID[k] for k in freeze['external_options']]
        target={}
        for path in sorted((REPO/'TinHieuKiemThu').glob('*.wav')):
            fs,audio=core.load_audio(path);f=matrix.base.design(audio,fs)
            saved=dict(np.load(OUT/f'H51_test_{path.stem}.npz',allow_pickle=False))
            for key in ('x','pitch','times'):assert np.allclose(f[key],saved[key],atol=1e-12,equal_nan=True)
            f.update(base_pred=saved['base_pred'],base_f0=saved['base_f0'],fs=fs)
            target[path.name]=f;output=OUT/f'H56_test_design_{path.stem}.npz';assert not output.exists()
            np.savez_compressed(output,**f);outputs.append(output)
        pools=[tuple(names)];models=json.loads((OUT/'H56_models.json').read_text())
    designs={name:{o['id']:pitches(f,f['fs'],o['width'])[0] for o in options} for name,f in target.items()}
    for pool in pools:
        held=list(target) if len(pool)==4 else [name for name in names if name not in pool]
        for seed in SEEDS:
            if stage=='train':
                native=matrix.fit(bank,list(pool),RECIPE,seed);model=serialize(native,pool,seed);model_id=len(models);models.append(model)
            else:
                model_id=next(i for i,m in enumerate(models) if m['fit_files']==list(pool) and m['seed']==seed);model=models[model_id]
            for name in held:
                f=target[name];prob=response(f['x'],model)
                if stage=='train':assert np.allclose(prob,matrix.response(f['x'],native),atol=1e-12)
                item=core.frame_features((core.TRAIN if stage=='train' else REPO/'TinHieuKiemThu')/name,split=stage)
                for option in options:
                    pred,f0,recover=infer(f,prob,designs[name][option['id']],option['id'])
                    row=dict(model_id=model_id,fit_pool='|'.join(pool),seed=seed,option_id=option['id'],recovered=int(sum(recover)),**core.score_file(item,pred,f0));rows.append(row)
                    proofs.append(dict(file=name,model_id=model_id,option_id=option['id'],pred=pred.tolist(),f0=[float(v) if np.isfinite(v) else None for v in f0],prob=prob.tolist()))
        print('H56',stage,'fit pool',','.join(pool),flush=True)
    for filename,value in [(f'H56_{stage}_fixed.csv',rows)]:
        output=OUT/filename;pd.DataFrame(value).to_csv(output,index=False);outputs.append(output)
    output=OUT/f'H56_{stage}_proofs.json';audit.json_write(output,proofs);outputs.append(output)
    receipt=dict(measured_commit=matrix.commit_id(),seeds=SEEDS,test_tuning=False,historical_test_exposure=True,
        runtime=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__),
        actual_model_fits=len(matrix.FIT_LOG) if stage=='train' else 0,wall_time_s=time.perf_counter()-started)
    if stage=='train':
        assert len(models)==33 and len(rows)==300
        selections=[];traces=[]
        for outer in ['final']+names:
            pool=[n for n in names if n!=outer];selection=[]
            for inner in pool:
                fit='|'.join(n for n in pool if n!=inner)
                selected=[r for r in rows if r['file']==inner and r['fit_pool']==fit];selection+=selected
                traces += [dict(outer_held=outer,inner_held=inner,**r) for r in selected]
            selections.append(dict(outer_held=outer,selection_files=pool,option_id=choose(selection)))
        chosen={r['outer_held']:r['option_id'] for r in selections};metrics=[]
        for split in ('train','lofo','nested'):
            for name in names:
                fit='|'.join(names if split=='train' else [n for n in names if n!=name])
                for model,identity in [('accepted','hard170'),('candidate',chosen[name] if split=='nested' else chosen['final'])]:
                    metrics += [dict(split=split,model=model,**r) for r in rows if r['file']==name and r['fit_pool']==fit and r['option_id']==identity]
        decisions={seed:matrix.base.gates(pd.DataFrame([r for r in metrics if r['seed']==seed]))[1] for seed in SEEDS}
        receipt.update(selections=selections,decisions=decisions)
        for filename,value in [('H56_models.json',models),('H56_FROZEN_SELECTION.json',dict(option=BY_ID[chosen['final']],external_options=list(dict.fromkeys(['hard170',chosen['final'],'recovery_acf','recovery_bound_200'])),seeds=SEEDS,no_test_selection=True)),('H56_inner_traces.json',traces)]:
            output=OUT/filename;audit.json_write(output,value);outputs.append(output)
        output=OUT/'H56_metrics.csv';pd.DataFrame(metrics).to_csv(output,index=False);outputs.append(output)
        print(json.dumps(dict(selections=selections,decisions=decisions),indent=2))
    else:receipt['freeze_sha256']=audit.digest(OUT/'H56_FROZEN_SELECTION.json')
    receipt['artifacts']={str(p.relative_to(REPO)):audit.digest(p) for p in outputs};audit.json_write(OUT/f'H56_{stage}_experiment.json',receipt)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['precheck','register','train','test']);arg=parser.parse_args().action
    with threadpool_limits(limits=1):{'precheck':precheck,'register':register,'train':lambda:run('train'),'test':lambda:run('test')}[arg]()
