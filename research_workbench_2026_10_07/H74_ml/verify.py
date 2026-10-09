"""Independent scalar tree routing, bootstrap class totals and metric checks."""
import json,math,sys
from pathlib import Path
import numpy as np
import pandas as pd
import experiment as api

def scalar_probability(x,model):
    answer=[]
    for row in np.asarray(x,dtype=np.float32):
        probs=[]
        for tree in model['trees']:
            node=0
            while tree['left'][node]>=0:node=tree['left'][node] if float(row[tree['feature'][node]])<=tree['threshold'][node] else tree['right'][node]
            probs.append(tree['probability'][node][1])
        answer.append(math.fsum(probs)/len(probs))
    return np.asarray(answer)

def certificate(x,y,w,model):
    assert model['training_rows']==len(y) and len(model['trees'])==api.PARAMETERS['n_estimators'];x=np.asarray(x,dtype=np.float32);checked_nodes=0
    seeds=np.random.RandomState(api.PARAMETERS['random_state']).randint(np.iinfo(np.int32).max,size=len(model['trees']));assert [t['seed'] for t in model['trees']]==seeds.tolist()
    for tree in model['trees']:
        samples=np.random.RandomState(tree['seed']).randint(0,len(y),len(y),dtype=np.int32);counts=np.bincount(samples,minlength=len(y));weighted=w*counts;paths=[[] for _ in tree['left']]
        for i,row in enumerate(x):
            if not counts[i]:continue
            node=0
            while True:
                paths[node].append(i)
                if tree['left'][node]<0:break
                node=tree['left'][node] if float(row[tree['feature'][node]])<=tree['threshold'][node] else tree['right'][node]
        assert tree['max_depth']<=model['depth']
        for node,indices in enumerate(paths):
            total=math.fsum(float(weighted[i]) for i in indices);assert total>0 and len(indices)==tree['distinct_samples'][node];assert np.isclose(total,tree['weighted_samples'][node],atol=1e-9,rtol=1e-10)
            prob=[math.fsum(float(weighted[i]) for i in indices if y[i]==label)/total for label in (0,1)];assert np.allclose(prob,tree['probability'][node],atol=1e-10,rtol=1e-10);checked_nodes+=1
    assert np.allclose(scalar_probability(x,model),api.response(x,model),atol=1e-12,rtol=1e-12)
    return dict(rows=len(y),trees=len(model['trees']),nodes=checked_nodes,bootstrap_weighted_class_totals=True,scalar_routing=True)

def verify(out):
    api.check_registry();receipt=json.loads((out/'final_info.json').read_text())
    for p,d in receipt['artifacts'].items():assert api.audit.digest(api.REPO/p)==d,p
    from verify_srh import independent_item,independent_score
    bank={};names=[]
    for path in sorted(api.core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');b=dict(np.load(api.WORK/f'H73_ml/run_train/bank_{path.stem}.npz'));assert np.array_equal(b['times'],item['times']) and np.array_equal(b['labels'],item['labels']);bank[path.name]={**b,'stats':item['stats']};names.append(path.name)
    models=json.loads((out/'models.json').read_text());table=pd.read_csv(out/'all_train_metrics.csv',float_precision='round_trip');proofs=json.loads((out/'prediction_proofs.json').read_text());checks=[]
    for model in models:
        pool=model['fit_files'];assert pool==sorted(pool) and set(pool)<=set(names) and model['parameters']==api.PARAMETERS;xs=[];ys=[];weights=[];counts={n:int(bank[n]['native_voiced'].sum()) for n in pool};total=sum(counts.values())
        for name in pool:
            indices=np.flatnonzero(bank[name]['native_voiced']);xs.extend(bank[name]['x'][indices]);ys.extend((bank[name]['labels'][indices]=='v').astype(int));weights.extend([total/(len(pool)*counts[name])]*len(indices))
        checks.append(certificate(np.asarray(xs),np.asarray(ys),np.asarray(weights),model))
        for name in names:
            probability=scalar_probability(bank[name]['x'],model);pred=bank[name]['native_voiced']&(probability>=.5);f0=np.where(pred,bank[name]['native_f0'],np.nan);proof=next(p for p in proofs if p['option_id']==model['option_id'] and p['fit_pool']=='|'.join(pool) and p['file']==name);assert np.allclose(probability,proof['probability'],atol=1e-12,rtol=1e-12) and np.array_equal(pred,proof['pred']) and np.allclose(f0,np.array([np.nan if v is None else v for v in proof['f0']]),equal_nan=True,atol=0,rtol=0)
            metrics=independent_score(dict(file=name,labels=bank[name]['labels'],stats=bank[name]['stats']),pred,f0);row=table[(table.file==name)&(table.option_id==model['option_id'])&(table.fit_pool=='|'.join(pool))].iloc[0];assert bool(row.eval_file_in_fit)==(name in pool)
            for k,v in metrics.items():assert np.isclose(v,row[k],atol=1e-9,rtol=1e-9,equal_nan=True),(name,k)
    prior=pd.read_csv(api.WORK/'H73_ml/run_train/all_train_metrics.csv',float_precision='round_trip')
    for name in names:
        a=table[(table.file==name)&(table.option_id=='energy07')].iloc[0];b=prior[(prior.file==name)&(prior.option_id=='energy07')].iloc[0]
        for k in table.select_dtypes(include='number').columns:assert a[k]==b[k]
    numeric=table.select_dtypes(include='number').columns;inner=pd.read_csv(out/'inner_traces.csv',float_precision='round_trip',keep_default_na=False,na_values={k:[''] for k in numeric});selections=[]
    for held in ['final']+names:
        group=inner[inner.outer_held==held];pool=[n for n in names if n!=held];assert len(group)==len(pool)*len(api.OPTIONS)
        for _,row in group.iterrows():
            assert row['file']==row.inner_held and (not row.fit_pool or set(row.fit_pool.split('|'))==set(pool)-{row['file']}) and not row.eval_file_in_fit
            source=table[(table.file==row['file'])&(table.option_id==row.option_id)&(table.fit_pool.fillna('')==row.fit_pool)].iloc[0]
            for k in numeric:assert np.isclose(row[k],source[k],atol=1e-12,rtol=1e-12,equal_nan=True)
        records=group.to_dict('records');control=[a for a in records if a['option_id']=='energy07'];rank=[]
        for option in api.OPTIONS:
            rows=[a for a in records if a['option_id']==option['id']];valid=all(math.isfinite(a['average_mape']) for a in rows) and all(sum(a[k] for a in rows)/len(rows)>=sum(a[k] for a in control)/len(control)-.01 for k in ('macro_f1','recall_v')) and sum(a['false_voiced_sil'] for a in rows)<=sum(a['false_voiced_sil'] for a in control)+1;rank.append((not valid,max(a['average_mape'] for a in rows) if valid else math.inf,sum(a['average_mape'] for a in rows)/len(rows) if valid else math.inf,option['id']))
        selections.append(dict(outer_held=held,selection_files=pool,option_id=min(rank)[-1]))
    assert selections==receipt['selections'] and len(models)==33 and len(table)==136 and len(inner)==64
    summary=pd.read_csv(out/'selected_metrics.csv',float_precision='round_trip',keep_default_na=False);assert len(summary)==12;chosen={s['outer_held']:s['option_id'] for s in selections}
    for _,row in summary.iterrows():
        name=row['file'];option=chosen[name if row.stage=='nested_diagnostic' else 'final'];pool=names if row.stage=='full_train' else [n for n in names if n!=name];key='' if option=='energy07' else '|'.join(pool);assert row.option_id==option and row.fit_pool==key;source=table[(table.file==name)&(table.option_id==option)&(table.fit_pool.fillna('')==key)].iloc[0]
        for k in numeric:assert np.isclose(row[k],source[k],atol=1e-12,rtol=1e-12,equal_nan=True)
    api.audit.json_write(out/'verification.json',dict(status='PASS',supervised_fits=len(checks),trees=sum(c['trees'] for c in checks),nodes=sum(c['nodes'] for c in checks),checks=checks,source_inputs_masks_pitch_metrics=True,bootstrap_seeds_weighted_node_classes=True,fit_pool_independence=True,control_parity_selection_copies=True,limitation='Tree split optimization not independently refitted; synthetic and direct node-count checks verify prediction representation, not generalization.'))
    print('PASS H74',len(checks),'forests, weighted bootstrap nodes, predictions and train metrics',flush=True)

if __name__=='__main__':verify(Path(sys.argv[1]).resolve())
