import argparse
import json
import numpy as np
import pandas as pd
import two_sided_recovery as api
from verify_srh import independent_item,independent_score


def scalar_infer(base,recovered,option):
    pred=[];pitch=[];removed=[]
    for b,bf,v,f,p in zip(base['pred'],base['f0'],recovered['pred'],recovered['f0'],recovered['prob']):
        if option['id']=='hard170':pred.append(b);pitch.append(np.nan if bf is None else bf);removed.append(False)
        else:
            reject=b and p<option['reject'];removed.append(reject);pred.append(v and not reject);pitch.append(np.nan if reject or f is None else f)
    return np.array(pred,bool),np.array(pitch,float),np.array(removed,bool)


def choose(rows):
    ranks=[]
    for identity in api.BY_ID:
        group=[r for r in rows if r['option_id']==identity];valid=True
        for seed in api.SEEDS:
            g=[r for r in group if r['seed']==seed];b=[r for r in rows if r['seed']==seed and r['option_id']=='hard170']
            valid &= all(np.isfinite(r['average_mape']) for r in g)
            for key in ('macro_f1','recall_v'):valid &= sum(r[key] for r in g)/len(g)>=sum(r[key] for r in b)/len(b)-.01
            valid &= sum(r['false_voiced_sil'] for r in g)<=sum(r['false_voiced_sil'] for r in b)+1
        ranks.append((not valid,max(r['average_mape'] for r in group) if valid else np.inf,sum(r['average_mape'] for r in group)/len(group) if valid else np.inf,identity))
    return sorted(ranks)[0][-1]


def verify(stage):
    api.check_registry();receipt=json.loads((api.OUT/f'H57_{stage}_experiment.json').read_text())
    for path,digest in receipt['artifacts'].items():assert api.audit.digest(api.REPO/path)==digest,path
    assert receipt['new_model_fits']==0 and receipt['new_native_calls']==0 and not receipt['test_tuning']
    assert json.loads((api.OUT/f'H56_{stage}_verification.json').read_text())['passed']
    models=json.loads((api.OUT/'H56_models.json').read_text());old=json.loads((api.OUT/f'H56_{stage}_proofs.json').read_text())
    outputs=json.loads((api.OUT/f'H57_{stage}_proofs.json').read_text());stored=pd.read_csv(api.OUT/f'H57_{stage}_fixed.csv',float_precision='round_trip');rows=[]
    for output in outputs:
        name=output['file'];mid=output['model_id'];m=models[mid];identity=output['option_id']
        base=next(r for r in old if r['file']==name and r['model_id']==mid and r['option_id']=='hard170')
        recovered=next(r for r in old if r['file']==name and r['model_id']==mid and r['option_id']=='recovery_bound_200')
        pred,f0,removed=scalar_infer(base,recovered,api.BY_ID[identity])
        assert np.array_equal(pred,output['pred']) and np.allclose(f0,np.array(output['f0'],float),equal_nan=True,atol=1e-12)
        item,_,_=independent_item((api.core.TRAIN if stage=='train' else api.REPO/'TinHieuKiemThu')/name,stage);metrics=independent_score(item,pred,f0)
        row=stored[(stored.file==name)&(stored.model_id==mid)&(stored.option_id==identity)].iloc[0]
        assert row.seed==m['seed'] and row.fit_pool=='|'.join(m['fit_files']) and row.removed==sum(removed)
        for key,value in metrics.items():assert np.isclose(row[key],value,atol=1e-8,rtol=1e-10,equal_nan=True),key
        rows.append(dict(file=name,model_id=mid,seed=m['seed'],option_id=identity,**metrics))
    assert len(rows)==len(stored)
    if stage=='train':
        assert len(rows)==300
        traces=json.loads((api.OUT/'H57_inner_traces.json').read_text());assert len(traces)==240
        for trace in traces:
            fit=trace['fit_pool'].split('|');pool=next(r['selection_files'] for r in receipt['selections'] if r['outer_held']==trace['outer_held'])
            assert trace['inner_held'] not in fit and trace['outer_held'] not in fit and set(fit)==set(pool)-{trace['inner_held']}
            r=next(r for r in rows if r['model_id']==trace['model_id'] and r['file']==trace['file'] and r['option_id']==trace['option_id'])
            for key in metrics:assert np.isclose(trace[key],r[key],atol=1e-8,equal_nan=True)
        for s in receipt['selections']:assert choose([r for r in traces if r['outer_held']==s['outer_held']])==s['option_id']
        table=pd.read_csv(api.OUT/'H57_metrics.csv',float_precision='round_trip');assert len(table)==72
        for _,r in table.iterrows():
            original=next(o for o in rows if o['model_id']==r.model_id and o['file']==r['file'] and o['option_id']==r.option_id)
            for key in metrics:assert np.isclose(r[key],original[key],atol=1e-8,equal_nan=True)
        for seed in api.SEEDS:assert api.source.matrix.base.gates(table[table.seed==seed])[1]==receipt['decisions'][str(seed)]
    else:
        freeze=json.loads((api.OUT/'H57_FROZEN_SELECTION.json').read_text());assert set(stored.option_id)==set(freeze['external_options'])
        assert receipt['freeze_sha256']==api.audit.digest(api.OUT/'H57_FROZEN_SELECTION.json')
    api.audit.json_write(api.OUT/f'H57_{stage}_verification.json',dict(passed=True,metric_groups=len(rows),new_model_fits=0,
        scalar_removal_retained_pitch_metrics_folds_selection_checked=True,source='H56 verified GMM posterior and anchored pitch',verifier_sha256=api.audit.digest(__file__)))
    print('PASS H57',stage,len(rows),'groups')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['train','test']);verify(p.parse_args().stage)
