"""Independent weighted scaler, logistic gradient, predictions, pools and metrics."""
import json,math,sys
from pathlib import Path
import numpy as np
import pandas as pd
import experiment as api

def certificate(x,y,w,m):
    assert m['training_rows']==len(y)
    columns=m['columns'];data=x[:,columns];total=math.fsum(map(float,w));means=np.array([math.fsum(float(v)*float(q) for v,q in zip(data[:,j],w))/total for j in range(len(columns))]);variances=np.array([math.fsum(float(q)*(float(v)-means[j])**2 for v,q in zip(data[:,j],w))/total for j in range(len(columns))]);scale=np.sqrt(variances);scale=np.where(scale>0,scale,1.)
    assert np.allclose(means,m['mean'],atol=1e-10) and np.allclose(variances,m['variance'],atol=1e-10) and np.allclose(scale,m['scale'],atol=1e-10)
    z=(data-means)/scale;b=np.array(m['coefficient']);logit=z@b+m['intercept'];prob=np.array([1/(1+math.exp(-float(t))) if t>=0 else math.exp(float(t))/(1+math.exp(float(t))) for t in logit]);res=w*(prob-y);gradient=np.r_[z.T@res+b/m['C'],sum(res)]/total;assert max(abs(gradient))<1e-6,max(abs(gradient))
    return dict(rows=len(y),features=len(columns),weighted_scaler_verified=True,max_normalized_gradient=float(max(abs(gradient))))

def verify(out):
    api.check_registry();r=json.loads((out/'final_info.json').read_text())
    for p,d in r['artifacts'].items():assert api.audit.digest(api.REPO/p)==d,p
    from verify_srh import independent_item,independent_score
    bank={};names=[]
    for path in sorted(api.core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');saved=dict(np.load(out/f'bank_{path.stem}.npz'));raw=dict(np.load(api.WORK/f'results/H50_design_{path.stem}.npz'));native=dict(np.load(api.WORK/f'results/H69_native_{path.stem}_pyin25_beta2_8.npz'));assert np.array_equal(saved['acf_pitch'],raw['pitch'],equal_nan=True) and np.array_equal(saved['x'][:,:4],raw['x'][:,:4]) and np.array_equal(saved['x'][:,4],native['probability']) and np.array_equal(saved['labels'],item['labels']) and np.array_equal(saved['times'],item['times']);bank[path.name]={**saved,'stats':item['stats']};names.append(path.name)
    models=json.loads((out/'models.json').read_text());table=pd.read_csv(out/'all_train_metrics.csv',float_precision='round_trip');proofs=json.loads((out/'prediction_proofs.json').read_text());checks=[]
    for model in models:
        pool=model['fit_files'];assert set(pool)<=set(names);xs=[];ys=[];weights=[];counts={n:int((bank[n]['native_voiced']|np.isfinite(bank[n]['acf_pitch'])).sum()) for n in pool};total=sum(counts.values())
        for name in sorted(pool):
            indices=np.flatnonzero(bank[name]['native_voiced']|np.isfinite(bank[name]['acf_pitch']));xs.extend(bank[name]['x'][indices]);ys.extend((bank[name]['labels'][indices]=='v').astype(int));weights.extend([total/(len(pool)*counts[name])]*len(indices))
        checks.append(certificate(np.asarray(xs),np.asarray(ys),np.asarray(weights),model))
        for name in names:
            z=(bank[name]['x'][:,model['columns']]-model['mean'])/model['scale'];logit=z@model['coefficient']+model['intercept'];pred=np.asarray([float(t)>=0 and float(row[1])>=math.log(.07) and (bool(native) or (float(row[0])>=.6 and math.isfinite(float(pitch)))) for t,row,native,pitch in zip(logit,bank[name]['x'],bank[name]['native_voiced'],bank[name]['acf_pitch'])]);candidate=np.asarray([float(native_f0) if native else float(pitch) for native,native_f0,pitch in zip(bank[name]['native_voiced'],bank[name]['native_f0'],bank[name]['acf_pitch'])]);f0=np.where(pred,candidate,np.nan);proof=next(p for p in proofs if p['option_id']==model['option_id'] and p['fit_pool']=='|'.join(pool) and p['file']==name);assert np.array_equal(pred,proof['pred']) and np.allclose(f0,np.array([np.nan if v is None else v for v in proof['f0']]),equal_nan=True,atol=0,rtol=0)
            metrics=independent_score(dict(file=name,labels=bank[name]['labels'],stats=bank[name]['stats']),pred,f0);row=table[(table.file==name)&(table.option_id==model['option_id'])&(table.fit_pool=='|'.join(pool))].iloc[0]
            for k,v in metrics.items():assert np.isclose(v,row[k],atol=1e-9,rtol=1e-9,equal_nan=True),(name,k)
    control=pd.read_csv(api.WORK/'results/H71_fixed.csv',float_precision='round_trip')
    for name in names:
        a=table[(table.file==name)&(table.option_id=='energy07')].iloc[0];b=control[(control.file==name)&(control.option_id=='pyin8_energy_0.07')].iloc[0]
        for k in b.index:
            if k!='option_id':assert a[k]==b[k],k
    inner=pd.read_csv(out/'inner_traces.csv',float_precision='round_trip',keep_default_na=False,na_values={k:[''] for k in table.select_dtypes(include='number').columns});selections=[]
    for held in ['final']+names:
        group=inner[inner.outer_held==held];pool=[n for n in names if n!=held];assert len(group)==len(pool)*len(api.OPTIONS)
        for _,row in group.iterrows():
            assert row['file']==row.inner_held and (not row.fit_pool or set(row.fit_pool.split('|'))==set(pool)-{row['file']}) and not row.eval_file_in_fit
            source=table[(table.file==row['file'])&(table.option_id==row.option_id)&(table.fit_pool.fillna('')==row.fit_pool)].iloc[0]
            for k in table.select_dtypes(include='number').columns:assert np.isclose(row[k],source[k],atol=1e-12,rtol=1e-12,equal_nan=True),(held,k)
        records=group.to_dict('records');rank=[];controls=[a for a in records if a['option_id']=='energy07']
        for opt in api.OPTIONS:
            rows=[a for a in records if a['option_id']==opt['id']];valid=all(math.isfinite(a['average_mape']) for a in rows) and all(sum(a[k] for a in rows)/len(rows)>=sum(a[k] for a in controls)/len(controls)-.01 for k in ('macro_f1','recall_v')) and sum(a['false_voiced_sil'] for a in rows)<=sum(a['false_voiced_sil'] for a in controls)+1;rank.append((not valid,max(a['average_mape'] for a in rows) if valid else math.inf,sum(a['average_mape'] for a in rows)/len(rows) if valid else math.inf,opt['id']))
        selections.append(dict(outer_held=held,selection_files=pool,option_id=min(rank)[-1]))
    assert selections==r['selections'] and len(models)==33 and len(table)==136 and len(inner)==64
    summary=pd.read_csv(out/'selected_metrics.csv',float_precision='round_trip',keep_default_na=False)
    assert len(summary)==12
    chosen={s['outer_held']:s['option_id'] for s in selections}
    for _,row in summary.iterrows():
        name=row['file'];option=chosen[name if row.stage=='nested_diagnostic' else 'final'];pool=names if row.stage=='full_train' else [n for n in names if n!=name];key='' if option=='energy07' else '|'.join(pool)
        assert row.option_id==option and row.fit_pool==key
        source=table[(table.file==name)&(table.option_id==option)&(table.fit_pool.fillna('')==key)].iloc[0]
        for k in table.select_dtypes(include='number').columns:assert np.isclose(row[k],source[k],atol=1e-12,rtol=1e-12,equal_nan=True),(name,k)
    api.audit.json_write(out/'verification.json',dict(status='PASS',supervised_fits=len(checks),checks=checks,weighted_scaler_logistic_gradient=True,source_cache_labels_fitpool_masks_pitch_metrics=True,selection_pool_independence=True,inner_summary_copies_verified=True,limitation='Optimizer not refitted; four files and historical exposure limit generalization; F0 ACF fallback is a candidate, not per-frame ground truth; control has historical all-train exposure.'))
    print('PASS H75',len(checks),'supervised models and train metrics')
if __name__=='__main__':verify(Path(sys.argv[1]).resolve())
