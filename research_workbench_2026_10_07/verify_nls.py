import json
import numpy as np
import pandas as pd
from scipy.linalg import qr


def qr_residual(segment,fs,frequency,order):
    time=np.array([(i-(len(segment)-1)/2)/fs for i in range(len(segment))])
    columns=[np.ones(len(segment))]
    columns += [np.cos(2*np.pi*h*frequency*time) for h in range(1,order+1)]
    columns += [np.sin(2*np.pi*h*frequency*time) for h in range(1,order+1)]
    weights=np.sqrt(.5-.5*np.cos(2*np.pi*np.arange(len(segment))/(len(segment)-1)))
    design=np.column_stack(columns)*weights[:,None];target=segment*weights
    q,r=qr(design,mode='economic');error=target-q@(q.T@target)
    return float(error@error)


def verify():
    import nls_experiment as api
    from verify_srh import independent_item,independent_score
    from voicing_recovery import gates
    from threadpoolctl import threadpool_limits
    api.check_registry();receipt=json.loads((api.OUT/'H61_train_experiment.json').read_text())
    for p,d in receipt['artifacts'].items():assert api.audit.digest(api.REPO/p)==d,p
    fixed=pd.read_csv(api.OUT/'H61_fixed.csv',float_precision='round_trip')
    old=pd.read_csv(api.OUT/'H47_nested_contours.csv',float_precision='round_trip');checks=[]
    with threadpool_limits(limits=1):
        for path in sorted(api.core.TRAIN.glob('*.wav')):
            item,fs,audio=independent_item(path,'train');length,hop=round(fs*.025),round(fs*.01)
            saved=dict(np.load(api.OUT/f'H61_predictions_{path.stem}.npz'))
            baseline=old[(old.file==path.name)&(old.model=='candidate')]
            pred=baseline.pred_voiced.to_numpy(bool);base=baseline.f0_hz.to_numpy()
            assert np.array_equal(pred,saved['pred']) and np.array_equal(item['times'],saved['times'])
            for k,option in enumerate(api.OPTIONS):
                f0=saved['f0'][k];assert np.array_equal(np.isfinite(f0),pred)
                if not option['order']:assert np.allclose(f0,base,equal_nan=True,rtol=0,atol=0)
                else:
                    p=dict(np.load(api.OUT/f'H61_{option["id"]}_{path.stem}.npz'))
                    assert np.array_equal(p['indices'],np.flatnonzero(pred)) and np.array_equal(p['f0'],f0[p['indices']])
                    for j,i in enumerate(p['indices']):
                        segment=audio[i*hop:i*hop+length]
                        lower=max(70,base[i]*2**(-100/1200));upper=min(400,base[i]*2**(100/1200))
                        assert lower-1e-8<=f0[i]<=upper+1e-8
                        cost=qr_residual(segment,fs,f0[i],option['order'])
                        assert np.isclose(cost,p['cost'][j],rtol=1e-8,atol=1e-10)
                        grid=np.unique(np.clip(base[i]*2**(np.arange(-100,101,5)/1200),lower,upper))
                        grid_cost=[qr_residual(segment,fs,f,option['order']) for f in grid]
                        assert cost <= min(grid_cost)+1e-9
                        best=int(np.argmin(grid_cost));bracket=np.array([grid[max(0,best-1)],grid[min(len(grid)-1,best+1)]])
                        assert np.allclose(bracket,p['bracket'][j],atol=1e-8)
                        assert bracket[0]-1e-8<=f0[i]<=bracket[1]+1e-8
                metrics=independent_score(item,pred,f0)
                row=fixed[(fixed.file==path.name)&(fixed.option_id==option['id'])].iloc[0]
                for key,val in metrics.items():assert np.isclose(val,row[key],rtol=1e-9,atol=1e-9),(path,key)
                checks.append(dict(file=path.name,option_id=option['id'],voiced_frames=int(pred.sum())))
            print('H61 verified',path.name,flush=True)
    # Independent selector implementation from the earlier reference audit.
    import yaapt_extension as previous
    from verify_yaapt_extension_v2 import independent_choose
    old_options=previous.BY_ID;previous.BY_ID={o['id']:o for o in api.OPTIONS}
    try:
        records=fixed.to_dict('records');names=sorted(fixed.file.unique());selections=[]
        for held in ['final']+names:
            pool=[n for n in names if n!=held]
            selections.append(dict(outer_held=held,selection_files=pool,
                option_id=independent_choose([r for r in records if r['file'] in pool])))
    finally:previous.BY_ID=old_options
    assert selections==receipt['selections']
    _,decision=gates(pd.read_csv(api.OUT/'H61_metrics.csv'));assert decision==receipt['decision']
    api.audit.json_write(api.OUT/'H61_verification.json',dict(status='PASS',groups=len(checks),checks=checks,
        independent_qr_basis_weighted_residual_grid_bracket=True,
        independent_grid_metrics_selection=True,mask_count_invariant=True,
        limitation='Independent QR verifies objective/grid/local bracket; optimizer is not independently rerun.'))
    print('PASS H61',len(checks),'groups')


if __name__=='__main__':verify()
