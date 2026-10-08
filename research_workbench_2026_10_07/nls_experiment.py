import argparse
import json
import platform
import time
import numpy as np
import pandas as pd
import scipy
from threadpoolctl import threadpool_limits
import recovery_pitch as common
from harmonic_nls import refine
from verify_srh import independent_item
from voicing_recovery import gates

HERE, OUT, REPO, core, audit=common.HERE,common.OUT,common.REPO,common.core,common.audit
OPTIONS=[dict(id='hard170',order=0),dict(id='nls_3',order=3),dict(id='nls_5',order=5)]


def choose(rows):
    base=[r for r in rows if r['option_id']=='hard170'];rank=[]
    for option in OPTIONS:
        group=[r for r in rows if r['option_id']==option['id']]
        good=all(np.isfinite(r['average_mape']) for r in group)
        for key in ('macro_f1','recall_v'):
            good &= np.mean([r[key] for r in group])>=np.mean([r[key] for r in base])-.01
        good &= sum(r['false_voiced_sil'] for r in group)<=sum(r['false_voiced_sil'] for r in base)+1
        rank.append((not good,max(r['average_mape'] for r in group) if good else np.inf,
            np.mean([r['average_mape'] for r in group]) if good else np.inf,option['id']))
    return sorted(rank)[0][-1]


def check_registry():
    registry=json.loads((HERE/'H61_REGISTRY.json').read_text());assert registry['options']==OPTIONS
    for path,digest in registry['source_hashes'].items():assert audit.digest(REPO/path)==digest,path
    return registry


def precheck():
    from verify_nls import qr_residual
    rows=[]
    with threadpool_limits(limits=1):
        for fs in (16000,44100):
            t=np.arange(round(.025*fs))/fs
            for seed in (11,29,47):
                for order in (3,5):
                    for frequency in (90,200,320):
                        clean=sum(np.cos(2*np.pi*frequency*h*t+.3*h)/h for h in range(1,order+1))
                        audio=clean+np.random.default_rng(seed).normal(0,np.std(clean)*.1,len(t))
                        p=refine(audio,fs,frequency*2**(50/1200),order)
                        error=abs(1200*np.log2(p['f0']/frequency));assert error<100,(fs,seed,order,frequency,error)
                        assert np.isclose(qr_residual(audio,fs,p['f0'],order),p['cost'],atol=1e-9,rtol=1e-9)
                        scaled=refine(audio*3+1,fs,frequency*2**(50/1200),order)
                        assert abs(scaled['f0']-p['f0'])<1e-3
                        rows.append(dict(fs=fs,seed=seed,order=order,true_hz=frequency,absolute_cents_error=error))
    audit.json_write(OUT/'H61_precheck.json',dict(status='PASS',synthetic_only=True,BT2_used=False,
        tests=rows,independent_qr_parity=True,gain_dc_invariance=True,
        seeds_are_fixture_noise_not_model_training=True))
    sources=[HERE/'harmonic_nls.py',HERE/'nls_experiment.py',HERE/'verify_nls.py',
        HERE/'H61_REGISTRATION.md',HERE/'NLS_SOURCE_REVIEW.md',OUT/'H61_precheck.json',
        HERE/'recovery_pitch.py',HERE/'voicing_matrix.py',HERE/'voicing_recovery.py',
        HERE/'verify_srh.py',HERE/'verify_yaapt_extension_v2.py',HERE/'yaapt_extension.py',
        REPO/'research_3gt_2026_10_05/core.py',REPO/'research_workbench_2026_10_06/audit.py',
        core.RESULTS/'frozen_config.json',OUT/'H47_nested_contours.csv']
    sources+=list(core.TRAIN.glob('*.wav'))+list(core.TRAIN.glob('*.lab'))+list(core.TRAIN_GT.glob('*.lab'))
    audit.json_write(HERE/'H61_REGISTRY.json',dict(family='H61',options=OPTIONS,rollback=common.matrix.commit_id(),
        source_hashes={str(p.relative_to(REPO)):audit.digest(p) for p in sources},
        test_enabled_only_if_eligible=True,random_training=False))
    print('PASS H61',len(rows),'synthetic noise fixtures; registered; no BT2 measurement')


def train():
    check_registry();assert not (OUT/'H61_train_experiment.json').exists()
    started=time.perf_counter();rows=[];artifacts=[]
    old=pd.read_csv(OUT/'H47_nested_contours.csv',float_precision='round_trip')
    with threadpool_limits(limits=1):
        for path in sorted(core.TRAIN.glob('*.wav')):
            item,fs,audio=independent_item(path,'train');length,hop=round(.025*fs),round(.01*fs)
            base=old[(old.file==path.name)&(old.model=='candidate')]
            pred=base.pred_voiced.to_numpy(bool);pitch=base.f0_hz.to_numpy()
            assert np.allclose(base.time_s,item['times'],atol=1e-12)
            indices=np.flatnonzero(pred);proofs={};values=[]
            for option in OPTIONS:
                f0=pitch.copy()
                if option['order']:
                    evidence=[]
                    for i in indices:
                        p=refine(audio[i*hop:i*hop+length],fs,pitch[i],option['order'])
                        f0[i]=p['f0'];evidence.append(p)
                    proofs[option['id']]=dict(indices=indices,f0=f0[indices],
                        cost=[p['cost'] for p in evidence],bracket=[p['bracket'] for p in evidence],
                        at_boundary=[p['at_boundary'] for p in evidence],coefficients=[p['coefficients'] for p in evidence])
                    proofpath=OUT/f'H61_{option["id"]}_{path.stem}.npz'
                    np.savez_compressed(proofpath,**proofs[option['id']]);artifacts.append(proofpath)
                values.append(f0);rows.append(dict(option_id=option['id'],**core.score_file(item,pred,f0)))
                print('H61 measured',path.name,option['id'],flush=True)
            saved=OUT/f'H61_predictions_{path.stem}.npz'
            np.savez_compressed(saved,times=item['times'],pred=pred,f0=values);artifacts.append(saved)
    names=sorted({r['file'] for r in rows});inner=[];selections=[]
    for held in ['final']+names:
        pool=[n for n in names if n!=held];records=[r for r in rows if r['file'] in pool]
        selections.append(dict(outer_held=held,selection_files=pool,option_id=choose(records)))
        for r in records:inner.append(dict(outer_held=held,inner_held=r['file'],actual_fit_files='',**r))
    selection={r['outer_held']:r['option_id'] for r in selections};summary=[]
    for split in ('train','lofo','nested'):
        for name in names:
            for model,identity in [('accepted','hard170'),('candidate',selection[name] if split=='nested' else selection['final'])]:
                metric=next(r for r in rows if r['file']==name and r['option_id']==identity)
                summary.append(dict(split=split,model=model,**metric))
    summaries,decision=gates(pd.DataFrame(summary))
    for filename,data in [('H61_fixed.csv',rows),('H61_inner_traces.csv',inner),('H61_metrics.csv',summary)]:
        p=OUT/filename;pd.DataFrame(data).to_csv(p,index=False);artifacts.append(p)
    audit.json_write(OUT/'H61_train_experiment.json',dict(family='H61',prereg_commit=common.matrix.commit_id(),
        registry_sha256=audit.digest(HERE/'H61_REGISTRY.json'),selections=selections,summaries=summaries,decision=decision,
        actual_fits=0,unique_measured_groups=len(rows),test_used=False,
        cv_note='Deterministic signal regression per voiced frame; config selection grouped by file, no LAB fitting.',
        runtime=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
        wall_time_s=time.perf_counter()-started,artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in artifacts}))
    print(json.dumps(dict(selections=selections,decision=decision),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['precheck','train'])
    args=parser.parse_args();precheck() if args.action=='precheck' else train()
