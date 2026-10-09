"""Unlabeled clustering and temporal decoding of physically concatenated audio."""
import argparse,importlib.util,inspect,itertools,json,math,subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import soundfile as sf
import scipy.signal._signaltools,scipy.optimize._nnls,sklearn.cluster._kmeans
from scipy.signal import resample_poly
from scipy.optimize import nnls
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
HERE=Path(__file__).resolve().parent;WORK=HERE.parent
spec=importlib.util.spec_from_file_location('h79_nmf',WORK/'H79_nmf/experiment.py');previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
REPO=previous.REPO;core=previous.core;audit=previous.audit
ORDER=['phone_F1.wav','studio_F1.wav','phone_M1.wav','studio_M1.wav']
CONFIG=dict(fs=16000,frame_ms=25,hop_ms=10,block_frames=25,minimum_last_block=5,n_clusters=2,n_init=10,random_state=80,max_iter=300,tol=1e-4,algorithm='lloyd',switch_penalty=3.,boundary_tolerance_s=.35)

def stream(bank,order):
    pieces=[];manifest=[];cursor=0
    for n in order:
        audio,fs=bank[n];g=math.gcd(fs,CONFIG['fs']);piece=resample_poly(audio,CONFIG['fs']//g,fs//g,window=('kaiser',5.),padtype='constant') if fs!=CONFIG['fs'] else audio.copy()
        manifest.append(dict(file=n,original_fs=fs,start_sample=cursor,end_sample=cursor+len(piece),up=CONFIG['fs']//g,down=fs//g));pieces.append(piece);cursor+=len(piece)
    return np.concatenate(pieces),manifest

def features(audio,basis):
    s=previous.spectrum(audio,CONFIG['fs']);coeff=np.asarray([nnls(basis.T,row,maxiter=120)[0] for row in s['x']]);mass=coeff*basis.sum(axis=1);shares=mass/np.maximum(mass.sum(axis=1,keepdims=True),1e-12);power=s['x']**2;high=power[:,previous.GRID>=1000].sum(axis=1)/np.maximum(power.sum(axis=1),1e-12);log_rms=np.log(np.maximum(s['relative_rms'],1e-12));rows=[];times=[];ranges=[]
    for start in range(0,len(coeff),CONFIG['block_frames']):
        end=min(start+CONFIG['block_frames'],len(coeff))
        if end-start<CONFIG['minimum_last_block']:continue
        rows.append([float(np.quantile(log_rms[start:end],.2,method='linear')),float(np.median(high[start:end])),*shares[start:end].mean(axis=0)]);times.append(float(s['times'][start:end].mean()));ranges.append((start,end))
    return dict(x=np.asarray(rows),block_times=np.asarray(times),block_ranges=np.asarray(ranges),coefficients=coeff,spectrum=s['x'],relative_rms=s['relative_rms'],frame_times=s['times'])

def decode(z,centers):
    emission=np.sum((z[:,None,:]-centers[None,:,:])**2,axis=2)/2.;cost=emission[0].copy();back=[]
    for row in emission[1:]:
        candidate=cost[:,None]+CONFIG['switch_penalty']*(1-np.eye(2));prev=np.argmin(candidate,axis=0);cost=row+candidate[prev,np.arange(2)];back.append(prev)
    last=int(np.argmin(cost));labels=[last]
    for prev in reversed(back):last=int(prev[last]);labels.append(last)
    return np.asarray(labels[::-1]),emission,float(min(cost))

def boundaries(times,labels):return [(float(times[j-1])+float(times[j]))/2 for j in range(1,len(labels)) if labels[j]!=labels[j-1]]

def match(pred,true):
    candidates=[]
    for assignment in itertools.product(range(-1,len(pred)),repeat=len(true)):
        used=[j for j in assignment if j>=0]
        if len(used)!=len(set(used)):continue
        errors=[abs(pred[j]-true[i]) for i,j in enumerate(assignment) if j>=0]
        if any(e>CONFIG['boundary_tolerance_s'] for e in errors):continue
        candidates.append((-len(errors),sum(errors),assignment,errors))
    best=min(candidates,key=lambda x:x[:3]);matched=-best[0];return dict(predicted_boundaries=len(pred),true_boundaries=len(true),matched=matched,precision=matched/max(len(pred),1),recall=matched/max(len(true),1),mean_abs_error_s=float(np.mean(best[3])) if matched else None)

def evaluate(times,labels,manifest):
    names=[]
    for t in times:names.append(next(m['file'] for m in manifest if m['start_sample']<=t*CONFIG['fs']<m['end_sample']))
    domains=np.asarray([int(n.startswith('studio')) for n in names]);sex=np.asarray([int('_M' in n) for n in names]);files=np.asarray([ORDER.index(n) for n in names]);pred=boundaries(times,labels);true=[m['end_sample']/CONFIG['fs'] for m in manifest[:-1]];score=match(pred,true)
    score.update(domain_ARI=float(adjusted_rand_score(domains,labels)),sex_ARI=float(adjusted_rand_score(sex,labels)),file_ARI=float(adjusted_rand_score(files,labels)),domain_accuracy_up_to_permutation=max(float(np.mean(labels==domains)),float(np.mean(1-labels==domains))))
    return score,dict(files=names,domains=domains.tolist(),sex=sex.tolist(),file_ids=files.tolist(),predicted_boundaries_s=pred,true_boundaries_s=true)

def check_registry():
    r=json.loads((HERE/'REGISTRY.json').read_text());assert r['config']==CONFIG and r['order']==ORDER
    for p,d in r['source_hashes'].items():assert audit.digest(REPO/p)==d,p
    for p,d in r['external_protected'].items():assert audit.digest(Path(p))==d,p
    return r

def precheck(out):
    assert not out.exists() and not (HERE/'REGISTRY.json').exists();out.mkdir()
    from verify import brute_path,scalar_match
    z=np.asarray([[0.,0.],[.2,.1],[3.,3.],[3.2,3.1]]);centers=np.asarray([[0.,0.],[3.,3.]]);labels,e,cost=decode(z,centers);expected=brute_path(e,CONFIG['switch_penalty']);assert np.array_equal(labels,expected[0]) and abs(cost-expected[1])<1e-12
    for pred,true in [([1.,2.,3.],[1.1,2.1,3.1]),([1.,1.2],[1.1]),([],[1.])]:assert match(pred,true)==scalar_match(pred,true)
    audio=np.sin(2*np.pi*173*np.arange(4410)/44100);joined,m=stream({'a':(audio,44100),'b':(np.ones(1600),16000)},['a','b']);assert len(joined)==3200 and m[0]['end_sample']==1600 and m[1]['start_sample']==1600
    audit.json_write(out/'final_info.json',dict(status='PASS',BT2_used=False,synthetic_fits=0,bruteforce_temporal_optimum=True,matching_corner_cases=True,physical_resampling_concat_lengths=True))
    old=previous.check_registry();sources=dict(old['source_hashes']);complete=json.loads((WORK/'H79_nmf/run_train/completion.json').read_text());sources.update(complete['artifacts']);paths=[HERE/p for p in ('experiment.py','verify.py','plot.py','notes.txt','REGISTRATION.md')]+[out/'final_info.json',WORK/'H79_nmf/REGISTRY.json',WORK/'H79_nmf/run_train/completion.json']
    for p in paths:sources[str(p.relative_to(REPO))]=audit.digest(p)
    external=dict(old['external_protected'])
    for module in (scipy.signal._signaltools,scipy.optimize._nnls,sklearn.cluster._kmeans):p=Path(inspect.getfile(module));external[str(p)]=audit.digest(p)
    git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip()
    audit.json_write(HERE/'REGISTRY.json',dict(family='H80',rollback=head,config=CONFIG,order=ORDER,source_hashes=sources,external_protected=external,domain_labels_used_for_fitting=False,physical_sample_rate_shared=True,NMF_basis_reused_from_H79=True,pitch_inferences=0,test_used=False,historical_test_exposure=True))
    print('PASS H80 synthetic temporal/matching/concat checks; no BT2 fitting',flush=True)

def train(out):
    check_registry();assert not out.exists();git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip();branch=subprocess.check_output(git+['branch','--show-current'],cwd=REPO,text=True).strip()
    assert subprocess.check_output(git+['ls-remote','origin','refs/heads/'+branch],cwd=REPO,text=True).split()[0]==head and not subprocess.check_output(git+['status','--porcelain'],cwd=REPO,text=True).strip();out.mkdir()
    bank={}
    for n in ORDER:audio,fs=sf.read(core.TRAIN/n,dtype='float64');bank[n]=(audio,fs)
    basis=np.load(WORK/'H79_nmf/run_train/model_full.npz')['h'];model=None;rows=[];evaluations=[]
    print('H80: same-rate physical streams, fixed NMF basis, one unlabeled KMeans fit; no pitch inference',flush=True)
    for identity,order in [('primary',ORDER),('reverse',ORDER[::-1])]:
        audio,manifest=stream(bank,order);sf.write(out/f'{identity}_stream.wav',audio,CONFIG['fs'],subtype='DOUBLE');f=features(audio,basis)
        if model is None:
            scaler=StandardScaler().fit(f['x']);z=scaler.transform(f['x']);km=KMeans(n_clusters=2,n_init=10,random_state=80,max_iter=300,tol=1e-4,algorithm='lloyd').fit(z);model=dict(mean=scaler.mean_.tolist(),variance=scaler.var_.tolist(),scale=scaler.scale_.tolist(),centers=km.cluster_centers_.tolist(),fit_labels=km.labels_.tolist(),iterations=int(km.n_iter_),inertia=float(km.inertia_));audit.json_write(out/'locked_clusters.json',model)
        else:z=(f['x']-model['mean'])/model['scale']
        decoded,emission,cost=decode(z,np.asarray(model['centers']));raw=np.argmin(emission,axis=1);np.savez_compressed(out/f'{identity}_proof.npz',**f,z=z,raw_labels=raw,decoded_labels=decoded,emission=emission,path_cost=np.asarray(cost));audit.json_write(out/f'{identity}_manifest.json',manifest)
        for method,labels in [('raw',raw),('decoded',decoded)]:
            score,truth=evaluate(f['block_times'],labels,manifest);rows.append(dict(stream=identity,method=method,**score));evaluations.append(dict(stream=identity,method=method,**truth))
        print('H80 stream measured',identity,flush=True)
    pd.DataFrame(rows).to_csv(out/'stream_metrics.csv',index=False);audit.json_write(out/'evaluation_only_labels.json',evaluations);artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in out.iterdir()}
    audit.json_write(out/'final_info.json',dict(status='MEASURED',family='H80',prereg_commit=head,kmeans_fits=1,NMF_basis_fits=0,NNLS_stream_transforms=2,streams=2,new_pitch_inferences=0,test_used=False,domain_labels_used_for_fitting=False,reverse_is_same_sources_reordered=True,artifacts=artifacts,limitation='Both streams reuse four training recordings; reverse is an order diagnostic, not unseen-file validation or improved F0 MAPE.'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--action',choices=['precheck','train'],required=True);p.add_argument('--out_dir',required=True);a=p.parse_args();precheck(Path(a.out_dir).resolve()) if a.action=='precheck' else train(Path(a.out_dir).resolve())
