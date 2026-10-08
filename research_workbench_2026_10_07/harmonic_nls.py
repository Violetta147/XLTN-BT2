"""Custom bounded weighted harmonic regression; not the fastF0Nls source port."""
import numpy as np
from scipy.optimize import minimize_scalar

OFFSETS=np.linspace(-100,100,41)


def basis(length,fs,frequency,order):
    time=(np.arange(length)-(length-1)/2)/fs
    angles=2*np.pi*time[:,None]*frequency*np.arange(1,order+1)[None,:]
    return np.column_stack((np.ones(length),np.cos(angles),np.sin(angles)))


def residual(segment,fs,frequency,order):
    weight=np.sqrt(np.hanning(len(segment)))
    matrix=basis(len(segment),fs,frequency,order)*weight[:,None]
    target=segment*weight
    coefficients,_,rank,_=np.linalg.lstsq(matrix,target,rcond=None)
    assert rank==matrix.shape[1]
    error=target-matrix@coefficients
    return float(error@error),coefficients


def refine(segment,fs,anchor,order):
    lower=max(70.,anchor*2**(-100/1200));upper=min(400.,anchor*2**(100/1200))
    grid=np.unique(np.clip(anchor*2**(OFFSETS/1200),lower,upper))
    costs=np.array([residual(segment,fs,f,order)[0] for f in grid])
    k=int(np.argmin(costs))
    left,right=grid[max(0,k-1)],grid[min(len(grid)-1,k+1)]
    candidates=[(costs[k],grid[k])]
    if right>left:
        result=minimize_scalar(lambda logf:residual(segment,fs,np.exp(logf),order)[0],
            bounds=(np.log(left),np.log(right)),method='bounded',options=dict(xatol=1e-8,maxiter=100))
        if result.success and np.isfinite(result.fun):candidates.append((float(result.fun),float(np.exp(result.x))))
    cost,f0=min(candidates,key=lambda x:(x[0],x[1]))
    verified_cost,coefficients=residual(segment,fs,f0,order)
    assert np.isclose(cost,verified_cost,atol=1e-12)
    return dict(f0=f0,cost=cost,grid=grid,grid_cost=costs,coefficients=coefficients,
                bracket=np.array([left,right]),at_boundary=bool(np.isclose(f0,lower,atol=1e-4) or np.isclose(f0,upper,atol=1e-4)))
