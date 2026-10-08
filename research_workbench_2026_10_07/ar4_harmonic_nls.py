"""Custom residual AR(4) conditional weighted NLS; not paper's joint ML solver."""
import numpy as np
from scipy.optimize import minimize_scalar
from harmonic_nls import basis, OFFSETS

def noise_parameter(segment, fs, anchor, order=3):
    weights=np.sqrt(np.hanning(len(segment)))
    design=basis(len(segment),fs,anchor,order)
    beta,_,rank,_=np.linalg.lstsq(design*weights[:,None],segment*weights,rcond=None)
    assert rank==design.shape[1]
    r=segment-design@beta
    lags=np.column_stack([r[4-k:len(r)-k] for k in range(1,5)])
    raw=np.linalg.lstsq(lags,r[4:],rcond=None)[0]
    norm=float(np.sum(np.abs(raw)))
    # Sufficient stability bound, deliberately conservative, not root reflection.
    a=raw*min(1.,.95/norm) if norm else raw.copy()
    return a,raw

def whiten(values,a):
    coefficients=np.broadcast_to(np.asarray(a), (4,))
    out=values[4:].copy()
    for k in range(1,5):out-=coefficients[k-1]*values[4-k:len(values)-k]
    return out

def residual(segment,fs,frequency,order,a):
    weights=np.sqrt(np.hanning(len(segment)))[4:]
    matrix=whiten(basis(len(segment),fs,frequency,order),a)*weights[:,None]
    target=whiten(segment,a)*weights
    beta,_,rank,_=np.linalg.lstsq(matrix,target,rcond=None)
    assert rank==matrix.shape[1]
    r=target-matrix@beta
    return float(r@r),beta

def refine(segment,fs,anchor,order=3):
    assert order==3
    lower,upper=max(70.,anchor*2**(-100/1200)),min(400.,anchor*2**(100/1200))
    grid=np.unique(np.clip(anchor*2**(OFFSETS/1200),lower,upper))
    if not np.any(segment-segment[0]):
        return dict(f0=float(anchor),cost=0.,score=0.,a=np.zeros(4),a_raw=np.zeros(4),rho=0.,rho_raw=0.,grid=grid,grid_cost=np.zeros(len(grid)),bracket=np.array([anchor,anchor]),at_boundary=False,silent_fallback=True)
    a,raw=noise_parameter(segment,fs,anchor,order)
    costs=np.array([residual(segment,fs,f,order,a)[0] for f in grid]);best=int(np.argmin(costs))
    left,right=grid[max(0,best-1)],grid[min(len(grid)-1,best+1)]
    candidates=[(costs[best],grid[best])]
    if right>left:
        optimized=minimize_scalar(lambda logf:residual(segment,fs,np.exp(logf),order,a)[0],bounds=(np.log(left),np.log(right)),method='bounded',options=dict(xatol=1e-8,maxiter=100))
        if optimized.success and np.isfinite(optimized.fun):candidates.append((float(optimized.fun),float(np.exp(optimized.x))))
    cost,f=min(candidates,key=lambda p:(p[0],p[1]))
    return dict(f0=float(f),cost=float(cost),score=float(-cost),a=a,a_raw=raw,rho=float(a[0]),rho_raw=float(raw[0]),grid=grid,grid_cost=costs,bracket=np.array([left,right]),at_boundary=bool(np.isclose(f,lower,atol=1e-4) or np.isclose(f,upper,atol=1e-4)),silent_fallback=False)
