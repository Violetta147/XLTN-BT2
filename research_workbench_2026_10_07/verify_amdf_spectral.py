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


def independent_pick(curve,lags,fs,gate):
    if not np.isfinite(curve).all():
        return gate,'praat_window_unsupported',-1
    if np.ptp(curve)<=1e-12:
        return gate,'praat_no_candidate',-1
    indices=[j for j in range(1,len(curve)-1) if curve[j]<=curve[j-1] and curve[j]<=curve[j+1]]
    if not indices:
        indices=[int(np.argmin(curve))]
    allowed=[]
    finite=0
    for j in indices:
        lag=float(lags[j])
        if 0<j<len(curve)-1:
            a,b,c=curve[j-1:j+2]
            denom=a-2*b+c
            if abs(denom)>1e-12:
                delta=.5*(a-c)/denom
                if abs(delta)<=1:
                    lag+=float(delta)
        f=fs/lag
        if not 70<=f<=400:
            continue
        finite+=1
        deviation=abs(1200*np.log2(f/gate))
        if deviation<=200+1e-9:
            allowed.append((float(curve[j]),float(deviation),float(f),int(j)))
    if allowed:
        _,_,f,j=min(allowed)
        return f,'amdf_dip',j
    return gate,'praat_disagreement' if finite else 'praat_no_candidate',-1


def main():
    verify_amdf_loop.verify('H42','praat7_filtered_v0.3')
    result=json.loads((HERE/'results/H42_experiment.json').read_text())
    prior=json.loads((HERE/'results/H41_experiment.json').read_text())
    options=json.loads((HERE/'H42_REGISTRY.json').read_text())['options']
    raw=pd.read_csv(HERE/'results/H42_raw_native_frames.csv',float_precision='round_trip')
    fixed=pd.read_csv(HERE/'results/H42_fixed_lofo.csv').set_index(['option_id','file'])
    contour=pd.read_csv(HERE/'results/H42_nested_contours.csv')
    assert result['new_native_calls']==0 and result['historical_source_groups']==4
    assert len(result['source_calls'])==4 and len(result['native_calls'])==28
    assert set(raw.option_id)=={o['id'] for o in options}
    curve_rows,spectral_rows,checked=0,0,0
    for file in sorted(result['data_sha256']):
        fs,pcm=wavfile.read(REPO/'TinHieuHuanLuyen'/file)
        assert pcm.dtype==np.int16 and pcm.ndim==1
        audio=np.ascontiguousarray(pcm.astype(np.float64)/32768)
        stem=Path(file).stem
        spectrum_path=HERE/f'results/H42_spectral_{stem}.npz'
        feature=dict(np.load(spectrum_path,allow_pickle=False))
        nt,gate=feature['times'],feature['gate_frequency']
        ratio=np.full(len(nt),np.nan)
        curves={}
        for window in (25,40):
            path=HERE/f'results/H41_curves_w{window}_{stem}.npz'
            proof=prior['native_calls'][f'amdf_anchor_w{window}_b200|{file}']['AMDF_evidence']
            assert digest(path)==proof['sha256']
            data=curves[window]=dict(np.load(path,allow_pickle=False))
            assert np.array_equal(data['times'],nt) and np.array_equal(data['gate_frequency'],gate)
            assert str(data['audio_sha256'])==hashlib.sha256(audio.tobytes()).hexdigest()
            length=round(fs*window/1000)
            assert int(data['frame_samples'])==length and int(data['fs'])==fs
            assert int(data['input_samples'])==len(pcm)
            starts=np.array([round(t*fs-length/2) for t in nt])
            assert np.array_equal(starts,data['starts'])
            lags=np.arange(max(1,int(np.floor(fs/400))),min(length-1,int(np.ceil(fs/70)))+1)
            assert np.array_equal(lags,data['lags'])
            for i,(start,g) in enumerate(zip(starts,gate)):
                valid=70<=g<=400 and 0<=start and start+length<=len(audio)
                if not valid:
                    assert np.isnan(data['curve'][i]).all() and str(data['frame_sha256'][i])==''
                    continue
                frame=audio[start:start+length]
                assert str(data['frame_sha256'][i])==hashlib.sha256(frame.tobytes()).hexdigest()
                centered=frame-frame.mean()
                fresh=np.ones(len(lags)) if abs(centered).mean()<1e-8 else np.array([
                    abs(centered[:-lag]-centered[lag:]).mean()/(abs(centered[:-lag]).mean()+abs(centered[lag:]).mean()+1e-12) for lag in lags])
                np.testing.assert_allclose(data['curve'][i],fresh,atol=1e-12,rtol=1e-12)
                curve_rows+=1
        length=round(fs*.040)
        assert int(feature['frame_samples'])==length and int(feature['fs'])==fs
        assert np.array_equal(feature['starts'],curves[40]['starts'])
        for i,(start,g) in enumerate(zip(feature['starts'],gate)):
            valid=70<=g<=400 and 0<=start and start+length<=len(audio)
            if not valid:
                assert np.isnan(feature['ratio'][i]) and str(feature['frame_sha256'][i])==''
                continue
            frame=audio[start:start+length]
            assert str(feature['frame_sha256'][i])==hashlib.sha256(frame.tobytes()).hexdigest()
            centered=frame-frame.mean()
            if abs(centered).mean()>=1e-8:
                hann=.5-.5*np.cos(2*np.pi*np.arange(length)/(length-1))
                # Full complex FFT independently accounts for both spectral halves.
                full=np.abs(np.fft.fft(centered*hann))**2
                frequencies=np.abs(np.fft.fftfreq(length,1/fs))
                denominator=full[frequencies>0].sum()
                ratio[i]=full[frequencies>=1000].sum()/denominator if denominator>0 else np.nan
            spectral_rows+=1
        np.testing.assert_allclose(feature['ratio'],ratio,atol=1e-12,rtol=1e-12,equal_nan=True)
        canonical=contour[(contour.model=='accepted')&(contour.file==file)]
        times,labels=canonical.time_s.to_numpy(),canonical.label.to_numpy()
        gt={tokens[0]:float(tokens[1]) for tokens in [line.split() for line in
            (REPO/'research_3gt_2026_10_05/train_3gt'/file.replace('.wav','.lab')).read_text().splitlines()]}
        for option in options:
            identity=option['id']
            group=raw[(raw.option_id==identity)&(raw.file==file)]
            call=result['native_calls'][identity+'|'+file]
            assert len(group)==call['native_frames']==len(nt)
            assert call['historical_native_call'] is True and call['new_native_call'] is False
            original=prior['source_calls']['praat7_filtered_v0.3|'+file]
            assert result['source_calls']['praat7_filtered_v0.3|'+file]==original
            for key in ('command','returncode','stdout_sha256','exe_sha256','script_sha256'):
                assert call[key]==original[key]
            assert call['rule_sha256']==digest(HERE/'amdf_spectral.py')
            evidence=call['spectral_evidence']
            assert evidence['sha256']==digest(spectrum_path)
            assert evidence['H41_experiment_sha256']==digest(HERE/'results/H41_experiment.json')
            for proof in evidence['curve_paths'].values():
                assert digest(HERE/proof['path'])==proof['sha256']
            output=gate.copy()
            selected=np.full(len(gate),-1,dtype=int)
            windows=np.zeros(len(gate),dtype=int)
            tags=np.where(gate>0,'praat_control','unvoiced').astype('<U40')
            for i in np.flatnonzero((gate>=70)&(gate<=400)):
                if option['method']=='control':
                    continue
                window=option['amdf_window_ms'] if option['method']=='fixed_window' else (
                    40 if np.isfinite(ratio[i]) and ratio[i]<=option['hf_threshold'] else 25)
                windows[i]=window
                data=curves[window]
                output[i],tags[i],selected[i]=independent_pick(data['curve'][i],data['lags'],fs,gate[i])
            actual=group.raw_f0_hz.to_numpy()
            np.testing.assert_allclose(group.time_s,nt,atol=1e-12)
            np.testing.assert_allclose(actual,output,atol=1e-10,rtol=1e-12)
            assert np.array_equal(actual>0,gate>0) and np.array_equal(group.raw_voiced,actual>0)
            assert call['source']==tags.tolist() and call['selected_windows']==windows.tolist()
            assert call['selected_curve_indices']==selected.tolist()
            assert call['output_f0_sha256']==hashlib.sha256(np.ascontiguousarray(actual).tobytes()).hexdigest()
            idx=np.array([int(np.argmin(abs(nt-t))) for t in times])
            support=abs(nt[idx]-times)<=.005+1/fs
            pred=support&(actual[idx]>=70)&(actual[idx]<=400)
            valid=actual[idx][pred]
            saved=fixed.loc[(identity,file)]
            statistics={'F0mean':valid.mean(),'F0std':valid.std(ddof=0),'F0num':len(valid)}
            errors=[]
            for key,value in statistics.items():
                np.testing.assert_allclose(saved[key],value,atol=1e-8)
                error=100*abs(value-gt[key])/gt[key]
                np.testing.assert_allclose(saved[key+'_mape'],error,atol=1e-8)
                errors.append(error)
            np.testing.assert_allclose(saved.average_mape,np.mean(errors),atol=1e-8)
            counts={'TP':int(((labels=='v')&pred).sum()),'FN':int(((labels=='v')&~pred).sum()),
                    'FP':int(((labels=='uv')&pred).sum()),'TN':int(((labels=='uv')&~pred).sum()),
                    'false_voiced_sil':int(((labels=='sil')&pred).sum())}
            assert all(saved[key]==value for key,value in counts.items())
            tp,tn,fp,fn=[counts[k] for k in ('TP','TN','FP','FN')]
            rv,ru=tp/max(tp+fn,1),tn/max(tn+fp,1)
            f1=(2*tp/max(2*tp+fp+fn,1)+2*tn/max(2*tn+fp+fn,1))/2
            np.testing.assert_allclose([saved.macro_f1,saved.recall_v,saved.recall_uv,saved.balanced_accuracy],
                                       [f1,rv,ru,(rv+ru)/2],atol=1e-10)
            assert np.isclose(saved.projection_coverage,support.mean())
            checked+=1
        print('Verified full FFT/PCM/NAMDF and routing',file,flush=True)
    old=pd.read_csv(HERE/'results/H41_fixed_lofo.csv').set_index(['option_id','file'])
    keys=['F0mean','F0std','F0num','average_mape','macro_f1','recall_v','false_voiced_sil']
    for identity in ('praat7_filtered_v0.3','amdf_anchor_w25_b200','amdf_anchor_w40_b200'):
        np.testing.assert_allclose(fixed.loc[identity].sort_index()[keys],old.loc[identity].sort_index()[keys],atol=1e-8)
    fits=json.loads((HERE/'results/H42_fits.json').read_text())['fits']
    assert all(x['fitted']['actual_fit_files']==[] and not x['fitted']['requires_fit'] and x['classifier'] is None for x in fits)
    metrics=pd.read_csv(HERE/'results/H42_metrics.csv').query("split=='nested' and model=='candidate'")
    assert result['goal_all_nested_files_le_2']==bool((metrics.average_mape<=2).all())
    receipt={'family':'H42','fixed_groups_verified':checked,'curve_groups_recomputed':8,'curve_rows_recomputed':curve_rows,
             'spectral_groups_recomputed':4,'spectral_rows_recomputed':spectral_rows,'FFT_verification':'full complex FFT; explicit Hann formula',
             'new_native_calls':0,'historical_native_source_groups_verified':4,'fit_logs_checked':len(fits),
             'H41_controls_parity':True,'voicing_count_preservation':True,'GT_poison_runner_check':result['poisoned_gt_inference_invariant'],
             'verifier_sha256':digest(__file__),'experiment_sha256':digest(HERE/'results/H42_experiment.json')}
    (HERE/'results/H42_spectral_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
