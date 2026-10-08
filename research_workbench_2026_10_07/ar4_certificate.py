"""Independent QR noise fit + scalar conditional filtering certificate."""
import math
import numpy as np
from scipy.linalg import qr
from verify_ar_nls import independent_design
def independent_certificate(segment,fs,anchor,order,frequency):
    n=len(segment); w=np.sqrt(.5-.5*np.cos(2*np.pi*np.arange(n)/(n-1)))
    if not np.any(segment-segment[0]):
        return dict(cost=0.,a=np.zeros(4),a_raw=np.zeros(4),rho=0.,rho_raw=0.,grid_cost=np.zeros(41),bracket=np.array([anchor,anchor]),boundary=False,silent=True)
    matrix=independent_design(n,fs,anchor,order)
    q,r=qr(matrix*w[:,None],mode='economic');b=np.linalg.solve(r,q.T@(segment*w));error=segment-matrix@b
    lags=np.array([[error[i-k] for k in range(1,5)] for i in range(4,n)])
    q,r=qr(lags,mode='economic');raw=np.linalg.solve(r,q.T@error[4:]);size=sum(abs(float(x)) for x in raw);a=raw*(.95/size if size>.95 else 1.)
    def objective(f):
        matrix=independent_design(n,fs,f,order)
        transformed=np.array([matrix[i]-sum(a[k-1]*matrix[i-k] for k in range(1,5)) for i in range(4,n)])*w[4:,None]
        target=np.array([segment[i]-sum(a[k-1]*segment[i-k] for k in range(1,5)) for i in range(4,n)])*w[4:]
        q,_=qr(transformed,mode='economic');e=target-q@(q.T@target);return float(e@e)
    lower=max(70.,anchor*2**(-1/12));upper=min(400.,anchor*2**(1/12))
    grid=np.array(sorted(set(min(upper,max(lower,anchor*2**(k/1200))) for k in range(-100,101,5))))
    costs=np.array([objective(f) for f in grid]);best=int(np.argmin(costs));bracket=np.array([grid[max(0,best-1)],grid[min(len(grid)-1,best+1)]])
    cost=objective(frequency)
    assert bracket[0]-1e-8<=frequency<=bracket[1]+1e-8 and cost<=min(costs)+1e-9
    return dict(cost=cost,a=a,a_raw=raw,rho=float(a[0]),rho_raw=float(raw[0]),grid_cost=costs,bracket=bracket,boundary=bool(np.isclose(frequency,lower,atol=1e-4) or np.isclose(frequency,upper,atol=1e-4)),silent=False)
