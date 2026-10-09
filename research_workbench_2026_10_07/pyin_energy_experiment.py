"""H70: one energy rejection stage on cached actual-25ms H69 pYIN."""
import argparse, json, platform, subprocess, time
from pathlib import Path
import numpy as np
import pandas as pd
import pyin25_experiment as old
from verify_srh import independent_item
from voicing_recovery import gates
HERE, OUT, REPO, core, audit = old.HERE, old.OUT, old.REPO, old.core, old.audit
THRESHOLDS = [0., .01, .02, .04, .08, .16, .32]
OPTIONS = [dict(id='hard170', threshold=None)] + [dict(id=f'pyin8_energy_{q:g}', threshold=q) for q in THRESHOLDS]

def energy(audio, fs):
    length, hop = round(.025*fs), round(.01*fs)
    frames = np.lib.stride_tricks.sliding_window_view(audio, length)[::hop]
    centered = frames - frames.mean(axis=1, keepdims=True)
    rms = np.sqrt(np.mean(centered**2, axis=1))
    reference = max(float(np.quantile(rms, .95, method='linear')), 1e-12)
    return dict(rms=rms, reference=np.asarray(reference), relative_rms=rms/reference,
                times=(np.arange(len(frames))*hop+length/2)/fs,
                frame_samples=np.asarray(length), hop_samples=np.asarray(hop), fs=np.asarray(fs))

def reject(pred, f0, relative_rms, threshold):
    keep = pred & (relative_rms >= threshold)
    return keep, np.where(keep, f0, np.nan)

def choose(rows, strict=False):
    if not strict:
        return historical_choose(rows)
    candidates=[]
    for option in OPTIONS[1:]:
        group=[r for r in rows if r['option_id']==option['id']]
        if all(np.isfinite(r['average_mape']) for r in group):
            candidates.append((max(r['average_mape'] for r in group),np.mean([r['average_mape'] for r in group]),option['id']))
    return min(candidates)[-1] if candidates else None

def historical_choose(rows):
    controls=[r for r in rows if r['option_id']=='hard170'];ranks=[]
    for option in OPTIONS:
        group=[r for r in rows if r['option_id']==option['id']]
        valid=all(np.isfinite(r['average_mape']) for r in group)
        valid &= all(np.mean([r[k] for r in group])>=np.mean([r[k] for r in controls])-.01 for k in ('macro_f1','recall_v'))
        valid &= sum(r['false_voiced_sil'] for r in group)<=sum(r['false_voiced_sil'] for r in controls)+1
        ranks.append((not valid,max(r['average_mape'] for r in group) if valid else np.inf,np.mean([r['average_mape'] for r in group]) if valid else np.inf,option['id']))
    return min(ranks)[-1]

def check_registry():
    r=json.loads((HERE/'H70_REGISTRY.json').read_text());assert r['options']==OPTIONS
    for p,d in r['source_hashes'].items(): assert audit.digest(REPO/p)==d,p
    for p,d in r['external_protected'].items(): assert audit.digest(Path(p))==d,p
    return r

def precheck():
    assert not (HERE/'H70_REGISTRY.json').exists() and not (OUT/'H70_precheck.json').exists()
    from verify_pyin_energy import scalar_energy
    checks=[]
    for fs in (16000,44100):
        t=np.arange(fs)/fs
        audio=np.sin(2*np.pi*173*t)*np.repeat([0.,.01,.1,1.],[fs//4,fs//4,fs//4,fs-3*(fs//4)])
        proof=energy(audio,fs);ref=scalar_energy(audio,fs)
        assert np.allclose(proof['rms'],ref['rms'],atol=1e-12,rtol=1e-12)
        assert np.allclose(proof['relative_rms'],ref['relative_rms'],atol=1e-12,rtol=1e-12)
        assert np.array_equal(proof['times'],ref['times'])
        changed=energy(7*audio+2,fs);assert np.allclose(changed['relative_rms'],proof['relative_rms'],atol=1e-12,rtol=1e-12)
        zero=energy(np.zeros(fs),fs);assert np.all(zero['relative_rms']==0)
        for q in THRESHOLDS:
            values=np.array(THRESHOLDS+[.5,1.]);p=np.ones(len(values),bool);f=np.full(len(values),200.)
            keep,out=reject(p,f,values,q);expected=np.array([float(v)>=q for v in values]);assert np.array_equal(keep,expected) and np.array_equal(np.isfinite(out),expected)
        checks.append(dict(fs=fs,scalar_rms_quantile_parity=True,dc_gain_invariance=True,zero_finite=True,inclusive_threshold_boundary=True,frame_samples=int(proof['frame_samples']),hop_samples=int(proof['hop_samples'])))
    audit.json_write(OUT/'H70_precheck.json',dict(status='PASS',BT2_used=False,checks=checks))
    r=json.loads((HERE/'H69_REGISTRY.json').read_text())
    sources=dict(r['source_hashes'])
    paths=[HERE/p for p in ('H70_REGISTRATION.md','pyin_energy_experiment.py','verify_pyin_energy.py','results/H70_precheck.json','H69_REGISTRY.json','verify_pyin25_v2.py','results/H69_train_experiment.json','results/H69_verification_v2.json')]
    receipt=json.loads((OUT/'H69_train_experiment.json').read_text());paths += [REPO/p for p in receipt['artifacts']]
    for p in paths:sources[str(p.relative_to(REPO))]=audit.digest(p)
    audit.json_write(HERE/'H70_REGISTRY.json',dict(family='H70',rollback=old.common.matrix.commit_id(),options=OPTIONS,source_hashes=sources,external_protected=r['external_protected'],new_native_inference=False,strict_diagnostic='Finite minimax only, no promotion or relaxation of historical gates',test_enabled_only_if_historical_gates_and_actual25_compliance=True))
    print('PASS H70 synthetic RMS/quantile/boundary; no BT2 measurement')

def train():
    check_registry();assert not (OUT/'H70_train_experiment.json').exists()
    git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip()
    branch=subprocess.check_output(git+['branch','--show-current'],cwd=REPO,text=True).strip()
    remote=subprocess.check_output(git+['ls-remote','origin','refs/heads/'+branch],cwd=REPO,text=True).split()[0]
    assert head==remote and not subprocess.check_output(git+['status','--porcelain'],cwd=REPO,text=True).strip()
    start=time.perf_counter();rows=[];artifacts=[];energies=[];removals=[];old_contours=pd.read_csv(OUT/'H47_nested_contours.csv',float_precision='round_trip')
    for path in sorted(core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');proof=energy(audio,fs)
        native=dict(np.load(OUT/f'H69_native_{path.stem}_pyin25_beta2_8.npz'));assert np.array_equal(proof['times'],native['native_times']) and np.array_equal(proof['times'],item['times'])
        bp,bf=native['voiced'],native['raw_f0'];old_rows=old_contours[(old_contours.file==path.name)&(old_contours.model=='candidate')];preds=[];pitches=[]
        for option in OPTIONS:
            if option['threshold'] is None:pred,f0=old_rows.pred_voiced.to_numpy(bool),old_rows.f0_hz.to_numpy()
            else:pred,f0=reject(bp,bf,proof['relative_rms'],option['threshold'])
            preds.append(pred);pitches.append(f0);rows.append(dict(option_id=option['id'],**core.score_file(item,pred,f0)))
            if option['threshold'] is not None:
                for i in np.flatnonzero(bp & ~pred):removals.append(dict(file=path.name,option_id=option['id'],frame=int(i),time_s=item['times'][i],label=item['labels'][i],relative_rms=proof['relative_rms'][i],removed_f0=bf[i]))
        for i in range(len(bp)):energies.append(dict(file=path.name,frame=i,time_s=item['times'][i],label=item['labels'][i],pyin8_voiced=bool(bp[i]),relative_rms=proof['relative_rms'][i],rms=proof['rms'][i]))
        p=OUT/f'H70_proof_{path.stem}.npz';np.savez_compressed(p,**proof,pred=preds,f0=pitches);artifacts.append(p)
    names=sorted({r['file'] for r in rows});inner=[];selections=[];strict=[]
    for held in ['final']+names:
        pool=[n for n in names if n!=held];records=[r for r in rows if r['file'] in pool]
        selections.append(dict(outer_held=held,selection_files=pool,option_id=choose(records)))
        strict.append(dict(outer_held=held,selection_files=pool,option_id=choose(records,strict=True)))
        inner += [dict(outer_held=held,inner_held=r['file'],actual_fit_files='',**r) for r in records]
    selected={r['outer_held']:r['option_id'] for r in selections};summary=[]
    for split in ('train','lofo','nested'):
        for name in names:
            for model,identity in [('accepted','hard170'),('candidate',selected[name] if split=='nested' else selected['final'])]:
                original=next(r for r in rows if r['file']==name and r['option_id']==identity);summary.append(dict(split=split,model=model,**original))
    summaries,decision=gates(pd.DataFrame(summary))
    for name,data in [('H70_fixed.csv',rows),('H70_inner_traces.csv',inner),('H70_metrics.csv',summary),('H70_energy_frames.csv',energies),('H70_removed_frames.csv',removals)]:
        p=OUT/name;pd.DataFrame(data).to_csv(p,index=False);artifacts.append(p)
    audit.json_write(OUT/'H70_train_experiment.json',dict(family='H70',prereg_commit=head,registry_sha256=audit.digest(HERE/'H70_REGISTRY.json'),selections=selections,strict_diagnostic_selections=strict,summaries=summaries,decision=decision,actual_native_inferences=0,actual_supervised_fits=0,groups=len(rows),new_energy_only_groups=24,test_used=False,frame_ms=25,hop_ms=10,normalization='Own-file centered RMS / linear p95 RMS; denominator floor1e-12; unlabeled full-file transform',runtime=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__),wall_time_s=time.perf_counter()-start,artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in artifacts}))
    print(json.dumps(dict(selections=selections,strict_diagnostic=strict,decision=decision),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['precheck','train']);a=p.parse_args();precheck() if a.action=='precheck' else train()
