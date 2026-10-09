"""H74: nonlinear feature interactions, frozen five-feature H73 bank."""
import argparse,importlib.util,inspect,itertools,json,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

HERE=Path(__file__).resolve().parent;WORK=HERE.parent
spec=importlib.util.spec_from_file_location('h73_cached',WORK/'H73_ml/experiment.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
REPO=previous.REPO;core=previous.core;audit=previous.audit
OPTIONS=[dict(id='energy07',depth=None)]+[dict(id=f'rf5_depth{d}',depth=d) for d in (2,4,6)]
PARAMETERS=dict(n_estimators=96,min_samples_leaf=8,max_features=None,bootstrap=True,max_samples=None,class_weight=None,criterion='gini',random_state=74,n_jobs=1)

def tree_probability(x,tree):
    x=np.asarray(x,dtype=np.float32);nodes=np.zeros(len(x),dtype=int)
    left=np.asarray(tree['left']);right=np.asarray(tree['right']);feature=np.asarray(tree['feature']);threshold=np.asarray(tree['threshold'])
    while np.any(left[nodes]>=0):
        active=np.flatnonzero(left[nodes]>=0);at=nodes[active];go_left=x[active,feature[at]]<=threshold[at];nodes[active]=np.where(go_left,left[at],right[at])
    return np.asarray(tree['probability'])[nodes,1]

def response(x,model):return np.mean([tree_probability(x,t) for t in model['trees']],axis=0)

def fit(x,y,weights,option,names):
    pipe=Pipeline([('forest',RandomForestClassifier(max_depth=option['depth'],**PARAMETERS))]);pipe.fit(x,y,forest__sample_weight=weights);forest=pipe.named_steps['forest'];assert np.array_equal(forest.classes_,[0,1])
    trees=[]
    for estimator in forest.estimators_:
        t=estimator.tree_;trees.append(dict(seed=int(estimator.random_state),left=t.children_left.tolist(),right=t.children_right.tolist(),feature=t.feature.tolist(),threshold=t.threshold.tolist(),probability=t.value[:,0,:].tolist(),weighted_samples=t.weighted_n_node_samples.tolist(),distinct_samples=t.n_node_samples.tolist(),max_depth=t.max_depth))
    model=dict(option_id=option['id'],fit_files=sorted(names),depth=option['depth'],parameters=PARAMETERS,training_rows=len(y),trees=trees)
    assert np.allclose(response(x,model),pipe.predict_proba(x)[:,1],atol=1e-12,rtol=1e-12)
    return model

def check_registry():
    r=json.loads((HERE/'REGISTRY.json').read_text());assert r['options']==OPTIONS and r['parameters']==PARAMETERS
    for p,d in r['source_hashes'].items():assert audit.digest(REPO/p)==d,p
    for p,d in r['external_protected'].items():assert audit.digest(Path(p))==d,p
    return r

def precheck(out):
    assert not (HERE/'REGISTRY.json').exists() and not out.exists();out.mkdir()
    from verify import certificate
    rng=np.random.default_rng(74);x=rng.normal(size=(100,5));y=((x[:,0]>0)^(x[:,1]>0)).astype(int);w=np.linspace(.5,1.5,len(y));checks=[]
    for option in OPTIONS[1:]:checks.append(certificate(x,y,w,fit(x,y,w,option,['synthetic'])))
    audit.json_write(out/'final_info.json',dict(status='PASS',BT2_used=False,synthetic_models=len(checks),checks=checks))
    old=previous.check_registry();sources=dict(old['source_hashes']);paths=[HERE/p for p in ('experiment.py','verify.py','plot.py','notes.txt','REGISTRATION.md')]+[out/'final_info.json',WORK/'H73_ml/REGISTRY.json',WORK/'H73_ml/experiment.py',WORK/'H73_ml/run_train/final_info.json',WORK/'H73_ml/run_train/verification.json']
    receipt=json.loads((WORK/'H73_ml/run_train/final_info.json').read_text());paths += [REPO/p for p in receipt['artifacts']]
    import sklearn.ensemble._forest,sklearn.tree._classes,sklearn.tree._tree,sklearn.tree._splitter,sklearn.tree._criterion
    runtime=[Path(inspect.getfile(m)) for m in (sklearn.ensemble._forest,sklearn.tree._classes,sklearn.tree._tree,sklearn.tree._splitter,sklearn.tree._criterion)]
    external=dict(old['external_protected']);external.update({str(p):audit.digest(p) for p in runtime})
    for p in paths:sources[str(p.relative_to(REPO))]=audit.digest(p)
    audit.json_write(HERE/'REGISTRY.json',dict(family='H74',rollback=previous.base.previous.old.common.matrix.commit_id(),options=OPTIONS,parameters=PARAMETERS,features=previous.FEATURES,source_hashes=sources,external_protected=external,sklearn=sklearn.__version__,prediction_threshold=.5,test_used_for_selection=False,historical_test_exposure=True))
    print('PASS H74 three synthetic forest certificates; no BT2 fitting',flush=True)

def choose(rows):
    rank=[];control=[r for r in rows if r['option_id']=='energy07']
    for option in OPTIONS:
        group=[r for r in rows if r['option_id']==option['id']];valid=all(np.isfinite(r['average_mape']) for r in group)
        valid &= all(np.mean([r[k] for r in group])>=np.mean([r[k] for r in control])-.01 for k in ('macro_f1','recall_v'))
        valid &= sum(r['false_voiced_sil'] for r in group)<=sum(r['false_voiced_sil'] for r in control)+1
        rank.append((not valid,max(r['average_mape'] for r in group) if valid else np.inf,np.mean([r['average_mape'] for r in group]) if valid else np.inf,option['id']))
    return min(rank)[-1]

def train(out):
    check_registry();assert not out.exists();git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip();branch=subprocess.check_output(git+['branch','--show-current'],cwd=REPO,text=True).strip();assert subprocess.check_output(git+['ls-remote','origin','refs/heads/'+branch],cwd=REPO,text=True).split()[0]==head and not subprocess.check_output(git+['status','--porcelain'],cwd=REPO,text=True).strip()
    out.mkdir();bank={};from verify_srh import independent_item
    for path in sorted(core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');saved=dict(np.load(WORK/f'H73_ml/run_train/bank_{path.stem}.npz'));assert np.array_equal(saved['times'],item['times']) and np.array_equal(saved['labels'],item['labels']);bank[path.name]={**saved,'stats':item['stats']}
    names=sorted(bank);pools=[list(p) for k in (2,3,4) for p in itertools.combinations(names,k)];models=[];rows=[];proofs=[]
    print('H74: test nonlinear interactions with three forest depths; unchanged features, labels, F0 and probability threshold; train-only fits',flush=True)
    for pool in pools:
        x,y,w,membership=previous.design(bank,pool)
        for option in OPTIONS[1:]:
            model=fit(x,y,w,option,pool);models.append(model)
            for name in names:
                probability=response(bank[name]['x'],model);pred=bank[name]['native_voiced']&(probability>=.5);f0=np.where(pred,bank[name]['native_f0'],np.nan);rows.append(dict(option_id=option['id'],fit_pool='|'.join(pool),eval_file_in_fit=name in pool,**core.score_file(dict(file=name,labels=bank[name]['labels'],stats=bank[name]['stats']),pred,f0)));proofs.append(dict(option_id=option['id'],fit_pool='|'.join(pool),file=name,probability=probability.tolist(),pred=pred.tolist(),f0=[float(v) if np.isfinite(v) else None for v in f0]))
        print('H74 completed pool', '|'.join(pool),flush=True)
    old=pd.read_csv(WORK/'H73_ml/run_train/all_train_metrics.csv',float_precision='round_trip');rows += old[old.option_id=='energy07'].fillna({'fit_pool':''}).to_dict('records')
    def score(name,option,pool):return next(r for r in rows if r['file']==name and r['option_id']==option and r['fit_pool']==('' if option=='energy07' else '|'.join(sorted(pool))))
    inner=[];selections=[]
    for held in ['final']+names:
        pool=[n for n in names if n!=held];records=[]
        for name in pool:
            for option in OPTIONS:
                row=score(name,option['id'],[n for n in pool if n!=name]);records.append(row);inner.append(dict(outer_held=held,inner_held=name,**row))
        selections.append(dict(outer_held=held,selection_files=pool,option_id=choose(records)))
    selected={s['outer_held']:s['option_id'] for s in selections};summary=[]
    for name in names:summary += [dict(stage='full_train',**score(name,selected['final'],names)),dict(stage='selected_lofo',**score(name,selected['final'],[n for n in names if n!=name])),dict(stage='nested_diagnostic',**score(name,selected[name],[n for n in names if n!=name]))]
    audit.json_write(out/'models.json',models);audit.json_write(out/'prediction_proofs.json',proofs);pd.DataFrame(rows).to_csv(out/'all_train_metrics.csv',index=False);pd.DataFrame(inner).to_csv(out/'inner_traces.csv',index=False);pd.DataFrame(summary).to_csv(out/'selected_metrics.csv',index=False)
    artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in out.iterdir()};audit.json_write(out/'final_info.json',dict(status='MEASURED',family='H74',prereg_commit=head,selections=selections,actual_supervised_fits=len(models),actual_trees_fitted=len(models)*PARAMETERS['n_estimators'],metric_groups=len(rows),inner_rows=len(inner),selected_summary_rows=len(summary),test_used=False,native_inferences=0,feature_extraction_repeated=False,sklearn=sklearn.__version__,selected_config=selected['final'],artifacts=artifacts,limitation='Classifier only rejects native pYIN candidates; file LAB is not per-frame pitch GT; control has historical all-train exposure.'))
    print('H74 selected',selected['final'],'fits',len(models),'groups',len(rows),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--action',choices=['precheck','train'],required=True);p.add_argument('--out_dir',required=True);a=p.parse_args();precheck(Path(a.out_dir).resolve()) if a.action=='precheck' else train(Path(a.out_dir).resolve())
