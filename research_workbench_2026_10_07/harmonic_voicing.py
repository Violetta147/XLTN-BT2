import argparse
import hashlib
import itertools
import json
import time
import platform
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
import recovery_pitch as common
from harmonic_nls import residual
from voicing_recovery import gates

HERE, OUT, REPO, core, audit=common.HERE,common.OUT,common.REPO,common.core,common.audit
OPTIONS=[dict(id='hard170',dimensions=0,reject=0.)]+[
    dict(id=f'logistic_{dimensions}_reject_{int(q*100):02d}',dimensions=dimensions,reject=q)
    for dimensions in (4,6) for q in (0.,.1,.25)]
BY_ID={o['id']:o for o in OPTIONS}


def coherence(segment,fs,pitch):
    if not np.isfinite(pitch):return np.zeros(2)
    weight=np.hanning(len(segment));center=float(np.sum(segment*weight)/np.sum(weight))
    energy=float(np.sum(weight*(segment-center)**2))
    if energy<=1e-20:return np.zeros(2)
    costs=[residual(segment,fs,pitch,order)[0] for order in (3,5)]
    explained=np.clip(1-np.array(costs)/energy,0,1)
    assert explained[1]>=explained[0]-1e-10
    return np.array([explained[0],max(0,explained[1]-explained[0])])


def fit(bank,names,dimensions):
    n=min(len(bank[name]['x']) for name in names)
    ids={name:np.round(np.linspace(0,len(bank[name]['x'])-1,n)).astype(int) for name in sorted(names)}
    x=np.vstack([bank[name]['x'][ids[name],:dimensions] for name in sorted(names)])
    y=np.concatenate([(bank[name]['labels'][ids[name]]=='v').astype(int) for name in sorted(names)])
    scaler=StandardScaler().fit(x);z=scaler.transform(x)
    learner=LogisticRegression(C=1.,solver='lbfgs',max_iter=2000,tol=1e-8,random_state=0).fit(z,y)
    assert learner.n_iter_[0]<2000
    return dict(fit_files=sorted(names),dimensions=dimensions,indices={k:v.tolist() for k,v in ids.items()},
        mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist(),coefficient=learner.coef_[0].tolist(),
        intercept=float(learner.intercept_[0]),n_iter=int(learner.n_iter_[0]),
        design_sha256=hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest(),positive_frames=int(y.sum()))


def response(feature,model):
    z=(feature['x'][:,:model['dimensions']]-np.array(model['mean']))/np.array(model['scale'])
    return expit(z@np.array(model['coefficient'])+model['intercept'])


def infer(feature,probability,option):
    pred=feature['base_pred'].copy();f0=feature['base_f0'].copy()
    if option['dimensions']:
        remove=pred&(probability<option['reject'])
        recover=(~feature['base_pred'])&(probability>=.5)&(feature['x'][:,0]>=.6)&(feature['x'][:,1]>=np.log(.01))&np.isfinite(feature['pitch'])
        pred[remove]=False;f0[remove]=np.nan;pred[recover]=True;f0[recover]=feature['pitch'][recover]
    assert np.array_equal(pred,np.isfinite(f0))
    return pred,f0


def choose(rows):
    base=[r for r in rows if r['option_id']=='hard170'];rank=[]
    for identity in BY_ID:
        group=[r for r in rows if r['option_id']==identity];good=all(np.isfinite(r['average_mape']) for r in group)
        for key in ('macro_f1','recall_v'):
            good &= np.mean([r[key] for r in group])>=np.mean([r[key] for r in base])-.01
        good &= sum(r['false_voiced_sil'] for r in group)<=sum(r['false_voiced_sil'] for r in base)+1
        rank.append((not good,max(r['average_mape'] for r in group) if good else np.inf,
            np.mean([r['average_mape'] for r in group]) if good else np.inf,identity))
    return sorted(rank)[0][-1]


def check_registry():
    r=json.loads((HERE/'H62_REGISTRY.json').read_text());assert r['options']==OPTIONS
    for p,d in r['source_hashes'].items():assert audit.digest(REPO/p)==d,p
    return r


def precheck():
    from verify_harmonic_voicing import independent_coherence
    rows=[]
    with threadpool_limits(limits=1):
        for fs in (16000,44100):
            t=np.arange(round(.025*fs))/fs
            for seed in (11,29,47):
                for pitch in (90,200,320):
                    clean=sum(np.sin(2*np.pi*pitch*h*t)/h for h in range(1,6))
                    audio=clean+np.random.default_rng(seed).normal(0,.1,len(t))
                    feature=coherence(audio,fs,pitch)
                    assert np.allclose(feature,independent_coherence(audio,fs,pitch),atol=1e-10)
                    assert np.allclose(feature,coherence(audio*3+1,fs,pitch),atol=1e-10)
                    assert np.isfinite(coherence(np.zeros(len(t)),fs,pitch)).all()
                    rows.append(dict(fs=fs,seed=seed,pitch=pitch,features=feature.tolist()))
    fixture={'a':dict(x=np.arange(120).reshape(20,6)/120,labels=np.array(['v','uv']*10)),
             'b':dict(x=np.arange(180).reshape(30,6)/180,labels=np.array(['uv','v']*15))}
    first=fit(fixture,['a'],6);fixture['b']['labels'][:]='sil';second=fit(fixture,['a'],6)
    assert first==second
    audit.json_write(OUT/'H62_precheck.json',dict(status='PASS',synthetic_only=True,BT2_used=False,
        tests=rows,independent_qr_features=True,gain_dc_invariance=True,held_label_poisoning=True,
        seeds_are_fixture_noise_not_training=True))
    paths=[HERE/'harmonic_voicing.py',HERE/'verify_harmonic_voicing.py',HERE/'H62_REGISTRATION.md',
        HERE/'harmonic_nls.py',HERE/'verify_nls.py',HERE/'NLS_SOURCE_REVIEW.md',OUT/'H62_precheck.json',
        HERE/'recovery_pitch.py',HERE/'voicing_matrix.py',HERE/'voicing_recovery.py',
        HERE/'verify_srh.py',HERE/'verify_yaapt_extension_v2.py',HERE/'yaapt_extension.py',HERE/'verify_recovery_pitch.py',
        REPO/'research_3gt_2026_10_05/core.py',REPO/'research_workbench_2026_10_06/audit.py',core.RESULTS/'frozen_config.json']
    paths+=list(OUT.glob('H50_design_*.npz'))+list(core.TRAIN.glob('*.wav'))+list(core.TRAIN.glob('*.lab'))+list(core.TRAIN_GT.glob('*.lab'))
    audit.json_write(HERE/'H62_REGISTRY.json',dict(family='H62',rollback=common.matrix.commit_id(),options=OPTIONS,
        source_hashes={str(p.relative_to(REPO)):audit.digest(p) for p in paths},
        expected_unique_train_groups=140,expected_logistic_fits=22,test_enabled_only_if_eligible=True))
    print('PASS H62 precheck; registry written; no BT2 measurement')


def train():
    check_registry();assert not (OUT/'H62_train_experiment.json').exists();started=time.perf_counter()
    bank=common.matrix.load_bank();artifacts=[];items={}
    with threadpool_limits(limits=1):
        for name,feature in bank.items():
            path=core.TRAIN/name;fs,audio=core.load_audio(path);length,hop=round(fs*.025),round(fs*.01)
            bounded,_,_=common.pitches(feature,fs,200);anchor=np.where(feature['base_pred'],feature['base_f0'],bounded)
            extra=np.array([coherence(audio[i*hop:i*hop+length],fs,pitch) for i,pitch in enumerate(anchor)])
            feature['x']=np.column_stack((feature['x'][:,:4],extra));feature['pitch']=bounded;feature['anchor']=anchor
            item=dict(file=name,labels=feature['labels'],stats=core.read_stats(core.TRAIN_GT/path.with_suffix('.lab').name))
            items[name]=item
            p=OUT/f'H62_design_{path.stem}.npz';np.savez_compressed(p,**feature);artifacts.append(p)
            print('H62 features',name,flush=True)
        names=sorted(bank);pools=[pool for size in (2,3,4) for pool in itertools.combinations(names,size)]
        models={};records=[];proofs=[]
        for pool in pools:
            for dimensions in (4,6):models[(pool,dimensions)]=fit(bank,pool,dimensions)
            targets=names if len(pool)==4 else [n for n in names if n not in pool]
            for held in targets:
                feature=bank[held];predictions=[];pitches=[];probabilities=[]
                for option in OPTIONS:
                    p=response(feature,models[(pool,option['dimensions'])]) if option['dimensions'] else np.zeros(len(feature['x']))
                    pred,f0=infer(feature,p,option)
                    records.append(dict(fit_files='|'.join(pool),option_id=option['id'],**core.score_file(items[held],pred,f0)))
                    predictions.append(pred);pitches.append(f0);probabilities.append(p)
                stem=held.removesuffix('.wav');pool_id='_'.join(n.removesuffix('.wav') for n in pool)
                p=OUT/f'H62_predictions_{pool_id}__{stem}.npz'
                np.savez_compressed(p,pred=predictions,f0=pitches,probability=probabilities);artifacts.append(p)
                proofs.append(dict(fit_files=list(pool),held_file=held,path=str(p.relative_to(REPO))))
            print('H62 fitted pool','|'.join(pool),flush=True)
    selections=[];inner=[]
    for outer in ['final']+names:
        available=[n for n in names if n!=outer];trace=[]
        for held in available:
            fit_files='|'.join(n for n in available if n!=held)
            for r in records:
                if r['file']==held and r['fit_files']==fit_files:
                    trace.append(r);inner.append(dict(outer_held=outer,inner_held=held,**r))
        selections.append(dict(outer_held=outer,selection_files=available,option_id=choose(trace)))
    chosen={r['outer_held']:r['option_id'] for r in selections};summary=[];fixed=[]
    for split in ('train','lofo','nested'):
        for held in names:
            pool='|'.join(names if split=='train' else [n for n in names if n!=held])
            for model,identity in [('accepted','hard170'),('candidate',chosen[held] if split=='nested' else chosen['final'])]:
                row=next(r for r in records if r['file']==held and r['fit_files']==pool and r['option_id']==identity)
                summary.append(dict(split=split,model=model,**row))
    for held in names:
        pool='|'.join(n for n in names if n!=held);fixed.extend(r for r in records if r['file']==held and r['fit_files']==pool)
    summaries,decision=gates(pd.DataFrame(summary))
    for filename,rows in [('H62_groups.csv',records),('H62_fixed_lofo.csv',fixed),('H62_inner_traces.csv',inner),('H62_metrics.csv',summary)]:
        p=OUT/filename;pd.DataFrame(rows).to_csv(p,index=False);artifacts.append(p)
    p=OUT/'H62_models.json';audit.json_write(p,dict(models=list(models.values())));artifacts.append(p)
    audit.json_write(OUT/'H62_train_experiment.json',dict(family='H62',prereg_commit=common.matrix.commit_id(),
        registry_sha256=audit.digest(HERE/'H62_REGISTRY.json'),selections=selections,summaries=summaries,decision=decision,
        actual_fits=len(models),unique_measured_groups=len(records),test_used=False,proofs=proofs,
        runtime=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__),
        wall_time_s=time.perf_counter()-started,artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in artifacts}))
    print(json.dumps(dict(selections=selections,decision=decision),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['precheck','train']);args=parser.parse_args()
    precheck() if args.action=='precheck' else train()
