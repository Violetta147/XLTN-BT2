import hashlib
import json
from pathlib import Path

import numpy as np
import amdf_anchor as anchor

HERE = Path(__file__).resolve().parent
core, audit = anchor.core, anchor.audit
SOURCE_CACHE = {}
FEATURE_CACHE = {}


def high_frequency_ratio(frame, fs):
    if not np.isfinite(frame).all() or len(frame) < 3:
        return np.nan
    centered = frame-frame.mean()
    if np.mean(np.abs(centered)) < 1e-8:
        return np.nan
    spectrum = np.abs(np.fft.rfft(centered*np.hanning(len(frame))))**2
    frequencies = np.fft.rfftfreq(len(frame),1/fs)
    weights = np.full(len(spectrum),2.)
    weights[0] = 1
    if len(frame)%2 == 0:
        weights[-1] = 1
    power = spectrum*weights
    denominator = power[frequencies > 0].sum()
    return float(power[frequencies >= 1000].sum()/denominator) if denominator > 0 else np.nan


def weight(ratio, option, gate):
    if option['method'] in ('control','fixed_window'):
        return 0.
    if not np.isfinite(ratio) or ratio > .05:
        return 0.
    if option['method']=='spectral_window':
        return float(gate>=option['minimum_gate_hz'])
    assert option['method']=='soft_spectral'
    return float(np.clip((gate-option['center_hz'])/option['width_hz']+.5,0,1))


def blend(short,long,alpha):
    if alpha==0:
        return short
    if alpha==1:
        return long
    return float(short*2**(alpha*np.log2(long/short)))


def load_evidence(item, audio):
    if item['file'] in FEATURE_CACHE:
        return FEATURE_CACHE[item['file']]
    name = Path(item['file']).stem
    proof = json.loads((HERE/'results/H41_experiment.json').read_text())
    assert proof['data_sha256'][item['file']] == audit.digest(core.TRAIN/item['file'])
    data = {}
    for window in (25,40):
        path = HERE/f'results/H41_curves_w{window}_{name}.npz'
        recorded = proof['native_calls'][f'amdf_anchor_w{window}_b200|{item["file"]}']['AMDF_evidence']
        assert audit.digest(path) == recorded['sha256']
        data[window] = dict(np.load(path,allow_pickle=False))
        assert str(data[window]['audio_sha256']) == hashlib.sha256(np.ascontiguousarray(audio,dtype=np.float64).tobytes()).hexdigest()
    times,gate = data[25]['times'],data[25]['gate_frequency']
    assert np.array_equal(data[40]['times'],times) and np.array_equal(data[40]['gate_frequency'],gate)
    SOURCE_CACHE[('praat7_filtered_v0.3',item['file'])] = (times,gate,proof['source_calls']['praat7_filtered_v0.3|'+item['file']])
    ratios = np.full(len(times),np.nan)
    frame_hashes = np.full(len(times),'',dtype='<U64')
    length = int(data[40]['frame_samples'])
    for i in np.flatnonzero((gate>=70)&(gate<=400)):
        start = int(data[40]['starts'][i])
        if 0 <= start and start+length <= len(audio):
            frame = np.ascontiguousarray(audio[start:start+length],dtype=np.float64)
            frame_hashes[i] = hashlib.sha256(frame.tobytes()).hexdigest()
            ratios[i] = high_frequency_ratio(frame,item['fs'])
    path = HERE/f'results/H44_spectral_{name}.npz'
    assert not path.exists(), 'Preserve completed H44 features'
    np.savez_compressed(path,times=times,gate_frequency=gate,ratio=ratios,
                        starts=data[40]['starts'],frame_samples=length,frame_sha256=frame_hashes,fs=item['fs'])
    value = {'data':data,'times':times,'gate':gate,'ratio':ratios,
             'proof':{'path':str(path.relative_to(HERE)),'sha256':audit.digest(path),
                      'curve_paths':{str(w):{'path':f'results/H41_curves_w{w}_{name}.npz',
                                            'sha256':audit.digest(HERE/f'results/H41_curves_w{w}_{name}.npz')} for w in (25,40)},
                      'H41_experiment_sha256':audit.digest(HERE/'results/H41_experiment.json'),
                      'rule_sha256':audit.digest(__file__)}}
    FEATURE_CACHE[item['file']] = value
    return value


def extract(item, audio, option):
    evidence=load_evidence(item,audio)
    times,gate=evidence['times'],evidence['gate']
    frequency=gate.copy()
    values={w:gate.copy() for w in (25,40)}
    indices={w:np.full(len(gate),-1,dtype=int) for w in (25,40)}
    tags={w:np.where(gate>0,'praat_control','unvoiced').astype('<U40') for w in (25,40)}
    alpha=np.zeros(len(gate))
    for i in np.flatnonzero((gate>=70)&(gate<=400)):
        for w in (25,40):
            data=evidence['data'][w]
            curve=data['curve'][i]
            if not np.isfinite(curve).all():
                tags[w][i]='praat_window_unsupported'
                continue
            candidates,dips,lag_indices=anchor.candidates(data['lags'],curve,item['fs'])
            values[w][i],tags[w][i],chosen=anchor.choose(gate[i],candidates,dips,200)
            if chosen>=0:
                indices[w][i]=lag_indices[chosen]
        if option['method']=='control':
            continue
        alpha[i]=weight(evidence['ratio'][i],option,gate[i])
        frequency[i]=blend(values[25][i],values[40][i],alpha[i])
    pred=(frequency>=70)&(frequency<=400)
    assert np.array_equal(pred,(gate>=70)&(gate<=400))
    original=SOURCE_CACHE[('praat7_filtered_v0.3',item['file'])][2]
    log=dict(original,engine='H44 soft spectral NAMDF blend',historical_native_call=True,new_native_call=False,
             spectral_evidence=evidence['proof'],weights40=alpha.tolist(),
             candidate_f0={str(w):values[w].tolist() for w in (25,40)},
             candidate_indices={str(w):indices[w].tolist() for w in (25,40)},
             candidate_tags={str(w):tags[w].tolist() for w in (25,40)},
             rule_sha256=audit.digest(__file__),output_f0_sha256=hashlib.sha256(frequency.tobytes()).hexdigest())
    return dict(item,times=times,preprocess=option['id'],native_pred=pred,native_f0=np.where(pred,frequency,np.nan),
                raw_native_frequency=frequency,raw_native_voiced=frequency>0,native_call=log,
                range_rejected_frames=int(((frequency>0)&~pred).sum()))


def check():
    cases=[]
    for center in (140,170,200):
        for width in (20,40):
            option={'method':'soft_spectral','center_hz':center,'width_hz':width}
            for gate,expected in ((center-width/2-1,0),(center-width/2,0),(center,.5),(center+width/2,1),(center+width/2+1,1)):
                assert weight(.05,option,gate)==expected
                assert weight(.05+1e-9,option,gate)==0
                assert weight(np.nan,option,gate)==0
            assert blend(100.,200.,0)==100 and blend(100.,200.,1)==200
            assert np.isclose(blend(100.,200.,.5),np.sqrt(20000),atol=1e-12)
            assert all(100<=blend(100.,200.,a)<=200 for a in np.linspace(0,1,11))
            cases.append(dict(center_hz=center,width_hz=width))
    assert weight(.01,{'method':'spectral_window','minimum_gate_hz':170},170)==1
    assert weight(.01,{'method':'spectral_window','minimum_gate_hz':170},169.999)==0
    for fs in (16000,44100):
        t=np.arange(round(fs*.04))/fs
        low=.2*np.sin(2*np.pi*200*t)
        assert high_frequency_ratio(low,fs)<1e-5
        assert high_frequency_ratio(.2*np.sin(2*np.pi*2000*t),fs)>.999
        assert np.isnan(high_frequency_ratio(np.zeros(len(t)),fs))
        assert np.isclose(high_frequency_ratio(low*3+.037,fs),high_frequency_ratio(low,fs),atol=1e-14)
    audit.json_write(HERE/'results/H44_precheck.json',{'synthetic_cases':cases,'rule_sha256':audit.digest(__file__),
                     'uses_BT2_WAV':False,'new_native_calls':0,'blend':'log2 frequency interpolation; exact endpoints',
                     'ratio_threshold':.05,'band_cents':200})
    print('PASS soft weights/boundaries/NaN/log-blend/endpoints/range and synthetic FFT checks')
