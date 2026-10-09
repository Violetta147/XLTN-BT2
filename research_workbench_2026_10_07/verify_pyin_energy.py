"""H70 independent scalar RMS, quantile, rejection, metrics and selection."""
import json, math
from pathlib import Path
import numpy as np
import pandas as pd

def scalar_energy(audio,fs):
    length,hop=round(.025*fs),round(.01*fs);starts=list(range(0,len(audio)-length+1,hop));values=[]
    for s in starts:
        frame=[float(v) for v in audio[s:s+length]];mean=math.fsum(frame)/length
        values.append(math.sqrt(math.fsum((v-mean)**2 for v in frame)/length))
    ordered=sorted(values);position=.95*(len(ordered)-1);left=math.floor(position);right=math.ceil(position)
    reference=max(ordered[left]+(position-left)*(ordered[right]-ordered[left]),1e-12)
    return dict(rms=np.array(values),relative_rms=np.array([v/reference for v in values]),reference=reference,times=np.array([(s+length/2)/fs for s in starts]))

def strict_choose(records):
    choices=[]
    for name in sorted({r['option_id'] for r in records if r['option_id']!='hard170'}):
        rows=[r for r in records if r['option_id']==name]
        if all(math.isfinite(r['average_mape']) for r in rows):choices.append((max(r['average_mape'] for r in rows),sum(r['average_mape'] for r in rows)/len(rows),name))
    return min(choices)[-1] if choices else None

def same(a,b):
    return a==b or (isinstance(a,(float,np.floating)) and np.isnan(a) and pd.isna(b))

def verify():
    import pyin_energy_experiment as api
    from verify_srh import independent_item,independent_score
    from verify_ar_nls import independent_choose
    from voicing_recovery import gates
    reg=api.check_registry();receipt=json.loads((api.OUT/'H70_train_experiment.json').read_text());assert api.audit.digest(api.HERE/'H70_REGISTRY.json')==receipt['registry_sha256']
    for path,digest in receipt['artifacts'].items():assert api.audit.digest(api.REPO/path)==digest,path
    fixed=pd.read_csv(api.OUT/'H70_fixed.csv',float_precision='round_trip');energy_rows=pd.read_csv(api.OUT/'H70_energy_frames.csv',float_precision='round_trip');removed=pd.read_csv(api.OUT/'H70_removed_frames.csv',float_precision='round_trip');prior=pd.read_csv(api.OUT/'H69_fixed.csv',float_precision='round_trip');control=pd.read_csv(api.OUT/'H47_nested_contours.csv',float_precision='round_trip');checks=[];expected_removed=[]
    for path in sorted(api.core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');proof=dict(np.load(api.OUT/f'H70_proof_{path.stem}.npz'));manual=scalar_energy(audio,fs);native=dict(np.load(api.OUT/f'H69_native_{path.stem}_pyin25_beta2_8.npz'))
        assert int(proof['frame_samples'])==round(.025*fs) and int(proof['hop_samples'])==round(.01*fs) and int(proof['fs'])==fs
        for key in ('rms','relative_rms','reference'):assert np.allclose(proof[key],manual[key],atol=1e-12,rtol=1e-12),(path,key)
        assert np.array_equal(proof['times'],manual['times']) and np.array_equal(proof['times'],item['times']) and np.array_equal(proof['times'],native['native_times'])
        energies=energy_rows[energy_rows.file==path.name];assert np.array_equal(energies.frame,np.arange(len(item['times']))) and np.array_equal(energies.label,item['labels']) and np.array_equal(energies.pyin8_voiced,native['voiced'])
        assert np.allclose(energies.relative_rms,manual['relative_rms'],rtol=1e-12,atol=1e-12) and np.allclose(energies.rms,manual['rms'],rtol=1e-12,atol=1e-12) and np.array_equal(energies.time_s,item['times'])
        old=control[(control.file==path.name)&(control.model=='candidate')];assert np.allclose(old.time_s,item['times'],rtol=0,atol=1e-12)
        for k,option in enumerate(api.OPTIONS):
            if option['threshold'] is None:pred,f0=old.pred_voiced.to_numpy(bool),old.f0_hz.to_numpy()
            else:
                pred=np.array([bool(v) and float(e)>=option['threshold'] for v,e in zip(native['voiced'],manual['relative_rms'])]);f0=np.array([float(f) if p else np.nan for p,f in zip(pred,native['raw_f0'])])
                for i in range(len(pred)):
                    if native['voiced'][i] and not pred[i]:expected_removed.append((path.name,option['id'],i,item['times'][i],item['labels'][i],float(proof['relative_rms'][i]),float(native['raw_f0'][i])))
                assert not np.any(pred & ~native['voiced'])
                assert np.array_equal(f0[pred],native['raw_f0'][pred])
            assert np.array_equal(pred,proof['pred'][k]) and np.allclose(f0,proof['f0'][k],atol=0,rtol=0,equal_nan=True)
            metrics=independent_score(item,pred,f0);row=fixed[(fixed.file==path.name)&(fixed.option_id==option['id'])].iloc[0]
            for key,value in metrics.items():assert np.isclose(value,row[key],atol=1e-9,rtol=1e-9,equal_nan=True),(path,option['id'],key)
            if option['threshold'] is None or option['threshold']==0:
                identity='hard170' if option['threshold'] is None else 'pyin25_beta2_8';cached=prior[(prior.file==path.name)&(prior.option_id==identity)].iloc[0]
                for key,value in metrics.items():assert np.isclose(value,cached[key],atol=1e-9,rtol=1e-9,equal_nan=True)
            checks.append(dict(file=path.name,option_id=option['id'],voiced_count=int(pred.sum()),assignment_compliant=option['threshold'] is not None,scalar_rms_quantile_mask_unchanged_pitch_metrics=True))
    expected=pd.DataFrame(expected_removed,columns=['file','option_id','frame','time_s','label','relative_rms','removed_f0']);assert len(expected)==len(removed)
    for key in expected.columns:
        if key in ('time_s','relative_rms','removed_f0'):assert np.allclose(expected[key],removed[key],rtol=1e-12,atol=1e-12)
        else:assert np.array_equal(expected[key],removed[key])
    records=fixed.to_dict('records');names=sorted(fixed.file.unique());inner=pd.read_csv(api.OUT/'H70_inner_traces.csv',float_precision='round_trip',keep_default_na=False,na_values={key:[''] for key in fixed.select_dtypes(include='number').columns});selections=[];strict=[]
    for held in ['final']+names:
        pool=[n for n in names if n!=held];rows=[r for r in records if r['file'] in pool];selections.append(dict(outer_held=held,selection_files=pool,option_id=independent_choose(rows)));strict.append(dict(outer_held=held,selection_files=pool,option_id=strict_choose(rows)));group=inner[inner.outer_held==held];assert len(group)==len(pool)*len(api.OPTIONS) and set(group.inner_held)==set(pool) and (group.actual_fit_files=='').all()
        for _,row in group.iterrows():
            original=next(r for r in rows if r['file']==row['file'] and r['option_id']==row.option_id)
            for key,value in original.items():assert same(value,row[key]),(held,key)
    assert selections==receipt['selections'] and strict==receipt['strict_diagnostic_selections'];selected={r['outer_held']:r['option_id'] for r in selections};summary=pd.read_csv(api.OUT/'H70_metrics.csv',float_precision='round_trip');assert len(summary)==24
    for _,row in summary.iterrows():
        identity='hard170' if row.model=='accepted' else selected[row['file']] if row.split=='nested' else selected['final'];assert row.option_id==identity;original=next(r for r in records if r['file']==row['file'] and r['option_id']==identity)
        for key,value in original.items():assert same(value,row[key])
    _,decision=gates(summary);assert decision==receipt['decision']
    api.audit.json_write(api.OUT/'H70_verification.json',dict(status='PASS',groups=len(checks),checks=checks,independent_scalar_rms_linear_quantile=True,mask_pitch_metrics_cached_control_parity=True,removed_energy_inner_summary_membership=True,selections_and_immutable_gates=True,protected_source_runtime_output_hashes=True,new_native_inferences=0,limitation='No reimplementation of pYIN or new per-frame F0 ground truth; strict selection is exploratory finite minimax diagnostic, not promotion.'))
    print('PASS H70',len(checks),'groups; scalar energy and unchanged-pitch rejection')
if __name__=='__main__':verify()
