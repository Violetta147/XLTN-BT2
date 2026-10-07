import argparse
import hashlib
import itertools
import json
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from threadpoolctl import threadpool_limits

import voicing_recovery as base

HERE, OUT, REPO, core, audit = base.HERE, base.OUT, base.REPO, base.core, base.audit
SEEDS = [11, 29, 47]
BLOCKS = dict(P=[0], E=[1], Z=[2], S=[3], M=list(range(4,17)))
METHODS = ['logistic', 'svm', 'knn', 'rf', 'gmm']
RECIPES = [dict(id='hard170', method='control', blocks='', columns=[])] + [
    dict(id=method+'_'+''.join(name for i,name in enumerate(BLOCKS) if mask & (1<<i)), method=method,
         blocks=''.join(name for i,name in enumerate(BLOCKS) if mask & (1<<i)),
         columns=[col for i,cols in enumerate(BLOCKS.values()) if mask & (1<<i) for col in cols])
    for mask in range(1,32) for method in METHODS]
BY_ID = {r['id']:r for r in RECIPES}
FULL = [method+'_PEZSM' for method in METHODS]
MODEL_CACHE = {}
FIT_LOG = []


def load_bank():
    return {name: dict(np.load(OUT/f'H50_design_{Path(name).stem}.npz',allow_pickle=False)) for name in sorted(p.name for p in core.TRAIN.glob('*.wav'))}


def fit(bank,names,recipe,seed):
    if recipe['method']=='control':
        return None
    actual_seed = seed if recipe['method'] in ('rf','gmm') else 0
    key=(recipe['id'],tuple(sorted(names)),actual_seed)
    if key in MODEL_CACHE:
        return MODEL_CACHE[key]
    n=min(len(bank[name]['x']) for name in names)
    indices={name: np.round(np.linspace(0,len(bank[name]['x'])-1,n)).astype(int) for name in sorted(names)}
    raw=np.vstack([bank[name]['x'][indices[name]] for name in sorted(names)])
    x=raw[:,recipe['columns']]
    scaler=StandardScaler().fit(x)
    z=scaler.transform(x)
    method=recipe['method']
    if method=='gmm':
        model=GaussianMixture(n_components=3,covariance_type='diag',reg_covar=1e-3,n_init=3,max_iter=500,tol=1e-4,random_state=actual_seed).fit(z)
        assert model.converged_,key
        responsibility=model.predict_proba(z)
        periodicity=responsibility.T @ raw[:,0] / responsibility.sum(axis=0)
        component=int(np.argmax(periodicity))
    else:
        y=np.concatenate([(bank[name]['labels'][indices[name]]=='v').astype(int) for name in sorted(names)])
        if method=='logistic':
            model=LogisticRegression(C=1,max_iter=1000).fit(z,y)
            assert model.n_iter_[0]<1000,key
        elif method=='svm':
            model=SVC(C=1,kernel='rbf',gamma='scale',probability=False).fit(z,y)
        elif method=='knn':
            model=KNeighborsClassifier(n_neighbors=5,weights='uniform',algorithm='brute').fit(z,y)
        else:
            model=RandomForestClassifier(n_estimators=64,max_depth=6,min_samples_leaf=4,random_state=actual_seed,n_jobs=1).fit(z,y)
        component=None
    result=dict(scaler=scaler,estimator=model,component=component,recipe=recipe)
    MODEL_CACHE[key]=result
    train_response=response(raw,result)
    FIT_LOG.append(dict(recipe_id=recipe['id'],fit_files=sorted(names),actual_seed=actual_seed,
                        per_file_rows=n,indices={name:value.tolist() for name,value in indices.items()},
                        scaler_mean=scaler.mean_.tolist(),scaler_scale=scaler.scale_.tolist(),
                        training_design_sha256=hashlib.sha256(np.ascontiguousarray(raw).tobytes()).hexdigest(),
                        training_response_sha256=hashlib.sha256(train_response.tobytes()).hexdigest(),
                        component_periodicity=periodicity.tolist() if method=='gmm' else None,voiced_component=component))
    return result


def response(x,model):
    z=model['scaler'].transform(x[:,model['recipe']['columns']])
    estimator=model['estimator']
    if model['recipe']['method']=='gmm':
        return estimator.predict_proba(z)[:,model['component']]
    if model['recipe']['method']=='svm':
        return expit(estimator.decision_function(z))
    return estimator.predict_proba(z)[:,int(np.flatnonzero(estimator.classes_==1)[0])]


def infer(features,model,override=None):
    pred,f0=features['base_pred'].copy(),features['base_f0'].copy()
    prob=np.full(len(pred),np.nan)
    recover=np.zeros(len(pred),dtype=bool)
    if model:
        prob=response(features['x'] if override is None else override,model)
        recover=(~pred)&(prob>=.5)&(features['x'][:,0]>=.6)&(features['x'][:,1]>=np.log(.01))&np.isfinite(features['pitch'])
        pred[recover]=True
        f0[recover]=features['pitch'][recover]
    assert np.array_equal(f0[features['base_pred']],features['base_f0'][features['base_pred']])
    return pred,f0,prob,recover


def measured(item,features,model,override=None):
    pred,f0,prob,recover=infer(features,model,override)
    row=core.score_file(item,pred,f0)
    row.update(recovered=int(recover.sum()),**{'recovered_'+lab:int((recover&(item['labels']==lab)).sum()) for lab in ('v','uv','sil')})
    return row,pred,f0,prob,recover


def choose(records):
    table=pd.DataFrame(records)
    control=table[table.recipe_id=='hard170']
    ranks=[]
    for identity,group in table.groupby('recipe_id'):
        valid=True
        for seed in SEEDS:
            part,ref=group[group.seed==seed],control[control.seed==seed]
            valid &= np.isfinite(part.average_mape).all() and part.macro_f1.mean()>=ref.macro_f1.mean()-.01 and part.recall_v.mean()>=ref.recall_v.mean()-.01 and part.false_voiced_sil.sum()<=ref.false_voiced_sil.sum()+1
        ranks.append((not valid,float(group.average_mape.max()) if valid else np.inf,float(group.average_mape.mean()) if valid else np.inf,identity))
    return min(ranks)[3]


def write_csv(name,rows):
    pd.DataFrame(rows).to_csv(OUT/name,index=False)


def verify_registry():
    registry=json.loads((HERE/'H51_REGISTRY.json').read_text())
    assert registry['recipes']==RECIPES and registry['seeds']==SEEDS
    for path,digest in registry['hashes'].items():
        assert audit.digest(REPO/path)==digest,path
    return registry


def commit_id():
    return subprocess.check_output(['git','-c','safe.directory='+str(REPO).replace('\\','/'),'-C',str(REPO),'rev-parse','HEAD'],text=True).strip()


def register():
    assert not (HERE/'H51_REGISTRY.json').exists()
    assert json.loads((OUT/'H50_verification.json').read_text())['passed']
    sources=[Path(__file__),HERE/'verify_voicing_matrix.py',HERE/'report_voicing_matrix.py',HERE/'check_voicing_matrix.py',OUT/'H51_precheck.json',HERE/'H51_REGISTRATION.md',
             HERE/'voicing_recovery.py',HERE/'verify_voicing_recovery.py',HERE/'benchmark_keele.py',core.RESULTS/'frozen_config.json',
             OUT/'H50_verification.json',OUT/'H50_experiment.json',OUT/'H46_augmentation_manifest.json',OUT/'H48_test_contours.csv',
             OUT/'H48_test_verification.json',OUT/'H49_dataset_manifest.json',OUT/'H49_verification.json',Path(core.__file__)]
    sources+=list(OUT.glob('H50_design_*.npz'))+list(OUT.glob('H49_native_*.npz'))
    for directory in (core.TRAIN,REPO/'TinHieuKiemThu',core.TRAIN_GT,core.HERE/'test_3gt'):
        sources+=list(directory.glob('*.wav'))+list(directory.glob('*.lab'))
    manifest=json.loads((OUT/'H46_augmentation_manifest.json').read_text())
    for case in manifest['cases']:
        sources += [HERE/case['path'],HERE/case['features']['path']]
    cases=json.loads((OUT/'H49_dataset_manifest.json').read_text())['cases']
    for case in cases:
        sources += [HERE/case['relative_dir']/filename for filename in case['hashes']]
    audit.json_write(HERE/'H51_REGISTRY.json',dict(recipes=RECIPES,seeds=SEEDS,rollback=commit_id(),
        hashes={str(p.relative_to(REPO)):audit.digest(p) for p in sources},full_reference_recipes=FULL,
        selection='worst file across all seeds, mean, ID; validation guards pass each seed; never choose a seed'))
    print('Registered',len(RECIPES)-1,'factorial recipes x3 seeds + control; no new measurement')


def train():
    assert not (OUT/'H51_train_experiment.json').exists()
    verify_registry()
    started=time.perf_counter()
    items={item['file']:item for item in core.load_training()}
    bank=load_bank();names=sorted(bank); cache={}
    def score(recipe,seed,fits,held):
        key=(recipe['id'],seed,tuple(sorted(fits)),held)
        if key not in cache:
            model=fit(bank,sorted(fits),recipe,seed)
            cache[key]=measured(items[held],bank[held],model)
        return cache[key]
    traces,selections=[],[]
    for outer in ['final']+names:
        pool=[name for name in names if name!=outer];records=[]
        for number,recipe in enumerate(RECIPES):
            for seed in SEEDS:
                for held in pool:
                    fits=[name for name in pool if name!=held]
                    row=dict(outer_held=outer,recipe_id=recipe['id'],seed=seed,inner_held=held,fit_files='|'.join(fits),**score(recipe,seed,fits,held)[0])
                    traces.append(row);records.append(row)
            if number%25==0:
                print('H51 inner',outer,number,'/',len(RECIPES),flush=True)
        selected=choose(records)
        selections.append(dict(outer_held=outer,selection_files=pool,recipe_id=selected))
        print('H51 selected',outer,selected,flush=True)
    selected={row['outer_held']:row['recipe_id'] for row in selections}
    fixed=[]
    for held in names:
        arrays={key:[] for key in ('pred','f0','prob','recover')};ids=[];seeds=[]
        for recipe in RECIPES:
            for seed in SEEDS:
                row,pred,f0,prob,recover=score(recipe,seed,[name for name in names if name!=held],held)
                fixed.append(dict(recipe_id=recipe['id'],method=recipe['method'],blocks=recipe['blocks'],seed=seed,**row))
                ids.append(recipe['id']);seeds.append(seed)
                for key,value in zip(arrays,(pred,f0,prob,recover)):
                    arrays[key].append(value)
        np.savez_compressed(OUT/f'H51_predictions_{Path(held).stem}.npz',recipe_id=np.array(ids),seed=np.array(seeds),times=bank[held]['times'],**{key:np.array(value) for key,value in arrays.items()})
    rows=[]
    for split in ('train','lofo','nested'):
        for held in names:
            fits=names if split=='train' else [name for name in names if name!=held]
            for model,identity in [('accepted','hard170'),('candidate',selected[held] if split=='nested' else selected['final'])]:
                for seed in SEEDS:
                    rows.append(dict(split=split,model=model,option_id=identity,seed=seed,**score(BY_ID[identity],seed,fits,held)[0]))
    summaries,decisions={},{}
    table=pd.DataFrame(rows)
    for seed in SEEDS:
        summaries[str(seed)],decisions[str(seed)]=base.gates(table[table.seed==seed])
    freeze=dict(recipe=BY_ID[selected['final']],seeds=SEEDS,reference_recipes=FULL,
                test_used_for_selection=False,KEELE_used_for_selection=False,clean_train_only_selection=True)
    audit.json_write(OUT/'H51_FROZEN_SELECTION.json',freeze)
    write_csv('H51_fixed_lofo.csv',fixed);write_csv('H51_inner_traces.csv',traces);write_csv('H51_metrics.csv',rows)
    robustness=[]
    chosen=list(dict.fromkeys(['hard170',selected['final']]+FULL))
    manifest=json.loads((OUT/'H46_augmentation_manifest.json').read_text())
    for case in manifest['cases']:
        held=case['origin_file'];fs,audio=core.load_audio(HERE/case['path']);features=base.design(audio,fs)
        data=dict(np.load(HERE/case['features']['path'],allow_pickle=False))
        index=int(np.flatnonzero(data['members']=='amdf_pitch_spectral_p170')[0])
        pitch,support=nearest(data['times'],data['member_frequencies'][index],features['times'],fs)
        features.update(base_pred=(pitch>=70)&(pitch<=400)&support,base_f0=np.where((pitch>=70)&(pitch<=400)&support,pitch,np.nan),labels=items[held]['labels'])
        np.savez_compressed(OUT/f'H51_robust_design_{case["case_id"]}.npz',**features)
        for identity in chosen:
            for seed in SEEDS:
                row,*_=measured(items[held],features,fit(bank,[name for name in names if name!=held],BY_ID[identity],seed))
                robustness.append(dict(recipe_id=identity,seed=seed,condition=f'{case["kind"]}_{case["transformation"]["snr_db"]}dB',case_id=case['case_id'],inherited_latent_reference=True,**row))
    permutation=[]
    for identity in FULL:
        for held in names:
            fits=[name for name in names if name!=held]
            for seed in SEEDS:
                model=fit(bank,fits,BY_ID[identity],seed)
                clean=measured(items[held],bank[held],model)[0]
                for block,columns in BLOCKS.items():
                    for repeat in range(3):
                        digest=hashlib.sha256(f'{held}|{seed}|{block}|{repeat}'.encode()).digest()
                        rng=np.random.default_rng(int.from_bytes(digest[:8],'little'))
                        x=bank[held]['x'].copy();order=rng.permutation(len(x));x[:,columns]=x[order][:,columns]
                        row,*_=measured(items[held],bank[held],model,x)
                        permutation.append(dict(recipe_id=identity,seed=seed,block=block,repeat=repeat,clean_average_mape=clean['average_mape'],clean_macro_f1=clean['macro_f1'],
                                                delta_average_mape=row['average_mape']-clean['average_mape'],delta_macro_f1=row['macro_f1']-clean['macro_f1'],**row))
    cross=[]
    for direction in ('phone_to_studio','studio_to_phone'):
        source,target=direction.split('_to_');fits=[name for name in names if name.startswith(source)]
        for identity in chosen:
            for seed in SEEDS:
                model=fit(bank,fits,BY_ID[identity],seed)
                for held in (name for name in names if name.startswith(target)):
                    row,*_=measured(items[held],bank[held],model)
                    cross.append(dict(direction=direction,fit_files='|'.join(fits),recipe_id=identity,seed=seed,**row))
    write_csv('H51_robustness.csv',robustness);write_csv('H51_permutation.csv',permutation);write_csv('H51_cross_condition.csv',cross)
    audit.json_write(OUT/'H51_train_fits.json',dict(fits=FIT_LOG))
    paths=list(OUT.glob('H51_*.csv'))+list(OUT.glob('H51_predictions_*.npz'))+list(OUT.glob('H51_robust_design_*.npz'))+[OUT/'H51_train_fits.json',OUT/'H51_FROZEN_SELECTION.json']
    audit.json_write(OUT/'H51_train_experiment.json',dict(prereg_commit=commit_id(),registry_sha256=audit.digest(HERE/'H51_REGISTRY.json'),
        selections=selections,summaries=summaries,decisions=decisions,all_seed_gates_pass=all(d['eligible'] for d in decisions.values()),
        each_nested_file_all_seeds_below2=all(d['each_nested_file_below_2'] for d in decisions.values()),actual_model_fits=len(FIT_LOG),
        artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in paths},native_calls=0,wall_time_s=time.perf_counter()-started,
        runtime=json.loads((OUT/'H50_experiment.json').read_text())['runtime'],blas_threads=1))
    print('H51 train complete',len(FIT_LOG),'fits',time.perf_counter()-started,flush=True)


def nearest(times,values,target,fs):
    right=np.minimum(np.searchsorted(times,target),len(times)-1);left=np.maximum(right-1,0)
    index=np.where(abs(times[left]-target)<=abs(times[right]-target),left,right)
    support=abs(times[index]-target)<=.005+1/fs
    return values[index],support


def external():
    assert not (OUT/'H51_external_experiment.json').exists()
    verify_registry()
    assert json.loads((OUT/'H51_train_verification.json').read_text())['passed']
    freeze=json.loads((OUT/'H51_FROZEN_SELECTION.json').read_text())
    bank=load_bank();names=sorted(bank)
    chosen=list(dict.fromkeys(['hard170',freeze['recipe']['id']]+FULL))
    from benchmark_keele import score as benchmark_score, align
    baseline=pd.read_csv(OUT/'H48_test_contours.csv',float_precision='round_trip')
    rows=[];saved=[]
    for path in sorted((REPO/'TinHieuKiemThu').glob('*.wav')):
        fs,audio=core.load_audio(path);features=base.design(audio,fs)
        old=baseline[(baseline.model=='candidate')&(baseline.file==path.name)]
        assert np.allclose(features['times'],old.time_s,atol=1e-12)
        features.update(base_pred=old.pred_voiced.to_numpy(bool),base_f0=old.f0_hz.to_numpy())
        item=core.frame_features(path,split='test')
        arrays={key:[] for key in ('pred','f0','prob','recover')};ids=[];seeds=[]
        for identity in chosen:
            for seed in SEEDS:
                row,pred,f0,prob,recover=measured(item,features,fit(bank,names,BY_ID[identity],seed))
                rows.append(dict(recipe_id=identity,seed=seed,**row));ids.append(identity);seeds.append(seed)
                for key,value in zip(arrays,(pred,f0,prob,recover)):arrays[key].append(value)
        output=OUT/f'H51_test_{path.stem}.npz'
        np.savez_compressed(output,recipe_id=np.array(ids),seed=np.array(seeds),times=features['times'],x=features['x'],pitch=features['pitch'],base_pred=features['base_pred'],base_f0=features['base_f0'],**{key:np.array(value) for key,value in arrays.items()})
        saved.append(output);print('H51 test',path.name,flush=True)
    write_csv('H51_test_metrics.csv',rows)
    keele=[]
    manifest=json.loads((OUT/'H49_dataset_manifest.json').read_text())
    for case in manifest['cases']:
        directory=HERE/case['relative_dir'];fs,audio=core.load_audio(directory/'signal.wav');canonical=base.design(audio,fs)
        native=dict(np.load(OUT/f'H49_native_{case["id"]}.npz',allow_pickle=False))
        indices,support_features=nearest(canonical['times'],np.arange(len(canonical['times'])),native['times'],fs)
        features=dict(x=canonical['x'][indices],pitch=np.where(support_features,canonical['pitch'][indices],np.nan),
                      base_pred=(native['gate']>=70)&(native['gate']<=400),base_f0=np.where((native['gate']>=70)&(native['gate']<=400),native['f0'],np.nan))
        reference=np.load(directory/'pitch.npy',allow_pickle=False)
        ids=[];seeds=[];estimates=[];supports=[];native_pred=[];native_f0=[];probs=[]
        for identity in chosen:
            for seed in SEEDS:
                pred,f0,prob,recover=infer(features,fit(bank,names,BY_ID[identity],seed))
                estimate,support=align(native['times'],np.where(pred,f0,0.),reference['time'],fs)
                keele.append(dict(recipe_id=identity,seed=seed,file=case['id'],native_recovered=int(recover.sum()),**benchmark_score(reference['pitch'],estimate,support)))
                ids.append(identity);seeds.append(seed);estimates.append(estimate);supports.append(support);native_pred.append(pred);native_f0.append(f0);probs.append(prob)
        output=OUT/f'H51_keele_{case["id"]}.npz'
        np.savez_compressed(output,recipe_id=np.array(ids),seed=np.array(seeds),estimate=np.array(estimates),support=np.array(supports),
                            pred=np.array(native_pred),f0=np.array(native_f0),prob=np.array(probs),x=features['x'],pitch=features['pitch'],
                            base_pred=features['base_pred'],base_f0=features['base_f0'],times=native['times'])
        saved.append(output);print('H51 KEELE',case['id'],flush=True)
    write_csv('H51_keele_metrics.csv',keele)
    audit.json_write(OUT/'H51_external_fits.json',dict(fits=FIT_LOG))
    saved += [OUT/'H51_test_metrics.csv',OUT/'H51_keele_metrics.csv',OUT/'H51_external_fits.json']
    audit.json_write(OUT/'H51_external_experiment.json',dict(frozen_commit=commit_id(),freeze_sha256=audit.digest(OUT/'H51_FROZEN_SELECTION.json'),
        registry_sha256=audit.digest(HERE/'H51_REGISTRY.json'),native_calls=0,test_or_KEELE_tuning=False,historical_exposure=True,
        artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in saved}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['register','train','external']);args=parser.parse_args()
    with threadpool_limits(limits=1):
        {'register':register,'train':train,'external':external}[args.action]()
