import argparse
import json
import platform
import time
import numpy as np
import pandas as pd
import scipy
from threadpoolctl import threadpool_limits
import recovery_pitch as common
from ar4_harmonic_nls import refine
from verify_srh import independent_item
from voicing_recovery import gates

HERE, OUT, REPO, core, audit = common.HERE, common.OUT, common.REPO, common.core, common.audit
OPTIONS = [dict(id='hard170', order=0), dict(id='ar4_nls_3', order=3)]


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
    registry = json.loads((HERE/'H67_REGISTRY.json').read_text())
    assert registry['options'] == OPTIONS
    for path, digest in registry['source_hashes'].items():
        assert audit.digest(REPO/path) == digest, path
    return registry


def precheck():
    assert not (HERE/'H67_REGISTRY.json').exists() and not (OUT/'H67_precheck.json').exists()
    from ar4_certificate import independent_certificate
    from ar4_harmonic_nls import residual
    tests=[]
    with threadpool_limits(limits=1):
        for fs in (16000,44100):
            t=np.arange(round(.025*fs))/fs
            for seed in (11,29,47):
                for frequency in (90,200,320):
                    for noise_id,true_a in [('ar1',[.8,0,0,0]),('ar4',[.5,.2,.1,-.15])]:
                        clean=sum(np.cos(2*np.pi*frequency*h*t+.3*h)/h for h in range(1,4))
                        innovations=np.random.default_rng(seed).normal(size=len(t)+200)
                        noise=np.zeros(len(innovations))
                        for i in range(4,len(noise)):noise[i]=sum(true_a[k-1]*noise[i-k] for k in range(1,5))+innovations[i]
                        noise=noise[200:];audio=clean+noise*(.1*np.std(clean)/np.std(noise));anchor=frequency*2**(50/1200)
                        p=refine(audio,fs,anchor,3);certificate=independent_certificate(audio,fs,anchor,3,p['f0']);changed=refine(audio*3+1,fs,anchor,3)
                        error=abs(1200*np.log2(p['f0']/frequency))
                        objective=bool(np.isclose(p['cost'],certificate['cost'],rtol=1e-8,atol=1e-10) and np.allclose(p['grid_cost'],certificate['grid_cost'],rtol=1e-8,atol=1e-10) and np.allclose(p['bracket'],certificate['bracket'],atol=1e-8) and np.allclose(p['a'],certificate['a'],atol=1e-8) and np.allclose(p['a_raw'],certificate['a_raw'],atol=1e-8))
                        invariant=bool(abs(1200*np.log2(changed['f0']/p['f0']))<.01 and np.allclose(changed['a'],p['a'],atol=1e-8))
                        # Zero AR: conditional rows retain original basis/data after row4.
                        from verify_ar_nls import independent_design
                        from scipy.linalg import qr
                        weights=np.sqrt(np.hanning(len(audio)))[4:];q,_=qr(independent_design(len(audio),fs,frequency,3)[4:]*weights[:,None],mode='economic');v=audio[4:]*weights;e=v-q@(q.T@v)
                        zero_parity=bool(np.isclose(residual(audio,fs,frequency,3,np.zeros(4))[0],e@e,atol=1e-10,rtol=0))
                        tests.append(dict(fs=fs,seed=seed,true_hz=frequency,noise_id=noise_id,absolute_cents_error=error,independent_coefficients_objective_grid=objective,gain_dc_invariant=invariant,conditional_zero_ar_parity=zero_parity,passed=bool(error<100 and objective and invariant and zero_parity)))
    fallback=all(refine(np.full(400,value),16000,200.,3)['silent_fallback'] for value in (0.,1.))
    passed=all(r['passed'] for r in tests) and fallback
    audit.json_write(OUT/'H67_precheck.json',dict(status='PASS' if passed else 'FAIL',synthetic_only=True,BT2_used=False,tests=tests,zero_constant_fallback=fallback))
    assert passed,'H67 precheck failed; saved; no BT2 allowed'
    old=json.loads((HERE/'H66_REGISTRY.json').read_text())
    sources=[REPO/p for p in old['source_hashes']]
    sources += [HERE/p for p in ('ar4_harmonic_nls.py','ar4_nls_experiment.py','verify_ar4_nls.py','ar4_certificate.py','H67_REGISTRATION.md','results/H67_precheck.json','results/H66_fixed.csv','results/H66_train_experiment.json','results/H66_verification.json')]
    audit.json_write(HERE/'H67_REGISTRY.json',dict(family='H67',options=OPTIONS,rollback=common.matrix.commit_id(),source_hashes={str(p.relative_to(REPO)):audit.digest(p) for p in sources},external_protected=old['external_protected'],test_enabled_only_if_eligible=True,random_training=False,selection='minimax_file_mape_then_mean_then_id'))
    print('PASS H67',len(tests),'new synthetic fixtures; no BT2 used')


def train():
    registry = check_registry()
    for path, digest in registry['external_protected'].items():
        from pathlib import Path
        assert audit.digest(Path(path)) == digest
    assert not (OUT/'H67_train_experiment.json').exists()
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
    with threadpool_limits(limits=1):
        for path in sorted(core.TRAIN.glob('*.wav')):
            item, fs, audio = independent_item(path, 'train')
            length, hop = round(.025*fs), round(.01*fs)
            base = old[(old.file == path.name) & (old.model == 'candidate')]
            pred, pitch = base.pred_voiced.to_numpy(bool), base.f0_hz.to_numpy()
            assert np.allclose(base.time_s, item['times'], atol=1e-12)
            values = []
            for option in OPTIONS:
                f0 = pitch.copy()
                hits = 0
                for i in np.flatnonzero(pred) if option['order'] else []:
                    proof = refine(audio[i*hop:i*hop+length], fs, pitch[i], option['order'])
                    f0[i] = proof['f0']; hits += proof['at_boundary']
                    changes.append(dict(file=path.name, option_id=option['id'], frame=int(i), time_s=item['times'][i],
                        label=item['labels'][i], baseline_hz=pitch[i], candidate_hz=f0[i],
                        cents_shift=1200*np.log2(f0[i]/pitch[i]), at_boundary=proof['at_boundary'],
                        silent_fallback=proof['silent_fallback'], score=proof['score'],
                        rho=proof['rho'], rho_raw=proof['rho_raw'], cost=proof['cost'], **{f'a{k+1}':float(proof['a'][k]) for k in range(4)}, **{f'raw_a{k+1}':float(proof['a_raw'][k]) for k in range(4)},
                        left_hz=proof['bracket'][0], right_hz=proof['bracket'][1]))
                values.append(f0)
                rows.append(dict(option_id=option['id'], **core.score_file(item, pred, f0)))
                boundaries.append(dict(file=path.name, option_id=option['id'], boundary_count=hits,
                    voiced_frames=int(pred.sum()), boundary_fraction=hits/max(int(pred.sum()), 1)))
                print('H67 measured', path.name, option['id'], flush=True)
            saved = OUT/f'H67_predictions_{path.stem}.npz'
            np.savez_compressed(saved, times=item['times'], pred=pred, f0=values)
            artifacts.append(saved)
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
    for filename, data in [('H67_fixed.csv', rows), ('H67_inner_traces.csv', inner), ('H67_metrics.csv', summary),
                           ('H67_changed_cases.csv', changes), ('H67_boundaries.csv', boundaries)]:
        p = OUT/filename; pd.DataFrame(data).to_csv(p, index=False); artifacts.append(p)
    audit.json_write(OUT/'H67_train_experiment.json', dict(family='H67', prereg_commit=head,
        registry_sha256=audit.digest(HERE/'H67_REGISTRY.json'), selections=selections, summaries=summaries,
        decision=decision, actual_supervised_fits=0, actual_frame_noise_fits=len(changes), unique_measured_groups=len(rows), test_used=False,
        cv_note='Per-frame waveform harmonic/AR nuisance fits; no LAB/GT supervised fitting; grouped config selection; exploratory.',
        runtime=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__),
        wall_time_s=time.perf_counter()-started, artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in artifacts}))
    print(json.dumps(dict(selections=selections, decision=decision), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['precheck', 'train'])
    args = parser.parse_args(); precheck() if args.action == 'precheck' else train()
