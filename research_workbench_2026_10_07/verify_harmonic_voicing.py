import hashlib
import json
import math
import numpy as np
import pandas as pd
from verify_nls import qr_residual


def independent_coherence(segment,fs,pitch):
    if not np.isfinite(pitch):return np.zeros(2)
    weights=.5-.5*np.cos(2*np.pi*np.arange(len(segment))/(len(segment)-1))
    center=sum(float(x*w) for x,w in zip(segment,weights))/sum(weights)
    total=sum(float(w*(x-center)**2) for x,w in zip(segment,weights))
    if total<=1e-20:return np.zeros(2)
    first=np.clip(1-qr_residual(segment,fs,pitch,3)/total,0,1)
    second=np.clip(1-qr_residual(segment,fs,pitch,5)/total,0,1)
    return np.array([first,max(0,second-first)])


def scalar_response(x,model):
    output=[]
    for row in x:
        logit=model['intercept']
        for i,coef in enumerate(model['coefficient']):logit+=coef*(row[i]-model['mean'][i])/model['scale'][i]
        if logit>=0:output.append(1/(1+math.exp(-logit)))
        else:
            e=math.exp(logit);output.append(e/(1+e))
    return np.array(output)


def verify():
    import harmonic_voicing as api
    from verify_srh import independent_item,independent_score
    from verify_recovery_pitch import scalar_pitches
    from threadpoolctl import threadpool_limits
    api.check_registry();receipt=json.loads((api.OUT/'H62_train_experiment.json').read_text())
    for p,d in receipt['artifacts'].items():assert api.audit.digest(api.REPO/p)==d,p
    models=json.loads((api.OUT/'H62_models.json').read_text())['models'];bank={};items={};model_checks=[]
    with threadpool_limits(limits=1):
        for path in sorted(api.core.TRAIN.glob('*.wav')):
            item,fs,audio=independent_item(path,'train');items[path.name]=item
            old=dict(np.load(api.OUT/f'H50_design_{path.stem}.npz'))
            feature=dict(np.load(api.OUT/f'H62_design_{path.stem}.npz'));bank[path.name]=feature
            assert np.array_equal(item['labels'],feature['labels']) and np.array_equal(item['times'],feature['times'])
            assert np.array_equal(old['x'][:,:4],feature['x'][:,:4])
            assert np.array_equal(old['base_pred'],feature['base_pred'])
            assert np.allclose(old['base_f0'],feature['base_f0'],rtol=0,atol=0,equal_nan=True)
            pitch,anchor,_=scalar_pitches(old,fs,200)
            assert np.allclose(pitch,feature['pitch'],atol=1e-10,equal_nan=True)
            anchors=np.where(old['base_pred'],old['base_f0'],pitch)
            assert np.allclose(anchors,feature['anchor'],atol=1e-10,equal_nan=True)
            length,hop=round(.025*fs),round(.01*fs)
            for i,f in enumerate(anchors):
                extra=independent_coherence(audio[i*hop:i*hop+length],fs,f)
                assert np.allclose(extra,feature['x'][i,4:],rtol=1e-9,atol=1e-9),(path,i)
            print('H62 verified features',path.name,flush=True)
        for model in models:
            names=model['fit_files'];n=min(len(bank[name]['x']) for name in names)
            ids={name:np.round(np.linspace(0,len(bank[name]['x'])-1,n)).astype(int) for name in names}
            assert {name:value.tolist() for name,value in ids.items()}==model['indices']
            x=np.vstack([bank[name]['x'][ids[name],:model['dimensions']] for name in names])
            y=np.concatenate([(bank[name]['labels'][ids[name]]=='v').astype(int) for name in names])
            assert hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()==model['design_sha256']
            mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale==0]=1
            assert np.allclose(mean,model['mean'],atol=1e-12) and np.allclose(scale,model['scale'],atol=1e-12)
            assert y.sum()==model['positive_frames']
            z=(x-np.array(model['mean']))/np.array(model['scale']);p=scalar_response(x,model)
            gradient=np.r_[z.T@(p-y)+np.array(model['coefficient']),sum(p-y)]/len(y)
            assert np.max(abs(gradient))<1e-6,np.max(abs(gradient))
            model_checks.append(dict(fit_files=names,dimensions=model['dimensions'],
                max_normalized_gradient=float(np.max(abs(gradient))),training_rows=len(y)))
        rows=pd.read_csv(api.OUT/'H62_groups.csv',float_precision='round_trip');group_checks=[]
        for proof in receipt['proofs']:
            feature=bank[proof['held_file']];item=items[proof['held_file']]
            saved=dict(np.load(api.REPO/proof['path']));pool=proof['fit_files'];poolkey='|'.join(pool)
            for k,option in enumerate(api.OPTIONS):
                if option['dimensions']:
                    model=next(m for m in models if m['fit_files']==pool and m['dimensions']==option['dimensions'])
                    p=scalar_response(feature['x'],model)
                else:p=np.zeros(len(feature['x']))
                assert np.allclose(p,saved['probability'][k],atol=1e-12)
                pred=feature['base_pred'].copy();f0=feature['base_f0'].copy()
                for i in range(len(pred)):
                    if not option['dimensions']:continue
                    if feature['base_pred'][i] and p[i]<option['reject']:pred[i]=False;f0[i]=np.nan
                    if (not feature['base_pred'][i] and p[i]>=.5 and feature['x'][i,0]>=.6 and
                        feature['x'][i,1]>=math.log(.01) and np.isfinite(feature['pitch'][i])):
                        pred[i]=True;f0[i]=feature['pitch'][i]
                assert np.array_equal(pred,saved['pred'][k]) and np.allclose(f0,saved['f0'][k],rtol=0,atol=0,equal_nan=True)
                metrics=independent_score(item,pred,f0)
                r=rows[(rows.file==proof['held_file'])&(rows.fit_files==poolkey)&(rows.option_id==option['id'])].iloc[0]
                for key,val in metrics.items():assert np.isclose(val,r[key],atol=1e-9,rtol=1e-9,equal_nan=True),(proof,key)
                group_checks.append(dict(file=proof['held_file'],fit_files=pool,option_id=option['id']))
    import yaapt_extension as previous
    from verify_yaapt_extension_v2 import independent_choose
    from voicing_recovery import gates
    old_options=previous.BY_ID;previous.BY_ID=api.BY_ID
    try:
        records=rows.to_dict('records');names=sorted(bank);selections=[];inner=[]
        for held in ['final']+names:
            available=[n for n in names if n!=held];trace=[]
            for target in available:
                key='|'.join(n for n in available if n!=target)
                trace.extend(r for r in records if r['file']==target and r['fit_files']==key)
            selections.append(dict(outer_held=held,selection_files=available,option_id=independent_choose(trace)))
            for r in trace:inner.append(dict(outer_held=held,inner_held=r['file'],**r))
    finally:previous.BY_ID=old_options
    assert selections==receipt['selections']
    saved_inner=pd.read_csv(api.OUT/'H62_inner_traces.csv',float_precision='round_trip').fillna('')
    for r,s in zip(inner,saved_inner.to_dict('records')):
        for key,val in r.items():
            if isinstance(val,(float,int)):assert np.isclose(val,s[key],atol=1e-9)
            else:assert val==s[key]
    assert len(inner)==len(saved_inner)==112
    _,decision=gates(pd.read_csv(api.OUT/'H62_metrics.csv'));assert decision==receipt['decision']
    assert len(models)==22 and len(group_checks)==140
    api.audit.json_write(api.OUT/'H62_verification.json',dict(status='PASS',groups=len(group_checks),models=model_checks,
        independent_qr_features_pcm_grid_scalar_response_inference_metrics_selection=True,
        gradient_stationarity_checked=True,optimizer_independently_refit=False,
        old_PEZS_features_are_verified_H50_cache=True,inner_traces=len(inner)))
    print('PASS H62 140 groups/22 model pools/112 inner traces')


if __name__=='__main__':verify()
