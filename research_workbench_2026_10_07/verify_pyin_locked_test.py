"""H72 verify locked test config, raw cache, scalar energy, metrics and hashes."""
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from verify_srh import independent_item,independent_score
from verify_pyin25_v2 import certify_native
from verify_pyin_energy import scalar_energy

def verify():
    import pyin_locked_test as api
    reg=api.check_registry();r=json.loads((api.OUT/'H72_test_experiment.json').read_text());assert r['locked_config']==api.CONFIG and r['registry_sha256']==api.audit.digest(api.HERE/'H72_REGISTRY.json')
    for p,d in r['artifacts'].items():assert api.audit.digest(api.REPO/p)==d,p
    table=pd.read_csv(api.OUT/'H72_all_files.csv',float_precision='round_trip');old=pd.read_csv(api.OUT/'H71_fixed.csv',float_precision='round_trip');train=table[table.eval_split=='train'];checks=[]
    for _,row in train.iterrows():
        source=old[(old.file==row['file'])&(old.option_id=='pyin8_energy_0.07')].iloc[0]
        for key in old.columns:assert row[key]==source[key],key
    assert len(train)==4 and len(table)==8 and table.file.nunique()==8 and (table.pipeline_id==api.CONFIG['pipeline_id']).all()
    for path in sorted(api.TEST.glob('*.wav')):
        item,fs,audio=independent_item(path,'test');proof=dict(np.load(api.OUT/f'H72_test_proof_{path.stem}.npz'));cert=certify_native(proof,len(audio),fs);energy=scalar_energy(audio,fs)
        assert np.array_equal(proof['times'],item['times']) and np.array_equal(proof['native_times'],energy['times'])
        for key in ('rms','relative_rms','reference'):assert np.allclose(proof[key],energy[key],atol=1e-12,rtol=1e-12),key
        pred=np.array([bool(p) and float(e)>=.07 for p,e in zip(proof['voiced'],energy['relative_rms'])]);f0=np.array([float(f) if p else np.nan for p,f in zip(pred,proof['raw_f0'])]);assert np.array_equal(pred,proof['pred']) and np.allclose(f0,proof['f0'],atol=0,rtol=0,equal_nan=True)
        metrics=independent_score(item,pred,f0);row=table[(table.file==path.name)&(table.eval_split=='test')].iloc[0]
        for key,value in metrics.items():assert np.isclose(value,row[key],atol=1e-9,rtol=1e-9,equal_nan=True),(path,key)
        checks.append(dict(file=path.name,voiced_count=int(pred.sum()),native_certificate=cert,scalar_energy_mask_unchanged_pitch_metrics=True))
    logs=json.loads((api.OUT/'H72_runtime_logs.json').read_text());assert len(logs)==4 and {v['file'] for v in logs}=={p.name for p in api.TEST.glob('*.wav')}
    for log in logs:
        for p,d in log['source_hashes'].items():assert api.audit.digest(Path(p))==d,p
        _,fs,audio=independent_item(api.TEST/log['file'],'test');assert hashlib.sha256(np.ascontiguousarray(audio,dtype=np.float64).tobytes()).hexdigest()==log['PCM_sha256'];assert log['beta_parameters']==[2,8] and not log['center'] and not log['audio_padding'] and log['frame_samples']==round(.025*fs) and log['hop_samples']==round(.01*fs)
    all8=bool(np.isfinite(table.average_mape).all() and (table.average_mape<2).all());assert all8==r['user_all8_target_pass'] and r['actual_native_inferences']==4 and not r['parameter_search_on_test'] and not r['train_inference_repeated'] and not r['historical_H71_decision_modified']
    api.audit.json_write(api.OUT/'H72_verification.json',dict(status='PASS',test_groups=4,train_cached_groups=4,checks=checks,locked_config_and_train_parity=True,scalar_RMS_quantile_timestamp_mask_metric=True,PCM_source_runtime_protected_output_hashes=True,all8_criterion_verified=True,limitation='Native pYIN candidate probabilities/Viterbi are pinned source-backed, not independently reimplemented; test historically exposed; original H71 gates preserved.'))
    print('PASS H72 four new test + four cached train groups')
if __name__=='__main__':verify()
