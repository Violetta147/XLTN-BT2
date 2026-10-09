"""Independent FFT interpolation, contribution mask, overlap-add and metrics."""
import json,math,sys
from pathlib import Path
import numpy as np
import pandas as pd
import soundfile as sf
import experiment as api

def scalar_spectrum(audio,fs):
    length,hop=round(fs*.025),round(fs*.01);rms=[];spectra=[]
    window=np.asarray([.54-.46*math.cos(2*math.pi*j/(length-1)) for j in range(length)])
    for start in range(0,len(audio)-length+1,hop):
        frame=np.asarray(audio[start:start+length]);mean=math.fsum(map(float,frame))/length;centered=frame-mean;rms.append(math.sqrt(math.fsum(float(t)**2 for t in centered)/length));raw=np.abs(np.fft.rfft(centered*window))/length
        row=[]
        for target in api.GRID:
            pos=float(target)*length/fs;lo=int(math.floor(pos));hi=min(lo+1,len(raw)-1);lo=min(lo,len(raw)-1);row.append(float(raw[lo])+(pos-math.floor(pos))*(float(raw[hi])-float(raw[lo])))
        spectra.append(row)
    ref=max(float(np.quantile(rms,.95,method='linear')),1e-12);return np.asarray(spectra)/ref

def scalar_reconstruct(audio,fs,mask):
    length,hop=round(fs*.025),round(fs*.01);window=np.asarray([.54-.46*math.cos(2*math.pi*j/(length-1)) for j in range(length)]);result=np.zeros(len(audio));norm=np.zeros(len(audio))
    for j,start in enumerate(range(0,len(audio)-length+1,hop)):
        frame=np.asarray(audio[start:start+length]);mean=math.fsum(map(float,frame))/length;fft=np.fft.rfft((frame-mean)*window);values=[]
        for k in range(len(fft)):
            frequency=k*fs/length
            if frequency>8000:values.append(1.);continue
            pos=frequency/40;lo=min(int(math.floor(pos)),200);hi=min(lo+1,200);values.append(float(mask[j,lo])+(pos-lo)*(float(mask[j,hi])-float(mask[j,lo])))
        y=np.fft.irfft(fft*np.asarray(values),n=length)/window+mean;result[start:start+length]+=y*window**2;norm[start:start+length]+=window**2
    valid=norm>0;result[valid]/=norm[valid];result[~valid]=audio[~valid];return result

def scalar_mask(w,h,k):
    result=[]
    for row in w:
        out=[]
        for j in range(h.shape[1]):
            total=math.fsum(float(a)*float(b) for a,b in zip(row,h[:,j]));noise=float(row[k])*float(h[k,j]);out.append(1-noise/total if total>0 else 1.)
        result.append(out)
    return np.clip(np.asarray(result),0,1)

def verify(out):
    api.check_registry();receipt=json.loads((out/'final_info.json').read_text())
    for p,d in receipt['artifacts'].items():assert api.audit.digest(api.REPO/p)==d,p
    from verify_srh import independent_item,independent_score
    from verify_pyin_energy import scalar_energy
    items={};bank={};signals={}
    for path in sorted(api.core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');b=dict(np.load(out/f'spectrum_{path.stem}.npz'));assert np.allclose(b['x'],scalar_spectrum(audio,fs),atol=1e-10,rtol=1e-9);assert np.array_equal(item['times'],b['times']);items[path.name]=item;bank[path.name]=b;signals[path.name]=(audio,fs)
    models=json.loads((out/'models.json').read_text());table=pd.read_csv(out/'all_train_metrics.csv',float_precision='round_trip');audit=pd.read_csv(out/'component_audit.csv',float_precision='round_trip');checks=0
    for m in models:
        pool=m['fit_files'];held=m['held'];assert pool==sorted(pool) and (set(pool)==set(items) if held=='full' else set(pool)==set(items)-{held});tag='full' if held=='full' else 'without_'+Path(held).stem;p=dict(np.load(out/f'model_{tag}.npz'));assert np.min(p['w'])>=0 and np.min(p['h'])>=0 and np.isclose(np.linalg.norm(p['x']-p['w']@p['h']),m['reconstruction_error'],rtol=1e-10)
        count=sum(len(bank[n]['x']) for n in pool);scores=[];mass=p['h'].sum(axis=1)
        for n,start,end in m['ranges']:
            assert n in pool and end-start==len(bank[n]['x']);scale=math.sqrt(count/(len(pool)*(end-start)));assert np.allclose(p['scales'][start:end],scale) and np.allclose(p['x'][start:end],bank[n]['x']*scale,atol=1e-12)
            w=p['w'][start:end]/scale;low=bank[n]['relative_rms']<=np.quantile(bank[n]['relative_rms'],.2,method='linear');a=w*mass;scores.append(np.asarray([math.fsum(map(float,a[low,k]))/sum(low)/max(math.fsum(map(float,a[:,k]))/len(a),1e-12) for k in range(4)]))
        score=np.asarray([math.fsum(float(row[k]) for row in scores)/len(scores) for k in range(4)]);assert np.allclose(score,m['noise_proxy_scores'],atol=1e-10);assert m['noise_component']==max(range(4),key=lambda k:score[k])
        for n in (sorted(items) if held=='full' else [held]):
            d=dict(np.load(out/f'decomposition_{tag}_{Path(n).stem}.npz'));assert np.min(d['coefficients'])>=0;mask=scalar_mask(d['coefficients'],p['h'],m['noise_component']);assert np.allclose(mask,d['mask'],atol=1e-10)
            if n in pool:
                start,end=next((a,b) for name,a,b in m['ranges'] if name==n);assert np.allclose(d['coefficients'],p['w'][start:end]/p['scales'][start:end,None],atol=1e-12)
            shares=d['coefficients']*mass;shares/=np.maximum(shares.sum(axis=1,keepdims=True),1e-12)
            for label in ('v','uv','sil'):
                chosen=items[n]['labels']==label
                for k in range(4):
                    row=audit[(audit.held==held)&(audit.file==n)&(audit.label==label)&(audit.component==k)].iloc[0];assert row.frames==sum(chosen) and bool(row.candidate_noise)==(k==m['noise_component']);expected=float(shares[chosen,k].mean()) if chosen.any() else np.nan;assert np.isclose(expected,row.mean_contribution,atol=1e-10,equal_nan=True)
            if held=='full':
                audio,fs=signals[n];speech=scalar_reconstruct(audio,fs,mask);saved,saved_fs=sf.read(out/f'speech_candidate_{Path(n).stem}.wav');noise,_=sf.read(out/f'noise_candidate_{Path(n).stem}.wav');assert saved_fs==fs and np.allclose(saved,speech,atol=1e-10) and np.allclose(saved+noise,audio,atol=1e-12)
                native=dict(np.load(out/f'pitch_{Path(n).stem}.npz'));e=scalar_energy(speech,fs);assert np.allclose(e['relative_rms'],native['relative_rms'],atol=1e-10) and np.array_equal(native['native_times'],items[n]['times']);pred=np.asarray([bool(v) and float(r)>=.07 for v,r in zip(native['voiced'],e['relative_rms'])]);f0=np.asarray([float(f) if v else math.nan for f,v in zip(native['raw_f0'],pred)]);assert np.array_equal(pred,native['pred']) and np.allclose(f0,native['f0'],equal_nan=True,atol=0);assert np.array_equal(np.isfinite(native['raw_f0']),native['voiced']) and np.all((native['raw_f0'][native['voiced']]>=70)&(native['raw_f0'][native['voiced']]<=400))
                metrics=independent_score(items[n],pred,f0);row=table[(table.file==n)&(table.pipeline_id=='H79_nmf4_pyin25_energy07')].iloc[0]
                for k,v in metrics.items():assert np.isclose(row[k],v,atol=1e-8,rtol=1e-9,equal_nan=True),(n,k)
            checks+=1
    old=pd.read_csv(api.WORK/'H78_context/run_train/all_train_metrics.csv',float_precision='round_trip');numeric=table.select_dtypes(include='number').columns
    for _,row in table[table.pipeline_id=='H72_energy07_cached'].iterrows():
        source=old[(old.file==row['file'])&(old.option_id=='energy07')].iloc[0]
        for k in numeric:assert np.isclose(row[k],source[k],atol=0,rtol=0,equal_nan=True)
    assert len(models)==5 and checks==8 and len(table)==8 and len(audit)==96
    api.audit.json_write(out/'verification.json',dict(status='PASS',nmf_models=5,decompositions=8,new_pitch_metrics=4,cached_controls=4,independent_fft_contributions_masks_overlap_add_audio_identity=True,labels_used_only_for_audit_and_scoring=True,original_pyin_not_rerun=True,limitation='Verifier checks factorization and inference arithmetic; no refit optimizer or per-frame pitch truth, no proof that the designated component is pure noise.'))
    print('PASS H79 5 NMF models, 8 decompositions, 4 new pitch metrics and 4 cached controls',flush=True)

if __name__=='__main__':verify(Path(sys.argv[1]).resolve())
