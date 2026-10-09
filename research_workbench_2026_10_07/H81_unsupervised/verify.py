"""Independent four-dimensional Gaussian posterior and frozen teacher audit."""
import json,math,sys
from pathlib import Path
import numpy as np
import pandas as pd
import experiment as api

def scalar_response(x,m):
    logs=[];dimension=4
    for row in x:
        z=[(float(v)-float(a))/float(b) for v,a,b in zip(row,m['mean'],m['scale'])];parts=[]
        for weight,mean,cov in zip(m['weights'],m['centers'],m['covariances']):
            chol=np.linalg.cholesky(np.asarray(cov));delta=np.asarray([a-b for a,b in zip(z,mean)]);solution=np.linalg.solve(chol,delta);quadratic=math.fsum(float(v)**2 for v in solution);logdet=2*math.fsum(math.log(float(v)) for v in np.diag(chol));parts.append(math.log(weight)-.5*(dimension*math.log(2*math.pi)+logdet+quadratic))
        peak=max(parts);terms=[math.exp(v-peak) for v in parts];total=math.fsum(terms);logs.append(([v/total for v in terms],peak+math.log(total)-math.fsum(math.log(float(v)) for v in m['scale'])))
    return np.asarray([v[0] for v in logs]),np.asarray([v[1] for v in logs])

def check_scaler(x,m):
    mean=np.asarray([math.fsum(map(float,x[:,j]))/len(x) for j in range(4)]);var=np.asarray([math.fsum((float(v)-mean[j])**2 for v in x[:,j])/len(x) for j in range(4)]);eps=np.finfo(float).eps;constant=var<=len(x)*eps*var+(len(x)*mean*eps)**2;scale=np.where(constant,1.,np.sqrt(var));assert np.allclose(mean,m['mean'],atol=1e-10) and np.allclose(var,m['variance'],atol=1e-10) and np.allclose(scale,m['scale'],atol=1e-10);return True

def verify_train(out):
    api.check_registry();receipt=json.loads((out/'final_info.json').read_text())
    for p,d in receipt['artifacts'].items():assert api.audit.digest(api.REPO/p)==d,p
    bank={}
    for path in sorted((api.WORK/'H75_ml/run_train').glob('bank_*.npz')):
        with np.load(path) as b:bank[path.stem[5:]+'.wav']=b['x'][:,:4].copy()
    names=sorted(bank);models=json.loads((out/'models.json').read_text());proofs=json.loads((out/'held_density_proofs.json').read_text());table=pd.read_csv(out/'held_density.csv',float_precision='round_trip');fulls={};errors=[]
    for m in models:
        pool=m['fit_files'];assert pool==sorted(pool) and set(pool)<=set(names) and len(pool) in (3,4);count=min(len(bank[n]) for n in pool);rows=[]
        for n in pool:
            ids=[int(j*(len(bank[n])-1)/(count-1)) for j in range(count)];ids[0]=0;ids[-1]=len(bank[n])-1
            # linspace can round the binary product just below an integer: certify saved design by its explicit NumPy contract.
            expected=np.linspace(0,len(bank[n])-1,count,dtype=int);assert len(set(expected))==count and np.max(abs(expected-np.asarray(ids)))<=1;rows.extend(bank[n][expected])
        x=np.asarray(rows);check_scaler(x,m);assert m['training_rows']==len(x) and abs(math.fsum(m['weights'])-1)<1e-10 and all(w>0 for w in m['weights']);p,ll=scalar_response(x,m);assert np.allclose(p.sum(axis=1),1.)
        bic=-2*math.fsum(float(v)+math.fsum(math.log(float(s)) for s in m['scale']) for v in ll)+m['parameter_count']*math.log(len(x));assert m['parameter_count']==15*m['k']-1 and np.isclose(bic,m['bic'],atol=1e-7,rtol=1e-10)
        if len(pool)==4:fulls[m['k']]=m
        else:
            held=next(n for n in names if n not in pool);q,ld=scalar_response(bank[held],m);proof=next(v for v in proofs if v['k']==m['k'] and v['file']==held);assert proof['fit_pool']=='|'.join(pool) and np.allclose(q,proof['probability'],atol=1e-9) and np.allclose(ld,proof['log_density'],atol=1e-8);row=table[(table.k==m['k'])&(table.file==held)].iloc[0];assert np.isclose(row.negative_log_density,-math.fsum(map(float,ld))/len(ld),atol=1e-8)
    ranks=[]
    for k in api.KS:
        g=table[table.k==k];valid=all(m['converged'] for m in models if m['k']==k) and all(math.isfinite(float(v)) for v in g.negative_log_density);ranks.append((not valid,float(max(g.negative_log_density)) if valid else math.inf,math.fsum(map(float,g.negative_log_density))/len(g) if valid else math.inf,fulls[k]['bic'],k))
    selected=min(ranks)[-1];assert selected==receipt['selected_k'];locked=json.loads((out/'locked_model.json').read_text());assert locked['model']==fulls[selected];m=locked['model'];physical=np.asarray(m['centers'])*m['scale']+m['mean'];acf=sorted(map(float,physical[:,0]));cut=(acf[(selected-1)//2]+acf[selected//2])/2;components=[j for j,v in enumerate(physical[:,0]) if v>=cut];assert components==locked['voiced_components'] and locked['energy_threshold'] is None and locked['pitch_prior']==[2,18]
    for n in names:
        p=np.load(out/f'prediction_{Path(n).stem}.npz');q,ll=scalar_response(bank[n],m);assert np.array_equal(p['x'],bank[n]) and np.allclose(q,p['probability'],atol=1e-9);native=np.load(api.WORK/f'results/H69_native_{Path(n).stem}_pyin25_beta2_18.npz');assert np.array_equal(native['voiced'],p['native_voiced']) and np.allclose(native['raw_f0'],p['native_f0'],equal_nan=True,atol=0) and np.array_equal(native['native_times'],p['times']);pred=np.asarray([bool(v) and math.fsum(float(row[j]) for j in components)>=.5 for row,v in zip(q,p['native_voiced'])]);f0=np.asarray([float(f) if v else math.nan for f,v in zip(p['native_f0'],pred)]);assert np.array_equal(pred,p['pred']) and np.allclose(f0,p['f0'],atol=0,equal_nan=True)
    assert len(models)==15 and len(table)==12 and len(proofs)==12 and receipt['teacher_labels_or_statistics_used'] is False
    api.audit.json_write(out/'verification.json',dict(status='PASS',gmm_models=15,held_density_groups=12,selected_k=selected,independent_scaler_cholesky_density_posterior_BIC_selection=True,frozen_centroid_mapping_native_pitch_predictions=True,LAB_or_teacher_statistics_parsed=False,limitation='Certifies arithmetic and cached inputs; does not refit EM or establish semantic component truth.'))
    print('PASS H81 unlabeled model/selection/freeze verification; no teacher parsing',flush=True)

def verify_audit(out):
    api.check_registry();r=json.loads((out/'final_info.json').read_text())
    for p,d in r['artifacts'].items():assert api.audit.digest(api.REPO/p)==d,p
    train=api.HERE/'run_train';assert api.audit.digest(train/'locked_model.json')==r['locked_model_sha256'];locked=json.loads((train/'locked_model.json').read_text());table=pd.read_csv(out/'all_train_metrics.csv',float_precision='round_trip');audit=pd.read_csv(out/'component_audit.csv',float_precision='round_trip');from verify_srh import independent_item,independent_score
    for path in sorted(api.core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');p=np.load(train/f'prediction_{path.stem}.npz');assert np.array_equal(item['times'],p['times']);metrics=independent_score(item,p['pred'],p['f0']);row=table[(table.file==path.name)&(table.pipeline_id=='H81_unlabeled_selected')].iloc[0]
        for k,v in metrics.items():assert np.isclose(row[k],v,atol=1e-8,rtol=1e-9,equal_nan=True),(path.name,k)
        labels=np.argmax(p['probability'],axis=1)
        for j in range(locked['model']['k']):
            row=audit[(audit.file==path.name)&(audit.component==j)].iloc[0];mask=labels==j;assert row.frames==sum(mask) and bool(row.mapped_voiced)==(j in locked['voiced_components'])
            for label in ('v','uv','sil'):assert row[label]==sum(mask&(item['labels']==label))
    old=pd.read_csv(api.WORK/'H78_context/run_train/all_train_metrics.csv',float_precision='round_trip');numeric=table.select_dtypes(include='number').columns
    for _,row in table[table.pipeline_id=='H72_energy07_cached'].iterrows():
        source=old[(old.file==row['file'])&(old.option_id=='energy07')].iloc[0]
        for k in numeric:assert np.isclose(row[k],source[k],atol=0,rtol=0,equal_nan=True)
    assert len(table)==8 and len(audit)==4*locked['model']['k'] and r['selection_unchanged']
    api.audit.json_write(out/'verification.json',dict(status='PASS',posthoc_train_metrics=4,cached_controls=4,teacher_labels_only_after_freeze=True,independent_metrics_attribution_hashes=True,test_used=False));print('PASS H81 post-freeze teacher audit',flush=True)

if __name__=='__main__':
    out=Path(sys.argv[1]).resolve();verify_train(out) if out.name=='run_train' else verify_audit(out)
