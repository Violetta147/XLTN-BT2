import argparse
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import srh_experiment as source

HERE,REPO,OUT,core,audit,common=source.HERE,source.REPO,source.OUT,source.core,source.audit,source.common
OPTIONS=[dict(id='hard170',width_cents=0)]+[dict(id=f'srh_bound_{width}',width_cents=width) for width in (100,200,400)]
BY_ID={o['id']:o for o in OPTIONS}


def infer(proof,times,baseline,width):
    f0=baseline['f0'].copy();pred=baseline['pred'].copy()
    if not width:return pred,f0
    native=proof['native_times'];right=np.minimum(np.searchsorted(native,times),len(native)-1);left=np.maximum(right-1,0)
    indices=np.where(abs(native[left]-times)<=abs(native[right]-times),left,right)
    lower,upper=proof['passes'][-1];frequencies=np.arange(1,proof['curves'].shape[1]+1)
    for i in np.flatnonzero(pred):
        k=indices[i]
        if abs(times[i]-native[k])>.005+1/int(proof['native_fs']):continue
        distance=abs(1200*np.log2(frequencies/f0[i]))
        eligible=(distance<=width)&(frequencies>=max(70,lower))&(frequencies<=min(400,upper))
        candidates=np.flatnonzero(eligible)
        if not len(candidates):continue
        best=candidates[np.argmax(proof['curves'][k,candidates])]
        if proof['curves'][k,best]>0:f0[i]=float(frequencies[best])
    assert np.array_equal(pred,np.isfinite(f0))
    return pred,f0


def choose(rows):
    control=[r for r in rows if r['option_id']=='hard170'];rank=[]
    for option in OPTIONS:
        group=[r for r in rows if r['option_id']==option['id']]
        valid=all(np.isfinite(r['average_mape']) for r in group)
        valid &= np.mean([r['macro_f1'] for r in group])>=np.mean([r['macro_f1'] for r in control])-.01
        valid &= np.mean([r['recall_v'] for r in group])>=np.mean([r['recall_v'] for r in control])-.01
        valid &= sum(r['false_voiced_sil'] for r in group)<=sum(r['false_voiced_sil'] for r in control)+1
        rank.append((not valid,max(r['average_mape'] for r in group) if valid else np.inf,
                     np.mean([r['average_mape'] for r in group]) if valid else np.inf,option['id']))
    return min(rank)[-1]


def precheck():
    assert not (OUT/'H55_precheck.json').exists()
    from scipy.signal import lfilter
    from verify_bounded_srh import scalar_infer
    rows=[]
    for fs in (16000,44100):
        times=np.arange(round(.6*fs))/fs
        for f in (100.,173.,300.):
            x=sum(np.sin(2*np.pi*h*f*times)/h for h in range(1,min(30,int(fs/(2*f)))))
            denominator=np.array([1.])
            for formant in (600.,1400.,2500.):
                radius=np.exp(-np.pi*100/fs);denominator=np.convolve(denominator,[1.,-2*radius*np.cos(2*np.pi*formant/fs),radius**2])
            x=lfilter([1.],denominator,x);x=.5*x/max(abs(x))
            proof=source.srh_port.analyze(x,fs,100);canonical=proof['native_times']
            base=dict(pred=np.ones(len(canonical),bool),f0=np.full(len(canonical),f*1.015))
            for width in (100,200,400):
                pred,pitch=infer(proof,canonical,base,width);p,q=scalar_infer(proof,canonical,base,width)
                assert np.array_equal(pred,p) and np.array_equal(pitch,q)
                center=(canonical>.15)&(canonical<.45);error=float(np.median(abs(pitch[center]-f)))
                assert error<5 and np.max(abs(1200*np.log2(pitch/base['f0'])))<=width+1e-9
                rows.append(dict(fs=fs,frequency=f,width_cents=width,median_error_hz=error,passed=True))
    curves=np.zeros((2,400));curves[:,199:201]=1
    fixture=dict(native_times=np.array([.1,.11]),native_fs=16000,passes=np.array([[70,400]]),curves=curves)
    base=dict(pred=np.array([True,False,True]),f0=np.array([200.,np.nan,200.]))
    for width in (100,200,400):
        pred,pitch=infer(fixture,np.array([.105,.11,.4]),base,width)
        assert pitch[0]==200 and np.isnan(pitch[1]) and pitch[2]==200
    audit.json_write(OUT/'H55_precheck.json',dict(passed=True,cases=rows,native_window_ms=100,
        tests=['scalar selector equality','biased-anchor known periodicity','bounded displacement','tie lower frequency','UV remains NaN','unsupported timestamp fallback'],
        limits='Biased synthetic anchors are near truth; this cannot certify correction of baseline octave errors outside the bound. H54 unbounded synthetic failures remain.'))
    print('PASS H55: 18 synthetic bounded selections and fallback/tie/mask checks')


def register():
    assert not (HERE/'H55_REGISTRY.json').exists()
    paths=[Path(__file__),HERE/'verify_bounded_srh.py',HERE/'H55_REGISTRATION.md',OUT/'H55_precheck.json',
        HERE/'H54_REGISTRY.json',Path(source.__file__),Path(source.srh_port.__file__),HERE/'verify_srh.py',
        Path(core.__file__),Path(common.__file__),HERE/'verify_yaapt_extension_v2.py',HERE/'yaapt_extension.py',
        OUT/'H47_nested_contours.csv',OUT/'H48_test_contours.csv',core.RESULTS/'frozen_config.json']
    paths+=list(OUT.glob('H54_*_native_*_w100.npz'))+[OUT/f'H54_{s}_verification.json' for s in ('train','test')]
    for directory in (core.TRAIN,REPO/'TinHieuKiemThu',core.TRAIN_GT,core.HERE/'test_3gt'):
        paths+=list(directory.glob('*.wav'))+list(directory.glob('*.lab'))
    audit.json_write(HERE/'H55_REGISTRY.json',dict(rollback_commit=source.git('rev-parse','HEAD'),options=OPTIONS,actual_fit_files=[],seed=None,
        hashes={str(p.relative_to(REPO)):audit.digest(p) for p in paths}))


def check_registry():
    registry=json.loads((HERE/'H55_REGISTRY.json').read_text());assert registry['options']==OPTIONS
    for relative,digest in registry['hashes'].items():assert audit.digest(REPO/relative)==digest,relative


def measure(stage):
    check_registry();assert not (OUT/f'H55_{stage}_experiment.json').exists()
    assert json.loads((OUT/'H55_precheck.json').read_text())['passed']
    options=OPTIONS
    if stage=='test':
        assert json.loads((OUT/'H55_train_verification.json').read_text())['passed']
        freeze=json.loads((OUT/'H55_FROZEN_SELECTION.json').read_text());options=[BY_ID[s] for s in freeze['external_options']]
    old=pd.read_csv(OUT/('H47_nested_contours.csv' if stage=='train' else 'H48_test_contours.csv'),float_precision='round_trip')
    rows=[];outputs=[];started=time.perf_counter()
    for path in sorted((core.TRAIN if stage=='train' else REPO/'TinHieuKiemThu').glob('*.wav')):
        item=core.frame_features(path,split=stage);group=old[(old.file==path.name)&(old.model=='candidate')]
        base=dict(pred=group.pred_voiced.to_numpy(bool),f0=group.f0_hz.to_numpy())
        assert np.allclose(item['times'],group.time_s,atol=1e-12)
        proof=dict(np.load(OUT/f'H54_{stage}_native_{path.stem}_w100.npz',allow_pickle=False))
        ids=[];masks=[];pitches=[]
        for option in options:
            pred,pitch=infer(proof,item['times'],base,option['width_cents'])
            assert np.array_equal(pred,base['pred'])
            rows.append(dict(option_id=option['id'],**core.score_file(item,pred,pitch)))
            ids.append(option['id']);masks.append(pred);pitches.append(pitch)
        output=OUT/f'H55_{stage}_predictions_{path.stem}.npz';assert not output.exists()
        np.savez_compressed(output,times=item['times'],option_id=np.array(ids),pred=np.array(masks),f0=np.array(pitches));outputs.append(output)
        print('H55 measured',stage,path.name,flush=True)
    output=OUT/f'H55_{stage}_fixed.csv';pd.DataFrame(rows).to_csv(output,index=False);outputs.append(output)
    receipt=dict(measured_commit=source.git('rev-parse','HEAD'),actual_fit_files=[],seed=None,new_native_calls=0,
        reused_verified_native_source='H54 SRH100',test_tuning=False,historical_test_exposure=True,wall_time_s=time.perf_counter()-started)
    if stage=='train':
        names=sorted({r['file'] for r in rows});selections=[];traces=[]
        for outer in ['final']+names:
            pool=[name for name in names if name!=outer];group=[r for r in rows if r['file'] in pool]
            selections.append(dict(outer_held=outer,selection_files=pool,option_id=choose(group)))
            traces += [dict(outer_held=outer,inner_held=r['file'],actual_fit_files='',**r) for r in group]
        chosen={r['outer_held']:r['option_id'] for r in selections};metrics=[]
        for split in ('train','lofo','nested'):
            for name in names:
                for model,identity in [('accepted','hard170'),('candidate',chosen[name] if split=='nested' else chosen['final'])]:
                    metrics.append(dict(split=split,model=model,**next(r for r in rows if r['file']==name and r['option_id']==identity)))
        summaries,gates=common.gates(pd.DataFrame(metrics));receipt.update(selections=selections,summaries=summaries,decision=gates)
        for filename,value in [('H55_inner_traces.csv',traces),('H55_metrics.csv',metrics)]:
            output=OUT/filename;pd.DataFrame(value).to_csv(output,index=False);outputs.append(output)
        output=OUT/'H55_FROZEN_SELECTION.json';audit.json_write(output,dict(option=BY_ID[chosen['final']],actual_fit_files=[],seed=None,
            external_options=list(dict.fromkeys(['hard170',chosen['final'],'srh_bound_200'])),no_test_selection=True));outputs.append(output)
        print(json.dumps(dict(selections=selections,decision=gates),indent=2))
    else:receipt['freeze_sha256']=audit.digest(OUT/'H55_FROZEN_SELECTION.json')
    receipt['artifacts']={str(p.relative_to(REPO)):audit.digest(p) for p in outputs}
    audit.json_write(OUT/f'H55_{stage}_experiment.json',receipt)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['precheck','register','train','test']);args=parser.parse_args()
    {'precheck':precheck,'register':register,'train':lambda:measure('train'),'test':lambda:measure('test')}[args.action]()
