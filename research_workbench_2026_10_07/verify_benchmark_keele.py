import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import benchmark_keele as engine
from verify_amdf_spectral import independent_pick

HERE=Path(__file__).resolve().parent


def main():
    result=json.loads((HERE/'results/H49_experiment.json').read_text())
    registry=json.loads((HERE/'H49_REGISTRY.json').read_text())
    manifest=json.loads((HERE/'results/H49_dataset_manifest.json').read_text())
    assert result['registry_sha256']==engine.audit.digest(HERE/'H49_REGISTRY.json')
    assert result['dataset_manifest_sha256']==registry['dataset_manifest_sha256']==engine.audit.digest(HERE/'results/H49_dataset_manifest.json')
    for path,value in registry['source_sha256'].items():
        assert engine.audit.digest(engine.core.REPO/path)==value
    for name,value in result['output_hashes'].items():
        assert engine.audit.digest(HERE/'results'/name)==value
    assert not result['tuned_on_benchmark'] and result['fit_files']==[] and result['new_native_calls']==10
    assert engine.audit.digest(engine.ARCHIVE)==manifest['archive_sha256']
    metrics=pd.read_csv(HERE/'results/H49_metrics.csv')
    frames=pd.read_csv(HERE/'results/H49_frames.csv',float_precision='round_trip')
    assert len(metrics)==20 and len(result['source_calls'])==10
    curve_rows,groups,checks=0,0,0
    for case in manifest['cases']:
        name=case['id']; directory=HERE/case['relative_dir']; proof=result['source_calls'][name]
        for filename,value in case['hashes'].items():
            assert engine.audit.digest(directory/filename)==value
        fs,audio=engine.core.load_audio(directory/'signal.wav')
        reference=np.load(directory/'pitch.npy',allow_pickle=False)
        assert engine.audit.digest(HERE/proof['path'])==proof['sha256']
        data=dict(np.load(HERE/proof['path']))
        call=proof['native_call']
        assert call['returncode']==0 and call['exe_sha256']==engine.fixed.praat.metadata()['exe_sha256']
        assert call['script_sha256']==engine.audit.digest(HERE/'praat_extract_native.praat')
        assert call['command']==[engine.fixed.praat.metadata()['exe'],'--run',str(HERE/'praat_extract_native.praat'),str(directory/'signal.wav'),'filtered','0.3']
        bank={}
        for window in (25,40):
            p=proof['curves'][str(window)]
            assert engine.audit.digest(HERE/p['path'])==p['sha256']
            curves=dict(np.load(HERE/p['path']))
            assert np.array_equal(curves['times'],data['times']) and np.array_equal(curves['gate_frequency'],data['gate'])
            assert str(curves['audio_sha256'])==hashlib.sha256(np.ascontiguousarray(audio,dtype=np.float64).tobytes()).hexdigest()
            length=round(fs*window/1000)
            expected_lags=np.arange(max(1,int(np.floor(fs/400))),min(length-1,int(np.ceil(fs/70)))+1)
            assert np.array_equal(curves['lags'],expected_lags) and int(curves['frame_samples'])==length
            assert np.array_equal(curves['starts'],[round(t*fs-length/2) for t in data['times']])
            for i,gate in enumerate(data['gate']):
                start=int(curves['starts'][i])
                if not (70<=gate<=400 and 0<=start and start+length<=len(audio)):
                    assert np.isnan(curves['curve'][i]).all()
                    continue
                frame=audio[start:start+length]; c=frame-frame.mean()
                if abs(c).mean()<1e-8:
                    fresh=np.ones(len(expected_lags))
                else:
                    fresh=np.array([abs(c[:-lag]-c[lag:]).mean()/(abs(c[:-lag]).mean()+abs(c[lag:]).mean()+1e-12) for lag in expected_lags])
                np.testing.assert_allclose(curves['curve'][i],fresh,atol=1e-12,rtol=1e-12)
                assert str(curves['frame_sha256'][i])==hashlib.sha256(frame.tobytes()).hexdigest()
                curve_rows+=1
            bank[window]=curves
            groups+=1
        predicted=data['gate'].copy()
        for i,gate in enumerate(data['gate']):
            if not 70<=gate<=400:
                continue
            start=int(bank[40]['starts'][i]); length=int(bank[40]['frame_samples'])
            ratio=np.nan
            if 0<=start and start+length<=len(audio):
                c=audio[start:start+length]; c=c-c.mean()
                if abs(c).mean()>=1e-8:
                    power=abs(np.fft.fft(c*np.hanning(length)))**2
                    hz=abs(np.fft.fftfreq(length,1/fs))
                    ratio=power[hz>=1000].sum()/power[hz>0].sum()
            np.testing.assert_allclose(data['ratio'][i],ratio,atol=1e-12,equal_nan=True)
            window=40 if np.isfinite(ratio) and ratio<=.05 and gate>=170 else 25
            predicted[i]=independent_pick(bank[window]['curve'][i],bank[window]['lags'],fs,gate)[0]
        np.testing.assert_allclose(data['f0'],predicted,atol=1e-12)
        for model,frequency in [('control',data['gate']),('candidate',predicted)]:
            saved=frames[(frames.file==name)&(frames.model==model)]
            assert np.array_equal(saved.time_s,reference['time'])
            assert np.array_equal(saved.reference_f0_hz,reference['pitch'])
            nt=data['times']; index=np.array([np.argmin(abs(nt-t)) for t in reference['time']])
            support=abs(nt[index]-reference['time'])<=.005+1/fs
            aligned=frequency[index].copy()
            aligned[~support|(aligned<70)|(aligned>400)]=0
            assert np.array_equal(saved.support,support)
            np.testing.assert_allclose(saved.predicted_f0_hz,aligned,atol=1e-12)
            use=support&(reference['pitch']>=0)&np.isfinite(reference['pitch'])
            r,e=reference['pitch'][use],aligned[use]
            rv,ev=r>0,e>0; both=rv&ev
            tp,tn,fp,fn=[int(v.sum()) for v in (both,~rv&~ev,~rv&ev,rv&~ev)]
            relative=abs(e[both]-r[both])/r[both]
            cents=abs(1200*np.log2(e[both]/r[both]))
            gross=int((relative>.2).sum()); correct=int((cents<=50).sum())
            values=dict(scored_frames=len(r),TP=tp,TN=tn,FP=fp,FN=fn,gross_error_frames=gross,correct50_frames=correct,
                        gpe20_pct=100*gross/max(tp,1),vde_pct=100*(fp+fn)/len(r),ffe20_pct=100*(fp+fn+gross)/len(r),
                        rpa50_pct=100*correct/max(rv.sum(),1),voiced_recall=tp/max(tp+fn,1),unvoiced_recall=tn/max(tn+fp,1),
                        macro_f1=(2*tp/max(2*tp+fp+fn,1)+2*tn/max(2*tn+fp+fn,1))/2,
                        mae_hz_both_voiced=abs(e[both]-r[both]).mean())
            p,t=e[ev],r[rv]
            components=[]
            for key,a,b in [('F0mean',p.mean(),t.mean()),('F0std',p.std(ddof=0),t.std(ddof=0)),('F0num',len(p),len(t))]:
                values[key]=a; values['reference_'+key]=b
                values[key+'_mape']=100*abs(a-b)/b
                components.append(values[key+'_mape'])
            values['average_mape']=sum(components)/3
            row=metrics[(metrics.model==model)&(metrics.file==name)].iloc[0]
            for key,value in values.items():
                np.testing.assert_allclose(row[key],value,atol=1e-8,rtol=1e-9)
            checks+=1
        print('Verified KEELE',name,flush=True)
    for model,part in metrics.groupby('model'):
        fresh=engine.pooled(part)
        for key,value in fresh.items():
            np.testing.assert_allclose(result['summaries'][model][key],value,atol=1e-10)
    s=result['summaries']['candidate']
    assert result['predeclared_engineering_good_gate']==bool(s['rpa50_pct']>=90 and s['vde_pct']<=10 and s['ffe20_pct']<=10)
    receipt=dict(family='H49',recordings_checked=10,curve_groups=groups,independent_curve_rows=curve_rows,
                 metric_groups_recomputed=checks,full_fft_and_independent_candidate_pick=True,numeric_reference_and_source_hashes=True,
                 fixed_config_no_benchmark_fit=True,new_native_calls_in_verifier=0,reference_window_caveat_preserved=True,
                 experiment_sha256=engine.audit.digest(HERE/'results/H49_experiment.json'),verifier_sha256=engine.audit.digest(__file__))
    engine.audit.json_write(HERE/'results/H49_verification.json',receipt)
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
