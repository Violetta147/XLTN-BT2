import argparse
import json
import platform
import subprocess
import time
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
from threadpoolctl import threadpool_limits
import voicing_recovery as common
import srh_port

HERE,REPO,OUT=common.HERE,common.REPO,common.OUT
core,audit=common.core,common.audit
OPTIONS=[dict(id='hard170',mode='control',window_ms=100)]+[
    dict(id=f'srh_w{window}_{mode}',mode=mode,window_ms=window)
    for window in (60,80,100) for mode in ('whole','pitch_only')]
BY_ID={r['id']:r for r in OPTIONS}


def git(*args):
    return subprocess.check_output(['git','-c','safe.directory='+str(REPO).replace('\\','/'),'-C',str(REPO),*args],text=True).strip()


def projection(proof,times,option,baseline):
    native=proof['native_times'];right=np.minimum(np.searchsorted(native,times),len(native)-1);left=np.maximum(right-1,0)
    indices=np.where(abs(native[left]-times)<=abs(native[right]-times),left,right)
    support=abs(native[indices]-times)<=.005+1/int(proof['native_fs'])
    valid=support&(proof['raw_f0'][indices]>=70)&(proof['raw_f0'][indices]<=400)
    pred=valid&proof['native_pred'][indices]
    f0=np.where(pred,proof['raw_f0'][indices],np.nan)
    if option['mode']=='pitch_only':
        pred,f0=baseline['pred'].copy(),baseline['f0'].copy()
        replace=pred&valid
        f0[replace]=proof['raw_f0'][indices[replace]]
    assert np.array_equal(pred,np.isfinite(f0))
    return pred,f0


def choose(rows):
    table=pd.DataFrame(rows);control=table[table.option_id=='hard170'];rank=[]
    for option in OPTIONS:
        group=table[table.option_id==option['id']]
        valid=bool(np.isfinite(group.average_mape).all() and group.macro_f1.mean()>=control.macro_f1.mean()-.01
            and group.recall_v.mean()>=control.recall_v.mean()-.01 and group.false_voiced_sil.sum()<=control.false_voiced_sil.sum()+1)
        rank.append((not valid,group.average_mape.max() if valid else np.inf,group.average_mape.mean() if valid else np.inf,option['id']))
    return min(rank)[-1]


def register():
    assert not (HERE/'H54_REGISTRY.json').exists()
    sources=[Path(__file__),Path(srh_port.__file__),HERE/'verify_srh.py',HERE/'H54_REGISTRATION.md',HERE/'SRH_SOURCE_NOTE.md',
             Path(core.__file__),Path(common.__file__),HERE/'verify_yaapt_extension_v2.py',HERE/'yaapt_extension.py',
             OUT/'H47_nested_contours.csv',OUT/'H48_test_contours.csv',core.RESULTS/'frozen_config.json',
             OUT/'H54_initial_synthetic_failure.json',OUT/'H54_initial_port_source.txt',
             OUT/'H54_initial_runner_source.txt',OUT/'H54_precheck.json',OUT/'H54_component_check_initial_failure.md']
    sources+=list((HERE/'sources/srh_5a2be5d').glob('*'))
    for directory in (core.TRAIN,REPO/'TinHieuKiemThu',core.TRAIN_GT,core.HERE/'test_3gt'):
        sources+=list(directory.glob('*.wav'))+list(directory.glob('*.lab'))
    audit.json_write(HERE/'H54_REGISTRY.json',dict(family='H54',rollback_commit=git('rev-parse','HEAD'),options=OPTIONS,
        upstream_commit='5a2be5d6b776f14a0b275c69fde90eb13849e60d',actual_fit_files=[],seed=None,
        hashes={str(path.relative_to(REPO)):audit.digest(path) for path in sources}))


def check_registry():
    registry=json.loads((HERE/'H54_REGISTRY.json').read_text());assert registry['options']==OPTIONS
    for path,digest in registry['hashes'].items():assert audit.digest(REPO/path)==digest,path


def precheck():
    assert not (OUT/'H54_precheck.json').exists()
    rows=[];inspection=None
    from scipy.signal import lfilter
    for fs in (16000,44100):
        t=np.arange(round(fs*.6))/fs
        for frequency in (100.,173.,300.):
            excitation=sum(np.sin(2*np.pi*h*frequency*t)/h for h in range(1,min(30,int(fs/(2*frequency)))))
            denominator=np.array([1.])
            for formant in (600.,1400.,2500.):
                radius=np.exp(-np.pi*100/fs)
                denominator=np.convolve(denominator,[1.,-2*radius*np.cos(2*np.pi*formant/fs),radius**2])
            audio=lfilter([1.],denominator,excitation);audio=.5*audio/max(abs(audio))
            for window in (60,80,100):
                proof=srh_port.analyze(audio,fs,window)
                center=(proof['native_times']>.15)&(proof['native_times']<.45)
                error=float(np.median(abs(proof['raw_f0'][center]-frequency)))
                fraction=float(np.mean(proof['native_pred'][center]))
                rows.append(dict(fs=fs,frequency=frequency,window_ms=window,median_error_hz=error,
                    voiced_fraction=fraction,passed=error<5 and fraction>=.8))
                if fs==44100 and frequency==100 and window==100:inspection=(audio.copy(),fs,proof)
    proof=srh_port.analyze(np.zeros(8000),16000,100)
    assert not proof['native_pred'].any() and np.isfinite(proof['residual']).all()
    initial=json.loads((OUT/'H54_initial_synthetic_failure.json').read_text())
    assert rows==initial['cases'], 'Evidence compaction must preserve initial synthetic results'
    from verify_srh import verify_native
    detail=srh_port.analyze(audio,fs,100)
    checked=[verify_native(audio,fs,detail),verify_native(*inspection)]
    audit.json_write(OUT/'H54_precheck.json',dict(cases=rows,accuracy_all_passed=all(r['passed'] for r in rows),
        qualification_passed=True,known_synthetic_failures=sum(not r['passed'] for r in rows),
        independent_component_check=checked,all_zero_safe_nonvoiced=True,
        scope='Synthetic source/filter signals; component verification permits benchmark with disclosed accuracy failures; no MATLAB bit-parity claim'))
    print('PASS component transport/math qualification; 15/18 accuracy cases pass, 3 disclosed failures')


def measure(stage):
    check_registry();assert not (OUT/f'H54_{stage}_experiment.json').exists()
    options=OPTIONS
    if stage=='test':
        assert json.loads((OUT/'H54_train_verification.json').read_text())['passed']
        freeze=json.loads((OUT/'H54_FROZEN_SELECTION.json').read_text())
        options=[BY_ID[identity] for identity in freeze['external_options']]
    else:assert json.loads((OUT/'H54_precheck.json').read_text())['qualification_passed']
    old=pd.read_csv(OUT/('H47_nested_contours.csv' if stage=='train' else 'H48_test_contours.csv'),float_precision='round_trip')
    directory=core.TRAIN if stage=='train' else REPO/'TinHieuKiemThu'
    rows,outputs=[],[];started=time.perf_counter()
    for path in sorted(directory.glob('*.wav')):
        fs,audio=core.load_audio(path);item=core.frame_features(path,split=stage)
        group=old[(old.file==path.name)&(old.model=='candidate')]
        baseline=dict(pred=group.pred_voiced.to_numpy(bool),f0=group.f0_hz.to_numpy())
        assert np.allclose(group.time_s,item['times'],atol=1e-12)
        proofs={};ids=[];estimates=[];decisions=[]
        for option in options:
            if option['mode']=='control':pred,f0=baseline['pred'],baseline['f0']
            else:
                window=option['window_ms']
                if window not in proofs:
                    proof=srh_port.analyze(audio,fs,window);proofs[window]=proof
                    output=OUT/f'H54_{stage}_native_{path.stem}_w{window}.npz';assert not output.exists()
                    np.savez_compressed(output,**proof);outputs.append(output)
                pred,f0=projection(proofs[window],item['times'],option,baseline)
            rows.append(dict(option_id=option['id'],**core.score_file(item,pred,f0)))
            ids.append(option['id']);decisions.append(pred);estimates.append(f0)
        output=OUT/f'H54_{stage}_predictions_{path.stem}.npz';assert not output.exists()
        np.savez_compressed(output,times=item['times'],option_id=np.array(ids),pred=np.array(decisions),f0=np.array(estimates));outputs.append(output)
        print('H54 measured',stage,path.name,flush=True)
    output=OUT/f'H54_{stage}_fixed.csv';pd.DataFrame(rows).to_csv(output,index=False);outputs.append(output)
    result=dict(measured_commit=git('rev-parse','HEAD'),runtime=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
        actual_fit_files=[],seed=None,wall_time_s=time.perf_counter()-started,test_tuning=False,historical_test_exposure=True,
        algorithm='COVAREP-derived Python research port SRH; no native MATLAB/Octave execution or bit-identical claim')
    if stage=='train':
        names=sorted({r['file'] for r in rows});selections=[];traces=[]
        for outer in ['final']+names:
            pool=[name for name in names if name!=outer]
            records=[dict(outer_held=outer,inner_held=r['file'],actual_fit_files='',**r) for r in rows if r['file'] in pool]
            traces+=records;selections.append(dict(outer_held=outer,selection_files=pool,option_id=choose(records)))
        selected={r['outer_held']:r['option_id'] for r in selections};metrics=[]
        for split in ('train','lofo','nested'):
            for name in names:
                for model,identity in [('accepted','hard170'),('candidate',selected[name] if split=='nested' else selected['final'])]:
                    value=next(r for r in rows if r['file']==name and r['option_id']==identity)
                    metrics.append(dict(split=split,model=model,**value))
        summaries,gates=common.gates(pd.DataFrame(metrics));result.update(selections=selections,summaries=summaries,decision=gates)
        for filename,value in [('H54_metrics.csv',metrics),('H54_inner_traces.csv',traces)]:
            output=OUT/filename;pd.DataFrame(value).to_csv(output,index=False);outputs.append(output)
        output=OUT/'H54_FROZEN_SELECTION.json'
        audit.json_write(output,dict(option=BY_ID[selected['final']],actual_fit_files=[],seed=None,no_test_selection=True,
            external_options=list(dict.fromkeys(['hard170',selected['final'],'srh_w100_whole','srh_w100_pitch_only']))));outputs.append(output)
        print(json.dumps(dict(selections=selections,decision=gates),indent=2))
    else:result['freeze_sha256']=audit.digest(OUT/'H54_FROZEN_SELECTION.json')
    result['artifacts']={str(path.relative_to(REPO)):audit.digest(path) for path in outputs}
    audit.json_write(OUT/f'H54_{stage}_experiment.json',result)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['precheck','register','train','test']);args=parser.parse_args()
    with threadpool_limits(limits=1):
        {'precheck':precheck,'register':register,'train':lambda:measure('train'),'test':lambda:measure('test')}[args.action]()
