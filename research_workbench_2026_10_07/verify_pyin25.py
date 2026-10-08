"""Source-backed pYIN integration; independent timestamps, metrics and selection."""
import json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
def certify_native(proof,input_samples,fs):
    length=round(.025*fs);hop=round(.01*fs)
    assert int(proof['native_fs'])==fs and int(proof['frame_samples'])==length and int(proof['hop_samples'])==hop
    starts=list(range(0,input_samples-length+1,hop));times=np.array([(s+length/2)/fs for s in starts]);f=proof['raw_f0'];p=proof['voiced'];prob=proof['probability']
    assert len(f)==len(starts) and np.array_equal(times,proof['native_times'])
    assert np.array_equal(np.isfinite(f),p) and np.all((f[p]>=70)&(f[p]<=400))
    assert np.isfinite(prob).all() and np.all((prob>=0)&(prob<=1))
    return dict(frames=len(starts),frame_samples=length,hop_samples=hop,actual_frame_ms=1000*length/fs,actual_hop_ms=1000*hop/fs,independent_start_center_range_mask_probability=True)
def verify():
    import pyin25_experiment as api
    from verify_srh import independent_item,independent_score
    from verify_ar_nls import independent_choose
    from voicing_recovery import gates
    reg=api.check_registry();r=json.loads((api.OUT/'H69_train_experiment.json').read_text())
    for p,d in reg['external_protected'].items():assert api.audit.digest(Path(p))==d,p
    for p,d in r['artifacts'].items():assert api.audit.digest(api.REPO/p)==d,p
    old=pd.read_csv(api.OUT/'H47_nested_contours.csv',float_precision='round_trip');table=pd.read_csv(api.OUT/'H69_fixed.csv',float_precision='round_trip');checks=[];expected_changes=[]
    for path in sorted(api.core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');base=old[(old.file==path.name)&(old.model=='candidate')];bp,bf=base.pred_voiced.to_numpy(bool),base.f0_hz.to_numpy();prediction=dict(np.load(api.OUT/f'H69_predictions_{path.stem}.npz'));assert np.array_equal(prediction['times'],item['times'])
        for k,option in enumerate(api.OPTIONS):
            if option['mode']=='baseline':p,f=bp,bf;cert=dict(assignment_compliant=False)
            else:
                proof=dict(np.load(api.OUT/f'H69_native_{path.stem}_{option["id"]}.npz'));cert=certify_native(proof,len(audio),fs);p,f=proof['voiced'],proof['raw_f0'];cert['assignment_compliant']=True
            assert np.array_equal(p,prediction['pred'][k]) and np.allclose(f,prediction['f0'][k],equal_nan=True,atol=0,rtol=0)
            metrics=independent_score(item,p,f);row=table[(table.file==path.name)&(table.option_id==option['id'])].iloc[0]
            for key,value in metrics.items():assert np.isclose(value,row[key],atol=1e-9,rtol=1e-9),(path,key)
            for i in range(len(p)):
                if p[i]!=bp[i] or (p[i] and f[i]!=bf[i]):expected_changes.append((path.name,option['id'],i))
            checks.append(dict(file=path.name,option_id=option['id'],voiced_count=int(p.sum()),integration_certificate=cert))
        print('H69 verified',path.name,flush=True)
    changes=pd.read_csv(api.OUT/'H69_changed_cases.csv');assert list(zip(changes.file,changes.option_id,changes.frame))==expected_changes
    records=table.to_dict('records');names=sorted(table.file.unique());selections=[]
    inner=pd.read_csv(api.OUT/'H69_inner_traces.csv',float_precision='round_trip',keep_default_na=False)
    for held in ['final']+names:
        pool=[n for n in names if n!=held];selections.append(dict(outer_held=held,selection_files=pool,option_id=independent_choose([v for v in records if v['file'] in pool])));group=inner[inner.outer_held==held]
        assert len(group)==len(pool)*len(api.OPTIONS) and set(group.inner_held)==set(pool) and (group.actual_fit_files=='').all()
        for _,row in group.iterrows():
            original=next(v for v in records if v['file']==row['file'] and v['option_id']==row.option_id)
            for key,value in original.items():assert row[key]==value,(held,key)
    assert selections==r['selections'];selection={v['outer_held']:v['option_id'] for v in selections};summary=pd.read_csv(api.OUT/'H69_metrics.csv',float_precision='round_trip')
    for _,row in summary.iterrows():
        identity='hard170' if row.model=='accepted' else selection[row['file']] if row.split=='nested' else selection['final'];assert row.option_id==identity
        original=next(v for v in records if v['file']==row['file'] and v['option_id']==identity)
        for key,value in original.items():assert row[key]==value
    _,decision=gates(summary);assert decision==r['decision']
    logs=json.loads((api.OUT/'H69_runtime_logs.json').read_text())
    for row in logs:
        for p,d in row['source_hashes'].items():assert api.audit.digest(Path(p))==d,p
        path=api.core.TRAIN/row['file'];_,fs,audio=independent_item(path,'train');assert hashlib.sha256(np.ascontiguousarray(audio,dtype=np.float64).tobytes()).hexdigest()==row['PCM_sha256'];assert row['frame_samples']==round(.025*fs) and row['hop_samples']==round(.01*fs) and not row['center'] and not row['audio_padding']
    api.audit.json_write(api.OUT/'H69_verification.json',dict(status='PASS',groups=len(checks),checks=checks,independent_timestamp_mask_range_scalar_metrics_selection=True,source_runtime_protected_output_hashes=True,inner_summary_changedcase_membership=True,assignment_compliant_new_options=True,historical_control_compliant=False,limitation='Official pYIN candidate probabilities/Viterbi are source-backed, not independently reimplemented; immutable historical gate reused; hard170 is research control only.'))
    print('PASS H69',len(checks),'groups; real25ms/10ms new options')
if __name__=='__main__':verify()
