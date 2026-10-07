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


def route(ratio, option, gate):
    if option['method'] == 'control':
        return 0
    if option['method'] == 'fixed_window':
        return option['amdf_window_ms']
    assert option['method'] == 'spectral_window'
    return 40 if np.isfinite(ratio) and ratio <= option['hf_threshold'] and gate >= option['minimum_gate_hz'] else 25


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
    path = HERE/f'results/H43_spectral_{name}.npz'
    assert not path.exists(), 'Preserve completed H43 features'
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
    evidence = load_evidence(item,audio)
    times,gate = evidence['times'],evidence['gate']
    frequency = gate.copy()
    tags = np.where(gate>0,'praat_control','unvoiced').astype('<U40')
    chosen_windows = np.zeros(len(gate),dtype=int)
    selected = np.full(len(gate),-1,dtype=int)
    for i in np.flatnonzero((gate>=70)&(gate<=400)):
        window = route(evidence['ratio'][i],option,gate[i])
        chosen_windows[i] = window
        if window == 0:
            continue
        data = evidence['data'][window]
        curve = data['curve'][i]
        if not np.isfinite(curve).all():
            tags[i] = 'praat_window_unsupported'
            continue
        frequencies,dips,indices = anchor.candidates(data['lags'],curve,item['fs'])
        frequency[i],tags[i],chosen = anchor.choose(gate[i],frequencies,dips,200)
        if chosen >= 0:
            selected[i] = indices[chosen]
    pred = (frequency>=70)&(frequency<=400)
    assert np.array_equal(pred,(gate>=70)&(gate<=400))
    original = SOURCE_CACHE[('praat7_filtered_v0.3',item['file'])][2]
    log = dict(original,engine='H43 NAMDF spectral window controller',historical_native_call=True,
               new_native_call=False,spectral_evidence=evidence['proof'],source=tags.tolist(),
               selected_windows=chosen_windows.tolist(),selected_curve_indices=selected.tolist(),
               rule_sha256=audit.digest(__file__),
               output_f0_sha256=hashlib.sha256(frequency.tobytes()).hexdigest())
    return dict(item,times=times,preprocess=option['id'],native_pred=pred,native_f0=np.where(pred,frequency,np.nan),
                raw_native_frequency=frequency,raw_native_voiced=frequency>0,native_call=log,
                range_rejected_frames=int(((frequency>0)&~pred).sum()))


def check():
    tests=[]
    for fs in (16000,44100):
        t=np.arange(round(fs*.040))/fs
        low=.2*np.sin(2*np.pi*200*t)
        high=.2*np.sin(2*np.pi*2000*t)
        lr,hr=high_frequency_ratio(low,fs),high_frequency_ratio(high,fs)
        assert lr<1e-5 and hr>.999
        assert np.isnan(high_frequency_ratio(np.zeros(len(t)),fs))
        assert np.isclose(high_frequency_ratio(low+.037,fs),lr,atol=1e-14)
        assert np.isclose(high_frequency_ratio(low*3,fs),lr,atol=1e-14)
        for floor in (0,140,170,200):
            option={'method':'spectral_window','hf_threshold':.05,'minimum_gate_hz':floor}
            assert route(lr,option,floor)==40
            assert route(lr,option,floor-1e-9)==25
            assert route(hr,option,300)==25 and route(np.nan,option,300)==25
            assert route(.05,option,300)==40 and route(.05+1e-9,option,300)==25
        tests.append({'fs':fs,'low_ratio':lr,'high_ratio':hr})
    audit.json_write(HERE/'results/H43_precheck.json',{'synthetic_tests':tests,'rule_sha256':audit.digest(__file__),
                     'uses_BT2_WAV':False,'new_native_calls':0,'cutoff_hz':1000,'window_ms':40,
                     'hf_threshold':.05,'minimum_gate_hz_grid':[0,140,170,200]})
    print('PASS synthetic spectral calculation, pitch condition, equality/NaN boundaries and gain/DC invariance')
