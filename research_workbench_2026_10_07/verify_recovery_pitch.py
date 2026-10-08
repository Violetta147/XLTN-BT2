import argparse
import json
import numpy as np
import pandas as pd
import recovery_pitch as api
from verify_srh import independent_item,independent_score


def scalar_pitches(feature,fs,width):
    result=feature['pitch'].copy();anchor=np.full(len(result),np.nan);changed=np.zeros(len(result),bool)
    if width==0:return result,anchor,changed
    voiced=[i for i,p in enumerate(feature['base_pred']) if p]
    for i,t in enumerate(feature['times']):
        if not voiced:continue
        nearest=min(voiced,key=lambda k:(abs(t-feature['times'][k]),k))
        if abs(t-feature['times'][nearest])>.05+1/fs:continue
        anchor[i]=feature['base_f0'][nearest];candidates=[];curve=feature['curves'][i]
        for j in range(1,len(curve)-1):
            if curve[j]<curve[j-1] or curve[j]<curve[j+1] or curve[j]<.6:continue
            denominator=curve[j-1]-2*curve[j]+curve[j+1]
            delta=.5*(curve[j-1]-curve[j+1])/denominator if abs(denominator)>1e-12 else 0.
            pitch=min(400.,max(70.,fs/(feature['lags'][j]+min(.5,max(-.5,delta)))))
            if abs(1200*np.log2(pitch/anchor[i]))<=width:candidates.append((float(curve[j]),j,pitch))
        if candidates:
            winner=sorted(candidates,key=lambda r:(-r[0],r[1]))[0];result[i]=winner[2];changed[i]=result[i]!=feature['pitch'][i]
    return result,anchor,changed


def scalar_response(x,m):
    result=[]
    for row in x:
        z=(row[api.RECIPE['columns']]-np.array(m['mean']))/np.array(m['scale'])
        scores=[]
        for weight,center,variance in zip(m['weights'],m['centers'],m['variance']):
            scores.append(np.log(weight)-.5*sum(np.log(2*np.pi*v)+(value-mean)**2/v for value,mean,v in zip(z,center,variance)))
        p=np.exp(np.array(scores)-max(scores));result.append(p[m['component']]/sum(p))
    return np.array(result)


def scalar_choose(rows):
    ranks=[]
    for option in api.OPTIONS:
        allvalues=[r for r in rows if r['option_id']==option['id']];valid=True
        for seed in api.SEEDS:
            group=[r for r in allvalues if r['seed']==seed];base=[r for r in rows if r['seed']==seed and r['option_id']=='hard170']
            valid &= all(np.isfinite(r['average_mape']) for r in group)
            for key in ('macro_f1','recall_v'):valid &= sum(r[key] for r in group)/len(group)>=sum(r[key] for r in base)/len(base)-.01
            valid &= sum(r['false_voiced_sil'] for r in group)<=sum(r['false_voiced_sil'] for r in base)+1
        ranks.append((not valid,max(r['average_mape'] for r in allvalues) if valid else np.inf,
            sum(r['average_mape'] for r in allvalues)/len(allvalues) if valid else np.inf,option['id']))
    return sorted(ranks)[0][-1]


def verify(stage):
    api.check_registry();receipt=json.loads((api.OUT/f'H56_{stage}_experiment.json').read_text())
    for path,digest in receipt['artifacts'].items():assert api.audit.digest(api.REPO/path)==digest,path
    models=json.loads((api.OUT/'H56_models.json').read_text());bank=api.bank_train();seen=set()
    for m in models:
        key=(tuple(m['fit_files']),m['seed']);assert key not in seen;seen.add(key)
        n=min(len(bank[name]['x']) for name in m['fit_files'])
        raw=np.vstack([bank[name]['x'][np.round(np.linspace(0,len(bank[name]['x'])-1,n)).astype(int)] for name in m['fit_files']])
        x=raw[:,api.RECIPE['columns']];assert np.allclose(x.mean(axis=0),m['mean'],atol=1e-12)
        std=x.std(axis=0);std=np.where(std==0,1,std);assert np.allclose(std,m['scale'],atol=1e-12)
        z=(x-np.array(m['mean']))/np.array(m['scale']);logs=[]
        for k in range(3):
            variance=np.array(m['variance'][k]);logs.append(np.log(m['weights'][k])-.5*np.sum(np.log(2*np.pi*variance)+(z-np.array(m['centers'][k]))**2/variance,axis=1))
        logs=np.array(logs).T;p=np.exp(logs-logs.max(axis=1,keepdims=True));p/=p.sum(axis=1,keepdims=True)
        periodicity=p.T@raw[:,0]/p.sum(axis=0);assert int(np.argmax(periodicity))==m['component']
    proofs=json.loads((api.OUT/f'H56_{stage}_proofs.json').read_text());stored=pd.read_csv(api.OUT/f'H56_{stage}_fixed.csv',float_precision='round_trip')
    assert len(proofs)==len(stored);rows=[];cache={};parity=0
    for proof in proofs:
        name=proof['file'];m=models[proof['model_id']];identity=proof['option_id']
        if stage=='train':f=bank[name]
        else:f=dict(np.load(api.OUT/f'H56_test_design_{name[:-4]}.npz',allow_pickle=False))
        key=(name,proof['model_id'])
        if key not in cache:cache[key]=scalar_response(f['x'],m)
        prob=cache[key];assert np.allclose(prob,proof['prob'],atol=1e-10,rtol=1e-10)
        pitch,_,_=scalar_pitches(f,int(f['fs']),api.BY_ID[identity]['width'])
        recover=np.array([not base and probability>=.5 and strength>=.6 and energy>=np.log(.01) and np.isfinite(oldpitch)
            for base,probability,strength,energy,oldpitch in zip(f['base_pred'],prob,f['x'][:,0],f['x'][:,1],f['pitch'])])
        if identity=='hard170':recover[:]=False
        pred=f['base_pred']|recover;f0=np.array([pitch[i] if recover[i] else f['base_f0'][i] for i in range(len(pred))])
        assert np.array_equal(pred,proof['pred']) and np.allclose(f0,np.array(proof['f0'],float),equal_nan=True,atol=1e-10)
        item,_,_=independent_item((api.core.TRAIN if stage=='train' else api.REPO/'TinHieuKiemThu')/name,stage)
        score=independent_score(item,pred,f0)
        row=stored[(stored.model_id==proof['model_id'])&(stored.file==name)&(stored.option_id==identity)].iloc[0]
        assert row.fit_pool=='|'.join(m['fit_files']) and row.seed==m['seed'] and row.recovered==sum(recover)
        for field,value in score.items():assert np.isclose(row[field],value,atol=1e-8,rtol=1e-10,equal_nan=True),field
        rows.append(dict(model_id=proof['model_id'],fit_pool=row.fit_pool,seed=m['seed'],option_id=identity,file=name,**score))
        if stage=='train' and len(m['fit_files'])==3 and identity=='recovery_acf':
            legacy=dict(np.load(api.OUT/f'H51_predictions_{name[:-4]}.npz',allow_pickle=False))
            k=np.flatnonzero((legacy['recipe_id']=='gmm_PEZS')&(legacy['seed']==m['seed']))[0]
            assert np.array_equal(pred,legacy['pred'][k]) and np.allclose(f0,legacy['f0'][k],equal_nan=True,atol=1e-10);parity+=1
    # Same model/file implies the same decisions across all recovery pitch variants.
    for key in cache:
        group=[p for p in proofs if (p['file'],p['model_id'])==key and p['option_id']!='hard170']
        assert all(p['pred']==group[0]['pred'] for p in group)
    if stage=='train':
        assert len(models)==33 and len(rows)==300 and parity==12 and receipt['actual_model_fits']==33
        traces=json.loads((api.OUT/'H56_inner_traces.json').read_text());assert len(traces)==240
        for trace in traces:
            fit=trace['fit_pool'].split('|');assert trace['inner_held'] not in fit and trace['outer_held'] not in fit
            pool=next(s['selection_files'] for s in receipt['selections'] if s['outer_held']==trace['outer_held'])
            assert set(fit)==set(pool)-{trace['inner_held']}
            original=next(r for r in rows if r['model_id']==trace['model_id'] and r['file']==trace['file'] and r['option_id']==trace['option_id'])
            for field in score:assert np.isclose(trace[field],original[field],atol=1e-8,equal_nan=True)
        for selection in receipt['selections']:
            group=[r for r in traces if r['outer_held']==selection['outer_held']]
            assert scalar_choose(group)==selection['option_id']
        metrics=pd.read_csv(api.OUT/'H56_metrics.csv',float_precision='round_trip');assert len(metrics)==72
        for _,row in metrics.iterrows():
            r=next(r for r in rows if r['model_id']==row.model_id and r['file']==row['file'] and r['option_id']==row.option_id)
            for field in score:assert np.isclose(row[field],r[field],atol=1e-8,equal_nan=True)
        for seed in api.SEEDS:assert api.matrix.base.gates(metrics[metrics.seed==seed])[1]==receipt['decisions'][str(seed)]
    else:
        freeze=json.loads((api.OUT/'H56_FROZEN_SELECTION.json').read_text());assert set(stored.option_id)==set(freeze['external_options'])
        assert receipt['actual_model_fits']==0 and receipt['freeze_sha256']==api.audit.digest(api.OUT/'H56_FROZEN_SELECTION.json')
    api.audit.json_write(api.OUT/f'H56_{stage}_verification.json',dict(passed=True,metric_groups=len(rows),serialized_gmm_models_checked=33,
        scalar_gmm_and_pitch_mask_score_checks=True,legacy_fixed_lofo_parity_groups=parity,cached_features_previously_verified=True,
        verifier_sha256=api.audit.digest(__file__),limits='No new frame-level F0 ground truth; cached H50/H51 signal features, not a new independent corpus.'))
    print(f'PASS H56 {stage}: {len(rows)} groups, same recovery masks across pitch ablations, legacy parity {parity}')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['train','test']);verify(parser.parse_args().stage)
