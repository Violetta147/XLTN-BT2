"""Independent audio context, weighted model certificates and soft routing."""
import importlib.util,json,math,sys
from pathlib import Path
import numpy as np
import pandas as pd
import experiment as api

def quantile(values,p):
    a=sorted(map(float,values));where=(len(a)-1)*p;lo=int(math.floor(where));hi=int(math.ceil(where));return a[lo]+(where-lo)*(a[hi]-a[lo])

def independent_context(x):
    q=quantile(x[:,1],.2);high=[float(row[3]) for row in x if float(row[1])<=q];return np.asarray([q,quantile(high,.5)])

def independent_augment(x,c):return np.asarray([[*map(float,row),*map(float,c),*[float(v)*float(w) for v in row for w in c]] for row in x])

def probability(x,m):
    z=(x[:,m['columns']]-m['mean'])/m['scale'];logits=z@np.asarray(m['coefficient'])+m['intercept'];return np.asarray([1/(1+math.exp(-float(t))) if t>=0 else math.exp(float(t))/(1+math.exp(float(t))) for t in logits])

def independent_probabilities(bank,identity,assets):
    c=independent_context(bank['x'])
    if identity=='contextual_C1':return probability(independent_augment(bank['x'],c),assets['contextual']),None
    if assets['gate'] is None:return probability(bank['x'],assets['pooled']),.5
    g=float(probability(c[None,:],assets['gate'])[0]);phone=probability(bank['x'],assets['phone']);studio=probability(bank['x'],assets['studio']);return np.asarray([(1-g)*a+g*b for a,b in zip(phone,studio)]),g

def certificate(x,y,w,m):
    assert m['training_rows']==len(y) and m['C']==1.;data=x[:,m['columns']];total=math.fsum(map(float,w));mean=np.asarray([math.fsum(float(a)*float(b) for a,b in zip(data[:,j],w))/total for j in range(data.shape[1])]);var=np.asarray([math.fsum(float(b)*(float(a)-mean[j])**2 for a,b in zip(data[:,j],w))/total for j in range(data.shape[1])]);eps=np.finfo(float).eps;constant=var<=total*eps*var+(total*mean*eps)**2;scale=np.where(constant,1.,np.sqrt(var));assert np.allclose(mean,m['mean'],atol=1e-9,rtol=1e-10) and np.allclose(var,m['variance'],atol=1e-9,rtol=1e-10) and np.allclose(scale,m['scale'],atol=1e-9,rtol=1e-10)
    z=(data-mean)/scale;b=np.asarray(m['coefficient']);pred=probability(x,m);res=w*(pred-y);gradient=np.r_[z.T@res+b/m['C'],math.fsum(map(float,res))]/total;assert max(abs(gradient))<1e-6,max(abs(gradient));return dict(rows=len(y),features=data.shape[1],weighted_scaler=True,max_normalized_gradient=float(max(abs(gradient))))

def verify(out):
    api.check_registry();r=json.loads((out/'final_info.json').read_text())
    for path,d in r['artifacts'].items():assert api.audit.digest(api.REPO/path)==d,path
    from verify_srh import independent_item,independent_score
    spec=importlib.util.spec_from_file_location('h76_scalar',api.WORK/'H76_decode/verify.py');decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder);bank={};names=[];contexts=json.loads((out/'contexts.json').read_text())
    for path in sorted(api.core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');b=dict(np.load(api.WORK/f'H75_ml/run_train/bank_{path.stem}.npz'));assert np.array_equal(item['labels'],b['labels']) and np.array_equal(item['times'],b['times']);bank[path.name]={**b,'stats':item['stats']};names.append(path.name);assert np.allclose(contexts[path.name],independent_context(b['x']),atol=1e-12)
    models=json.loads((out/'new_models.json').read_text());assets=json.loads((out/'assets.json').read_text());checks=[]
    for m in models:
        pool=m['fit_files'];assert set(pool)<=set(names) and pool==sorted(pool)
        if m['role']=='gate':
            assert {api.TRAIN_DOMAIN[n] for n in pool}=={'phone','studio'};x=np.asarray([independent_context(bank[n]['x']) for n in pool]);y=np.asarray([int(api.TRAIN_DOMAIN[n]=='studio') for n in pool]);w=np.ones(len(pool))
        else:
            xs=[];ys=[];weights=[];counts={n:int(sum(bank[n]['native_voiced']|np.isfinite(bank[n]['acf_pitch']))) for n in pool};total=sum(counts.values())
            for n in pool:
                mask=bank[n]['native_voiced']|np.isfinite(bank[n]['acf_pitch']);xx=independent_augment(bank[n]['x'],independent_context(bank[n]['x'])) if m['role']=='contextual' else bank[n]['x'];xs.extend(xx[mask]);ys.extend((bank[n]['labels'][mask]=='v').astype(int));weights.extend([total/(len(pool)*counts[n])]*counts[n])
            x,y,w=np.asarray(xs),np.asarray(ys),np.asarray(weights)
        checks.append(certificate(x,y,w,m))
    cached=json.loads((api.WORK/'H75_ml/run_train/models.json').read_text());table=pd.read_csv(out/'all_train_metrics.csv',float_precision='round_trip');proofs=json.loads((out/'prediction_proofs.json').read_text());count=0
    for a in assets:
        pool=a['fit_files'];pooled=next(m for m in cached if m['option_id']=='recover5_C1' and m['fit_files']==pool);assert a['pooled']==pooled and a['contextual'] in models
        if a['gate'] is None:assert len({api.TRAIN_DOMAIN[n] for n in pool})==1 and a['fallback_missing_domain']
        else:
            assert a['gate'] in models and a['gate']['fit_files']==pool and not a['fallback_missing_domain']
            for domain in ('phone','studio'):
                sub=[n for n in pool if api.TRAIN_DOMAIN[n]==domain];assert a[domain]['fit_files']==sub
                if len(sub)==1:assert a[domain] in models and a[domain]['role']=='single_expert'
                else:assert a[domain]==next(m for m in cached if m['option_id']=='recover5_C1' and m['fit_files']==sub)
        for identity in api.OPTIONS[2:]:
            for n in names:
                b=bank[n];prob,g=independent_probabilities(b,identity,a);raw=np.asarray([float(p)>=.5 and float(row[1])>=math.log(.07) and (bool(native) or (float(row[0])>=.6 and math.isfinite(float(pitch)))) for p,row,native,pitch in zip(prob,b['x'],b['native_voiced'],b['acf_pitch'])]);rf=np.asarray([float(nf) if p and nv else float(acf) if p else math.nan for p,nv,nf,acf in zip(raw,b['native_voiced'],b['native_f0'],b['acf_pitch'])]);pred,f0,mode=decoder.scalar_decode(b,raw,rf,dict(edge_hops=25));proof=next(p for p in proofs if p['option_id']==identity and p['fit_pool']=='|'.join(pool) and p['file']==n);assert np.allclose(prob,proof['probability'],atol=1e-12) and (g is None and proof['studio_weight'] is None or g is not None and abs(g-proof['studio_weight'])<1e-12);assert np.array_equal(pred,proof['pred']) and np.array_equal(mode,proof['mode']) and np.allclose(f0,np.asarray([np.nan if v is None else v for v in proof['f0']]),atol=1e-8,rtol=1e-10,equal_nan=True)
                metrics=independent_score(dict(file=n,labels=b['labels'],stats=b['stats']),pred,f0);row=table[(table.file==n)&(table.option_id==identity)&(table.fit_pool=='|'.join(pool))].iloc[0];assert bool(row.eval_file_in_fit)==(n in pool)
                for k,v in metrics.items():assert np.isclose(row[k],v,atol=1e-8,rtol=1e-9,equal_nan=True),(n,k)
                count+=1
    numeric=table.select_dtypes(include='number').columns;old=pd.read_csv(api.WORK/'H76_decode/run_train/all_train_metrics.csv',float_precision='round_trip')
    for _,row in table[table.option_id.isin(['energy07','pooled_C1'])].iterrows():
        identity='bridge10_edge25' if row.option_id=='pooled_C1' else 'energy07';key='' if pd.isna(row.fit_pool) else row.fit_pool;source=old[(old.file==row['file'])&(old.option_id==identity)&(old.fit_pool.fillna('')==key)].iloc[0]
        for k in numeric:assert row[k]==source[k]
    inner=pd.read_csv(out/'inner_traces.csv',float_precision='round_trip').fillna({'fit_pool':''});selections=[]
    for held in ['final']+names:
        g=inner[inner.outer_held==held];pool=[n for n in names if n!=held];assert len(g)==len(pool)*len(api.OPTIONS)
        for _,row in g.iterrows():
            assert row['file']==row.inner_held and (not row.fit_pool or set(row.fit_pool.split('|'))==set(pool)-{row['file']}) and not row.eval_file_in_fit;source=table[(table.file==row['file'])&(table.option_id==row.option_id)&(table.fit_pool.fillna('')==row.fit_pool)].iloc[0]
            for k in numeric:assert np.isclose(row[k],source[k],atol=1e-12,rtol=1e-12,equal_nan=True)
        records=g.to_dict('records');control=[x for x in records if x['option_id']=='energy07'];rank=[]
        for identity in api.OPTIONS:
            rows=[x for x in records if x['option_id']==identity];valid=all(math.isfinite(x['average_mape']) for x in rows) and all(sum(x[k] for x in rows)/len(rows)>=sum(x[k] for x in control)/len(control)-.01 for k in ('macro_f1','recall_v')) and sum(x['false_voiced_sil'] for x in rows)<=sum(x['false_voiced_sil'] for x in control)+1;rank.append((not valid,max(x['average_mape'] for x in rows) if valid else math.inf,sum(x['average_mape'] for x in rows)/len(rows) if valid else math.inf,identity))
        selections.append(dict(outer_held=held,selection_files=pool,option_id=min(rank)[-1]))
    assert selections==r['selections'] and len(models)==24 and count==88 and len(table)==136 and len(inner)==64;summary=pd.read_csv(out/'selected_metrics.csv',float_precision='round_trip').fillna({'fit_pool':''});assert len(summary)==12;chosen={s['outer_held']:s['option_id'] for s in selections}
    for _,row in summary.iterrows():
        n=row['file'];identity=chosen[n if row.stage=='nested_diagnostic' else 'final'];pool=names if row.stage=='full_train' else [x for x in names if x!=n];key='' if identity=='energy07' else '|'.join(pool);assert row.option_id==identity and row.fit_pool==key;source=table[(table.file==n)&(table.option_id==identity)&(table.fit_pool.fillna('')==key)].iloc[0]
        for k in numeric:assert np.isclose(row[k],source[k],atol=1e-12,rtol=1e-12,equal_nan=True)
    diagnostics=pd.read_csv(out/'gate_diagnostics.csv',float_precision='round_trip');assert len(diagnostics)==44
    for _,row in diagnostics.iterrows():
        a=next(x for x in assets if '|'.join(x['fit_files'])==row.fit_pool);g=independent_probabilities(bank[row['file']],'soft_gate_C1',a)[1];assert abs(g-row.studio_weight)<1e-12 and row.actual_domain==api.TRAIN_DOMAIN[row['file']] and row.predicted_domain==('studio' if g>=.5 else 'phone')
    api.audit.json_write(out/'verification.json',dict(status='PASS',new_supervised_fits=len(models),checks=checks,new_metric_groups=count,cached_groups=48,independent_context_scaler_gradient_soft_mixture_decoder_metrics=True,fit_pool_domain_metadata_train_only=True,selection_copy_parity_hashes=True,limitation='Domain accuracy from four files is not causal evidence; no neural attention or end-to-end mixture-of-experts training.'))
    print('PASS H78 24 new models, context/gating, 88 new and 48 cached groups',flush=True)

if __name__=='__main__':verify(Path(sys.argv[1]).resolve())
