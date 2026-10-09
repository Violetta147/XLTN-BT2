"""H75: learn all candidate frames and recover missing native pYIN F0 with cached ACF25."""
import argparse,itertools,json,platform,subprocess,sys,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd
import sklearn
from scipy.special import expit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import pyin_locked_test as base
HERE=Path(__file__).resolve().parent;WORK=HERE.parent;REPO=base.REPO;core=base.core;audit=base.audit
OPTIONS=[dict(id='energy07',columns=[],C=None)]+[dict(id=f'recover5_C{c:g}',columns=[0,1,2,3,4],C=c) for c in (.1,1.,10.)]
FEATURES=['max_normalized_acf','log_relative_rms','zero_crossings_per_second','high_frequency_power_ratio','pyin_voiced_probability']

def response(x,model):
    z=(x[:,model['columns']]-model['mean'])/model['scale'];return expit(z@np.array(model['coefficient'])+model['intercept'])

def fit(x,y,weights,option,names):
    pipe=Pipeline([('scale',StandardScaler()),('model',LogisticRegression(C=option['C'],solver='lbfgs',tol=1e-9,max_iter=2000,random_state=0))])
    pipe.fit(x[:,option['columns']],y,scale__sample_weight=weights,model__sample_weight=weights)
    s,m=pipe.named_steps['scale'],pipe.named_steps['model'];assert m.n_iter_[0]<2000
    model=dict(option_id=option['id'],fit_files=sorted(names),columns=option['columns'],C=option['C'],mean=s.mean_.tolist(),variance=s.var_.tolist(),scale=s.scale_.tolist(),coefficient=m.coef_[0].tolist(),intercept=float(m.intercept_[0]),iterations=int(m.n_iter_[0]),training_rows=len(y))
    assert np.allclose(response(x,model),pipe.predict_proba(x[:,option['columns']])[:,1],atol=1e-12)
    return model

def design(bank,names):
    counts={n:int((bank[n]['native_voiced']|np.isfinite(bank[n]['acf_pitch'])).sum()) for n in names};total=sum(counts.values());xs=[];ys=[];weights=[];membership=[]
    for name in sorted(names):
        indices=np.flatnonzero(bank[name]['native_voiced']|np.isfinite(bank[name]['acf_pitch']));assert np.isin(bank[name]['labels'][indices],['v','uv','sil']).all()
        xs.extend(bank[name]['x'][indices]);ys.extend((bank[name]['labels'][indices]=='v').astype(int));weights.extend([total/(len(names)*counts[name])]*len(indices));membership.extend([(name,int(i)) for i in indices])
    return np.asarray(xs),np.asarray(ys),np.asarray(weights),membership

def infer(bank,option,model):
    if option['id']=='energy07':pred=bank['control_pred'].copy()
    else:pred=(response(bank['x'],model)>=.5)&(bank['x'][:,1]>=np.log(.07))&(bank['native_voiced']|((bank['x'][:,0]>=.6)&np.isfinite(bank['acf_pitch'])))
    candidate=np.where(bank['native_voiced'],bank['native_f0'],bank['acf_pitch'])
    return pred,np.where(pred,candidate,np.nan)

def choose(rows):
    rank=[];control=[r for r in rows if r['option_id']=='energy07']
    for o in OPTIONS:
        group=[r for r in rows if r['option_id']==o['id']];valid=all(np.isfinite(r['average_mape']) for r in group)
        valid &= all(np.mean([r[k] for r in group])>=np.mean([r[k] for r in control])-.01 for k in ('macro_f1','recall_v'))
        valid &= sum(r['false_voiced_sil'] for r in group)<=sum(r['false_voiced_sil'] for r in control)+1
        rank.append((not valid,max(r['average_mape'] for r in group) if valid else np.inf,np.mean([r['average_mape'] for r in group]) if valid else np.inf,o['id']))
    return min(rank)[-1]

def check_registry():
    r=json.loads((HERE/'REGISTRY.json').read_text());assert r['options']==OPTIONS
    for p,d in r['source_hashes'].items():assert audit.digest(REPO/p)==d,p
    for p,d in r['external_protected'].items():assert audit.digest(Path(p))==d,p
    return r

def precheck(out):
    assert not (HERE/'REGISTRY.json').exists() and not out.exists();out.mkdir()
    from verify import certificate
    rng=np.random.default_rng(75);x=rng.normal(size=(80,5));y=(x[:,0]+.5*x[:,1]+rng.normal(size=80)>.1).astype(int);w=np.linspace(.5,1.5,80);checks=[]
    for option in OPTIONS[1:]:
        model=fit(x,y,w,option,['synthetic']);checks.append(certificate(x,y,w,model))
    fixture=dict(x=np.asarray([[.2,np.log(.07),0,0,0],[.6,np.log(.07),0,0,0],[.59,np.log(.07),0,0,0],[.7,np.log(.069),0,0,0],[.8,np.log(.07),0,0,0],[.8,np.log(.069),0,0,0],[.6,np.log(.07),0,0,0]]),native_voiced=np.asarray([True,False,False,False,False,True,False]),native_f0=np.asarray([100,np.nan,np.nan,np.nan,np.nan,110,np.nan]),acf_pitch=np.asarray([200,120,120,120,np.nan,120,400]))
    dummy=dict(columns=[0,1,2,3,4],mean=[0]*5,scale=[1]*5,coefficient=[0]*5,intercept=0);pred,f0=infer(fixture,OPTIONS[1],dummy);assert np.array_equal(pred,[True,True,False,False,False,False,True]) and np.array_equal(f0,[100,120,np.nan,np.nan,np.nan,np.nan,400],equal_nan=True)
    audit.json_write(out/'final_info.json',dict(status='PASS',BT2_used=False,synthetic_models=len(checks),native_preference_recovery_energy_strength_boundaries=True,checks=checks))
    spec=importlib.util.spec_from_file_location('h74_cached',WORK/'H74_ml/experiment.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior);r=prior.check_registry();sources=dict(r['source_hashes']);paths=[HERE/p for p in ('experiment.py','verify.py','plot.py','notes.txt','REGISTRATION.md')]+[out/'final_info.json',WORK/'H72_REGISTRY.json',WORK/'results/H72_test_experiment.json',WORK/'results/H72_verification.json']
    receipt=json.loads((WORK/'H74_ml/run_train/final_info.json').read_text());paths += [REPO/p for p in receipt['artifacts']]+[WORK/'H74_ml/REGISTRY.json',WORK/'H74_ml/run_train/final_info.json',WORK/'H74_ml/run_train/verification.json'];paths += list((WORK/'H73_ml/run_train').glob('bank_*.npz'))
    paths += list((WORK/'results').glob('H50_design_*.npz'))
    import inspect,sklearn.linear_model._logistic,sklearn.preprocessing._data,sklearn.pipeline
    runtime=[Path(inspect.getfile(m)) for m in (sklearn.linear_model._logistic,sklearn.preprocessing._data,sklearn.pipeline)]
    external=dict(r['external_protected']);external.update({str(p):audit.digest(p) for p in runtime})
    for p in paths:sources[str(p.relative_to(REPO))]=audit.digest(p)
    audit.json_write(HERE/'REGISTRY.json',dict(family='H75',rollback=base.previous.old.common.matrix.commit_id(),options=OPTIONS,features=FEATURES,source_hashes=sources,external_protected=external,sklearn=sklearn.__version__,test_used_for_selection=False,prediction_threshold=.5))
    print('PASS H75 three synthetic logistic certificates; no BT2 fitting')

def train(out):
    check_registry();assert not out.exists()
    git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip();branch=subprocess.check_output(git+['branch','--show-current'],cwd=REPO,text=True).strip();assert subprocess.check_output(git+['ls-remote','origin','refs/heads/'+branch],cwd=REPO,text=True).split()[0]==head and not subprocess.check_output(git+['status','--porcelain'],cwd=REPO,text=True).strip()
    out.mkdir();bank={}
    from verify_srh import independent_item
    for path in sorted(core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');old=dict(np.load(WORK/f'results/H50_design_{path.stem}.npz'));native=dict(np.load(WORK/f'results/H69_native_{path.stem}_pyin25_beta2_8.npz'));control=dict(np.load(WORK/f'results/H71_proof_{path.stem}.npz'));ids=base.previous.OPTIONS;index=next(i for i,o in enumerate(ids) if o['id']=='pyin8_energy_0.07')
        assert np.array_equal(old['times'],item['times']) and np.array_equal(native['native_times'],item['times'])
        x=np.column_stack((old['x'][:,:4],native['probability']));bank[path.name]=dict(x=x,acf_pitch=old['pitch'],labels=item['labels'],times=item['times'],native_voiced=native['voiced'],native_f0=native['raw_f0'],control_pred=control['pred'][index],stats=item['stats'])
        np.savez_compressed(out/f'bank_{path.stem}.npz',**{k:v for k,v in bank[path.name].items() if k!='stats'})
    names=sorted(bank);pools=[list(p) for k in (2,3,4) for p in itertools.combinations(names,k)];models=[];rows=[];proofs=[]
    print('H75: fitting three candidate-recovery logistic variants on eleven train-only file pools; scalar energy control reused',flush=True)
    for pool in pools:
        x,y,w,membership=design(bank,pool)
        for option in OPTIONS[1:]:
            model=fit(x,y,w,option,pool);models.append(model)
            for name in names:
                pred,f0=infer(bank[name],option,model);row=dict(option_id=option['id'],fit_pool='|'.join(pool),eval_file_in_fit=name in pool,**core.score_file(dict(file=name,labels=bank[name]['labels'],stats=bank[name]['stats']),pred,f0));rows.append(row);proofs.append(dict(option_id=option['id'],fit_pool='|'.join(pool),file=name,pred=pred.tolist(),f0=[float(v) if np.isfinite(v) else None for v in f0]))
    for name in names:
        pred,f0=infer(bank[name],OPTIONS[0],None);rows.append(dict(option_id='energy07',fit_pool='',eval_file_in_fit=False,**core.score_file(dict(file=name,labels=bank[name]['labels'],stats=bank[name]['stats']),pred,f0)))
    def score(name,option,pool):return next(r for r in rows if r['file']==name and r['option_id']==option and r['fit_pool']==('' if option=='energy07' else '|'.join(sorted(pool))))
    inner=[];selections=[]
    for held in ['final']+names:
        pool=[n for n in names if n!=held];records=[]
        for name in pool:
            fit_pool=[n for n in pool if n!=name]
            for option in OPTIONS:
                row=score(name,option['id'],fit_pool);records.append(row);inner.append(dict(outer_held=held,inner_held=name,**row))
        selections.append(dict(outer_held=held,selection_files=pool,option_id=choose(records)))
    selected={s['outer_held']:s['option_id'] for s in selections};summary=[]
    for name in names:
        summary += [dict(stage='full_train',**score(name,selected['final'],names)),dict(stage='selected_lofo',**score(name,selected['final'],[n for n in names if n!=name])),dict(stage='nested_diagnostic',**score(name,selected[name],[n for n in names if n!=name]))]
    audit.json_write(out/'models.json',models);audit.json_write(out/'prediction_proofs.json',proofs)
    pd.DataFrame(rows).to_csv(out/'all_train_metrics.csv',index=False);pd.DataFrame(inner).to_csv(out/'inner_traces.csv',index=False);pd.DataFrame(summary).to_csv(out/'selected_metrics.csv',index=False)
    artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in out.iterdir()}
    audit.json_write(out/'final_info.json',dict(status='MEASURED',family='H75',prereg_commit=head,selections=selections,actual_supervised_fits=len(models),metric_groups=len(rows),inner_rows=len(inner),selected_summary_rows=len(summary),test_used=False,native_inferences=0,feature_extraction_repeated=False,sklearn=sklearn.__version__,selected_config=selected['final'],artifacts=artifacts,limitation='Classifier learns all frames with a native or ACF candidate; native F0 preferred, ACF25 fallback only on energy >=.07 and periodicity >=.6; LAB is not per-frame pitch GT.'))
    print('H75 selected',selected['final'],'fits',len(models),'groups',len(rows),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--action',choices=['precheck','train'],required=True);p.add_argument('--out_dir',required=True);a=p.parse_args();precheck(Path(a.out_dir).resolve()) if a.action=='precheck' else train(Path(a.out_dir).resolve())
