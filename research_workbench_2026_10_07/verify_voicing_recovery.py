import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
import voicing_recovery as api

HERE, OUT, REPO = api.HERE, api.OUT, api.REPO


def independent_features(audio, fs):
    length, hop = round(fs*.025), round(fs*.01)
    nfft = 1 << (length-1).bit_length()
    frequency = np.arange(nfft) * fs/nfft
    frequency = np.minimum(frequency, fs-frequency)
    mel_points = 700 * (np.power(10, np.linspace(2595*np.log10(1+70/700),2595*np.log10(1+min(8000,fs/2)/700),28)/2595)-1)
    filters = np.array([np.maximum(0,np.minimum((frequency-mel_points[i])/(mel_points[i+1]-mel_points[i]),
                                                (mel_points[i+2]-frequency)/(mel_points[i+2]-mel_points[i+1]))) for i in range(26)])
    cosine = np.sqrt(2/26)*np.cos(np.pi/26*(np.arange(26)+.5)[None,:]*np.arange(1,14)[:,None])
    rows, pitches, rms = [], [], []
    lo, hi = int(np.ceil(fs/400)), min(length-2,int(np.floor(fs/70)))
    for start in range(0, len(audio)-length+1, hop):
        x = audio[start:start+length].copy()
        x -= x.mean()
        rms.append(np.sqrt(np.dot(x,x)/len(x)))
        spectrum = abs(np.fft.fft(x*np.hanning(length),nfft))**2
        spectrum[0] = 0
        total = max(spectrum.sum(),1e-20)
        high = spectrum[frequency >= 1000-1e-8].sum()/total
        cepstrum = cosine @ np.log(np.maximum(filters @ (spectrum/total),1e-12))
        correlation = np.array([np.dot(x[:-lag],x[lag:])/max(np.linalg.norm(x[:-lag])*np.linalg.norm(x[lag:]),1e-20)
                                for lag in range(lo-1,hi+2)])
        candidates = [i for i in range(1,len(correlation)-1) if correlation[i] >= correlation[i-1] and correlation[i] >= correlation[i+1]]
        if candidates:
            strength = max(correlation[i] for i in candidates)
            k = next(i for i in candidates if correlation[i]>=.93*strength)
            a,b,c = correlation[k-1:k+2]
            delta = .5*(a-c)/(a-2*b+c) if abs(a-2*b+c)>1e-12 else 0
            pitch = np.clip(fs/(lo-1+k+np.clip(delta,-.5,.5)),70,400) if strength>0 else np.nan
            strength = max(strength,0)
        else:
            strength,pitch = 0,np.nan
        rows.append([strength,0.,sum(bool(a<0)!=bool(b<0) for a,b in zip(x[:-1],x[1:]))/(length-1)*fs,high,*cepstrum])
        pitches.append(pitch)
    rows = np.array(rows)
    rows[:,1] = np.log(np.maximum(np.array(rms)/max(np.quantile(rms,.95),1e-12),1e-6))
    return rows,np.array(pitches)


def independent_probability(x, model):
    z = (x[:,:model['dimensions']]-model['mean'])/model['scale']
    if model['method']=='logistic':
        return expit(np.dot(z,model['coefficient'])+model['intercept'])
    density=[]
    for weight,mean,var in zip(model['weights'],model['centers'],model['covariance']):
        density.append(np.log(weight)-.5*np.sum(np.log(2*np.pi*np.array(var))+(z-mean)**2/var,axis=1))
    density=np.array(density).T
    weights=np.exp(density-density.max(axis=1,keepdims=True))
    return (weights/weights.sum(axis=1,keepdims=True))[:,model['voiced_component']]


def independent_score(item,pred,f0):
    values=f0[np.isfinite(f0)]
    estimates=dict(F0mean=np.mean(values),F0std=np.std(values),F0num=len(values))
    errors={key+'_mape':100*abs(value-item['stats'][key])/item['stats'][key] for key,value in estimates.items()}
    lab=item['labels']; valid=np.isin(lab,['v','uv']); y=lab[valid]=='v'; p=pred[valid]
    tp,tn,fp,fn=sum(y&p),sum(~y&~p),sum(~y&p),sum(y&~p)
    rv,ru=tp/max(tp+fn,1),tn/max(tn+fp,1)
    return dict(**estimates,**errors,average_mape=np.mean(list(errors.values())),TP=tp,TN=tn,FP=fp,FN=fn,
                recall_v=rv,recall_uv=ru,balanced_accuracy=(rv+ru)/2,
                macro_f1=(2*tp/max(2*tp+fp+fn,1)+2*tn/max(2*tn+fp+fn,1))/2,false_voiced_sil=sum((lab=='sil')&pred))


def run():
    registry=json.loads((HERE/'H50_REGISTRY.json').read_text())
    experiment=json.loads((OUT/'H50_experiment.json').read_text())
    for relative,digest in {**registry['source_hashes'],**experiment['artifacts']}.items():
        assert api.audit.digest(REPO/relative)==digest,relative
    assert api.audit.digest(HERE/'H50_REGISTRY.json')==experiment['registry_sha256']
    items={item['file']:item for item in api.core.load_training()}
    bank={}
    checked_frames=0
    for name,item in items.items():
        fs,audio=api.core.load_audio(api.core.TRAIN/name)
        x,pitch=independent_features(audio,fs)
        with np.load(OUT/f'H50_design_{Path(name).stem}.npz',allow_pickle=False) as data:
            bank[name]={key:data[key].copy() for key in data.files}
        assert np.allclose(x,bank[name]['x'],atol=1e-8),name
        assert np.allclose(pitch,bank[name]['pitch'],atol=1e-8,equal_nan=True),name
        checked_frames+=len(x)
    fits=json.loads((OUT/'H50_fits.json').read_text())['fits']
    models={}
    refits=0
    for row in fits:
        option=next(option for option in api.OPTIONS if option['id']==row['option_id'])
        names=row['nominal_fit_files']
        model=row['model']
        models[(option['id'],tuple(names))]=model
        if model is None:
            continue
        rebuilt=api.fit_model(bank,names,option)
        for key in ('mean','scale','coefficient','intercept','weights','centers','covariance'):
            if key in model:
                assert np.allclose(model[key],rebuilt[key],atol=1e-10),key
        assert model['indices']==rebuilt['indices']
        if model['method']=='gmm':
            poisoned={name:{**data,'labels':np.full(len(data['labels']),'v')} for name,data in bank.items()}
            assert api.fit_model(poisoned,names,option)==rebuilt, 'GMM fit or semantic mapping used LAB'
        refits+=1
    contours=pd.read_csv(OUT/'H50_contours.csv',float_precision='round_trip')
    fixed=pd.read_csv(OUT/'H50_fixed_lofo.csv')
    metric_checks=0
    for (identity,name),group in contours.groupby(['option_id','file']):
        names=sorted(n for n in bank if n!=name)
        model=models[(identity,tuple(names))]
        data=bank[name]
        prob=independent_probability(data['x'],model) if model else np.full(len(data['x']),np.nan)
        recovered=(~data['base_pred']) & (prob>=.5) & (data['x'][:,0]>=.6) & (data['x'][:,1]>=np.log(.01)) & np.isfinite(data['pitch'])
        pred=data['base_pred']|recovered
        f0=np.where(recovered,data['pitch'],data['base_f0'])
        assert np.array_equal(recovered,group.recovered) and np.array_equal(pred,group.pred_voiced)
        assert np.allclose(f0,group.f0_hz,atol=1e-10,equal_nan=True)
        assert np.allclose(prob,group.probability_v,atol=1e-10,equal_nan=True)
        score=independent_score(items[name],pred,f0)
        measured=fixed[(fixed.option_id==identity)&(fixed.file==name)].iloc[0]
        assert all(np.isclose(measured[key],value,atol=1e-8) for key,value in score.items())
        assert measured.recovered==sum(recovered)
        for label in ('v','uv','sil'):
            assert measured['recovered_'+label]==sum(recovered&(items[name]['labels']==label))
        metric_checks+=1
    traces=pd.read_csv(OUT/'H50_inner_traces.csv')
    for selection in experiment['selections']:
        outer=selection['outer_held']; pool=selection['selection_files']
        assert outer=='final' or outer not in pool
        group=traces[traces.outer_held==outer]
        for _,row in group.iterrows():
            names=row.fit_files.split('|')
            assert row.inner_held not in names and (outer=='final' or outer not in names)
            model=models[(row.option_id,tuple(names))]
            option=next(option for option in api.OPTIONS if option['id']==row.option_id)
            pred,f0,_,_=api.infer(bank[row.inner_held],option,model)
            score=independent_score(items[row.inner_held],pred,f0)
            assert all(np.isclose(row[key],value,atol=1e-8) for key,value in score.items())
            metric_checks+=1
        base=group[group.option_id=='hard170']; ranks=[]
        for identity,g in group.groupby('option_id'):
            valid=g.macro_f1.mean()>=base.macro_f1.mean()-.01 and g.recall_v.mean()>=base.recall_v.mean()-.01 and g.false_voiced_sil.sum()<=base.false_voiced_sil.sum()+1
            ranks.append((not valid,g.average_mape.max() if valid else np.inf,g.average_mape.mean() if valid else np.inf,identity))
        assert min(ranks)[3]==selection['option_id']
    table=pd.read_csv(OUT/'H50_metrics.csv')
    summaries,decision=api.gates(table)
    assert decision==experiment['decision']
    api.audit.json_write(OUT/'H50_verification.json',dict(passed=True,pcm_full_fft_dct_acf_frames=checked_frames,
        independent_metric_groups=metric_checks,model_refits=refits,fit_selection_exclusion=True,unsupervised_label_poison_passed=True,
        old_pitch_and_mask_preserved=True,new_native_calls=0,experiment_sha256=api.audit.digest(OUT/'H50_experiment.json')))
    print('PASS H50 features/models/metrics/exclusion/selection/hashes',checked_frames,metric_checks,refits)


if __name__=='__main__':
    run()
