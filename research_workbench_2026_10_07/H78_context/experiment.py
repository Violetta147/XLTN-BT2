"""H78: audio-context conditioning and supervised soft domain routing."""
import argparse,importlib.util,itertools,json,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent;WORK=HERE.parent
spec=importlib.util.spec_from_file_location('h77_cached',WORK/'H77_test/experiment.py');baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
decoder=baseline.previous;model_api=decoder.previous;REPO=baseline.REPO;core=baseline.core;audit=baseline.audit
OPTIONS=['energy07','pooled_C1','contextual_C1','soft_gate_C1']
TRAIN_DOMAIN={'phone_F1.wav':'phone','phone_M1.wav':'phone','studio_F1.wav':'studio','studio_M1.wav':'studio'}
CONTEXT=['q20_log_relative_rms','median_high_frequency_power_of_low_energy_frames']

def context(x):
    q=float(np.quantile(x[:,1],.2,method='linear'));low=x[:,1]<=q;return np.asarray([q,float(np.median(x[low,3]))])

def augment(x,c):return np.column_stack((x,np.tile(c,(len(x),1)),(x[:,:,None]*c[None,None,:]).reshape(len(x),-1)))

def fit(x,y,w,identity,names):return model_api.fit(x,y,w,dict(id=identity,columns=list(range(x.shape[1])),C=1.),names)

def frame_design(bank,names,augmented=False):
    source={n:{**b,'x':augment(b['x'],context(b['x'])) if augmented else b['x']} for n,b in bank.items()};return model_api.design(source,names)[:3]

def probabilities(bank,identity,assets):
    x=bank['x'];c=context(x)
    if identity=='contextual_C1':return model_api.response(augment(x,c),assets['contextual']),None
    if assets['gate'] is None:return model_api.response(x,assets['pooled']),.5
    studio_weight=float(model_api.response(c[None,:],assets['gate'])[0]);phone=model_api.response(x,assets['phone']);studio=model_api.response(x,assets['studio']);return (1-studio_weight)*phone+studio_weight*studio,studio_weight

def infer(bank,probability):
    raw_pred=(probability>=.5)&(bank['x'][:,1]>=np.log(.07))&(bank['native_voiced']|((bank['x'][:,0]>=.6)&np.isfinite(bank['acf_pitch'])));raw_f0=np.where(raw_pred,np.where(bank['native_voiced'],bank['native_f0'],bank['acf_pitch']),np.nan);return decoder.decode(bank,raw_pred,raw_f0,dict(edge_hops=25))

def choose(rows):
    control=[r for r in rows if r['option_id']=='energy07'];rank=[]
    for identity in OPTIONS:
        g=[r for r in rows if r['option_id']==identity];valid=all(np.isfinite(r['average_mape']) for r in g) and all(np.mean([r[k] for r in g])>=np.mean([r[k] for r in control])-.01 for k in ('macro_f1','recall_v')) and sum(r['false_voiced_sil'] for r in g)<=sum(r['false_voiced_sil'] for r in control)+1;rank.append((not valid,max(r['average_mape'] for r in g) if valid else np.inf,np.mean([r['average_mape'] for r in g]) if valid else np.inf,identity))
    return min(rank)[-1]

def check_registry():
    r=json.loads((HERE/'REGISTRY.json').read_text());assert r['options']==OPTIONS and r['train_domain']==TRAIN_DOMAIN
    for p,d in r['source_hashes'].items():assert audit.digest(REPO/p)==d,p
    for p,d in r['external_protected'].items():assert audit.digest(Path(p))==d,p
    return r

def precheck(out):
    assert not out.exists() and not (HERE/'REGISTRY.json').exists();out.mkdir();from verify import independent_context,independent_augment,certificate,independent_probabilities
    rng=np.random.default_rng(78);x=rng.normal(size=(100,5));c=context(x);assert np.allclose(c,independent_context(x),atol=1e-12);phi=augment(x,c);assert np.array_equal(phi,independent_augment(x,c));y=(x[:,0]+x[:,1]>0).astype(int);w=np.linspace(.5,1.5,100);checks=[]
    for identity,data in [('synthetic_expert',x),('synthetic_context',phi),('synthetic_gate',rng.normal(size=(8,2)))]:
        yy=y if len(data)==len(y) else np.arange(8)%2;ww=w if len(data)==len(w) else np.ones(len(data));m=fit(data,yy,ww,identity,['synthetic']);checks.append(certificate(data,yy,ww,m))
        if identity=='synthetic_expert':expert=m
        if identity=='synthetic_context':conditioned=m
        if identity=='synthetic_gate':gate=m
    assets=dict(phone=expert,studio=expert,pooled=expert,gate=gate,contextual=conditioned);bank=dict(x=x,labels=np.full(len(x),'v'))
    for identity in OPTIONS[2:]:
        prob,g=probabilities(bank,identity,assets);other,h=independent_probabilities(bank,identity,assets);assert np.allclose(prob,other,atol=1e-12);poisoned={**bank,'labels':np.full(len(x),'sil'),'file':'different_name.wav','stats':{'F0mean':999}};assert np.array_equal(prob,probabilities(poisoned,identity,assets)[0])
    audit.json_write(out/'final_info.json',dict(status='PASS',BT2_used=False,synthetic_fits=3,checks=checks,context_quantile_interactions_soft_mixture=True,prediction_ignores_names_labels_teacher_stats=True))
    old=baseline.check_registry();sources=dict(old['source_hashes']);paths=[HERE/p for p in ('experiment.py','verify.py','plot.py','notes.txt','REGISTRATION.md')]+[out/'final_info.json',WORK/'H77_test/REGISTRY.json',WORK/'H77_test/experiment.py',WORK/'H77_test/run_test/final_info.json',WORK/'H77_test/run_test/verification.json'];receipt=json.loads((WORK/'H77_test/run_test/final_info.json').read_text());paths += [REPO/p for p in receipt['artifacts']]
    for p in paths:sources[str(p.relative_to(REPO))]=audit.digest(p)
    audit.json_write(HERE/'REGISTRY.json',dict(family='H78',rollback=model_api.base.previous.old.common.matrix.commit_id(),options=OPTIONS,train_domain=TRAIN_DOMAIN,context=CONTEXT,source_hashes=sources,external_protected=old['external_protected'],C=1.,new_fit_counts=dict(contextual=11,single_file_expert=4,file_context_gate=9),decoder='H76 bridge10_edge25 unchanged',historical_test_exposure=True,test_used_for_selection=False))
    print('PASS H78 synthetic context/scaler/gate mixture; no BT2 fitting',flush=True)

def train(out):
    check_registry();assert not out.exists();git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip();branch=subprocess.check_output(git+['branch','--show-current'],cwd=REPO,text=True).strip();assert subprocess.check_output(git+['ls-remote','origin','refs/heads/'+branch],cwd=REPO,text=True).split()[0]==head and not subprocess.check_output(git+['status','--porcelain'],cwd=REPO,text=True).strip();out.mkdir()
    from verify_srh import independent_item
    bank={}
    for path in sorted(core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');b=dict(np.load(WORK/f'H75_ml/run_train/bank_{path.stem}.npz'));assert np.array_equal(item['labels'],b['labels']) and np.array_equal(item['times'],b['times']);bank[path.name]={**b,'stats':item['stats']}
    names=sorted(bank);assert set(names)==set(TRAIN_DOMAIN);pools=[list(p) for k in (2,3,4) for p in itertools.combinations(names,k)];cached=json.loads((WORK/'H75_ml/run_train/models.json').read_text());pooled={'|'.join(m['fit_files']):m for m in cached if m['option_id']=='recover5_C1'};single={};new_models=[];assets_bank=[];rows=[];proofs=[];gate_rows=[]
    print('H78: compare pooled, context-conditioned and audio-routed domain experts; same decoder/F0 rules; train-file pools only',flush=True)
    for name in names:
        x,y,w=frame_design(bank,[name]);m=fit(x,y,w,'expert_C1',[name]);m['role']='single_expert';single[name]=m;new_models.append(m)
    for pool in pools:
        key='|'.join(pool);x,y,w=frame_design(bank,pool,True);conditioned=fit(x,y,w,'contextual_C1',pool);conditioned['role']='contextual';new_models.append(conditioned);domains={d:[n for n in pool if TRAIN_DOMAIN[n]==d] for d in ('phone','studio')};assets=dict(fit_files=pool,pooled=pooled[key],contextual=conditioned,gate=None,phone=None,studio=None,fallback_missing_domain=False)
        if all(domains.values()):
            ctx=np.asarray([context(bank[n]['x']) for n in pool]);targets=np.asarray([int(TRAIN_DOMAIN[n]=='studio') for n in pool]);gate=fit(ctx,targets,np.ones(len(pool)),'context_gate_C1',pool);gate['role']='gate';new_models.append(gate);assets['gate']=gate
            for domain,subset in domains.items():assets[domain]=single[subset[0]] if len(subset)==1 else pooled['|'.join(subset)]
        else:assets['fallback_missing_domain']=True
        assets_bank.append(assets)
        for identity in OPTIONS[2:]:
            for name in names:
                probability,studio_weight=probabilities(bank[name],identity,assets);pred,f0,mode=infer(bank[name],probability);row=dict(option_id=identity,fit_pool=key,eval_file_in_fit=name in pool,**core.score_file(dict(file=name,labels=bank[name]['labels'],stats=bank[name]['stats']),pred,f0));rows.append(row);proofs.append(dict(option_id=identity,fit_pool=key,file=name,probability=probability.tolist(),studio_weight=studio_weight,pred=pred.tolist(),f0=[float(v) if np.isfinite(v) else None for v in f0],mode=mode.tolist()))
                if identity=='soft_gate_C1':gate_rows.append(dict(fit_pool=key,file=name,eval_file_in_fit=name in pool,actual_domain=TRAIN_DOMAIN[name],studio_weight=studio_weight,predicted_domain='studio' if studio_weight>=.5 else 'phone',fallback_missing_domain=assets['fallback_missing_domain']))
    prior=pd.read_csv(WORK/'H76_decode/run_train/all_train_metrics.csv',float_precision='round_trip');rows += prior[prior.option_id.isin(['energy07','bridge10_edge25'])].fillna({'fit_pool':''}).replace({'option_id':{'bridge10_edge25':'pooled_C1'}}).to_dict('records')
    def score(name,identity,pool):return next(r for r in rows if r['file']==name and r['option_id']==identity and r['fit_pool']==('' if identity=='energy07' else '|'.join(sorted(pool))))
    inner=[];selections=[]
    for held in ['final']+names:
        pool=[n for n in names if n!=held];records=[]
        for name in pool:
            for identity in OPTIONS:
                row=score(name,identity,[n for n in pool if n!=name]);records.append(row);inner.append(dict(outer_held=held,inner_held=name,**row))
        selections.append(dict(outer_held=held,selection_files=pool,option_id=choose(records)))
    selected={s['outer_held']:s['option_id'] for s in selections};summary=[]
    for name in names:summary += [dict(stage='full_train',**score(name,selected['final'],names)),dict(stage='selected_lofo',**score(name,selected['final'],[n for n in names if n!=name])),dict(stage='nested_diagnostic',**score(name,selected[name],[n for n in names if n!=name]))]
    audit.json_write(out/'new_models.json',new_models);audit.json_write(out/'assets.json',assets_bank);audit.json_write(out/'prediction_proofs.json',proofs);audit.json_write(out/'contexts.json',{n:context(b['x']).tolist() for n,b in bank.items()});pd.DataFrame(rows).to_csv(out/'all_train_metrics.csv',index=False);pd.DataFrame(inner).to_csv(out/'inner_traces.csv',index=False);pd.DataFrame(summary).to_csv(out/'selected_metrics.csv',index=False);pd.DataFrame(gate_rows).to_csv(out/'gate_diagnostics.csv',index=False);artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in out.iterdir()};audit.json_write(out/'final_info.json',dict(status='MEASURED',family='H78',prereg_commit=head,selections=selections,new_supervised_fits=len(new_models),reused_pooled_models=11,reused_domain_expert_roles=2,new_metric_groups=88,cached_groups=48,metric_groups=len(rows),inner_rows=len(inner),selected_summary_rows=len(summary),selected_config=selected['final'],native_inferences=0,feature_extraction_repeated=False,test_used=False,artifacts=artifacts,limitation='Gate learns domain metadata on only two to four file-context rows; low-energy context is not measured SNR; no causal proof or neural attention.'))
    print('H78 selected',selected['final'],'new fits',len(new_models),'groups',len(rows),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--action',choices=['precheck','train'],required=True);p.add_argument('--out_dir',required=True);a=p.parse_args();precheck(Path(a.out_dir).resolve()) if a.action=='precheck' else train(Path(a.out_dir).resolve())
