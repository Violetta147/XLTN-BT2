"""Independent GMM log-density and DP of stored upstream PEFAC stages."""
import re, math
import numpy as np
from scipy.special import logsumexp,expit
from pathlib import Path
SOURCE=Path(__file__).resolve().parent/'vendor/voicebox_pefac/v_fxpefac.m'
def gaussian_log(features,kind):
    source=SOURCE.read_text()
    def numbers(s):return np.array([float(x) for x in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',s)])
    weights=numbers(re.search(r'w_'+kind+r'=\[(.*?)\]',source,re.S)[1])
    means=numbers(re.search(r'm_'+kind+r'=\[(.*?)\]',source,re.S)[1]).reshape(6,2)
    cov=numbers(re.search(r'v_'+kind+r'=reshape\(\[(.*?)\]',source,re.S)[1]).reshape(6,2,2)
    terms=[]
    for weight,mean,matrix in zip(weights,means,cov):
        delta=features-mean
        assert np.allclose(matrix,matrix.T) and np.linalg.det(matrix)>0
        quadratic=np.sum((delta@np.linalg.inv(matrix))*delta,axis=1)
        terms.append(math.log(weight)-math.log(2*math.pi)-.5*np.linalg.slogdet(matrix)[1]-.5*quadratic)
    return logsumexp(np.column_stack(terms),axis=1)
def certify(proof):
    ff=np.asarray(proof['ff']);amp=np.asarray(proof['amp']);pv=np.asarray(proof['pv']);times=np.asarray(proof['native_times']);w=np.asarray(proof['w']);n,k=ff.shape
    assert k==3 and np.isfinite(ff).all() and np.isfinite(amp).all()
    assert np.allclose(w,[1,.825,.01868,.006773,98.9,-.4238],atol=1e-12)
    probability=expit(gaussian_log(proof['vuvfea'],'v')-gaussian_log(proof['vuvfea'],'u'))
    assert np.allclose(pv,probability,atol=1e-10,rtol=1e-10)
    step=float(times[1]-times[0]);factor=2/step;assert np.isclose(float(proof['dffact']),factor,atol=1e-10)
    with np.errstate(divide='ignore',invalid='ignore'):camp=-amp/amp.max(axis=1)[:,None]
    camp[amp==0]=w[4]
    window=round(2/step)
    def median_frequency(position,mask_pv):
        # Match documented upstream legacy indexing, including the first window mask.
        for threshold in (.6,.5,.4,.3):
            selected=position[:len(mask_pv)][mask_pv>threshold]
            if len(selected):return float(np.median(selected))
        return 0.
    med=median_frequency(ff[:min(window,n),0],pv[:min(window,n)])
    costs=np.empty_like(ff);back=np.zeros((n,k),int);costs[0]=w[0]*camp[0]
    medians=[med]
    for i in range(1,n):
        if i+1>window:med=median_frequency(ff[i-window:i+1,0],pv[:window])
        medians.append(med)
        with np.errstate(divide='ignore',invalid='ignore'):
            df=factor*(ff[i,:,None]-ff[i-1,None,:])/(ff[i,:,None]+ff[i-1,None,:])
        transition=w[2]*np.fmin((df-w[5])**2,w[3])
        possibilities=transition+costs[i-1][None,:]
        back[i]=np.argmin(possibilities,axis=1)
        deviation=abs(ff[i]-med)/med if med else np.zeros(k)
        costs[i]=possibilities[np.arange(k),back[i]]+w[1]*deviation+w[0]*camp[i]
    assert np.isfinite(costs).all() and np.allclose(proof['medfx'],medians,atol=1e-10,rtol=1e-10)
    path=np.zeros(n,int);path[-1]=int(np.argmin(costs[-1]))
    for i in range(n-1,0,-1):path[i-1]=back[i,path[i]]
    assert np.array_equal(path+1,proof['best'])
    assert np.array_equal(ff[np.arange(n),path],proof['raw_f0'])
    return dict(native_frames=n,independent_gmm_max_abs_error=float(np.max(abs(pv-probability))),independent_dp_path=True,optimal_final_cost=float(costs[-1,path[-1]]),limitation='Uses stored spectral peaks/features; does not independently reconstruct spectrogram, LTASS compression or peaks.')
