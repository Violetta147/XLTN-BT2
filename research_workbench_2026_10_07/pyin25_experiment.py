import argparse
import json
import platform
import time
import numpy as np
import pandas as pd
import scipy
from threadpoolctl import threadpool_limits
import recovery_pitch as common
from pyin25_adapter import pitch
from verify_srh import independent_item
from voicing_recovery import gates

HERE, OUT, REPO, core, audit = common.HERE, common.OUT, common.REPO, common.core, common.audit
OPTIONS = [dict(id='hard170', mode='baseline', beta=[])] + [dict(id=f'pyin25_beta2_{b}', mode='whole', beta=[2,b]) for b in (8,18,38)]


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
    registry = json.loads((HERE/'H69_REGISTRY.json').read_text())
    assert registry['options'] == OPTIONS
    for path, digest in registry['source_hashes'].items():
        assert audit.digest(REPO/path) == digest, path
    return registry


def precheck():
    assert not (HERE/'H69_REGISTRY.json').exists() and not (OUT/'H69_precheck.json').exists()
    import sys
    from pathlib import Path
    tests=[];silence=[];artifacts=[]
    for fs in (16000,44100):
        t=np.arange(fs)/fs
        for option in OPTIONS[1:]:
            proof,log=pitch(np.zeros(fs),fs,option['beta'])
            silence.append(dict(fs=fs,option_id=option['id'],voiced=int(proof['voiced'].sum()),passed=bool(not np.any(proof['voiced'])),runtime_log=log))
            for frequency in (90,173,300):
                clean=sum(np.cos(2*np.pi*frequency*h*t+.3*h)/h for h in range(1,9));noise=np.random.default_rng(11).normal(size=len(t));audio=clean+noise*(.001*np.std(clean)/np.std(noise))
                proof,log=pitch(audio,fs,option['beta'])
                from verify_pyin25 import certify_native
                certificate=certify_native(proof,len(audio),fs)
                middle=(proof['native_times']>=.1)&(proof['native_times']<=.9);values=proof['raw_f0'][middle&proof['voiced']]
                fraction=float(proof['voiced'][middle].mean());error=float(abs(1200*np.log2(np.median(values)/frequency))) if len(values) else float('inf')
                path=OUT/f'H69_synthetic_{fs}_{frequency}_{option["id"]}.npz';np.savez_compressed(path,**proof);artifacts.append(path)
                tests.append(dict(fs=fs,true_hz=frequency,option_id=option['id'],absolute_median_cents_error=error,central_voiced_fraction=fraction,integration_certificate=certificate,passed=bool(error<100 and fraction>=.8),runtime_log=log))
    passed=all(t['passed'] for t in tests+silence)
    audit.json_write(OUT/'H69_precheck.json',dict(status='PASS' if passed else 'FAIL',BT2_used=False,tests=tests,silence_tests=silence))
    assert passed,'H69 precheck failed; saved; no BT2 allowed'
    old=json.loads((HERE/'H68_REGISTRY.json').read_text());sources=[REPO/p for p in old['source_hashes']]
    sources += [HERE/p for p in ('pyin25_adapter.py','pyin25_experiment.py','verify_pyin25.py','pyin_adapter.py','H69_REGISTRATION.md','FRAME_25MS_AUDIT.md','R02_DISTRIBUTION_REPORT.md','results/H69_precheck.json','results/librosa_011_provenance.json')]+artifacts
    sources += [REPO/'research_3gt_2026_10_05/results'/p for p in ('baseline_train.csv','baseline_summary.json')]
    external=dict(old['external_protected']);external[str(Path(sys.executable))]=audit.digest(Path(sys.executable))
    external.update(tests[0]['runtime_log']['source_hashes'])
    audit.json_write(HERE/'H69_REGISTRY.json',dict(family='H69',options=OPTIONS,rollback=common.matrix.commit_id(),source_hashes={str(p.relative_to(REPO)):audit.digest(p) for p in sources},external_protected=external,test_enabled_only_if_eligible=True,random_training=False,selection='minimax_file_mape_then_mean_then_id',assignment_compliant_options=[o['id'] for o in OPTIONS[1:]],historical_control_compliant=False))
    print('PASS H69',len(tests),'new synthetic fixtures +',len(silence),'zero fixtures; no BT2 used')


def train():
    registry = check_registry()
    for path, digest in registry['external_protected'].items():
        from pathlib import Path
        assert audit.digest(Path(path)) == digest
    assert not (OUT/'H69_train_experiment.json').exists()
    # Prereg must be exactly the already pushed HEAD before any new train measurement.
    import subprocess
    head = common.matrix.commit_id()
    branch = subprocess.check_output(['git', '-c', f'safe.directory={REPO.as_posix()}', 'branch', '--show-current'], cwd=REPO, text=True).strip()
    remote = subprocess.check_output(['git', '-c', f'safe.directory={REPO.as_posix()}', 'ls-remote', 'origin', f'refs/heads/{branch}'], cwd=REPO, text=True).split()[0]
    assert head == remote
    assert not subprocess.check_output(['git', '-c', f'safe.directory={REPO.as_posix()}', 'status', '--porcelain'], cwd=REPO, text=True).strip()
    started = time.perf_counter()
    rows,artifacts,changes=[],[],[]
    old=pd.read_csv(OUT/'H47_nested_contours.csv',float_precision='round_trip');logs=[]
    for path in sorted(core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train');base=old[(old.file==path.name)&(old.model=='candidate')];bp,bf=base.pred_voiced.to_numpy(bool),base.f0_hz.to_numpy()
        assert np.allclose(base.time_s,item['times'],atol=1e-12)
        values=[];masks=[]
        for option in OPTIONS:
            if option['mode']=='baseline':pred,f0=bp.copy(),bf.copy()
            else:
                proof,log=pitch(audio,fs,option['beta']);logs.append(dict(file=path.name,option_id=option['id'],**log))
                assert np.array_equal(proof['native_times'],item['times'])
                pred,f0=proof['voiced'],proof['raw_f0']
                native_path=OUT/f'H69_native_{path.stem}_{option["id"]}.npz';np.savez_compressed(native_path,**proof);artifacts.append(native_path)
            masks.append(pred);values.append(f0);rows.append(dict(option_id=option['id'],**core.score_file(item,pred,f0)))
            for i in range(len(pred)):
                if pred[i]!=bp[i] or (pred[i] and f0[i]!=bf[i]):changes.append(dict(file=path.name,option_id=option['id'],frame=i,time_s=item['times'][i],label=item['labels'][i],baseline_voiced=bool(bp[i]),candidate_voiced=bool(pred[i]),baseline_hz=bf[i],candidate_hz=f0[i]))
            print('H69 measured',path.name,option['id'],flush=True)
        saved=OUT/f'H69_predictions_{path.stem}.npz';np.savez_compressed(saved,times=item['times'],pred=masks,f0=values);artifacts.append(saved)
    logpath=OUT/'H69_runtime_logs.json';audit.json_write(logpath,logs);artifacts.append(logpath)
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
    for filename, data in [('H69_fixed.csv', rows), ('H69_inner_traces.csv', inner), ('H69_metrics.csv', summary),
                           ('H69_changed_cases.csv', changes)]:
        p = OUT/filename; pd.DataFrame(data).to_csv(p, index=False); artifacts.append(p)
    audit.json_write(OUT/'H69_train_experiment.json', dict(family='H69', prereg_commit=head,
        registry_sha256=audit.digest(HERE/'H69_REGISTRY.json'), selections=selections, summaries=summaries,
        decision=decision, actual_supervised_fits=0, actual_native_inferences=len(logs), unique_measured_groups=len(rows), test_used=False,
        cv_note='Official pYIN25 actual frames; 3 priors per file, no BT2 supervised fitting; historical control noncompliant25; grouped config selection exploratory.',
        runtime=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__),
        wall_time_s=time.perf_counter()-started, artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in artifacts}))
    print(json.dumps(dict(selections=selections, decision=decision), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['precheck', 'train'])
    args = parser.parse_args(); precheck() if args.action == 'precheck' else train()
