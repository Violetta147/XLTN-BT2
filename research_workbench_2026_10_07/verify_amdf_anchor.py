import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import wavfile

import verify_amdf_loop
from verify_results import digest

HERE=Path(__file__).resolve().parent
REPO=HERE.parent


def main():
    verify_amdf_loop.verify('H41','praat7_filtered_v0.3')
    result=json.loads((HERE/'results/H41_experiment.json').read_text())
    options=json.loads((HERE/'H41_REGISTRY.json').read_text())['options']
    raw=pd.read_csv(HERE/'results/H41_raw_native_frames.csv',float_precision='round_trip')
    contours=pd.read_csv(HERE/'results/H41_nested_contours.csv')
    fixed=pd.read_csv(HERE/'results/H41_fixed_lofo.csv').set_index(['option_id','file'])
    praat=json.loads((HERE/'results/praat_native_7002_provenance.json').read_text())
    assert digest(praat['exe'])==praat['exe_sha256']==result['environment']['native_exe_sha256']
    assert len(result['native_calls'])==40 and len(raw.groupby(['option_id','file']))==40
    assert len(result['source_calls'])==4
    assert set(raw.option_id)=={x['id'] for x in options}
    curve_cache={}
    curve_rows=0
    checked=0
    for file in sorted(result['data_sha256']):
        fs,pcm=wavfile.read(REPO/'TinHieuHuanLuyen'/file)
        assert pcm.dtype==np.int16 and pcm.ndim==1
        canonical=contours[(contours.model=='accepted')&(contours.file==file)]
        times=canonical.time_s.to_numpy()
        labels=canonical.label.to_numpy()
        gt={}
        for line in (REPO/'research_3gt_2026_10_05/train_3gt'/file.replace('.wav','.lab')).read_text().splitlines():
            key,value=line.split()[:2]
            if key in ('F0mean','F0std','F0num'):
                gt[key]=float(value)
        for option in options:
            identity=option['id']
            group=raw[(raw.option_id==identity)&(raw.file==file)]
            nt,nf=group.time_s.to_numpy(),group.raw_f0_hz.to_numpy()
            assert np.isfinite(nf).all() and (nf>=0).all()
            assert np.array_equal(group.raw_voiced.to_numpy(),nf>0)
            call=result['native_calls'][identity+'|'+file]
            assert call['native_frames']==len(group)
            base=raw[(raw.option_id=='praat7_filtered_v0.3')&(raw.file==file)]
            bt,bf=base.time_s.to_numpy(),base.raw_f0_hz.to_numpy()
            assert np.allclose(nt,bt,atol=1e-12) and np.array_equal(nf>0,bf>0)
            assert call['returncode']==0 and call['command']==[praat['exe'],'--run',str(HERE/'praat_extract_native.praat'),str(REPO/'TinHieuHuanLuyen'/file),'filtered','0.3']
            assert call['script_sha256']==digest(HERE/'praat_extract_native.praat') and call['exe_sha256']==praat['exe_sha256']
            assert np.allclose(np.diff(nt),.01,atol=1e-12)
            assert call['rule_sha256']==digest(HERE/'amdf_anchor.py')
            assert call['output_f0_sha256']==hashlib.sha256(np.ascontiguousarray(nf,dtype=np.float64).tobytes()).hexdigest()
            sourcecall=result['source_calls']['praat7_filtered_v0.3|'+file]
            assert call['command']==sourcecall['command'] and call['stdout_sha256']==sourcecall['stdout_sha256']
            if option['method']=='control':
                assert call['AMDF_evidence'] is None
            else:
                evidence=call['AMDF_evidence']
                assert evidence['sha256']==digest(HERE/evidence['path'])
                assert evidence['source_sha256']==digest(HERE/'amdf_anchor.py')
                assert evidence['frozen_notebook_sha256']==digest(REPO/'research_3gt_2026_10_05/baselines/AMDF.ipynb')
                key=(option['amdf_window_ms'],file)
                if key not in curve_cache:
                    data=dict(np.load(HERE/evidence['path'],allow_pickle=False))
                    length=round(fs*option['amdf_window_ms']/1000)
                    assert int(data['frame_samples'])==length and int(data['fs'])==fs and int(data['input_samples'])==len(pcm)
                    audio=np.ascontiguousarray(pcm.astype(np.float64)/32768)
                    assert str(data['audio_sha256'])==hashlib.sha256(audio.tobytes()).hexdigest()
                    assert np.allclose(data['times'],bt,atol=1e-12) and np.array_equal(data['gate_frequency'],bf)
                    starts=np.array([round(t*fs-length/2) for t in bt])
                    assert np.array_equal(data['starts'],starts)
                    lag_grid=np.arange(max(1,int(np.floor(fs/400))),min(length-1,int(np.ceil(fs/70)))+1)
                    assert np.array_equal(data['lags'],lag_grid)
                    for i,(start,gate) in enumerate(zip(starts,bf)):
                        supported=70<=gate<=400 and start>=0 and start+length<=len(audio)
                        if not supported:
                            assert np.isnan(data['curve'][i]).all() and str(data['frame_sha256'][i])==''
                            continue
                        frame=audio[start:start+length]
                        assert str(data['frame_sha256'][i])==hashlib.sha256(frame.tobytes()).hexdigest()
                        centered=frame-frame.mean()
                        if abs(centered).mean()<1e-8:
                            fresh=np.ones(len(lag_grid))
                        else:
                            fresh=np.array([abs(centered[:-lag]-centered[lag:]).mean()/(abs(centered[:-lag]).mean()+abs(centered[lag:]).mean()+1e-12) for lag in lag_grid])
                        assert np.allclose(data['curve'][i],fresh,atol=1e-12,rtol=1e-12)
                        curve_rows+=1
                    curve_cache[key]=data
                    print('Verified independent NAMDF curves',key,flush=True)
                data=curve_cache[key]
                selected=np.full(len(bf),-1,dtype=int)
                fresh_f0=bf.copy()
                tags=np.where(bf>0,'praat_control','unvoiced').astype('<U32')
                for i in np.flatnonzero((bf>=70)&(bf<=400)):
                    curve=data['curve'][i]
                    if not np.isfinite(curve).all():
                        tags[i]='praat_window_unsupported'
                        continue
                    if np.ptp(curve)<=1e-12:
                        tags[i]='praat_no_candidate'
                        continue
                    dip_indices=np.array([j for j in range(1,len(curve)-1) if curve[j]<=curve[j-1] and curve[j]<=curve[j+1]],dtype=int)
                    if not len(dip_indices):
                        dip_indices=np.array([int(np.argmin(curve))])
                    allowed=[]
                    finite_candidates=0
                    for j in dip_indices:
                        lag=float(data['lags'][j])
                        if 0<j<len(curve)-1:
                            a,b,c=curve[j-1:j+2]
                            denominator=a-2*b+c
                            if abs(denominator)>1e-12:
                                delta=.5*(a-c)/denominator
                                if abs(delta)<=1:
                                    lag+=float(delta)
                        frequency=fs/lag
                        if not 70<=frequency<=400:
                            continue
                        finite_candidates+=1
                        deviation=abs(1200*np.log2(frequency/bf[i]))
                        if deviation<=option['agreement_cents']+1e-9:
                            allowed.append((float(curve[j]),float(deviation),float(frequency),int(j)))
                    if allowed:
                        _,_,fresh_f0[i],selected[i]=min(allowed)
                        tags[i]='amdf_dip'
                    else:
                        tags[i]='praat_disagreement' if finite_candidates else 'praat_no_candidate'
                assert np.allclose(nf,fresh_f0,atol=1e-10)
                assert call['selected_curve_indices']==selected.tolist() and call['source']==tags.tolist()
            indices=np.array([int(np.argmin(abs(nt-t))) for t in times])
            support=abs(nt[indices]-times)<=.005+1/fs
            pred=support&(nf[indices]>=70)&(nf[indices]<=400)
            valid=nf[indices][pred]
            saved=fixed.loc[(identity,file)]
            stats={'F0mean':valid.mean() if len(valid) else np.nan,'F0std':valid.std(ddof=0) if len(valid) else np.nan,'F0num':len(valid)}
            errors=[]
            for key,value in stats.items():
                assert np.isclose(saved[key],value,atol=1e-8,equal_nan=True)
                error=100*abs(value-gt[key])/gt[key]
                assert np.isclose(saved[key+'_mape'],error,atol=1e-8,equal_nan=True)
                errors.append(error)
            assert np.isclose(saved.average_mape,np.mean(errors),atol=1e-8,equal_nan=True)
            counts={'TP':int(((labels=='v')&pred).sum()),'FN':int(((labels=='v')&~pred).sum()),
                    'FP':int(((labels=='uv')&pred).sum()),'TN':int(((labels=='uv')&~pred).sum()),
                    'false_voiced_sil':int(((labels=='sil')&pred).sum())}
            assert all(saved[k]==v for k,v in counts.items())
            tp,tn,fp,fn=[counts[k] for k in ('TP','TN','FP','FN')]
            rv,ru=tp/max(tp+fn,1),tn/max(tn+fp,1)
            f1=(2*tp/max(2*tp+fp+fn,1)+2*tn/max(2*tn+fp+fn,1))/2
            assert np.allclose([saved.macro_f1,saved.recall_v,saved.recall_uv,saved.balanced_accuracy],[f1,rv,ru,(rv+ru)/2],atol=1e-10)
            assert np.isclose(saved.projection_coverage,support.mean()) and saved.native_frames==len(group)
            assert result['range_rejected_frames'][identity+'|'+file]==int(((nf>0)&~((nf>=70)&(nf<=400))).sum())
            checked+=1
    prior=pd.read_csv(HERE/'results/H31_fixed_lofo.csv').query("option_id=='praat7_filtered_v0.3'").set_index('file').sort_index()
    control=fixed.loc['praat7_filtered_v0.3'].sort_index()
    keys=['F0mean','F0std','F0num','average_mape','macro_f1','recall_v','false_voiced_sil']
    assert np.allclose(control[keys],prior[keys],atol=1e-8)
    fits=json.loads((HERE/'results/H41_fits.json').read_text())['fits']
    assert all(x['fitted']['actual_fit_files']==[] and not x['fitted']['requires_fit'] and x['classifier'] is None for x in fits)
    nested=pd.read_csv(HERE/'results/H41_metrics.csv').query("split=='nested' and model=='candidate'")
    assert result['goal_all_nested_files_le_2']==bool((nested.average_mape<=2).all())
    assert result['poisoned_gt_inference_invariant'] is True
    receipt={'family':'H41','native_calls_and_fixed_groups_replayed':checked,'fit_logs':len(fits),
             'raw_statistics_mape_voicing_support_recomputed':True,'normalized_PCM_source_gate_time_and_count_preservation_checked':True,'raw_NAMDF_formula_all_frame_input_hashes_and_band_dips_replayed':True,'actual_Praat_calls':4,'curve_feature_groups':len(curve_cache),'curve_rows_recomputed':curve_rows,
             'H31_fixed_control_reproduced':True,'no_actual_training_fit':True,'verifier_sha256':digest(__file__),
             'input_sha256':{p.name:digest(p) for p in [HERE/'results/H41_experiment.json',HERE/'results/H41_fixed_lofo.csv',HERE/'results/H41_raw_native_frames.csv']}}
    (HERE/'results/H41_native_verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
