import argparse
import json
import platform
import time
import numpy as np
import pandas as pd
import scipy
from threadpoolctl import threadpool_limits
import recovery_pitch as common
from pefac_adapter import native, project
from verify_srh import independent_item
from voicing_recovery import gates

HERE, OUT, REPO, core, audit = common.HERE, common.OUT, common.REPO, common.core, common.audit
OPTIONS = [dict(id='hard170', mode='baseline', threshold=0.)] + [dict(id=f'pefac_whole_q{q}', mode='whole', threshold=q) for q in (.2,.5,.8)] + [dict(id='pefac_pitch_only', mode='pitch_only', threshold=0.)]


def choose(rows):
    control = [r for r in rows if r['option_id'] == 'hard170']
    ranks = []
    for option in OPTIONS:
        group = [r for r in rows if r['option_id'] == option['id']]
        valid = all(np.isfinite(r['average_mape']) for r in group)
        for key in ('macro_f1', 'recall_v'):
            valid &= np.mean([r[key] for r in group]) >= np.mean([r[key] for r in control])-.01
        valid &= sum(r['false_voiced_sil'] for r in group) <= sum(r['false_voiced_sil'] for r in control)+1
        ranks.append((not valid, max(r['average_mape'] for r in group) if valid else np.inf,
                      np.mean([r['average_mape'] for r in group]) if valid else np.inf, option['id']))
    return min(ranks)[-1]


def check_registry():
    registry = json.loads((HERE/'H68_REGISTRY.json').read_text())
    assert registry['options'] == OPTIONS
    for path, digest in registry['source_hashes'].items():
        assert audit.digest(REPO/path) == digest, path
    return registry


def precheck():
    assert not (HERE/'H68_REGISTRY.json').exists() and not (OUT/'H68_precheck.json').exists()
    from pefac_certificate import certify
    from pefac_adapter import EXE
    tests=[];artifacts=[]
    for fs in (16000,44100):
        t=np.arange(round(1.2*fs))/fs
        for frequency in (90,173,300):
            clean=sum(np.cos(2*np.pi*frequency*h*t+.3*h)/h for h in range(1,17))
            noise=np.random.default_rng(11).normal(size=len(t));audio=clean+noise*(.01*np.std(clean)/np.std(noise))
            proof,log=native(audio,fs);cert=certify(proof)
            changed,_=native(audio*3,fs)
            gain=abs(1200*np.log2(np.median(changed['raw_f0'])/np.median(proof['raw_f0'])))
            assert gain<.1
            times=np.arange(.0125,1.175,.01);pred=np.arange(len(times))%3==0;pitch=np.where(pred,frequency,np.nan)
            for option in OPTIONS[1:]:
                p,f=project(proof,times,fs,option,pred,pitch)
                from verify_pefac import independent_projection
                p2,f2=independent_projection(proof,times,fs,option,pred,pitch)
                assert np.array_equal(p,p2) and np.allclose(f,f2,equal_nan=True,atol=0,rtol=0)
            error=abs(1200*np.log2(np.median(proof['raw_f0'])/frequency))
            path=OUT/f'H68_synthetic_{fs}_{frequency}.npz';np.savez_compressed(path,**proof);artifacts.append(path)
            tests.append(dict(fs=fs,true_hz=frequency,median_hz=float(np.median(proof['raw_f0'])),absolute_median_cents_error=float(error),accuracy_diagnostic_pass=bool(error<100),integration_pass=True,gain_cents=float(gain),certificate=cert,runtime_log=log))
    audit.json_write(OUT/'H68_precheck.json',dict(status='PASS',integration_only=True,accuracy_all_pass=all(r['accuracy_diagnostic_pass'] for r in tests),BT2_used=False,tests=tests,earlier_runtime_probes=dict(missing_dependency_exit1='filtbankm missing; resolved by pinned upstream aliases; source unchanged',tone200_median_hz=100.5864,tone200_pv_median=.7279,tone200_accuracy='FAIL half-frequency; preserved; not an integration gate')))
    old=json.loads((HERE/'H67_REGISTRY.json').read_text());sources=[REPO/p for p in old['source_hashes']]
    sources += [HERE/p for p in ('pefac_adapter.py','pefac_bridge.m','pefac_certificate.py','pefac_experiment.py','verify_pefac.py','H68_REGISTRATION.md','results/H68_precheck.json','results/H67_fixed.csv','results/H67_verification.json','results/H67_train_experiment.json')]
    sources += list((HERE/'vendor/voicebox_pefac').iterdir())+artifacts
    external=dict(old['external_protected']);external[str(EXE)]=audit.digest(EXE)
    for r in tests:
        for key in ('image_filter','image_pad'):
            p=r['runtime_log'][key];external[p]=audit.digest(__import__('pathlib').Path(p))
    audit.json_write(HERE/'H68_REGISTRY.json',dict(family='H68',options=OPTIONS,rollback=common.matrix.commit_id(),source_hashes={str(p.relative_to(REPO)):audit.digest(p) for p in sources},external_protected=external,test_enabled_only_if_eligible=True,random_training=False,selection='minimax_file_mape_then_mean_then_id'))
    print('PASS H68 integration',len(tests),'new synthetic fixtures; accuracy diagnostics retained')


def train():
    registry = check_registry()
    for path, digest in registry['external_protected'].items():
        from pathlib import Path
        assert audit.digest(Path(path)) == digest
    assert not (OUT/'H68_train_experiment.json').exists()
    # Prereg must be exactly the already pushed HEAD before any new train measurement.
    import subprocess
    head = common.matrix.commit_id()
    branch = subprocess.check_output(['git', '-c', f'safe.directory={REPO.as_posix()}', 'branch', '--show-current'], cwd=REPO, text=True).strip()
    remote = subprocess.check_output(['git', '-c', f'safe.directory={REPO.as_posix()}', 'ls-remote', 'origin', f'refs/heads/{branch}'], cwd=REPO, text=True).split()[0]
    assert head == remote
    assert not subprocess.check_output(['git', '-c', f'safe.directory={REPO.as_posix()}', 'status', '--porcelain'], cwd=REPO, text=True).strip()
    started = time.perf_counter()
    rows, artifacts, changes, boundaries = [], [], [], []
    old = pd.read_csv(OUT/'H47_nested_contours.csv', float_precision='round_trip')
    logs=[]
    for path in sorted(core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train')
        base=old[(old.file==path.name)&(old.model=='candidate')]
        base_pred,base_f0=base.pred_voiced.to_numpy(bool),base.f0_hz.to_numpy()
        assert np.allclose(base.time_s,item['times'],atol=1e-12)
        proof,log=native(audio,fs);logs.append(dict(file=path.name,**log))
        native_path=OUT/f'H68_native_{path.stem}.npz';np.savez_compressed(native_path,**proof);artifacts.append(native_path)
        values=[];masks=[]
        for option in OPTIONS:
            if option['mode']=='baseline':pred,f0=base_pred.copy(),base_f0.copy()
            else:pred,f0=project(proof,item['times'],fs,option,base_pred,base_f0)
            masks.append(pred);values.append(f0)
            rows.append(dict(option_id=option['id'],**core.score_file(item,pred,f0)))
            for i in range(len(pred)):
                if pred[i]!=base_pred[i] or (pred[i] and f0[i]!=base_f0[i]):
                    changes.append(dict(file=path.name,option_id=option['id'],frame=i,time_s=item['times'][i],label=item['labels'][i],baseline_voiced=bool(base_pred[i]),candidate_voiced=bool(pred[i]),baseline_hz=base_f0[i],candidate_hz=f0[i]))
            print('H68 measured',path.name,option['id'],flush=True)
        saved=OUT/f'H68_predictions_{path.stem}.npz';np.savez_compressed(saved,times=item['times'],pred=masks,f0=values);artifacts.append(saved)
    logpath=OUT/'H68_runtime_logs.json';audit.json_write(logpath,logs);artifacts.append(logpath)
    names = sorted({r['file'] for r in rows})
    inner, selections = [], []
    for held in ['final']+names:
        pool = [n for n in names if n != held]
        records = [r for r in rows if r['file'] in pool]
        selections.append(dict(outer_held=held, selection_files=pool, option_id=choose(records)))
        for r in records:
            inner.append(dict(outer_held=held, inner_held=r['file'], actual_fit_files='', **r))
    selection = {r['outer_held']:r['option_id'] for r in selections}
    summary = []
    for split in ('train', 'lofo', 'nested'):
        for name in names:
            for model, identity in [('accepted', 'hard170'), ('candidate', selection[name] if split == 'nested' else selection['final'])]:
                metric = next(r for r in rows if r['file'] == name and r['option_id'] == identity)
                summary.append(dict(split=split, model=model, **metric))
    summaries, decision = gates(pd.DataFrame(summary))
    for filename, data in [('H68_fixed.csv', rows), ('H68_inner_traces.csv', inner), ('H68_metrics.csv', summary),
                           ('H68_changed_cases.csv', changes)]:
        p = OUT/filename; pd.DataFrame(data).to_csv(p, index=False); artifacts.append(p)
    audit.json_write(OUT/'H68_train_experiment.json', dict(family='H68', prereg_commit=head,
        registry_sha256=audit.digest(HERE/'H68_REGISTRY.json'), selections=selections, summaries=summaries,
        decision=decision, actual_supervised_fits=0, actual_native_inferences=len(logs), unique_measured_groups=len(rows), test_used=False,
        cv_note='Official fixed PEFAC; one native inference per file and 4 projections; no BT2 supervised fitting; grouped config selection; exploratory.',
        runtime=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__),
        wall_time_s=time.perf_counter()-started, artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in artifacts}))
    print(json.dumps(dict(selections=selections, decision=decision), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['precheck', 'train'])
    args = parser.parse_args(); precheck() if args.action == 'precheck' else train()
