import argparse
import json
import numpy as np
import pandas as pd
import markov_rejection as api
from verify_srh import independent_item,independent_score


def scalar_transitions(model,bank):
    initial=[1.,1.];counts=[[1.,1.],[1.,1.]]
    for name in model['fit_files']:
        labels=bank[name]['labels'];states=[int(v=='v') for v in labels]
        initial[states[0]]+=1
        for a,b in zip(states,states[1:]):counts[a][b]+=1
    return dict(fit_files=list(model['fit_files']),seed=model['seed'],initial_counts=initial,
                transition_counts=counts,initial=[v/sum(initial) for v in initial],
                transition=[[v/sum(row) for v in row] for row in counts])


def scalar_smooth(probability,fitted):
    p=[min(1-1e-6,max(1e-6,float(v))) for v in probability]
    emissions=[[1-v,v] for v in p];alpha=[];previous=fitted['initial']
    transition=fitted['transition']
    for i,row in enumerate(emissions):
        if i:
            previous=[sum(alpha[-1][k]*transition[k][j] for k in range(2)) for j in range(2)]
        current=[previous[j]*row[j] for j in range(2)];scale=sum(current)
        alpha.append([v/scale for v in current])
    beta=[[1.,1.] for _ in p]
    for i in range(len(p)-2,-1,-1):
        row=[sum(transition[j][k]*emissions[i+1][k]*beta[i+1][k] for k in range(2)) for j in range(2)]
        scale=sum(row);beta[i]=[v/scale for v in row]
    out=[]
    for a,b in zip(alpha,beta):
        row=[a[j]*b[j] for j in range(2)];out.append(row[1]/sum(row))
    return np.array(out)


def enumerated_smooth(probability,fitted):
    import itertools
    p=np.clip(probability,1e-6,1-1e-6);masses=np.zeros(len(p));total=0.
    for states in itertools.product((0,1),repeat=len(p)):
        weight=fitted['initial'][states[0]]
        for i,k in enumerate(states):
            weight*=p[i] if k else 1-p[i]
            if i:weight*=fitted['transition'][states[i-1]][k]
        total+=weight;masses+=weight*np.array(states)
    return masses/total


def scalar_responsibilities(x,model):
    import math
    result=[]
    for row in x:
        z=[(row[j]-model['mean'][i])/model['scale'][i] for i,j in enumerate(api.source.RECIPE['columns'])]
        logs=[]
        for k in range(3):
            value=math.log(model['weights'][k])
            for j in range(4):
                variance=model['variance'][k][j]
                value-=.5*(math.log(2*math.pi*variance)+(z[j]-model['centers'][k][j])**2/variance)
            logs.append(value)
        values=[math.exp(v-max(logs)) for v in logs];total=sum(values)
        result.append([v/total for v in values])
    return np.array(result)


def scalar_mapping(model,bank):
    mass=[0.]*3;voiced=[0.]*3
    n=min(len(bank[name]['x']) for name in model['fit_files'])
    for name in model['fit_files']:
        ix=np.round(np.linspace(0,len(bank[name]['x'])-1,n)).astype(int)
        resp=scalar_responsibilities(bank[name]['x'][ix],model)
        for row,label in zip(resp,bank[name]['labels'][ix]):
            for k in range(3):
                mass[k]+=row[k]
                if label=='v':voiced[k]+=row[k]
    return [(voiced[k]+1)/(mass[k]+2) for k in range(3)]


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
    api.check_registry();receipt=json.loads((api.OUT/f'H59_{stage}_experiment.json').read_text())
    for path,digest in receipt['artifacts'].items():assert api.audit.digest(api.REPO/path)==digest,path
    assert receipt['new_gmm_fits']==0 and receipt['new_label_mappings']==0 and receipt['new_transition_fits']==(33 if stage=='train' else 0) and receipt['new_native_calls']==0 and not receipt['test_tuning']
    assert json.loads((api.OUT/f'H56_{stage}_verification.json').read_text())['passed']
    models=json.loads((api.OUT/'H56_models.json').read_text());old=json.loads((api.OUT/f'H56_{stage}_proofs.json').read_text())
    bank=api.source.bank_train();mappings=json.loads((api.OUT/'H58_mappings.json').read_text())
    assert len(mappings)==33 and receipt['mapping_sha256']==api.audit.digest(api.OUT/'H58_mappings.json')
    for model,mapped in zip(models,mappings):
        assert mapped['fit_files']==model['fit_files'] and mapped['seed']==model['seed']
        weights=scalar_mapping(model,bank)
        assert np.allclose(weights,mapped['weights'],atol=1e-12)
    transitions=json.loads((api.OUT/'H59_transitions.json').read_text())
    assert len(transitions)==33 and receipt['transition_sha256']==api.audit.digest(api.OUT/'H59_transitions.json')
    for m,t in zip(models,transitions):assert scalar_transitions(m,bank)==t
    previous=json.loads((api.OUT/f'H58_{stage}_proofs.json').read_text())
    outputs=json.loads((api.OUT/f'H59_{stage}_proofs.json').read_text());stored=pd.read_csv(api.OUT/f'H59_{stage}_fixed.csv',float_precision='round_trip');rows=[]
    for output in outputs:
        name=output['file'];mid=output['model_id'];m=models[mid];identity=output['option_id']
        base=next(r for r in old if r['file']==name and r['model_id']==mid and r['option_id']=='hard170')
        recovered=next(r for r in old if r['file']==name and r['model_id']==mid and r['option_id']=='recovery_bound_200')
        features=bank[name] if stage=='train' else dict(np.load(api.OUT/f'H56_test_design_{api.source.Path(name).stem}.npz',allow_pickle=False))
        probability=scalar_responsibilities(features['x'],m)@np.array(mappings[mid]['weights'])
        assert np.allclose(output['unary'],probability,atol=1e-12)
        if api.BY_ID[identity]['temporal']:probability=scalar_smooth(probability,transitions[mid])
        assert np.allclose(output['prob'],probability,atol=1e-10)
        recovered=dict(recovered,prob=probability.tolist())
        pred,f0,removed=scalar_infer(base,recovered,api.BY_ID[identity])
        assert np.array_equal(pred,output['pred']) and np.allclose(f0,np.array(output['f0'],float),equal_nan=True,atol=1e-12)
        if not api.BY_ID[identity]['temporal']:
            prior=next(p for p in previous if p['file']==name and p['model_id']==mid and p['option_id']==identity)
            assert np.array_equal(pred,prior['pred']) and np.allclose(f0,np.array(prior['f0'],float),equal_nan=True,atol=1e-12)
        item,_,_=independent_item((api.core.TRAIN if stage=='train' else api.REPO/'TinHieuKiemThu')/name,stage);metrics=independent_score(item,pred,f0)
        row=stored[(stored.file==name)&(stored.model_id==mid)&(stored.option_id==identity)].iloc[0]
        assert row.seed==m['seed'] and row.fit_pool=='|'.join(m['fit_files']) and row.removed==sum(removed)
        for key,value in metrics.items():assert np.isclose(row[key],value,atol=1e-8,rtol=1e-10,equal_nan=True),key
        rows.append(dict(file=name,model_id=mid,seed=m['seed'],option_id=identity,**metrics))
    assert len(rows)==len(stored)
    assert len({(p['file'],p['model_id'],p['option_id']) for p in outputs})==len(rows)
    if stage=='train':
        assert len(rows)==360
        traces=json.loads((api.OUT/'H59_inner_traces.json').read_text());assert len(traces)==288
        for trace in traces:
            fit=trace['fit_pool'].split('|');pool=next(r['selection_files'] for r in receipt['selections'] if r['outer_held']==trace['outer_held'])
            assert trace['inner_held'] not in fit and trace['outer_held'] not in fit and set(fit)==set(pool)-{trace['inner_held']}
            r=next(r for r in rows if r['model_id']==trace['model_id'] and r['file']==trace['file'] and r['option_id']==trace['option_id'])
            for key in metrics:assert np.isclose(trace[key],r[key],atol=1e-8,equal_nan=True)
        for s in receipt['selections']:assert choose([r for r in traces if r['outer_held']==s['outer_held']])==s['option_id']
        table=pd.read_csv(api.OUT/'H59_metrics.csv',float_precision='round_trip');assert len(table)==72
        for _,r in table.iterrows():
            original=next(o for o in rows if o['model_id']==r.model_id and o['file']==r['file'] and o['option_id']==r.option_id)
            for key in metrics:assert np.isclose(r[key],original[key],atol=1e-8,equal_nan=True)
        for seed in api.SEEDS:assert api.source.matrix.base.gates(table[table.seed==seed])[1]==receipt['decisions'][str(seed)]
    else:
        freeze=json.loads((api.OUT/'H59_FROZEN_SELECTION.json').read_text());assert set(stored.option_id)==set(freeze['external_options'])
        assert freeze['mapping_sha256']==receipt['mapping_sha256'] and freeze['transition_sha256']==receipt['transition_sha256']
        assert all(models[r['model_id']]['fit_files']==sorted(bank) for r in outputs)
        assert receipt['freeze_sha256']==api.audit.digest(api.OUT/'H59_FROZEN_SELECTION.json')
    api.audit.json_write(api.OUT/f'H59_{stage}_verification.json',dict(passed=True,metric_groups=len(rows),new_gmm_fits=0,independent_scalar_mapping_and_responsibilities=True,
        scalar_removal_retained_pitch_metrics_folds_selection_checked=True,source='H56 pitch/GMM and H58 mappings; scalar fold transitions and scaled forward-backward recomputed',verifier_sha256=api.audit.digest(__file__)))
    print('PASS H59',stage,len(rows),'groups')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['train','test']);verify(p.parse_args().stage)
