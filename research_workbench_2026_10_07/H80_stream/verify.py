"""Independent resampling, NNLS KKT, context, clusters, path and evaluations."""
import importlib.util,itertools,json,math,sys
from pathlib import Path
import numpy as np
import pandas as pd
import soundfile as sf
from scipy.signal import upfirdn
import experiment as api

def resample(audio,fs):
    if fs==16000:return audio.copy()
    g=math.gcd(fs,16000);up,down=16000//g,fs//g;rate=max(up,down);half=10*rate;offset=np.arange(2*half+1)-half;h=np.sinc(offset/rate)/rate*np.kaiser(2*half+1,5.);h*=up/math.fsum(map(float,h));pad=down-half%down;h=np.r_[np.zeros(pad),h];remove=(half+pad)//down;count=(len(audio)*up+down-1)//down
    return upfirdn(h,audio,up,down,mode='constant',cval=0)[remove:remove+count]

def brute_path(emission,penalty):
    options=[]
    for path in itertools.product((0,1),repeat=len(emission)):
        cost=math.fsum(float(emission[j,k]) for j,k in enumerate(path))+penalty*sum(path[j]!=path[j-1] for j in range(1,len(path)));options.append((cost,path))
    cost,path=min(options);return np.asarray(path),cost

def scalar_match(pred,true):
    best=None
    def visit(i,used,errors):
        nonlocal best
        if i==len(true):
            rank=(-len(errors),math.fsum(errors));
            if best is None or rank<best[0]:best=(rank,list(errors))
            return
        visit(i+1,used,errors)
        for j,v in enumerate(pred):
            error=abs(v-true[i])
            if j not in used and error<=api.CONFIG['boundary_tolerance_s']:visit(i+1,used|{j},errors+[error])
    visit(0,set(),[]);n=-best[0][0]
    return dict(predicted_boundaries=len(pred),true_boundaries=len(true),matched=n,precision=n/max(len(pred),1),recall=n/max(len(true),1),mean_abs_error_s=float(np.mean(best[1])) if n else None)

def ari(a,b):
    choose=lambda n:n*(n-1)/2
    cells={};rows={};cols={}
    for x,y in zip(a,b):cells[(x,y)]=cells.get((x,y),0)+1;rows[x]=rows.get(x,0)+1;cols[y]=cols.get(y,0)+1
    total=choose(len(a));r=sum(choose(n) for n in rows.values());c=sum(choose(n) for n in cols.values());actual=sum(choose(n) for n in cells.values());expected=r*c/total if total else 0;den=(r+c)/2-expected
    return (actual-expected)/den if den else 1.

def verify(out):
    api.check_registry();r=json.loads((out/'final_info.json').read_text())
    for p,d in r['artifacts'].items():assert api.audit.digest(api.REPO/p)==d,p
    basis=np.load(api.WORK/'H79_nmf/run_train/model_full.npz')['h'];model=json.loads((out/'locked_clusters.json').read_text());table=pd.read_csv(out/'stream_metrics.csv',float_precision='round_trip');truths=json.loads((out/'evaluation_only_labels.json').read_text())
    spec=importlib.util.spec_from_file_location('h79_scalar',api.WORK/'H79_nmf/verify.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);helper.api=api.previous
    bank={}
    for n in api.ORDER:a,fs=sf.read(api.core.TRAIN/n,dtype='float64');bank[n]=resample(a,fs)
    max_gradient=0
    for identity,order in [('primary',api.ORDER),('reverse',api.ORDER[::-1])]:
        audio=np.concatenate([bank[n] for n in order]);saved,fs=sf.read(out/f'{identity}_stream.wav');assert fs==16000 and np.allclose(audio,saved,atol=1e-12);manifest=json.loads((out/f'{identity}_manifest.json').read_text());cursor=0
        for n,m in zip(order,manifest):assert m['file']==n and m['start_sample']==cursor and m['end_sample']==cursor+len(bank[n]);cursor=m['end_sample']
        p=dict(np.load(out/f'{identity}_proof.npz'));x=helper.scalar_spectrum(audio,16000);assert np.allclose(x,p['spectrum'],atol=1e-10,rtol=1e-9);coeff=p['coefficients'];assert np.min(coeff)>=0
        gradient=(coeff@basis-x)@basis.T;projected=np.where(coeff>1e-9,gradient,np.minimum(gradient,0));error=float(np.max(abs(projected)));max_gradient=max(max_gradient,error);assert error<1e-7
        mass=coeff*basis.sum(axis=1);shares=mass/np.maximum(mass.sum(axis=1,keepdims=True),1e-12);power=x**2;high=np.asarray([math.fsum(map(float,row[25:]))/max(math.fsum(map(float,row)),1e-12) for row in power]);logr=np.log(np.maximum(p['relative_rms'],1e-12));expected=[]
        from verify_pyin_energy import scalar_energy
        energy=scalar_energy(audio,16000);assert np.allclose(energy['relative_rms'],p['relative_rms'],atol=1e-10) and np.array_equal(energy['times'],p['frame_times'])
        for (start,end),t in zip(p['block_ranges'],p['block_times']):
            assert start%25==0 and end==min(start+25,len(x)) and end-start>=5
            expected.append([float(np.quantile(logr[start:end],.2,method='linear')),float(np.median(high[start:end])),*[math.fsum(map(float,shares[start:end,k]))/(end-start) for k in range(4)]]);assert abs(float(t)-math.fsum(map(float,p['frame_times'][start:end]))/(end-start))<1e-12
        expected=np.asarray(expected);assert np.allclose(expected,p['x'],atol=1e-10)
        if identity=='primary':
            mean=np.asarray([math.fsum(map(float,expected[:,j]))/len(expected) for j in range(6)]);var=np.asarray([math.fsum((float(v)-mean[j])**2 for v in expected[:,j])/len(expected) for j in range(6)]);assert np.allclose(mean,model['mean'],atol=1e-10) and np.allclose(var,model['variance'],atol=1e-10);assert np.allclose(np.where(var<=len(expected)*np.finfo(float).eps*var+(len(expected)*mean*np.finfo(float).eps)**2,1.,np.sqrt(var)),model['scale'],atol=1e-10)
        z=(expected-model['mean'])/model['scale'];centers=np.asarray(model['centers']);e=np.asarray([[math.fsum((float(v)-float(c))**2 for v,c in zip(row,center))/2 for center in centers] for row in z]);raw=np.argmin(e,axis=1);assert np.allclose(z,p['z'],atol=1e-10) and np.allclose(e,p['emission'],atol=1e-10) and np.array_equal(raw,p['raw_labels'])
        if identity=='primary':
            assert np.array_equal(raw,model['fit_labels'])
            for k in (0,1):assert np.allclose(centers[k],z[raw==k].mean(axis=0),atol=1e-9)
            assert np.isclose(math.fsum(float(e[i,k])*2 for i,k in enumerate(raw)),model['inertia'],atol=1e-9)
        decoded=p['decoded_labels'];pathcost=math.fsum(float(e[j,k]) for j,k in enumerate(decoded))+3.*sum(decoded[j]!=decoded[j-1] for j in range(1,len(decoded)));cost=[float(v) for v in e[0]]
        for row in e[1:]:cost=[float(row[k])+min(cost[k],cost[1-k]+3.) for k in (0,1)]
        assert np.isclose(pathcost,min(cost),atol=1e-9) and np.isclose(pathcost,p['path_cost'],atol=1e-9)
        names=[next(m['file'] for m in manifest if m['start_sample']<=float(t)*16000<m['end_sample']) for t in p['block_times']];domain=[int(n.startswith('studio')) for n in names];sex=[int('_M' in n) for n in names];files=[api.ORDER.index(n) for n in names];true=[m['end_sample']/16000 for m in manifest[:-1]]
        for method,labels in [('raw',raw),('decoded',decoded)]:
            pred=[(float(p['block_times'][j-1])+float(p['block_times'][j]))/2 for j in range(1,len(labels)) if labels[j]!=labels[j-1]];score=scalar_match(pred,true);row=table[(table.stream==identity)&(table.method==method)].iloc[0];truth=next(t for t in truths if t['stream']==identity and t['method']==method);assert truth['files']==names and truth['domains']==domain and truth['sex']==sex and truth['file_ids']==files and truth['predicted_boundaries_s']==pred and truth['true_boundaries_s']==true
            for k,v in score.items():assert np.isclose(row[k],np.nan if v is None else v,atol=1e-10,equal_nan=True),(identity,method,k)
            for k,gt in [('domain_ARI',domain),('sex_ARI',sex),('file_ARI',files)]:assert np.isclose(row[k],ari(gt,labels),atol=1e-12)
            expected_accuracy=max(sum(int(a==b) for a,b in zip(labels,domain)),sum(int(1-a==b) for a,b in zip(labels,domain)))/len(labels);assert np.isclose(row.domain_accuracy_up_to_permutation,expected_accuracy,atol=1e-12)
    assert len(table)==4 and r['kmeans_fits']==1 and r['new_pitch_inferences']==0
    api.audit.json_write(out/'verification.json',dict(status='PASS',streams=2,independent_FIR_resampling_concat_spectral_context=True,NNLS_KKT_max_gradient=max_gradient,centroid_assignment_SSE=True,temporal_global_cost_and_boundary_matching=True,ARI_contingency_and_mapping_audit=True,labels_evaluation_only=True,limitation='Same four recordings in both orders; no unseen-source evaluation or F0 MAPE measurement.'))
    print('PASS H80 physical streams, NNLS, clusters, temporal optimum and independent ARI/boundaries',flush=True)

if __name__=='__main__':verify(Path(sys.argv[1]).resolve())
