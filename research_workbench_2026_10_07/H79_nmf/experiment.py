"""Joint NMF decomposition with a label-free low-energy noise proxy."""
import argparse,importlib.util,inspect,json,subprocess,warnings
from pathlib import Path
import numpy as np
import pandas as pd
import soundfile as sf
import sklearn.decomposition._nmf
from sklearn.decomposition import NMF
HERE=Path(__file__).resolve().parent;WORK=HERE.parent
spec=importlib.util.spec_from_file_location('h78_previous',WORK/'H78_context/experiment.py');previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
REPO=previous.REPO;core=previous.core;audit=previous.audit
from pyin25_adapter import pitch
from pyin_energy_experiment import energy,reject
GRID=np.arange(201,dtype=float)*40.
CONFIG=dict(rank=4,init='nndsvda',solver='cd',beta_loss='frobenius',tol=1e-6,max_iter=2000,random_state=79,alpha_W=0.,alpha_H=0.,l1_ratio=0.,shuffle=False)

def spectrum(audio,fs):
    e=energy(audio,fs);length=int(e['frame_samples']);hop=int(e['hop_samples']);frames=np.lib.stride_tricks.sliding_window_view(audio,length)[::hop];means=frames.mean(axis=1);win=np.hamming(length);fft=np.fft.rfft((frames-means[:,None])*win,axis=1);freq=np.fft.rfftfreq(length,1/fs)
    x=np.asarray([np.interp(GRID,freq,np.abs(row)/length) for row in fft])/float(e['reference'])
    return dict(x=x,fft=fft,means=means,window=win,frequency=freq,**e)

def noise_component(coefficients,basis,ranges,bank):
    scores=[];mass=basis.sum(axis=1)
    for name,start,end in ranges:
        a=coefficients[start:end]*mass;low=bank[name]['relative_rms']<=np.quantile(bank[name]['relative_rms'],.2,method='linear')
        scores.append(np.mean(a[low],axis=0)/np.maximum(np.mean(a,axis=0),1e-12))
    scores=np.mean(scores,axis=0);return int(np.argmax(scores)),scores

def gain(coefficients,basis,k):
    reconstruction=coefficients@basis;noise=coefficients[:,k,None]*basis[k,None,:]
    ratio=np.divide(noise,reconstruction,out=np.zeros_like(noise),where=reconstruction>0);return np.clip(1-ratio,0,1)

def reconstruct(audio,spectral,mask):
    length=int(spectral['frame_samples']);hop=int(spectral['hop_samples']);result=np.zeros(len(audio));norm=np.zeros(len(audio));win=spectral['window']
    for j,row in enumerate(spectral['fft']):
        # >8 kHz is retained, since both device rates share only 0..8 kHz.
        g=np.interp(spectral['frequency'],GRID,mask[j],right=1.);frame=np.fft.irfft(row*g,n=length)/win+spectral['means'][j];start=j*hop;result[start:start+length]+=frame*win**2;norm[start:start+length]+=win**2
    covered=norm>0;result[covered]/=norm[covered];result[~covered]=audio[~covered];return result

def fit_model(names,bank):
    counts={n:len(bank[n]['x']) for n in names};total=sum(counts.values());ranges=[];xs=[];scales=[];cursor=0
    for n in names:
        s=np.sqrt(total/(len(names)*counts[n]));xs.extend(bank[n]['x']*s);scales.extend([s]*counts[n]);ranges.append((n,cursor,cursor+counts[n]));cursor+=counts[n]
    x=np.asarray(xs);scales=np.asarray(scales);model=NMF(n_components=CONFIG['rank'],**{k:v for k,v in CONFIG.items() if k!='rank'})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always');w=model.fit_transform(x)
    original=w/scales[:,None];k,scores=noise_component(original,model.components_,ranges,bank)
    return model,dict(x=x,w=w,h=model.components_,scales=scales),dict(fit_files=names,ranges=ranges,noise_component=k,noise_proxy_scores=scores.tolist(),iterations=int(model.n_iter_),reconstruction_error=float(model.reconstruction_err_),warnings=[str(t.message) for t in caught])

def check_registry():
    r=json.loads((HERE/'REGISTRY.json').read_text());assert r['config']==CONFIG
    for p,d in r['source_hashes'].items():assert audit.digest(REPO/p)==d,p
    for p,d in r['external_protected'].items():assert audit.digest(Path(p))==d,p
    return r

def precheck(out):
    assert not out.exists() and not (HERE/'REGISTRY.json').exists();out.mkdir();from verify import scalar_spectrum,scalar_reconstruct
    fs=16000;t=np.arange(fs//2)/fs;audio=.1*np.sin(2*np.pi*173*t)+.01*np.random.default_rng(79).normal(size=len(t));s=spectrum(audio,fs);ref=scalar_spectrum(audio,fs)
    assert np.allclose(s['x'],ref,atol=1e-10,rtol=1e-10);unity=reconstruct(audio,s,np.ones_like(s['x']));assert np.allclose(unity,audio,atol=1e-10)
    mask=np.full_like(s['x'],.4);filtered=reconstruct(audio,s,mask);assert np.allclose(filtered,scalar_reconstruct(audio,fs,mask),atol=1e-10)
    bank={'synthetic':s};m,p,log=fit_model(['synthetic'],bank);assert np.min(p['w'])>=0 and np.min(p['h'])>=0 and np.isclose(np.linalg.norm(p['x']-p['w']@p['h']),log['reconstruction_error'])
    g=gain(p['w'],p['h'],log['noise_component']);assert np.all(np.isfinite(g)) and np.all((g>=0)&(g<=1))
    audit.json_write(out/'final_info.json',dict(status='PASS',BT2_used=False,synthetic_nmf_fits=1,synthetic_log=log,scalar_spectrum_overlap_add=True,unity_mask_identity=True,nonnegative_factorization_mask=True))
    old=previous.check_registry();sources=dict(old['source_hashes']);complete=json.loads((WORK/'H78_context/run_train/completion.json').read_text());sources.update(complete['artifacts']);paths=[HERE/p for p in ('experiment.py','verify.py','plot.py','notes.txt','REGISTRATION.md')]+[out/'final_info.json',WORK/'H78_context/REGISTRY.json',WORK/'H78_context/run_train/completion.json']
    for p in paths:sources[str(p.relative_to(REPO))]=audit.digest(p)
    external=dict(old['external_protected']);p=Path(inspect.getfile(sklearn.decomposition._nmf));external[str(p)]=audit.digest(p)
    git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip()
    audit.json_write(HERE/'REGISTRY.json',dict(family='H79',rollback=head,config=CONFIG,source_hashes=sources,external_protected=external,frequency_grid=GRID.tolist(),frame_ms=25,hop_ms=10,noise_mapping='argmax fit-pool mean low-energy/all activation-mass ratio',mapping_uses_LAB=False,test_used_for_selection=False,historical_test_exposure=True))
    print('PASS H79 synthetic spectrum/NMF/mask/overlap-add; no BT2 fitting',flush=True)

def train(out):
    check_registry();assert not out.exists();git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip();branch=subprocess.check_output(git+['branch','--show-current'],cwd=REPO,text=True).strip()
    assert subprocess.check_output(git+['ls-remote','origin','refs/heads/'+branch],cwd=REPO,text=True).split()[0]==head and not subprocess.check_output(git+['status','--porcelain'],cwd=REPO,text=True).strip();out.mkdir()
    from verify_srh import independent_item
    bank={};items={};audio_bank={}
    for path in sorted(core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');s=spectrum(audio,fs);assert np.array_equal(item['times'],s['times']);bank[path.name]=s;items[path.name]=item;audio_bank[path.name]=(audio,fs);np.savez_compressed(out/f'spectrum_{path.stem}.npz',**s)
    names=sorted(bank);logs=[];decomp=[];metrics=[];pitch_logs=[]
    print('H79: five NMF fits on train pools; four new pYIN calls on filtered full-train signals',flush=True)
    for held in ['full']+names:
        pool=[n for n in names if n!=held];model,proof,log=fit_model(pool,bank);log['held']=held;tag='full' if held=='full' else 'without_'+Path(held).stem;np.savez_compressed(out/f'model_{tag}.npz',**proof)
        coefficients={n:proof['w'][start:end]/proof['scales'][start:end,None] for n,start,end in log['ranges']}
        if held!='full':
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always');coefficients[held]=model.transform(bank[held]['x'])
            log['transform_warnings']=[str(t.message) for t in caught]
        logs.append(log)
        for n in (names if held=='full' else [held]):
            c=coefficients[n];mask=gain(c,proof['h'],log['noise_component']);np.savez_compressed(out/f'decomposition_{tag}_{Path(n).stem}.npz',coefficients=c,mask=mask)
            shares=(c*proof['h'].sum(axis=1));shares/=np.maximum(shares.sum(axis=1,keepdims=True),1e-12);labels=items[n]['labels']
            for label in ('v','uv','sil'):
                chosen=labels==label
                for k in range(CONFIG['rank']):decomp.append(dict(held=held,file=n,label=label,frames=int(sum(chosen)),component=k,mean_contribution=float(shares[chosen,k].mean()) if chosen.any() else np.nan,candidate_noise=k==log['noise_component']))
            if held!='full':continue
            original,fs=audio_bank[n];filtered=reconstruct(original,bank[n],mask);sf.write(str(out/f'speech_candidate_{Path(n).stem}.wav'),filtered,fs,subtype='DOUBLE');sf.write(str(out/f'noise_candidate_{Path(n).stem}.wav'),original-filtered,fs,subtype='DOUBLE')
            native,plog=pitch(filtered,fs,[2,8]);e=energy(filtered,fs);assert np.array_equal(native['native_times'],items[n]['times']);pred,f0=reject(native['voiced'],native['raw_f0'],e['relative_rms'],.07)
            metrics.append(dict(pipeline_id='H79_nmf4_pyin25_energy07',eval_split='train',**core.score_file(items[n],pred,f0)));pitch_logs.append(dict(file=n,**plog));np.savez_compressed(out/f'pitch_{Path(n).stem}.npz',**native,**{k:v for k,v in e.items() if k not in native},pred=pred,f0=f0);print('H79 filtered train measured',n,flush=True)
    old=pd.read_csv(WORK/'H78_context/run_train/all_train_metrics.csv',float_precision='round_trip');baseline=old[old.option_id=='energy07'].copy();baseline['pipeline_id']='H72_energy07_cached';baseline['eval_split']='train';metrics+=baseline.to_dict('records')
    pd.DataFrame(metrics).to_csv(out/'all_train_metrics.csv',index=False);pd.DataFrame(decomp).to_csv(out/'component_audit.csv',index=False);audit.json_write(out/'models.json',logs);audit.json_write(out/'pitch_logs.json',pitch_logs);artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in out.iterdir()}
    audit.json_write(out/'final_info.json',dict(status='MEASURED',family='H79',prereg_commit=head,nmf_fits=5,held_transforms=4,new_native_inferences=4,original_native_rerun=False,new_train_metrics=4,cached_controls=4,test_used=False,artifacts=artifacts,limitation='Low-energy component is a noise candidate, not clean-source ground truth. NMF components may separate phonetics/speakers; no SI-SDR claim.'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--action',choices=['precheck','train'],required=True);p.add_argument('--out_dir',required=True);a=p.parse_args();precheck(Path(a.out_dir).resolve()) if a.action=='precheck' else train(Path(a.out_dir).resolve())
