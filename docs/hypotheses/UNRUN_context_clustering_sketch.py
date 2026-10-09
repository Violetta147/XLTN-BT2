"""Pool file contexts, discover two groups without domain labels, reuse experts."""
import argparse, importlib.util, itertools, json, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

HERE=Path(__file__).resolve().parent; WORK=HERE.parent
spec=importlib.util.spec_from_file_location('h78_context',WORK/'H78_context/experiment.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
REPO=previous.REPO;core=previous.core;audit=previous.audit
OPTIONS=['energy07','pooled_C1','soft_gate_C1','cluster_C1']

def fit_router(contexts,names):
    scaler=StandardScaler().fit(contexts);z=scaler.transform(contexts);choices=[]
    # Exact two-means: at most seven nonempty partitions for four file rows.
    for mask in range(1,2**(len(names)-1)):
        labels=np.asarray([0]+[(mask>>j)&1 for j in range(len(names)-1)])
        centers=np.asarray([z[labels==k].mean(axis=0) for k in (0,1)])
        sse=float(np.sum((z-centers[labels])**2));choices.append((sse,mask,labels,centers))
    sse,mask,labels,centers=min(choices,key=lambda x:x[:2])
    return dict(fit_files=list(names),mean=scaler.mean_.tolist(),variance=scaler.var_.tolist(),scale=scaler.scale_.tolist(),centers=centers.tolist(),labels=labels.tolist(),sse=sse,partitions_considered=len(choices),temperature=1.,algorithm='exact_two_means_file_context')

def weights(c,router):
    z=(c-router['mean'])/router['scale'];dist=np.sum((np.asarray(router['centers'])-z)**2,axis=1)
    logits=-dist/2.;logits-=max(logits);w=np.exp(logits);return w/sum(w)

def probabilities(bank,assets):
    w=weights(previous.context(bank['x']),assets['router'])
    p=[previous.model_api.response(bank['x'],m) for m in assets['experts']]
    return w[0]*p[0]+w[1]*p[1],w

def choose(rows):
    control=[r for r in rows if r['option_id']=='energy07'];rank=[]
    for identity in OPTIONS:
        g=[r for r in rows if r['option_id']==identity]
        valid=all(np.isfinite(r['average_mape']) for r in g) and all(np.mean([r[k] for r in g])>=np.mean([r[k] for r in control])-.01 for k in ('macro_f1','recall_v')) and sum(r['false_voiced_sil'] for r in g)<=sum(r['false_voiced_sil'] for r in control)+1
        rank.append((not valid,max(r['average_mape'] for r in g) if valid else np.inf,np.mean([r['average_mape'] for r in g]) if valid else np.inf,identity))
    return min(rank)[-1]

def check_registry():
    r=json.loads((HERE/'REGISTRY.json').read_text());assert r['options']==OPTIONS
    for p,d in r['source_hashes'].items():assert audit.digest(REPO/p)==d,p
    for p,d in r['external_protected'].items():assert audit.digest(Path(p))==d,p
    return r

def precheck(out):
    assert not out.exists() and not (HERE/'REGISTRY.json').exists();out.mkdir()
    from verify import certificate,scalar_weights,scalar_probabilities
    c=np.asarray([[-3.,.2],[-3.2,.25],[-5.,.22],[-5.1,.24]])
    router=fit_router(c,['a','b','c','d']);certificate(c,router)
    x=np.asarray([[.8,-2.,50.,.3,.9],[.6,-1.,80.,.1,.7]])
    experts=[dict(columns=list(range(5)),mean=[0]*5,scale=[1]*5,coefficient=[1,0,0,0,0],intercept=t,fit_files=[]) for t in (-1.,1.)]
    a=dict(router=router,experts=experts);b=dict(x=x)
    p,w=probabilities(b,a);q,v=scalar_probabilities(b,a);assert np.allclose(p,q,atol=1e-12) and np.allclose(w,v,atol=1e-12)
    poison={**b,'labels':['sil','sil'],'file':'studio_not_a_feature.wav','domain':'phone','stats':{'F0mean':999}}
    assert np.array_equal(probabilities(poison,a)[0],p)
    swapped={**a,'router':{**router,'centers':router['centers'][::-1]},'experts':experts[::-1]}
    assert np.allclose(probabilities(b,swapped)[0],p)
    audit.json_write(out/'final_info.json',dict(status='PASS',BT2_used=False,synthetic_router_fits=1,supervised_fits=0,exact_partition_certificate=True,mixture_and_cluster_permutation=True,inference_ignores_names_domain_labels_stats=True))
    old=previous.check_registry();sources=dict(old['source_hashes']);complete=json.loads((WORK/'H78_context/run_train/completion.json').read_text());sources.update(complete['artifacts'])
    paths=[HERE/p for p in ('experiment.py','verify.py','plot.py','notes.txt','REGISTRATION.md')]+[out/'final_info.json',WORK/'H78_context/REGISTRY.json',WORK/'H78_context/run_train/completion.json']
    for p in paths:sources[str(p.relative_to(REPO))]=audit.digest(p)
    git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip()
    audit.json_write(HERE/'REGISTRY.json',dict(family='H79',rollback=head,options=OPTIONS,context=previous.CONTEXT,source_hashes=sources,external_protected=old['external_protected'],algorithm='exact two-means on pooled unlabeled file contexts',router_fits=11,supervised_fits=0,soft_temperature=1.,domain_metadata_used=False,historical_test_exposure=True,test_used_for_selection=False))
    print('PASS H79 synthetic exact clustering and mixture; no BT2 fitting',flush=True)

def train(out):
    check_registry();assert not out.exists();git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip();branch=subprocess.check_output(git+['branch','--show-current'],cwd=REPO,text=True).strip()
    assert subprocess.check_output(git+['ls-remote','origin','refs/heads/'+branch],cwd=REPO,text=True).split()[0]==head and not subprocess.check_output(git+['status','--porcelain'],cwd=REPO,text=True).strip();out.mkdir()
    from verify_srh import independent_item
    bank={}
    for path in sorted(core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');b=dict(np.load(WORK/f'H75_ml/run_train/bank_{path.stem}.npz'));assert np.array_equal(item['labels'],b['labels']) and np.array_equal(item['times'],b['times']);bank[path.name]={**b,'stats':item['stats']}
    names=sorted(bank);pools=[list(p) for k in (2,3,4) for p in itertools.combinations(names,k)]
    cached=json.loads((WORK/'H75_ml/run_train/models.json').read_text());single=json.loads((WORK/'H78_context/run_train/new_models.json').read_text())
    models={'|'.join(m['fit_files']):m for m in cached if m['option_id']=='recover5_C1'};models.update({'|'.join(m['fit_files']):m for m in single if m['role']=='single_expert'})
    assets=[];proofs=[];rows=[];routes=[]
    print('H79: discover unlabeled context groups on eleven train pools; reuse all classifier fits',flush=True)
    for pool in pools:
        router=fit_router(np.asarray([previous.context(bank[n]['x']) for n in pool]),pool)
        groups=[[n for n,k in zip(pool,router['labels']) if k==j] for j in (0,1)]
        a=dict(fit_files=pool,router=router,cluster_members=groups,experts=[models['|'.join(g)] for g in groups]);assets.append(a)
        for name in names:
            prob,w=probabilities(bank[name],a);pred,f0,mode=previous.infer(bank[name],prob)
            row=dict(option_id='cluster_C1',fit_pool='|'.join(pool),eval_file_in_fit=name in pool,**core.score_file(dict(file=name,labels=bank[name]['labels'],stats=bank[name]['stats']),pred,f0));rows.append(row)
            proofs.append(dict(fit_pool='|'.join(pool),file=name,probability=prob.tolist(),weights=w.tolist(),pred=pred.tolist(),f0=[float(v) if np.isfinite(v) else None for v in f0],mode=mode.tolist()))
            routes.append(dict(fit_pool='|'.join(pool),file=name,eval_file_in_fit=name in pool,cluster0_weight=float(w[0]),cluster1_weight=float(w[1]),cluster0_members='|'.join(groups[0]),cluster1_members='|'.join(groups[1])))
    old=pd.read_csv(WORK/'H78_context/run_train/all_train_metrics.csv',float_precision='round_trip');rows+=old[old.option_id.isin(OPTIONS[:-1])].fillna({'fit_pool':''}).to_dict('records')
    def score(name,identity,pool):return next(r for r in rows if r['file']==name and r['option_id']==identity and r['fit_pool']==('' if identity=='energy07' else '|'.join(sorted(pool))))
    inner=[];selections=[]
    for held in ['final']+names:
        pool=[n for n in names if n!=held];records=[]
        for n in pool:
            for identity in OPTIONS:
                row=score(n,identity,[v for v in pool if v!=n]);records.append(row);inner.append(dict(outer_held=held,inner_held=n,**row))
        selections.append(dict(outer_held=held,selection_files=pool,option_id=choose(records)))
    chosen={s['outer_held']:s['option_id'] for s in selections};summary=[]
    for n in names:summary += [dict(stage='full_train',**score(n,chosen['final'],names)),dict(stage='selected_lofo',**score(n,chosen['final'],[v for v in names if v!=n])),dict(stage='nested_diagnostic',**score(n,chosen[n],[v for v in names if v!=n]))]
    audit.json_write(out/'assets.json',assets);audit.json_write(out/'prediction_proofs.json',proofs);pd.DataFrame(rows).to_csv(out/'all_train_metrics.csv',index=False);pd.DataFrame(inner).to_csv(out/'inner_traces.csv',index=False);pd.DataFrame(summary).to_csv(out/'selected_metrics.csv',index=False);pd.DataFrame(routes).to_csv(out/'cluster_diagnostics.csv',index=False)
    artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in out.iterdir()}
    audit.json_write(out/'final_info.json',dict(status='MEASURED',family='H79',prereg_commit=head,router_fits=11,new_supervised_fits=0,reused_expert_roles=22,new_metric_groups=44,cached_groups=92,metric_groups=len(rows),inner_rows=len(inner),summary_rows=len(summary),selected_config=chosen['final'],selections=selections,native_inferences=0,feature_extraction_repeated=False,domain_metadata_used=False,test_used=False,artifacts=artifacts))
    print('H79 selected',chosen['final'],'11 unlabeled router fits; 44 new +92 cached groups',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--action',choices=['precheck','train'],required=True);p.add_argument('--out_dir',required=True);a=p.parse_args();precheck(Path(a.out_dir).resolve()) if a.action=='precheck' else train(Path(a.out_dir).resolve())
