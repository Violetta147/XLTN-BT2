"""H76: bounded temporal decoder for cached H75 recovery, no refitting."""
import argparse,importlib.util,json,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent;WORK=HERE.parent
spec=importlib.util.spec_from_file_location('h75_cached',WORK/'H75_ml/experiment.py');previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
REPO=previous.REPO;core=previous.core;audit=previous.audit
OPTIONS=[dict(id='energy07',edge_hops=None),dict(id='raw_recovery_C1',edge_hops=None)]+[dict(id=f'bridge10_edge{h}',edge_hops=h) for h in (0,10,25)]
CONTEXT=dict(bridge_hops=10,max_anchor_ratio=1.15,max_edge_ratio=1.1,octave_factors=[.5,1.,2.],fmin=70,fmax=400,anchor='H75 C1 accepted native intersect energy07')

def decode(bank,raw_pred,raw_f0,option):
    pred=np.array(raw_pred,dtype=bool);f0=np.array(raw_f0,dtype=float);mode=np.zeros(len(pred),dtype=np.int8);anchors=np.flatnonzero(bank['control_pred']&pred&bank['native_voiced'])
    for i in np.flatnonzero(pred&~bank['native_voiced']):
        pred[i]=False;f0[i]=np.nan;position=np.searchsorted(anchors,i);left=int(anchors[position-1]) if position else None;right=int(anchors[position]) if position<len(anchors) else None
        if left is not None and right is not None and right-left<=10:
            lo,hi=float(bank['native_f0'][left]),float(bank['native_f0'][right])
            if abs(np.log(hi/lo))<=np.log(1.15):
                fraction=(i-left)/(right-left);f0[i]=np.exp((1-fraction)*np.log(lo)+fraction*np.log(hi));pred[i]=True;mode[i]=1;continue
        nearby=[a for a in (left,right) if a is not None and abs(a-i)<=option['edge_hops']]
        if not nearby or option['edge_hops']==0:continue
        anchor=min(nearby,key=lambda a:(abs(a-i),a));reference=float(bank['native_f0'][anchor]);choices=[(abs(np.log(float(bank['acf_pitch'][i])*factor/reference)),j,float(bank['acf_pitch'][i])*factor) for j,factor in enumerate((.5,1.,2.)) if 70<=float(bank['acf_pitch'][i])*factor<=400]
        if choices:
            distance,j,value=min(choices)
            if distance<=np.log(1.1):pred[i]=True;f0[i]=value;mode[i]=2
    return pred,f0,mode

def check_registry():
    r=json.loads((HERE/'REGISTRY.json').read_text());assert r['options']==OPTIONS and r['context']==CONTEXT
    for p,d in r['source_hashes'].items():assert audit.digest(REPO/p)==d,p
    for p,d in r['external_protected'].items():assert audit.digest(Path(p))==d,p
    return r

def precheck(out):
    assert not (HERE/'REGISTRY.json').exists() and not out.exists();out.mkdir()
    from verify import scalar_decode
    bank=dict(native_voiced=np.asarray([True,False,True,False,False,False,False]),native_f0=np.asarray([100,np.nan,100,np.nan,np.nan,np.nan,np.nan]),acf_pitch=np.asarray([np.nan,240,np.nan,205,80,400,70]),control_pred=np.asarray([True,False,True,False,False,False,False]));raw=np.ones(7,dtype=bool);f0=np.asarray([100,240,100,205,80,400,70],dtype=float);checks=[]
    for option in OPTIONS[2:]:
        actual=decode(bank,raw,f0,option);expected=scalar_decode(bank,raw,f0,option)
        for a,b in zip(actual,expected):assert np.allclose(a,b,equal_nan=True,atol=1e-12)
        assert actual[0].tolist()==([True,True,True,False,False,False,False] if option['edge_hops']==0 else [True,True,True,True,False,False,False]);assert abs(actual[1][1]-100)<1e-10;checks.append(dict(option_id=option['id'],bridge_verified=True,octave_edge_rejection_verified=True))
    changed={**bank,'native_f0':np.asarray([100,np.nan,200,np.nan,np.nan,np.nan,np.nan])};assert not decode(changed,raw,f0,OPTIONS[2])[0][1]
    far=dict(native_voiced=np.arange(30)==0,native_f0=np.where(np.arange(30)==0,100,np.nan),acf_pitch=np.full(30,100.),control_pred=np.arange(30)==0);assert not decode(far,np.ones(30,dtype=bool),np.full(30,100.),OPTIONS[-1])[0][-1]
    audit.json_write(out/'final_info.json',dict(status='PASS',BT2_used=False,supervised_fits=0,checks=checks,fast_anchor_change_and_max_distance_verified=True))
    old=previous.check_registry();sources=dict(old['source_hashes']);paths=[HERE/p for p in ('experiment.py','verify.py','plot.py','notes.txt','REGISTRATION.md')]+[out/'final_info.json',WORK/'H75_ml/REGISTRY.json',WORK/'H75_ml/experiment.py',WORK/'H75_ml/run_train/final_info.json',WORK/'H75_ml/run_train/verification.json']
    receipt=json.loads((WORK/'H75_ml/run_train/final_info.json').read_text());paths += [REPO/p for p in receipt['artifacts']]
    for p in paths:sources[str(p.relative_to(REPO))]=audit.digest(p)
    audit.json_write(HERE/'REGISTRY.json',dict(family='H76',rollback=previous.base.previous.old.common.matrix.commit_id(),options=OPTIONS,context=CONTEXT,source_hashes=sources,external_protected=old['external_protected'],reused_models='H75 C1, exact train pools',test_used_for_selection=False,historical_test_exposure=True))
    print('PASS H76 synthetic bridge/edge bounds; no fitting or BT2 measurement',flush=True)

def choose(rows):
    rank=[];control=[r for r in rows if r['option_id']=='energy07']
    for option in OPTIONS:
        group=[r for r in rows if r['option_id']==option['id']];valid=all(np.isfinite(r['average_mape']) for r in group) and all(np.mean([r[k] for r in group])>=np.mean([r[k] for r in control])-.01 for k in ('macro_f1','recall_v')) and sum(r['false_voiced_sil'] for r in group)<=sum(r['false_voiced_sil'] for r in control)+1;rank.append((not valid,max(r['average_mape'] for r in group) if valid else np.inf,np.mean([r['average_mape'] for r in group]) if valid else np.inf,option['id']))
    return min(rank)[-1]

def train(out):
    check_registry();assert not out.exists();git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip();branch=subprocess.check_output(git+['branch','--show-current'],cwd=REPO,text=True).strip();assert subprocess.check_output(git+['ls-remote','origin','refs/heads/'+branch],cwd=REPO,text=True).split()[0]==head and not subprocess.check_output(git+['status','--porcelain'],cwd=REPO,text=True).strip();out.mkdir()
    from verify_srh import independent_item
    bank={}
    for path in sorted(core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');saved=dict(np.load(WORK/f'H75_ml/run_train/bank_{path.stem}.npz'));assert np.array_equal(saved['times'],item['times']) and np.array_equal(saved['labels'],item['labels']);bank[path.name]={**saved,'stats':item['stats']}
    prior=pd.read_csv(WORK/'H75_ml/run_train/all_train_metrics.csv',float_precision='round_trip');rows=prior[prior.option_id.isin(['energy07','recover5_C1'])].fillna({'fit_pool':''}).replace({'option_id':{'recover5_C1':'raw_recovery_C1'}}).to_dict('records');raw=json.loads((WORK/'H75_ml/run_train/prediction_proofs.json').read_text());proofs=[]
    print('H76: change only recovered F0 decoding; three bounded context variants; cached H75 C1 model, no refit/native inference/feature extraction',flush=True)
    for proof in raw:
        if proof['option_id']!='recover5_C1':continue
        name=proof['file'];b=bank[name];original=np.asarray([np.nan if v is None else v for v in proof['f0']])
        for option in OPTIONS[2:]:
            pred,f0,mode=decode(b,proof['pred'],original,option);rows.append(dict(option_id=option['id'],fit_pool=proof['fit_pool'],eval_file_in_fit=name in proof['fit_pool'].split('|'),**core.score_file(dict(file=name,labels=b['labels'],stats=b['stats']),pred,f0)));proofs.append(dict(option_id=option['id'],fit_pool=proof['fit_pool'],file=name,pred=pred.tolist(),f0=[float(v) if np.isfinite(v) else None for v in f0],mode=mode.tolist()))
    names=sorted(bank)
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
    audit.json_write(out/'prediction_proofs.json',proofs);pd.DataFrame(rows).to_csv(out/'all_train_metrics.csv',index=False);pd.DataFrame(inner).to_csv(out/'inner_traces.csv',index=False);pd.DataFrame(summary).to_csv(out/'selected_metrics.csv',index=False);artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in out.iterdir()};audit.json_write(out/'final_info.json',dict(status='MEASURED',family='H76',prereg_commit=head,selections=selections,supervised_fits=0,native_inferences=0,feature_extraction_repeated=False,metric_groups=len(rows),new_decoder_groups=len(proofs),cached_groups=48,inner_rows=len(inner),selected_summary_rows=len(summary),selected_config=selected['final'],test_used=False,artifacts=artifacts,limitation='Offline temporal interpolation/extrapolation from estimated native anchors, not frame F0 ground truth.'))
    print('H76 selected',selected['final'],'new decoder groups',len(proofs),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--action',choices=['precheck','train'],required=True);p.add_argument('--out_dir',required=True);a=p.parse_args();precheck(Path(a.out_dir).resolve()) if a.action=='precheck' else train(Path(a.out_dir).resolve())
