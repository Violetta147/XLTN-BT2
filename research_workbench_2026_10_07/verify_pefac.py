"""Verify stored official stages, canonical projection, scalar metrics and CV."""
import json, math
import numpy as np
import pandas as pd
from pathlib import Path
def independent_projection(proof,times,fs,option,base_pred,base_f0):
    output=np.full(len(times),np.nan);pred=np.zeros(len(times),bool)
    for i,t in enumerate(times):
        k=min(range(len(proof['native_times'])),key=lambda j:(abs(float(proof['native_times'][j])-t),j))
        pitch=float(proof['raw_f0'][k]);valid=abs(float(proof['native_times'][k])-t)<=.005+1/fs and 70<=pitch<=400
        if valid and (option['mode']=='pitch_only' or float(proof['pv'][k])>option['threshold']):output[i]=pitch;pred[i]=True
    if option['mode']=='pitch_only':
        for i in range(len(times)):
            if not base_pred[i]:output[i]=np.nan
            elif not np.isfinite(output[i]):output[i]=base_f0[i]
        pred=base_pred.copy()
    return pred,output
def verify():
    import pefac_experiment as api
    from verify_srh import independent_item,independent_score
    from verify_ar_nls import independent_choose
    from pefac_certificate import certify
    from voicing_recovery import gates
    reg=api.check_registry();r=json.loads((api.OUT/'H68_train_experiment.json').read_text())
    for p,d in reg['external_protected'].items():assert api.audit.digest(Path(p))==d,p
    for p,d in r['artifacts'].items():assert api.audit.digest(api.REPO/p)==d,p
    old=pd.read_csv(api.OUT/'H47_nested_contours.csv',float_precision='round_trip')
    table=pd.read_csv(api.OUT/'H68_fixed.csv',float_precision='round_trip');checks=[];expected_changes=[]
    for path in sorted(api.core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');base=old[(old.file==path.name)&(old.model=='candidate')]
        bp,bf=base.pred_voiced.to_numpy(bool),base.f0_hz.to_numpy()
        proof=dict(np.load(api.OUT/f'H68_native_{path.stem}.npz'));stage=certify(proof)
        prediction=dict(np.load(api.OUT/f'H68_predictions_{path.stem}.npz'));assert np.array_equal(prediction['times'],item['times'])
        for k,option in enumerate(api.OPTIONS):
            p,f=(bp.copy(),bf.copy()) if option['mode']=='baseline' else independent_projection(proof,item['times'],fs,option,bp,bf)
            assert np.array_equal(p,prediction['pred'][k]) and np.allclose(f,prediction['f0'][k],equal_nan=True,atol=0,rtol=0)
            metrics=independent_score(item,p,f);row=table[(table.file==path.name)&(table.option_id==option['id'])].iloc[0]
            for key,value in metrics.items():assert np.isclose(value,row[key],atol=1e-9,rtol=1e-9),(path,key)
            for i in range(len(p)):
                if p[i]!=bp[i] or (p[i] and f[i]!=bf[i]):expected_changes.append((path.name,option['id'],i))
            checks.append(dict(file=path.name,option_id=option['id'],voiced_count=int(p.sum()),stage_certificate=stage))
        print('H68 verified',path.name,flush=True)
    changes=pd.read_csv(api.OUT/'H68_changed_cases.csv');assert list(zip(changes.file,changes.option_id,changes.frame))==expected_changes
    records=table.to_dict('records');names=sorted(table.file.unique());selections=[]
    inner=pd.read_csv(api.OUT/'H68_inner_traces.csv',float_precision='round_trip',keep_default_na=False)
    for held in ['final']+names:
        pool=[n for n in names if n!=held]
        selections.append(dict(outer_held=held,selection_files=pool,option_id=independent_choose([r for r in records if r['file'] in pool])))
        group=inner[inner.outer_held==held];assert len(group)==len(pool)*len(api.OPTIONS) and set(group.inner_held)==set(pool) and (group.actual_fit_files=='').all()
        for _,row in group.iterrows():
            original=next(v for v in records if v['file']==row['file'] and v['option_id']==row.option_id)
            for key,value in original.items():assert row[key]==value,(held,key)
    assert selections==r['selections'];selection={v['outer_held']:v['option_id'] for v in selections}
    summary=pd.read_csv(api.OUT/'H68_metrics.csv',float_precision='round_trip')
    for _,row in summary.iterrows():
        identity='hard170' if row.model=='accepted' else selection[row['file']] if row.split=='nested' else selection['final']
        assert row.option_id==identity
        original=next(v for v in records if v['file']==row['file'] and v['option_id']==identity)
        for key,value in original.items():assert row[key]==value
    _,decision=gates(summary);assert decision==r['decision']
    logs=json.loads((api.OUT/'H68_runtime_logs.json').read_text())
    for row in logs:
        for key in ('exe','image_filter','image_pad','source'):assert api.audit.digest(Path(row[key]))==row[key+'_sha256']
    api.audit.json_write(api.OUT/'H68_verification.json',dict(status='PASS',groups=len(checks),checks=checks,independent_gmm_dp_projection_metrics_selection=True,source_runtime_protected_output_hashes=True,inner_summary_membership=True,changed_case_membership=True,limitation='Certifies stored GMM features/peaks and DP; no independent upstream spectral/LTASS reconstruction or frame-F0 truth; immutable gate implementation reused.'))
    print('PASS H68',len(checks),'groups; official stage certificates')
if __name__=='__main__':verify()
