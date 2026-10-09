"""Scalar log interpolation, nearest-anchor octave checks and cached metrics."""
import json,math,sys
from pathlib import Path
import numpy as np
import pandas as pd
import experiment as api

def scalar_decode(bank,raw_pred,raw_f0,option):
    pred=list(map(bool,raw_pred));f0=list(map(float,raw_f0));modes=[0]*len(pred);anchors=[j for j in range(len(pred)) if bank['control_pred'][j] and pred[j] and bank['native_voiced'][j]]
    for i in range(len(pred)):
        if not pred[i] or bank['native_voiced'][i]:continue
        pred[i]=False;f0[i]=math.nan;left=next((a for a in reversed(anchors) if a<i),None);right=next((a for a in anchors if a>i),None)
        if left is not None and right is not None and right-left<=10:
            lo=float(bank['native_f0'][left]);hi=float(bank['native_f0'][right])
            if abs(math.log(hi/lo))<=math.log(1.15):
                t=(i-left)/(right-left);f0[i]=math.exp(math.log(lo)+t*(math.log(hi)-math.log(lo)));pred[i]=True;modes[i]=1;continue
        nearby=sorted((a for a in (left,right) if a is not None and abs(a-i)<=option['edge_hops']),key=lambda a:(abs(a-i),a))
        if not nearby or option['edge_hops']==0:continue
        reference=float(bank['native_f0'][nearby[0]]);choices=[]
        for j,factor in enumerate((.5,1.,2.)):
            value=float(bank['acf_pitch'][i])*factor
            if 70<=value<=400:choices.append((abs(math.log(value/reference)),j,value))
        if choices and min(choices)[0]<=math.log(1.1):pred[i]=True;f0[i]=min(choices)[2];modes[i]=2
    return np.asarray(pred),np.asarray(f0),np.asarray(modes)

def verify(out):
    api.check_registry();r=json.loads((out/'final_info.json').read_text())
    for path,d in r['artifacts'].items():assert api.audit.digest(api.REPO/path)==d,path
    from verify_srh import independent_item,independent_score
    bank={};names=[]
    for path in sorted(api.core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');b=dict(np.load(api.WORK/f'H75_ml/run_train/bank_{path.stem}.npz'));assert np.array_equal(item['labels'],b['labels']) and np.array_equal(item['times'],b['times']);bank[path.name]={**b,'stats':item['stats']};names.append(path.name)
    table=pd.read_csv(out/'all_train_metrics.csv',float_precision='round_trip');raw=json.loads((api.WORK/'H75_ml/run_train/prediction_proofs.json').read_text());proofs=json.loads((out/'prediction_proofs.json').read_text());checked=0
    for proof in proofs:
        parent=next(p for p in raw if p['option_id']=='recover5_C1' and p['file']==proof['file'] and p['fit_pool']==proof['fit_pool']);name=proof['file'];original=np.asarray([np.nan if v is None else v for v in parent['f0']]);option=next(o for o in api.OPTIONS if o['id']==proof['option_id']);pred,f0,mode=scalar_decode(bank[name],parent['pred'],original,option)
        assert np.array_equal(pred,proof['pred']) and np.array_equal(mode,proof['mode']) and np.allclose(f0,np.asarray([np.nan if v is None else v for v in proof['f0']]),equal_nan=True,atol=1e-9,rtol=1e-12)
        native=bank[name]['native_voiced'];assert np.array_equal(pred[native],np.asarray(parent['pred'])[native]) and np.allclose(f0[native],original[native],equal_nan=True,atol=0,rtol=0)
        metrics=independent_score(dict(file=name,labels=bank[name]['labels'],stats=bank[name]['stats']),pred,f0);row=table[(table.file==name)&(table.option_id==option['id'])&(table.fit_pool==proof['fit_pool'])].iloc[0]
        for k,v in metrics.items():assert np.isclose(v,row[k],atol=1e-8,rtol=1e-9,equal_nan=True),(name,k)
        assert bool(row.eval_file_in_fit)==(name in proof['fit_pool'].split('|'));checked+=1
    numeric=table.select_dtypes(include='number').columns;prior=pd.read_csv(api.WORK/'H75_ml/run_train/all_train_metrics.csv',float_precision='round_trip')
    for _,row in table[table.option_id.isin(['energy07','raw_recovery_C1'])].iterrows():
        old='recover5_C1' if row.option_id=='raw_recovery_C1' else 'energy07';source=prior[(prior.file==row['file'])&(prior.option_id==old)&(prior.fit_pool.fillna('')==('' if pd.isna(row.fit_pool) else row.fit_pool))].iloc[0]
        for k in numeric:assert row[k]==source[k]
    inner=pd.read_csv(out/'inner_traces.csv',float_precision='round_trip',keep_default_na=False,na_values={k:[''] for k in numeric});selections=[]
    for held in ['final']+names:
        group=inner[inner.outer_held==held];pool=[n for n in names if n!=held];assert len(group)==len(pool)*len(api.OPTIONS)
        for _,row in group.iterrows():
            assert row['file']==row.inner_held and (not row.fit_pool or set(row.fit_pool.split('|'))==set(pool)-{row['file']}) and not row.eval_file_in_fit;source=table[(table.file==row['file'])&(table.option_id==row.option_id)&(table.fit_pool.fillna('')==row.fit_pool)].iloc[0]
            for k in numeric:assert np.isclose(row[k],source[k],atol=1e-12,rtol=1e-12,equal_nan=True)
        records=group.to_dict('records');control=[a for a in records if a['option_id']=='energy07'];rank=[]
        for option in api.OPTIONS:
            rows=[a for a in records if a['option_id']==option['id']];valid=all(math.isfinite(a['average_mape']) for a in rows) and all(sum(a[k] for a in rows)/len(rows)>=sum(a[k] for a in control)/len(control)-.01 for k in ('macro_f1','recall_v')) and sum(a['false_voiced_sil'] for a in rows)<=sum(a['false_voiced_sil'] for a in control)+1;rank.append((not valid,max(a['average_mape'] for a in rows) if valid else math.inf,sum(a['average_mape'] for a in rows)/len(rows) if valid else math.inf,option['id']))
        selections.append(dict(outer_held=held,selection_files=pool,option_id=min(rank)[-1]))
    assert selections==r['selections'] and checked==132 and len(table)==180 and len(inner)==80;summary=pd.read_csv(out/'selected_metrics.csv',float_precision='round_trip',keep_default_na=False);assert len(summary)==12;chosen={s['outer_held']:s['option_id'] for s in selections}
    for _,row in summary.iterrows():
        name=row['file'];option=chosen[name if row.stage=='nested_diagnostic' else 'final'];pool=names if row.stage=='full_train' else [n for n in names if n!=name];key='' if option=='energy07' else '|'.join(pool);assert row.option_id==option and row.fit_pool==key;source=table[(table.file==name)&(table.option_id==option)&(table.fit_pool.fillna('')==key)].iloc[0]
        for k in numeric:assert np.isclose(row[k],source[k],atol=1e-12,rtol=1e-12,equal_nan=True)
    api.audit.json_write(out/'verification.json',dict(status='PASS',decoder_groups=checked,cached_groups=48,scalar_context_pitch_mask_metric=True,native_decisions_pitch_unchanged=True,fit_pool_independence=True,selection_copy_parity_hashes=True,limitation='Interpolated F0 from estimated anchors is not frame ground truth; original classifier optimizer not refitted.'))
    print('PASS H76',checked,'decoder groups and 48 cached groups',flush=True)

if __name__=='__main__':verify(Path(sys.argv[1]).resolve())
