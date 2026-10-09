"""Select GMM groups from unlabeled acoustic data; freeze before teacher audit."""
import argparse,importlib.util,inspect,json,subprocess,warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture
import sklearn.mixture._gaussian_mixture
HERE=Path(__file__).resolve().parent;WORK=HERE.parent
spec=importlib.util.spec_from_file_location('h80_previous',WORK/'H80_stream/experiment.py');previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
REPO=previous.REPO;core=previous.core;audit=previous.audit
KS=[2,3,4]
CONFIG=dict(covariance_type='full',reg_covar=1e-4,n_init=3,max_iter=500,tol=1e-5,random_state=81,init_params='kmeans')
FEATURES=['max_normalized_acf','log_relative_rms','zero_crossings_per_second','high_frequency_power_ratio']

def design(bank,names):
    count=min(len(bank[n]) for n in names);indices={n:np.linspace(0,len(bank[n])-1,count,dtype=int) for n in names}
    return np.vstack([bank[n][indices[n]] for n in names]),indices

def fit(x,k,names):
    s=StandardScaler().fit(x);z=s.transform(x)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always');m=GaussianMixture(n_components=k,**CONFIG).fit(z)
    model=dict(k=k,fit_files=names,mean=s.mean_.tolist(),variance=s.var_.tolist(),scale=s.scale_.tolist(),weights=m.weights_.tolist(),centers=m.means_.tolist(),covariances=m.covariances_.tolist(),converged=bool(m.converged_),iterations=int(m.n_iter_),warnings=[str(w.message) for w in caught],training_rows=len(x),bic=float(m.bic(z)),parameter_count=k*(4+4*5//2)+k-1)
    p,logdensity=response(x,model);assert np.allclose(p,m.predict_proba(z),atol=1e-10) and np.allclose(logdensity+np.log(s.scale_).sum(),m.score_samples(z),atol=1e-10)
    return model

def response(x,m):
    z=(x-m['mean'])/m['scale'];logs=[]
    for weight,mean,cov in zip(m['weights'],m['centers'],m['covariances']):
        cov=np.asarray(cov);delta=z-mean;sign,logdet=np.linalg.slogdet(cov);assert sign==1;quadratic=np.einsum('ij,ij->i',delta,np.linalg.solve(cov,delta.T).T);logs.append(np.log(weight)-.5*(4*np.log(2*np.pi)+logdet+quadratic))
    a=np.asarray(logs).T;peak=a.max(axis=1);terms=np.exp(a-peak[:,None]);total=terms.sum(axis=1);return terms/total[:,None],peak+np.log(total)-np.log(m['scale']).sum()

def voiced_components(model):
    physical=np.asarray(model['centers'])*model['scale']+model['mean'];threshold=float(np.median(physical[:,0]));return [j for j,v in enumerate(physical[:,0]) if v>=threshold]

def choose(models,held_rows):
    rank=[]
    for k in KS:
        group=[r for r in held_rows if r['k']==k];full=next(m for m in models if m['k']==k and len(m['fit_files'])==4);valid=all(m['converged'] for m in models if m['k']==k) and all(np.isfinite(r['negative_log_density']) for r in group)
        rank.append((not valid,max(r['negative_log_density'] for r in group) if valid else np.inf,np.mean([r['negative_log_density'] for r in group]) if valid else np.inf,full['bic'],k))
    assert not min(rank)[0],'No converged candidate';return min(rank)[-1],rank

def check_registry():
    r=json.loads((HERE/'REGISTRY.json').read_text());assert r['config']==CONFIG and r['ks']==KS
    for p,d in r['source_hashes'].items():assert audit.digest(REPO/p)==d,p
    for p,d in r['external_protected'].items():assert audit.digest(Path(p))==d,p
    return r

def clean_head():
    git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip();branch=subprocess.check_output(git+['branch','--show-current'],cwd=REPO,text=True).strip()
    assert subprocess.check_output(git+['ls-remote','origin','refs/heads/'+branch],cwd=REPO,text=True).split()[0]==head and not subprocess.check_output(git+['status','--porcelain'],cwd=REPO,text=True).strip();return head

def precheck(out):
    assert not out.exists() and not (HERE/'REGISTRY.json').exists();out.mkdir();from verify import scalar_response,check_scaler
    rng=np.random.default_rng(81);x=np.r_[rng.normal(-2,.6,(60,4)),rng.normal(2,.6,(60,4))];m=fit(x,2,['synthetic']);check_scaler(x,m);p,l=response(x,m);q,v=scalar_response(x,m);assert np.allclose(p,q,atol=1e-10) and np.allclose(l,v,atol=1e-10);assert m['converged'];assert len(voiced_components(m))==1
    bank={'a':x,'b':x[:80]};xx,indices=design(bank,['a','b']);assert len(xx)==160 and len(set(indices['a']))==80 and len(set(indices['b']))==80
    audit.json_write(out/'final_info.json',dict(status='PASS',BT2_used=False,synthetic_gmm_fits=1,balanced_subsample=True,scaler_gaussian_density_posterior=True,voiced_mapping_uses_periodicity_only=True))
    old=previous.check_registry();sources=dict(old['source_hashes']);complete=json.loads((WORK/'H80_stream/run_train/completion.json').read_text());sources.update(complete['artifacts']);paths=[HERE/p for p in ('experiment.py','verify.py','plot.py','notes.txt','REGISTRATION.md')]+[out/'final_info.json',WORK/'H80_stream/REGISTRY.json',WORK/'H80_stream/run_train/completion.json']
    for p in paths:sources[str(p.relative_to(REPO))]=audit.digest(p)
    external=dict(old['external_protected']);p=Path(inspect.getfile(sklearn.mixture._gaussian_mixture));external[str(p)]=audit.digest(p)
    git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip()
    audit.json_write(HERE/'REGISTRY.json',dict(family='H81',rollback=head,config=CONFIG,ks=KS,features=FEATURES,source_hashes=sources,external_protected=external,selection='held-file worst/mean physical negative log density, then full-model BIC and k',teacher_labels_or_statistics_used_for_fit_selection=False,pitch_source='cached H69 pYIN default beta(2,18), true25ms',historical_exposure=True,semantic_mapping='upper half of component ACF means',test_used=False))
    print('PASS H81 synthetic GMM/scaler/posterior/subsample; no BT2 fit',flush=True)

def train(out):
    check_registry();assert not out.exists();head=clean_head();out.mkdir();bank={};times={}
    for path in sorted((WORK/'H75_ml/run_train').glob('bank_*.npz')):
        n=path.stem[5:]+'.wav'
        with np.load(path) as b:bank[n]=b['x'][:,:4].copy();times[n]=b['times'].copy()
    names=sorted(bank);models=[];rows=[];proofs=[]
    print('H81: 15 new GMM fits; select only from acoustic held-file density, no LAB/statistics parsing',flush=True)
    for held in ['full']+names:
        pool=[n for n in names if n!=held];x,indices=design(bank,pool)
        for k in KS:
            m=fit(x,k,pool);models.append(m)
            if held!='full':
                prob,ld=response(bank[held],m);rows.append(dict(k=k,file=held,fit_pool='|'.join(pool),negative_log_density=float(-ld.mean())));proofs.append(dict(k=k,file=held,fit_pool='|'.join(pool),probability=prob.tolist(),log_density=ld.tolist()))
            print('H81 fit',held,'k',k,'converged',m['converged'],flush=True)
    k,rank=choose(models,rows);locked=next(m for m in models if m['k']==k and m['fit_files']==names);components=voiced_components(locked);audit.json_write(out/'locked_model.json',dict(model=locked,voiced_components=components,probability_threshold=.5,energy_threshold=None,pitch_prior=[2,18]))
    for n in names:
        prob,ld=response(bank[n],locked);native=np.load(WORK/f'results/H69_native_{Path(n).stem}_pyin25_beta2_18.npz');assert np.array_equal(times[n],native['native_times']);mask=native['voiced']&(prob[:,components].sum(axis=1)>=.5);f0=np.where(mask,native['raw_f0'],np.nan);np.savez_compressed(out/f'prediction_{Path(n).stem}.npz',x=bank[n],times=times[n],probability=prob,pred=mask,f0=f0,native_voiced=native['voiced'],native_f0=native['raw_f0'])
    audit.json_write(out/'models.json',models);audit.json_write(out/'held_density_proofs.json',proofs);pd.DataFrame(rows).to_csv(out/'held_density.csv',index=False);artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in out.iterdir()}
    audit.json_write(out/'final_info.json',dict(status='FROZEN_UNLABELED',family='H81',prereg_commit=head,gmm_fits=15,initializations=45,held_density_rows=12,selected_k=k,selection_rank=[list(v) for v in rank],new_pitch_inferences=0,new_feature_extraction=0,teacher_labels_or_statistics_used=False,artifacts=artifacts,limitation='Feature design and research choices follow prior data exposure; density selection does not ensure semantic voicing or correct pitch.'))
    print('H81 locked k',k,'components',components,'before teacher audit',flush=True)

def teacher_audit(out):
    check_registry();assert not out.exists();head=clean_head();train=HERE/'run_train';assert json.loads((train/'verification.json').read_text())['status']=='PASS'
    for p,d in json.loads((train/'final_info.json').read_text())['artifacts'].items():assert audit.digest(REPO/p)==d,p
    out.mkdir();from verify_srh import independent_item
    locked=json.loads((train/'locked_model.json').read_text());rows=[];attribution=[]
    for path in sorted(core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');p=np.load(train/f'prediction_{path.stem}.npz');assert np.array_equal(item['times'],p['times']);rows.append(dict(pipeline_id='H81_unlabeled_selected',**core.score_file(item,p['pred'],p['f0'])));labels=np.argmax(p['probability'],axis=1)
        for j in range(locked['model']['k']):
            chosen=labels==j
            attribution.append(dict(file=path.name,component=j,frames=int(sum(chosen)),v=int(sum(chosen&(item['labels']=='v'))),uv=int(sum(chosen&(item['labels']=='uv'))),sil=int(sum(chosen&(item['labels']=='sil'))),mapped_voiced=j in locked['voiced_components']))
    old=pd.read_csv(WORK/'H78_context/run_train/all_train_metrics.csv',float_precision='round_trip');base=old[old.option_id=='energy07'].copy();base['pipeline_id']='H72_energy07_cached';rows+=base.to_dict('records');pd.DataFrame(rows).to_csv(out/'all_train_metrics.csv',index=False);pd.DataFrame(attribution).to_csv(out/'component_audit.csv',index=False);artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in out.iterdir()}
    audit.json_write(out/'final_info.json',dict(status='AUDITED_AFTER_FREEZE',family='H81',freeze_commit=head,locked_model_sha256=audit.digest(train/'locked_model.json'),posthoc_train_groups=4,cached_controls=4,selection_unchanged=True,test_used=False,artifacts=artifacts));print('H81 teacher audit only; frozen model unchanged',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--action',choices=['precheck','train','audit'],required=True);p.add_argument('--out_dir',required=True);a=p.parse_args();action={'precheck':precheck,'train':train,'audit':teacher_audit}[a.action];action(Path(a.out_dir).resolve())
