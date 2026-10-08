import argparse
import json
import numpy as np
import pandas as pd
from scipy.signal import firwin, lfilter
import yaapt_extension as api


def independent_path(proof, params):
    candidates, merits, energy = proof['candidates'], proof['merits'], proof['energy']
    n, frames = candidates.shape
    anchor = candidates[n-2]
    mean_pitch = np.mean(anchor[anchor > 0])
    costs = 1-merits[:, 0]
    back = np.zeros((frames,n), dtype=int)
    for t in range(1,frames):
        updated = np.empty(n)
        for j in range(n):
            possibilities = np.empty(n)
            for i in range(n):
                a,b = candidates[i,t-1], candidates[j,t]
                if a>0 and b>0:
                    transition = params['dp_w1']*abs(a-b)/mean_pitch
                elif a==0 and b==0:
                    transition = params['dp_w3']
                else:
                    transition = params['dp_w2']*(1-min(1,abs(energy[t]-energy[t-1])))
                possibilities[i] = costs[i]+transition/params['dp_w4']
            i = n-1-int(np.argmin(possibilities[::-1]))
            back[t,j] = i
            updated[j] = possibilities[i]+1-merits[j,t]
        costs = updated
    indices = np.empty(frames,dtype=int)
    indices[-1] = n-1-int(np.argmin(costs[::-1]))
    for t in range(frames-1,0,-1):
        indices[t-1] = back[t,indices[t]]
    return candidates[indices,np.arange(frames)]


def independent_projection(proof, times, fs, option, baseline):
    values = np.full(len(times),np.nan)
    for i,t in enumerate(times):
        k = min(range(len(proof['times'])),key=lambda k:(abs(float(proof['times'][k])-t),k))
        pitch = proof['raw_f0'][k]
        if abs(proof['times'][k]-t) <= .005+1/fs and 70<=pitch<=400:
            values[i] = pitch
    pred = np.isfinite(values)
    if option['mode']=='pitch_only':
        pred = baseline['pred'].copy()
        values = np.where(pred & np.isfinite(values),values,baseline['f0'])
    return pred, values


def independent_item(path, stage):
    fs,audio = api.core.load_audio(path)
    length, hop = round(fs*.025),round(fs*.01)
    times = np.array([(s+length/2)/fs for s in range(0,len(audio)-length+1,hop)])
    segments = api.core.read_segments(path.with_suffix('.lab'))
    labels = np.array([next((label for a,b,label in segments if a<=t<b),'unknown') for t in times])
    gt = api.core.TRAIN_GT if stage=='train' else api.core.HERE/'test_3gt'
    return dict(file=path.name,stats=api.core.read_stats(gt/path.with_suffix('.lab').name),labels=labels,times=times), fs, audio


def independent_score(item,pred,f0):
    values = [float(v) for v in f0 if np.isfinite(v)]
    mean = sum(values)/len(values)
    std = np.sqrt(sum((v-mean)**2 for v in values)/len(values))
    estimates = dict(F0mean=mean,F0std=std,F0num=len(values))
    errors = {key+'_mape':100*abs(value-item['stats'][key])/item['stats'][key] for key,value in estimates.items()}
    tp=tn=fp=fn=sil=0
    for label,decision in zip(item['labels'],pred):
        if label=='v':
            tp+=int(decision);fn+=int(not decision)
        elif label=='uv':
            fp+=int(decision);tn+=int(not decision)
        elif label=='sil':
            sil+=int(decision)
    rv,ru = tp/max(tp+fn,1),tn/max(tn+fp,1)
    return dict(**estimates,**errors,average_mape=sum(errors.values())/3,
        F0mean_abs_error=abs(mean-item['stats']['F0mean']),F0std_abs_error=abs(std-item['stats']['F0std']),
        TP=tp,TN=tn,FP=fp,FN=fn,recall_v=rv,recall_uv=ru,balanced_accuracy=(rv+ru)/2,
        macro_f1=(2*tp/max(2*tp+fp+fn,1)+2*tn/max(2*tn+fp+fn,1))/2,
        accuracy_vu=(tp+tn)/max(tp+tn+fp+fn,1),false_voiced_sil=sil)


def independent_choose(rows):
    baseline = [r for r in rows if r['option_id']=='hard170']
    ordered=[]
    for identity in api.BY_ID:
        group=[r for r in rows if r['option_id']==identity]
        good = all(np.isfinite(r['average_mape']) for r in group)
        for key in ('macro_f1','recall_v'):
            good &= sum(r[key] for r in group)/len(group)>=sum(r[key] for r in baseline)/len(baseline)-.01
        good &= sum(r['false_voiced_sil'] for r in group)<=sum(r['false_voiced_sil'] for r in baseline)+1
        ordered.append((not good,max(r['average_mape'] for r in group) if good else np.inf,
                        sum(r['average_mape'] for r in group)/len(group) if good else np.inf,identity))
    return sorted(ordered)[0][-1]


def verify(stage):
    api.check_registry()
    receipt = json.loads((api.OUT/f'H52_{"train" if stage=="train" else "external"}_experiment.json').read_text())
    for relative,digest in receipt['artifacts'].items():
        assert api.audit.digest(api.REPO/relative)==digest,relative
    metrics = pd.read_csv(api.OUT/('H52_fixed.csv' if stage=='train' else 'H52_test_metrics.csv'),float_precision='round_trip')
    rows=[]; native_frames=pcm_frames=0; checked=set()
    baseline_file = 'H47_nested_contours.csv' if stage=='train' else 'H48_test_contours.csv'
    baseline_table = pd.read_csv(api.OUT/baseline_file,float_precision='round_trip')
    for name in sorted(metrics.file.unique()):
        path = (api.core.TRAIN if stage=='train' else api.REPO/'TinHieuKiemThu')/name
        item,fs,audio=independent_item(path,stage)
        saved=dict(np.load(api.OUT/f'H52_{stage}_predictions_{path.stem}.npz',allow_pickle=False))
        assert np.allclose(item['times'],saved['times'],rtol=0,atol=1e-12)
        old=baseline_table[(baseline_table.file==name)&(baseline_table.model=='candidate')]
        baseline=dict(pred=old.pred_voiced.to_numpy(bool),f0=old.f0_hz.to_numpy())
        for k,identity in enumerate(saved['option_id']):
            option=api.BY_ID[str(identity)]
            if identity=='hard170':
                pred,f0=baseline['pred'],baseline['f0']
            else:
                note=next(r for r in receipt['receipts'] if r['file']==name and r['option_id']==identity)
                assert note['actual_fit_files']==[] and note['input_sha256']==api.audit.digest(path)
                proof=dict(np.load(api.REPO/note['proof'],allow_pickle=False))
                assert api.audit.digest(api.REPO/note['proof'])==note['proof_sha256']
                if note['proof'] not in checked:
                    params=note['parameters']
                    expected=dict(api.PARAMETERS,nlfer_thresh1=option['nlfer'])
                    if not option['final_dp']:expected.update(dp_w1=0.,dp_w2=0.,dp_w3=0.)
                    assert params==expected
                    length=int(fs*.035);hop=int(fs*.01)
                    positions=np.arange(length//2,len(audio)-length//2,hop)
                    assert np.array_equal(proof['times'],positions/fs)
                    assert int(proof['frame_size'])==length and int(proof['frame_jump'])==hop
                    filtered=lfilter(firwin(151,[50.,1500.],fs=fs,pass_zero=False),1,audio)
                    window=np.hanning(length+2)[1:-1]
                    lo=int(np.around(140/fs*8192)-1);hi=int(np.around(400/fs*8192))
                    energy=[]
                    for start in range(0,hop*len(positions),hop):
                        spectrum=abs(np.fft.fft(filtered[start:start+length]*window,8192))
                        energy.append(sum(spectrum[lo:hi]))
                    energy=np.array(energy);energy/=np.mean(energy)
                    assert np.allclose(energy,proof['energy'],rtol=1e-10,atol=1e-10)
                    decoded=independent_path(proof,params)
                    assert np.array_equal(decoded,proof['raw_f0']) and np.array_equal(decoded,proof['dynamic_f0'])
                    if stage=='train' and option['nlfer']==.75 and option['final_dp']:
                        historical=pd.read_csv(api.OUT/'H40_raw_native_frames.csv',float_precision='round_trip')
                        historical=historical[(historical.file==name)&(historical.option_id=='yaapt_f35')]
                        assert np.allclose(historical.time_s,proof['times'],rtol=0,atol=1e-12)
                        assert np.allclose(historical.raw_f0_hz,proof['raw_f0'],rtol=0,atol=1e-12)
                    native_frames+=len(decoded);pcm_frames+=len(energy);checked.add(note['proof'])
                pred,f0=independent_projection(proof,item['times'],fs,option,baseline)
            assert np.array_equal(pred,saved['pred'][k])
            assert np.allclose(f0,saved['f0'][k],rtol=0,atol=1e-12,equal_nan=True)
            assert np.array_equal(pred,np.isfinite(f0))
            measured=independent_score(item,pred,f0)
            if stage=='train' and identity=='yaapt_default':
                historical=pd.read_csv(api.OUT/'H40_fixed_lofo.csv',float_precision='round_trip')
                historical=historical[(historical.file==name)&(historical.option_id=='yaapt_f35')].iloc[0]
                assert all(np.isclose(historical[key],value,atol=1e-9) for key,value in measured.items() if key in historical.index)
            stored=metrics[(metrics.file==name)&(metrics.option_id==identity)].iloc[0]
            assert all(np.isclose(stored[key],value,atol=1e-9,rtol=1e-10) for key,value in measured.items())
            rows.append(dict(file=name,option_id=identity,**measured))
    if stage=='train':
        assert len(rows)==24 and len(checked)==16
        traces=pd.read_csv(api.OUT/'H52_inner_traces.csv',keep_default_na=False)
        assert len(traces)==96 and (traces.actual_fit_files=='').all()
        for selection in receipt['selections']:
            outer=selection['outer_held'];pool=selection['selection_files']
            assert outer not in pool and set(pool)==set(metrics.file.unique())-({outer} if outer!='final' else set())
            assert independent_choose([r for r in rows if r['file'] in pool])==selection['option_id']
        table=pd.read_csv(api.OUT/'H52_metrics.csv',float_precision='round_trip')
        for _,row in table.iterrows():
            found=next(r for r in rows if r['file']==row['file'] and r['option_id']==row['option_id'])
            for key,value in found.items():
                if key not in ('file','option_id'):assert np.isclose(row[key],value,atol=1e-9)
        _,gates=api.common.gates(table)
        assert gates==receipt['decision']
        freeze=json.loads((api.OUT/'H52_FROZEN_SELECTION.json').read_text())
        final=next(r['option_id'] for r in receipt['selections'] if r['outer_held']=='final')
        assert freeze['option']==api.BY_ID[final]
    else:
        freeze=json.loads((api.OUT/'H52_FROZEN_SELECTION.json').read_text())
        assert receipt['freeze_sha256']==api.audit.digest(api.OUT/'H52_FROZEN_SELECTION.json')
        assert set(metrics.option_id)==set(freeze['external_options']) and not receipt['test_tuning']
    api.audit.json_write(api.OUT/f'H52_{stage}_verification.json',dict(passed=True,
        independent_native_dynamic_frames=native_frames,independent_full_fft_pcm_frames=pcm_frames,
        metric_groups=len(rows),native_proofs=len(checked),new_yaapt_calls=0,
        limits='Verifies vendor final DP path, NLFER PCM energy, transport/projection/scoring; not independent reimplementation of spectral candidate generation.',
        verifier_sha256=api.audit.digest(api.HERE/'verify_yaapt_extension.py')))
    print(f'PASS H52 {stage}: {native_frames} independent dynamic-path frames, {pcm_frames} full-FFT PCM frames, {len(rows)} metric groups')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['train','test'])
    verify(parser.parse_args().stage)
