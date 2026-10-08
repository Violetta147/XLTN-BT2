import argparse
import json
import platform
import subprocess
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from threadpoolctl import threadpool_limits
import voicing_recovery as common

HERE, REPO, OUT = common.HERE, common.REPO, common.OUT
core, audit = common.core, common.audit
VENDOR = HERE / 'vendor/yaapt_5c6c9bc'
sys.path.insert(0, str(VENDOR))
from amfm_decompy import basic_tools, pYAAPT

PARAMETERS = dict(frame_length=35., tda_frame_length=35., frame_space=10.,
    f0_min=70., f0_max=400., fft_length=8192, bp_forder=150, bp_low=50., bp_high=1500.,
    nlfer_thresh1=.75, nlfer_thresh2=.1, shc_numharms=3, shc_window=40., shc_maxpeaks=4,
    shc_pwidth=50., shc_thresh1=5., shc_thresh2=1.25, f0_double=150., f0_half=150.,
    dp5_k1=11., dec_factor=1, nccf_thresh1=.3, nccf_thresh2=.9, nccf_maxcands=3,
    nccf_pwidth=5, merit_boost=.2, merit_pivot=.99, merit_extra=.4, median_value=7,
    dp_w1=.15, dp_w2=.5, dp_w3=.1, dp_w4=.9, spec_pitch_min_std=.05)
OPTIONS = [dict(id='hard170', mode='control', nlfer=.75, final_dp=True),
           dict(id='yaapt_default', mode='whole', nlfer=.75, final_dp=True),
           dict(id='yaapt_nlfer050', mode='whole', nlfer=.5, final_dp=True),
           dict(id='yaapt_nlfer100', mode='whole', nlfer=1., final_dp=True),
           dict(id='yaapt_pitch_only', mode='pitch_only', nlfer=.75, final_dp=True),
           dict(id='yaapt_no_final_dp', mode='whole', nlfer=.75, final_dp=False)]
BY_ID = {option['id']: option for option in OPTIONS}


def git(*args):
    return subprocess.check_output(['git', '-c', 'safe.directory='+str(REPO).replace('\\', '/'),
                                   '-C', str(REPO), *args], text=True).strip()


def native(audio, fs, option):
    params = dict(PARAMETERS, nlfer_thresh1=option['nlfer'])
    if not option['final_dp']:
        params.update(dp_w1=0., dp_w2=0., dp_w3=0.)
    assert int(fs*.035) < 2048 and fs > 3000
    captured, notices = {}, []
    original = pYAAPT.dynamic
    def recording(candidates, merits, pitch, parameters):
        captured.update(candidates=candidates.copy(), merits=merits.copy(), energy=pitch.energy.copy())
        result = original(candidates, merits, pitch, parameters)
        captured['dynamic_f0'] = result.copy()
        return result
    assert np.isfinite(audio).all() and np.any(audio != 0)
    pYAAPT.dynamic = recording
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            signal = basic_tools.SignalObj(audio.astype(np.float64).copy(), fs)
            pitch = pYAAPT.yaapt(signal, **params)
            notices = [str(w.message) for w in caught]
    finally:
        pYAAPT.dynamic = original
    assert np.array_equal(pitch.samp_values, captured['dynamic_f0'])
    assert pYAAPT.PitchObj.PITCH_HALF == 0 and pYAAPT.PitchObj.PITCH_DOUBLE == 0
    assert np.isfinite(pitch.samp_values).all()
    captured.update(raw_f0=pitch.samp_values.copy(), times=pitch.frames_pos/fs,
                    frame_size=pitch.frame_size, frame_jump=pitch.frame_jump, fs=fs)
    return captured, dict(parameters=params, warnings=notices)


def project(proof, times, fs, option, baseline):
    source_times, values = proof['times'], proof['raw_f0']
    right = np.minimum(np.searchsorted(source_times, times), len(source_times)-1)
    left = np.maximum(right-1, 0)
    index = np.where(abs(source_times[left]-times) <= abs(source_times[right]-times), left, right)
    support = abs(source_times[index]-times) <= .005+1/fs
    valid = support & (values[index] >= 70) & (values[index] <= 400)
    pred = valid.copy()
    f0 = np.where(valid, values[index], np.nan)
    if option['mode'] == 'pitch_only':
        pred, f0 = baseline['pred'].copy(), baseline['f0'].copy()
        use = pred & valid
        f0[use] = values[index[use]]
    assert np.array_equal(pred, np.isfinite(f0))
    return pred, f0, support, index


def choose(records):
    table = pd.DataFrame(records)
    baseline = table[table.option_id == 'hard170']
    ranked = []
    for option in OPTIONS:
        group = table[table.option_id == option['id']]
        eligible = bool(np.isfinite(group.average_mape).all()
            and group.macro_f1.mean() >= baseline.macro_f1.mean()-.01
            and group.recall_v.mean() >= baseline.recall_v.mean()-.01
            and group.false_voiced_sil.sum() <= baseline.false_voiced_sil.sum()+1)
        ranked.append((not eligible, group.average_mape.max() if eligible else np.inf,
                       group.average_mape.mean() if eligible else np.inf, option['id']))
    return min(ranked)[-1]


def protected():
    paths = [Path(__file__), HERE/'verify_yaapt_extension.py', HERE/'H52_REGISTRATION.md',
             HERE/'H52_YAAPT_SOURCE_NOTE.md', Path(core.__file__), Path(common.__file__),
             OUT/'H47_nested_contours.csv', OUT/'H47_metrics.csv', OUT/'H48_test_contours.csv',
             OUT/'H48_all_files.csv', core.RESULTS/'frozen_config.json', OUT/'H49_dataset_manifest.json',
             OUT/'H40_raw_native_frames.csv', OUT/'H40_fixed_lofo.csv',
             HERE/'yaapt_reference.py', HERE/'verify_yaapt_reference.py', HERE/'YAAPT_SOURCE_NOTE.md']
    paths += [p for p in VENDOR.rglob('*') if p.is_file() and p.suffix != '.pyc']
    for directory in (core.TRAIN, REPO/'TinHieuKiemThu', core.TRAIN_GT, core.HERE/'test_3gt'):
        paths += list(directory.glob('*.wav'))+list(directory.glob('*.lab'))
    return paths


def register():
    assert not (HERE/'H52_REGISTRY.json').exists()
    audit.json_write(HERE/'H52_REGISTRY.json', dict(family='H52', rollback_commit=git('rev-parse','HEAD'),
        options=OPTIONS, parameters=PARAMETERS, actual_fit_files=[], seed=None, whole_pipeline=True,
        strict_target='Every one of 8 BT2 files average_mape < 2 percent',
        hashes={str(p.relative_to(REPO)):audit.digest(p) for p in protected()}))


def check_registry():
    registry = json.loads((HERE/'H52_REGISTRY.json').read_text())
    assert registry['options'] == OPTIONS and registry['parameters'] == PARAMETERS
    for relative, digest in registry['hashes'].items():
        assert audit.digest(REPO/relative) == digest, relative


def precheck():
    assert not (OUT/'H52_precheck.json').exists()
    cases = []
    for fs in (16000, 44100):
        t = np.arange(int(fs*.8))/fs
        for f0 in (100., 200., 300.):
            audio = .3*(np.sin(2*np.pi*f0*t)+.5*np.sin(4*np.pi*f0*t)+.3*np.sin(6*np.pi*f0*t))
            for identity in ('yaapt_default','yaapt_no_final_dp'):
                proof, metadata = native(audio, fs, BY_ID[identity])
                center = (proof['times'] > .15) & (proof['times'] < .65)
                values = proof['raw_f0'][center]
                error = float(np.median(abs(values[values > 0]-f0)))
                passed = bool(np.mean(values > 0) >= .8 and error < 5)
                cases.append(dict(fs=fs, f0=f0, option_id=identity, voiced_fraction=float(np.mean(values > 0)),
                                  median_absolute_error_hz=error, passed=passed, warnings=metadata['warnings']))
    audit.json_write(OUT/'H52_precheck.json', dict(cases=cases, passed=all(r['passed'] for r in cases),
        scope='12 synthetic harmonic calls; not BT2 measurement; silence not supported by vendor and no fake zero score'))
    assert all(r['passed'] for r in cases), cases
    print('PASS 12 synthetic rich harmonic cases', flush=True)


def baseline_train(name):
    rows = pd.read_csv(OUT/'H47_nested_contours.csv', float_precision='round_trip')
    rows = rows[(rows.file == name) & (rows.model == 'candidate')]
    return dict(times=rows.time_s.to_numpy(), pred=rows.pred_voiced.to_numpy(bool), f0=rows.f0_hz.to_numpy())


def compute(path, times, baseline, options, stage):
    fs, audio = core.load_audio(path)
    bank = {'hard170': (baseline['pred'], baseline['f0'])}
    outputs, receipts, cache = [], [], {}
    for option in options:
        if option['mode'] == 'control':
            continue
        key = (option['nlfer'], option['final_dp'])
        if key not in cache:
            proof, metadata = native(audio, fs, option)
            proof_path = OUT/f'H52_{stage}_native_{path.stem}_{option["id"]}.npz'
            assert not proof_path.exists()
            np.savez_compressed(proof_path, **proof)
            cache[key] = (proof, proof_path, metadata)
            outputs.append(proof_path)
        proof, proof_path, metadata = cache[key]
        pred, f0, support, index = project(proof, times, fs, option, baseline)
        bank[option['id']] = (pred, f0)
        receipts.append(dict(file=path.name, option_id=option['id'], input_sha256=audit.digest(path),
            proof=str(proof_path.relative_to(REPO)), proof_sha256=audit.digest(proof_path),
            actual_fit_files=[], source_commit='5c6c9bc48006d9eb5d5e874dd44f9a146a5ee38b', **metadata))
    arrays = OUT/f'H52_{stage}_predictions_{path.stem}.npz'
    assert not arrays.exists()
    np.savez_compressed(arrays, times=times, option_id=np.array(list(bank)),
        pred=np.array([x[0] for x in bank.values()]), f0=np.array([x[1] for x in bank.values()]))
    outputs.append(arrays)
    return bank, receipts, outputs, len(cache)


def train():
    check_registry()
    assert json.loads((OUT/'H52_precheck.json').read_text())['passed']
    assert not (OUT/'H52_train_experiment.json').exists()
    started = time.perf_counter()
    items = {item['file']:item for item in core.load_training()}
    fixed, receipts, outputs, calls = [], [], [], 0
    for name, item in items.items():
        baseline = baseline_train(name)
        assert np.allclose(baseline['times'], item['times'], atol=1e-12)
        bank, note, artifacts, count = compute(core.TRAIN/name, item['times'], baseline, OPTIONS, 'train')
        calls += count; receipts += note; outputs += artifacts
        for identity, (pred,f0) in bank.items():
            fixed.append(dict(option_id=identity, **core.score_file(item,pred,f0)))
        print('H52 measured train',name,flush=True)
    traces, selections = [], []
    for outer in ['final']+sorted(items):
        pool = [name for name in sorted(items) if name != outer]
        records = [dict(outer_held=outer, inner_held=row['file'], actual_fit_files='', **row)
                   for row in fixed if row['file'] in pool]
        traces += records
        selections.append(dict(outer_held=outer, selection_files=pool, option_id=choose(records)))
    selected = {r['outer_held']:r['option_id'] for r in selections}
    rows = []
    for split in ('train','lofo','nested'):
        for name in sorted(items):
            for model,identity in [('accepted','hard170'),('candidate',selected[name] if split=='nested' else selected['final'])]:
                metric = next(r for r in fixed if r['file']==name and r['option_id']==identity)
                rows.append(dict(split=split,model=model,**metric))
    summary, gates = common.gates(pd.DataFrame(rows))
    for filename, value in [('H52_fixed.csv',fixed),('H52_inner_traces.csv',traces),('H52_metrics.csv',rows)]:
        path = OUT/filename;pd.DataFrame(value).to_csv(path,index=False);outputs.append(path)
    freeze_path = OUT/'H52_FROZEN_SELECTION.json'
    audit.json_write(freeze_path,dict(option=BY_ID[selected['final']],parameters=PARAMETERS,
        selections=selections, external_options=list(dict.fromkeys(['hard170',selected['final'],'yaapt_default'])),
        no_test_selection=True, seed=None, actual_fit_files=[]))
    outputs.append(freeze_path)
    audit.json_write(OUT/'H52_train_experiment.json',dict(prereg_commit=git('rev-parse','HEAD'),
        selections=selections,decision=gates,summaries=summary,actual_fit_files=[],actual_yaapt_calls=calls,
        receipts=receipts,wall_time_s=time.perf_counter()-started,
        runtime=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,pandas=pd.__version__),
        artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in outputs}))
    print(json.dumps(dict(selections=selections,decision=gates),indent=2))


def external():
    check_registry()
    assert json.loads((OUT/'H52_train_verification.json').read_text())['passed']
    assert not (OUT/'H52_external_experiment.json').exists()
    freeze = json.loads((OUT/'H52_FROZEN_SELECTION.json').read_text())
    options = [BY_ID[identity] for identity in freeze['external_options']]
    old = pd.read_csv(OUT/'H48_test_contours.csv',float_precision='round_trip')
    rows, receipts, outputs, calls = [], [], [], 0
    for path in sorted((REPO/'TinHieuKiemThu').glob('*.wav')):
        item = core.frame_features(path,split='test')
        group = old[(old.file==path.name)&(old.model=='candidate')]
        baseline = dict(pred=group.pred_voiced.to_numpy(bool),f0=group.f0_hz.to_numpy())
        assert np.allclose(group.time_s,item['times'],atol=1e-12)
        bank,note,artifacts,count = compute(path,item['times'],baseline,options,'test')
        receipts += note;outputs += artifacts;calls += count
        for identity,(pred,f0) in bank.items():
            rows.append(dict(option_id=identity,**core.score_file(item,pred,f0)))
        print('H52 measured test',path.name,flush=True)
    path = OUT/'H52_test_metrics.csv';pd.DataFrame(rows).to_csv(path,index=False);outputs.append(path)
    audit.json_write(OUT/'H52_external_experiment.json',dict(frozen_commit=git('rev-parse','HEAD'),
        freeze_sha256=audit.digest(OUT/'H52_FROZEN_SELECTION.json'),actual_yaapt_calls=calls,
        receipts=receipts,historical_test_exposure=True,test_tuning=False,actual_fit_files=[],
        artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in outputs}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['precheck','register','train','external'])
    args=parser.parse_args()
    with threadpool_limits(limits=1):
        {'precheck':precheck,'register':register,'train':train,'external':external}[args.action]()
