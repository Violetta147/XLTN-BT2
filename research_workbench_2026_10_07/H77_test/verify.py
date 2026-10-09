"""Independent test features/pitch candidates, classifier, decoder and statistics."""
import importlib.util,json,math,sys
from pathlib import Path
import numpy as np
import pandas as pd
import experiment as api

def verify(out):
    api.check_registry();r=json.loads((out/'final_info.json').read_text())
    for path,d in r['artifacts'].items():assert api.audit.digest(api.REPO/path)==d,path
    from verify_srh import independent_item,independent_score
    from verify_voicing_recovery import independent_features
    spec=importlib.util.spec_from_file_location('h76_scalar',api.WORK/'H76_decode/verify.py');decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
    model=json.loads((api.HERE/'locked_model.json').read_text());table=pd.read_csv(out/'all_files.csv',float_precision='round_trip');checks=[]
    for path in sorted((api.REPO/'TinHieuKiemThu').glob('*.wav')):
        item,fs,audio=independent_item(path,'test');x,pitch=independent_features(audio,fs);b=dict(np.load(out/f'proof_{path.stem}.npz'));native=dict(np.load(api.WORK/f'results/H72_test_proof_{path.stem}.npz'));assert np.allclose(x[:,:4],b['x'][:,:4],atol=1e-8,rtol=1e-8) and np.allclose(pitch,b['acf_pitch'],atol=1e-8,rtol=1e-8,equal_nan=True);assert np.array_equal(b['x'][:,4],native['probability']) and np.array_equal(item['times'],b['times']) and np.array_equal(item['labels'],b['labels']) and np.array_equal(b['native_voiced'],native['voiced']) and np.array_equal(b['native_f0'],native['raw_f0'],equal_nan=True) and np.array_equal(b['control_pred'],native['pred'])
        logits=((b['x'][:,model['columns']]-model['mean'])/model['scale'])@model['coefficient']+model['intercept'];raw_pred=np.asarray([float(t)>=0 and float(row[1])>=math.log(.07) and (bool(n) or (float(row[0])>=.6 and math.isfinite(float(p)))) for t,row,n,p in zip(logits,b['x'],b['native_voiced'],b['acf_pitch'])]);raw_f0=np.asarray([float(nf) if pred and native else float(p) if pred else math.nan for pred,native,nf,p in zip(raw_pred,b['native_voiced'],b['native_f0'],b['acf_pitch'])]);assert np.array_equal(raw_pred,b['raw_pred']) and np.allclose(raw_f0,b['raw_f0'],atol=0,rtol=0,equal_nan=True)
        pred,f0,mode=decoder.scalar_decode(b,raw_pred,raw_f0,dict(edge_hops=25));assert np.array_equal(pred,b['pred']) and np.array_equal(mode,b['mode']) and np.allclose(f0,b['f0'],atol=1e-8,rtol=1e-10,equal_nan=True);metric=independent_score(item,pred,f0);row=table[(table.file==path.name)&(table.eval_split=='test')].iloc[0]
        for k,v in metric.items():assert np.isclose(row[k],v,atol=1e-8,rtol=1e-9,equal_nan=True),(path.name,k)
        checks.append(dict(file=path.name,frames=len(pred),features_acf25_independent=True,classifier_decoder_metric=True,recovered=int(sum(pred&~b['native_voiced'])),bridge=int(sum(mode==1)),edge=int(sum(mode==2))))
    old=pd.read_csv(api.WORK/'H76_decode/run_train/all_train_metrics.csv',float_precision='round_trip');pool='|'.join(model['fit_files'])
    for _,row in table[table.eval_split=='train'].iterrows():
        source=old[(old.file==row['file'])&(old.option_id=='bridge10_edge25')&(old.fit_pool==pool)].iloc[0]
        for k in old.select_dtypes(include='number').columns:assert row[k]==source[k]
    assert len(table)==8 and len(checks)==4;achieved=bool(np.isfinite(table.average_mape).all() and (table.average_mape<2).all());assert achieved==r['target_achieved'];api.audit.json_write(out/'verification.json',dict(status='PASS',checks=checks,new_test_files=4,cached_train_groups=4,target_achieved=achieved,test_search=False,feature_candidate_classifier_decoder_statistics_hashes=True,limitation='Test has historical exposure; no independent pitch ground truth; original classifier optimizer and native pYIN not refitted.'));print('PASS H77 four test files and four cached train groups; target',achieved,flush=True)

if __name__=='__main__':verify(Path(sys.argv[1]).resolve())
