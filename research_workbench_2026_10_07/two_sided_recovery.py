import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import recovery_pitch as source

HERE,OUT,REPO,core,audit=source.HERE,source.OUT,source.REPO,source.core,source.audit
SEEDS=source.SEEDS
OPTIONS=[dict(id='hard170',reject=0.)]+[dict(id=identity,reject=q) for identity,q in [('recovery_only',0.),('two_sided_010',.1),('two_sided_025',.25),('two_sided_050',.5)]]
BY_ID={o['id']:o for o in OPTIONS}


def infer(base,recovered,option):
    if option['id']=='hard170':return np.array(base['pred'],bool),np.array(base['f0'],float),np.zeros(len(base['pred']),bool)
    pred=np.array(recovered['pred'],bool);f0=np.array(recovered['f0'],float)
    removed=np.array(base['pred'],bool)&(np.array(recovered['prob'])<option['reject'])
    pred[removed]=False;f0[removed]=np.nan
    assert np.array_equal(pred,np.isfinite(f0))
    return pred,f0,removed


def choose(rows):
    ranked=[]
    for option in OPTIONS:
        allrows=[r for r in rows if r['option_id']==option['id']];valid=True
        for seed in SEEDS:
            values=[r for r in allrows if r['seed']==seed];base=[r for r in rows if r['seed']==seed and r['option_id']=='hard170']
            valid &= all(np.isfinite(r['average_mape']) for r in values)
            for key in ('macro_f1','recall_v'):valid &= np.mean([r[key] for r in values])>=np.mean([r[key] for r in base])-.01
            valid &= sum(r['false_voiced_sil'] for r in values)<=sum(r['false_voiced_sil'] for r in base)+1
        ranked.append((not valid,max(r['average_mape'] for r in allrows) if valid else np.inf,np.mean([r['average_mape'] for r in allrows]) if valid else np.inf,option['id']))
    return sorted(ranked)[0][-1]


def precheck():
    assert not (OUT/'H57_precheck.json').exists()
    from verify_two_sided_recovery import scalar_infer
    base=dict(pred=[True]*5+[False]*2,f0=[100.,110.,120.,130.,140.,None,None])
    recovered=dict(pred=[True]*7,f0=[100.,110.,120.,130.,140.,150.,160.],prob=[0.,.1,.249,.25,.5,.5,.9])
    rows=[]
    for option in OPTIONS:
        pred,f0,removed=infer(base,recovered,option);p,f,r=scalar_infer(base,recovered,option)
        assert np.array_equal(pred,p) and np.allclose(f0,f,equal_nan=True) and np.array_equal(removed,r)
        if option['id']!='hard170':
            assert np.all(pred[5:]) and np.array_equal(f0[~removed],np.array(recovered['f0'])[~removed])
            assert not removed[4]
        rows.append(dict(option=option['id'],removed=int(sum(removed)),count=int(sum(pred))))
    assert [r['removed'] for r in rows]==[0,0,1,3,4]
    audit.json_write(OUT/'H57_precheck.json',dict(passed=True,exact_threshold_ties_preserved=True,only_original_voiced_removed=True,kept_pitch_unchanged=True,cases=rows))
    print('PASS H57 synthetic decision, threshold tie, recovery and retained-pitch checks')


def register():
    assert not (HERE/'H57_REGISTRY.json').exists()
    paths=[Path(__file__),HERE/'verify_two_sided_recovery.py',HERE/'H57_REGISTRATION.md',OUT/'H57_precheck.json',Path(source.__file__),Path(core.__file__),HERE/'verify_srh.py',HERE/'verify_yaapt_extension_v2.py',HERE/'yaapt_extension.py',OUT/'H56_models.json']
    for stage in ('train','test'):paths += [OUT/f'H56_{stage}_proofs.json',OUT/f'H56_{stage}_verification.json',OUT/f'H56_{stage}_experiment.json']
    for folder in (core.TRAIN,REPO/'TinHieuKiemThu',core.TRAIN_GT,core.HERE/'test_3gt'):paths+=list(folder.glob('*.wav'))+list(folder.glob('*.lab'))
    paths += [core.RESULTS/'frozen_config.json']
    audit.json_write(HERE/'H57_REGISTRY.json',dict(rollback_commit=source.matrix.commit_id(),seeds=SEEDS,options=OPTIONS,new_model_fits=0,
        hashes={str(p.relative_to(REPO)):audit.digest(p) for p in paths}))


def check_registry():
    registry=json.loads((HERE/'H57_REGISTRY.json').read_text());assert registry['options']==OPTIONS and registry['seeds']==SEEDS
    for path,digest in registry['hashes'].items():assert audit.digest(REPO/path)==digest,path


def run(stage):
    check_registry();assert not (OUT/f'H57_{stage}_experiment.json').exists()
    assert json.loads((OUT/'H57_precheck.json').read_text())['passed']
    models=json.loads((OUT/'H56_models.json').read_text());old=json.loads((OUT/f'H56_{stage}_proofs.json').read_text())
    options=OPTIONS
    if stage=='test':
        assert json.loads((OUT/'H57_train_verification.json').read_text())['passed']
        freeze=json.loads((OUT/'H57_FROZEN_SELECTION.json').read_text());options=[BY_ID[k] for k in freeze['external_options']]
    rows=[];proofs=[];items={};outputs=[]
    for recovered in old:
        if recovered['option_id']!='recovery_bound_200':continue
        name=recovered['file'];mid=recovered['model_id'];m=models[mid]
        base=next(p for p in old if p['file']==name and p['model_id']==mid and p['option_id']=='hard170')
        if name not in items:items[name]=core.frame_features((core.TRAIN if stage=='train' else REPO/'TinHieuKiemThu')/name,split=stage)
        for option in options:
            pred,f0,removed=infer(base,recovered,option)
            rows.append(dict(model_id=mid,fit_pool='|'.join(m['fit_files']),seed=m['seed'],option_id=option['id'],removed=int(sum(removed)),**core.score_file(items[name],pred,f0)))
            proofs.append(dict(file=name,model_id=mid,option_id=option['id'],pred=pred.tolist(),f0=[float(v) if np.isfinite(v) else None for v in f0]))
    for filename,value in [(f'H57_{stage}_proofs.json',proofs)]:
        output=OUT/filename;audit.json_write(output,value);outputs.append(output)
    output=OUT/f'H57_{stage}_fixed.csv';pd.DataFrame(rows).to_csv(output,index=False);outputs.append(output)
    receipt=dict(measured_commit=source.matrix.commit_id(),new_model_fits=0,new_native_calls=0,reused_models='H56 gmm_PEZS 33 fit pools/3seeds',test_tuning=False,historical_test_exposure=True,
        runtime=json.loads((OUT/'H56_train_experiment.json').read_text())['runtime'])
    if stage=='train':
        assert len(rows)==300
        names=sorted(items);traces=[];selections=[]
        for outer in ['final']+names:
            pool=[n for n in names if n!=outer];group=[]
            for inner in pool:
                fit='|'.join(n for n in pool if n!=inner)
                selected=[r for r in rows if r['file']==inner and r['fit_pool']==fit];group+=selected
                traces += [dict(outer_held=outer,inner_held=inner,**r) for r in selected]
            selections.append(dict(outer_held=outer,selection_files=pool,option_id=choose(group)))
        chosen={s['outer_held']:s['option_id'] for s in selections};metrics=[]
        for split in ('train','lofo','nested'):
            for name in names:
                fit='|'.join(names if split=='train' else [n for n in names if n!=name])
                for model,identity in [('accepted','hard170'),('candidate',chosen[name] if split=='nested' else chosen['final'])]:
                    metrics += [dict(split=split,model=model,**r) for r in rows if r['file']==name and r['fit_pool']==fit and r['option_id']==identity]
        decisions={seed:source.matrix.base.gates(pd.DataFrame([r for r in metrics if r['seed']==seed]))[1] for seed in SEEDS}
        receipt.update(selections=selections,decisions=decisions)
        for filename,value in [('H57_inner_traces.json',traces),('H57_FROZEN_SELECTION.json',dict(option=BY_ID[chosen['final']],seeds=SEEDS,
            external_options=list(dict.fromkeys(['hard170',chosen['final'],'recovery_only','two_sided_025'])),no_test_selection=True))]:
            output=OUT/filename;audit.json_write(output,value);outputs.append(output)
        output=OUT/'H57_metrics.csv';pd.DataFrame(metrics).to_csv(output,index=False);outputs.append(output)
        print(json.dumps(dict(selections=selections,decisions=decisions),indent=2))
    else:receipt['freeze_sha256']=audit.digest(OUT/'H57_FROZEN_SELECTION.json')
    receipt['artifacts']={str(p.relative_to(REPO)):audit.digest(p) for p in outputs};audit.json_write(OUT/f'H57_{stage}_experiment.json',receipt)
    print('H57 measured',stage,len(rows),'groups')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['precheck','register','train','test']);arg=p.parse_args().action
    {'precheck':precheck,'register':register,'train':lambda:run('train'),'test':lambda:run('test')}[arg]()
