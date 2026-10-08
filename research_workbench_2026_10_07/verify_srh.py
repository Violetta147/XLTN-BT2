import argparse
import json
from math import gcd
import numpy as np
import pandas as pd
from scipy.linalg import toeplitz
from scipy.signal import resample_poly
import srh_experiment as api
from verify_yaapt_extension_v2 import independent_item


def independent_score(item,pred,f0):
    values=[float(v) for v in f0 if np.isfinite(v)]
    mean=sum(values)/len(values) if values else np.nan
    std=np.sqrt(sum((v-mean)**2 for v in values)/len(values)) if values else np.nan
    estimates=dict(F0mean=mean,F0std=std,F0num=len(values))
    errors={key+'_mape':100*abs(value-item['stats'][key])/item['stats'][key] for key,value in estimates.items()}
    tp=tn=fp=fn=sil=0
    for label,decision in zip(item['labels'],pred):
        if label=='v':tp+=int(decision);fn+=int(not decision)
        elif label=='uv':fp+=int(decision);tn+=int(not decision)
        elif label=='sil':sil+=int(decision)
    rv,ru=tp/max(tp+fn,1),tn/max(tn+fp,1)
    return dict(**estimates,**errors,average_mape=sum(errors.values())/3,
        F0mean_abs_error=abs(mean-item['stats']['F0mean']),F0std_abs_error=abs(std-item['stats']['F0std']),
        TP=tp,TN=tn,FP=fp,FN=fn,recall_v=rv,recall_uv=ru,balanced_accuracy=(rv+ru)/2,
        macro_f1=(2*tp/max(2*tp+fp+fn,1)+2*tn/max(2*tn+fp+fn,1))/2,
        accuracy_vu=(tp+tn)/max(tp+tn+fp+fn,1),false_voiced_sil=sil)


def verify_native(audio,fs,proof):
    if fs>16000:
        divisor=gcd(fs,16000);audio=resample_poly(audio,16000//divisor,fs//divisor);fs=16000
    assert np.array_equal(audio,proof['resampled_audio']) and int(proof['native_fs'])==fs
    length=int(np.floor(.025*fs+.5));shift=int(np.floor(.005*fs+.5));order=int(np.floor(.75*fs/1000+.5))
    starts=list(range(0,len(audio)-length-1,shift));reconstructed=np.zeros(len(audio));ill_conditioned=0;largest_condition=0.
    for k,start in enumerate(starts):
        segment=np.array(audio[start:start+length+1])*np.hanning(length+1)
        correlation=np.array([np.sum(segment[:len(segment)-j]*segment[j:]) for j in range(order+1)])
        a=proof['lp_coefficients'][k]
        if correlation[0]>0:
            matrix=toeplitz(correlation[:-1]);condition=np.linalg.cond(matrix);largest_condition=max(largest_condition,condition)
            dense=np.r_[1.,np.linalg.solve(matrix,-correlation[1:])]
            backward=np.linalg.norm(matrix@a[1:]+correlation[1:])/(np.linalg.norm(matrix)*np.linalg.norm(a[1:])+np.linalg.norm(correlation[1:]))
            assert backward<1e-12
            if condition<=1e8:assert np.allclose(a,dense,rtol=1e-6,atol=1e-7)
            else:ill_conditioned+=1
        else:assert np.array_equal(a,np.r_[1.,np.zeros(order)])
        inverse=np.convolve(segment,a)[:len(segment)]
        inverse_energy=np.sum(inverse*inverse)
        if inverse_energy>0:inverse*=np.sqrt(np.sum(segment*segment)/inverse_energy)
        reconstructed[start:start+length+1]+=inverse
        assert proof['lp_starts'][k]==start
    scale=max(abs(reconstructed))
    if scale>0:reconstructed/=scale
    assert np.allclose(reconstructed,proof['residual'],rtol=1e-6,atol=1e-6)
    window=int(proof['frame_samples']);half=window//2
    positions=np.array(list(range(half+1,len(audio)-half+1,int(np.floor(.01*fs+.5)))))
    assert np.array_equal(proof['native_positions'],positions)
    assert np.array_equal(proof['native_times'],positions/fs)
    assert np.array_equal(proof['native_starts'],positions-half-1)
    for i,start in enumerate(proof['native_starts']):
        x=proof['residual'][start:start+window]*np.blackman(window)
        x-=np.mean(x)
        spectrum=abs(np.fft.fft(x,fs))[:fs//2]
        norm=np.sqrt(np.sum(spectrum*spectrum))
        assert np.isclose(norm,proof['spectrum_norm'][i],atol=1e-10,rtol=1e-10)
        spectrum=spectrum[:2000]/max(norm,1e-20)
        assert np.allclose(spectrum,proof['spectrum'][i],atol=1e-10,rtol=1e-10)
    lower,upper=70,400;no_adjustment=True;passes=[]
    for iteration in range(2):
        curves=np.zeros((len(positions),upper));passes.append((lower,upper))
        for f in range(lower,upper+1):
            for i in range(len(positions)):
                spectrum=proof['spectrum'][i]
                plus=sum(float(spectrum[h*f-1]) for h in range(1,6))
                minus=sum(float(spectrum[int(np.floor((h+.5)*f+.5))-1]) for h in range(1,5))
                curves[i,f-1]=plus-minus
        raw=np.argmax(curves,axis=1)+1;scores=curves[np.arange(len(positions)),raw-1]
        if max(scores)>.1:
            pitch=np.median(raw[scores>.1])
            if int(np.floor(.5*pitch+.5))>lower:lower=int(np.floor(.5*pitch+.5));no_adjustment=False
            if int(np.floor(2*pitch+.5))<upper:upper=int(np.floor(2*pitch+.5));no_adjustment=False
        if no_adjustment:break
    assert np.array_equal(passes,proof['passes'])
    assert np.array_equal(raw,proof['raw_f0']) and np.allclose(scores,proof['score'],atol=1e-12,rtol=1e-12)
    assert np.allclose(curves,proof['curves'],atol=1e-12,rtol=1e-12)
    threshold=.085 if np.std(scores,ddof=1)>.05 else .07
    assert threshold==float(proof['threshold']) and np.array_equal(scores>threshold,proof['native_pred'])
    return dict(lp_frames=len(starts),spectrum_frames=len(positions),two_passes=len(passes),
                ill_conditioned_lp_frames=ill_conditioned,largest_lpc_condition=largest_condition)


def projection(proof,times,option,base):
    output=np.full(len(times),np.nan);pred=np.zeros(len(times),bool)
    for i,t in enumerate(times):
        k=min(range(len(proof['native_times'])),key=lambda k:(abs(t-proof['native_times'][k]),k))
        valid=abs(t-proof['native_times'][k])<=.005+1/int(proof['native_fs']) and 70<=proof['raw_f0'][k]<=400
        if valid and (option['mode']=='pitch_only' or proof['native_pred'][k]):
            output[i]=proof['raw_f0'][k];pred[i]=True
    if option['mode']=='pitch_only':
        output=np.where(base['pred']&np.isfinite(output),output,base['f0']);pred=base['pred']
    return pred,output


def choose(rows):
    baseline=[r for r in rows if r['option_id']=='hard170'];rank=[]
    for identity in api.BY_ID:
        group=[r for r in rows if r['option_id']==identity]
        valid=all(np.isfinite(r['average_mape']) for r in group)
        for key in ('macro_f1','recall_v'):
            valid &= sum(r[key] for r in group)/len(group)>=sum(r[key] for r in baseline)/len(baseline)-.01
        valid &= sum(r['false_voiced_sil'] for r in group)<=sum(r['false_voiced_sil'] for r in baseline)+1
        rank.append((not valid,max(r['average_mape'] for r in group) if valid else np.inf,
                     sum(r['average_mape'] for r in group)/len(group) if valid else np.inf,identity))
    return min(rank)[-1]


def verify(stage):
    api.check_registry()
    receipt=json.loads((api.OUT/f'H54_{stage}_experiment.json').read_text())
    for path,digest in receipt['artifacts'].items():assert api.audit.digest(api.REPO/path)==digest,path
    metrics=pd.read_csv(api.OUT/f'H54_{stage}_fixed.csv',float_precision='round_trip')
    old=pd.read_csv(api.OUT/('H47_nested_contours.csv' if stage=='train' else 'H48_test_contours.csv'),float_precision='round_trip')
    rows=[];checked=set();lp_frames=spectral_frames=ill_conditioned=0;largest_condition=0.
    for name in sorted(metrics.file.unique()):
        path=(api.core.TRAIN if stage=='train' else api.REPO/'TinHieuKiemThu')/name
        item,fs,audio=independent_item(path,stage)
        saved=dict(np.load(api.OUT/f'H54_{stage}_predictions_{path.stem}.npz',allow_pickle=False))
        baseline=old[(old.file==name)&(old.model=='candidate')]
        base=dict(pred=baseline.pred_voiced.to_numpy(bool),f0=baseline.f0_hz.to_numpy())
        assert np.allclose(saved['times'],item['times'],atol=1e-12)
        for k,identity in enumerate(saved['option_id']):
            option=api.BY_ID[str(identity)]
            if identity=='hard170':pred,f0=base['pred'],base['f0']
            else:
                native=api.OUT/f'H54_{stage}_native_{path.stem}_w{option["window_ms"]}.npz'
                proof=dict(np.load(native,allow_pickle=False))
                expected=int(np.floor(option['window_ms']*int(proof['native_fs'])/1000+.5))-2
                expected=int(np.floor(expected/2+.5))*2
                assert expected==int(proof['frame_samples'])
                if native not in checked:
                    detail=verify_native(audio,fs,proof);lp_frames+=detail['lp_frames'];spectral_frames+=detail['spectrum_frames'];checked.add(native)
                    ill_conditioned+=detail['ill_conditioned_lp_frames'];largest_condition=max(largest_condition,detail['largest_lpc_condition'])
                pred,f0=projection(proof,item['times'],option,base)
            assert np.array_equal(pred,saved['pred'][k]) and np.allclose(f0,saved['f0'][k],equal_nan=True,atol=1e-12)
            assert np.array_equal(pred,np.isfinite(f0))
            measured=independent_score(item,pred,f0)
            stored=metrics[(metrics.file==name)&(metrics.option_id==identity)].iloc[0]
            assert all(np.isclose(stored[key],value,atol=1e-8,rtol=1e-10,equal_nan=True) for key,value in measured.items())
            rows.append(dict(file=name,option_id=identity,**measured))
    if stage=='train':
        assert len(rows)==28 and len(checked)==12
        for selection in receipt['selections']:
            outer=selection['outer_held'];pool=selection['selection_files']
            assert outer not in pool and set(pool)==set(metrics.file.unique())-({outer} if outer!='final' else set())
            assert choose([r for r in rows if r['file'] in pool])==selection['option_id']
        trace=pd.read_csv(api.OUT/'H54_inner_traces.csv',keep_default_na=False)
        assert len(trace)==112 and (trace.actual_fit_files=='').all()
        table=pd.read_csv(api.OUT/'H54_metrics.csv',float_precision='round_trip')
        for _,row in table.iterrows():
            original=next(r for r in rows if r['file']==row['file'] and r['option_id']==row['option_id'])
            assert all(np.isclose(row[key],value,atol=1e-8,equal_nan=True) for key,value in original.items() if key not in ('file','option_id'))
        _,gates=api.common.gates(table);assert gates==receipt['decision']
    else:
        freeze=json.loads((api.OUT/'H54_FROZEN_SELECTION.json').read_text())
        assert set(metrics.option_id)==set(freeze['external_options']) and not receipt['test_tuning']
        assert receipt['freeze_sha256']==api.audit.digest(api.OUT/'H54_FROZEN_SELECTION.json')
    api.audit.json_write(api.OUT/f'H54_{stage}_verification.json',dict(passed=True,metric_groups=len(rows),
        lp_frames=lp_frames,spectrum_frames=spectral_frames,native_proofs=len(checked),
        ill_conditioned_lp_frames=ill_conditioned,largest_lpc_condition=largest_condition,
        independent_lpc_equation_convolution_full_fft_scalar_harmonic_sum=True,new_measurements=0,
        limits='Dense LPC coefficient comparison only where condition<=1e8; backward equation residual everywhere. Polyphase resampling uses the same SciPy implementation; no native MATLAB/Octave bit parity.',
        verifier_sha256=api.audit.digest(__file__)))
    print(f'PASS H54 {stage}: {lp_frames} dense LPC frames, {spectral_frames} full-FFT SRH frames, {len(rows)} metric groups')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['train','test']);verify(parser.parse_args().stage)
