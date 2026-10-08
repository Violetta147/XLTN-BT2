import argparse
import json
import platform
import time
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
import recovery_pitch as common
from harmonic_product import refine
from verify_srh import independent_item
from voicing_recovery import gates

HERE, OUT, REPO, core, audit = common.HERE, common.OUT, common.REPO, common.core, common.audit
OPTIONS = [dict(id='hard170', order=0), dict(id='hps_3', order=3), dict(id='hps_5', order=5)]


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
    registry = json.loads((HERE/'H63_REGISTRY.json').read_text())
    assert registry['options'] == OPTIONS
    for path, digest in registry['source_hashes'].items():
        assert audit.digest(REPO/path) == digest, path
    return registry


def precheck():
    assert not (HERE/'H63_REGISTRY.json').exists()
    from verify_hps import independent_refine
    rows = []
    with threadpool_limits(limits=1):
        for fs in (16000, 44100):
            t = np.arange(round(.025*fs))/fs
            for seed in (11, 29, 47):
                for order in (3, 5):
                    for frequency in (90, 200, 320):
                        clean = sum(np.cos(2*np.pi*frequency*h*t+.3*h)/h for h in range(1, order+1))
                        audio = clean+np.random.default_rng(seed).normal(0, np.std(clean)*.1, len(t))
                        anchor = frequency*2**(50/1200)
                        p = refine(audio, fs, anchor, order)
                        independent = independent_refine(audio, fs, anchor, order)
                        error = abs(1200*np.log2(p['f0']/frequency))
                        parity = np.allclose(p['scores'], independent['scores'], rtol=1e-9, atol=1e-9)
                        scaled = refine(audio*3+1, fs, anchor, order)
                        row = dict(fs=fs, seed=seed, order=order, true_hz=frequency,
                                   absolute_cents_error=error, dft_parity=bool(parity),
                                   gain_dc_invariant=bool(scaled['f0'] == p['f0']),
                                   argmax_parity=bool(p['f0'] == independent['f0']))
                        row['pass'] = bool(error < 100 and parity and row['gain_dc_invariant'] and row['argmax_parity'])
                        rows.append(row)
        silent = refine(np.zeros(400), 16000, 200., 3)
    passed = all(r['pass'] for r in rows) and silent['f0'] == 200. and silent['silent_fallback']
    audit.json_write(OUT/'H63_precheck.json', dict(status='PASS' if passed else 'FAIL', synthetic_only=True,
        BT2_used=False, tests=rows, zero_input_fallback=bool(silent['silent_fallback']),
        seeds_are_fixture_noise_not_model_training=True))
    assert passed, 'Precheck failed; saved evidence; no BT2 measurement allowed'
    old = json.loads((HERE/'H61_REGISTRY.json').read_text())
    sources = [REPO/p for p in old['source_hashes'] if p not in (
        'research_workbench_2026_10_07\\harmonic_nls.py', 'research_workbench_2026_10_07\\nls_experiment.py',
        'research_workbench_2026_10_07\\verify_nls.py', 'research_workbench_2026_10_07\\H61_REGISTRATION.md',
        'research_workbench_2026_10_07\\NLS_SOURCE_REVIEW.md', 'research_workbench_2026_10_07\\results\\H61_precheck.json')]
    # Include the original protected hashes as well as every local imported dependency.
    sources += [HERE/p for p in ('harmonic_product.py', 'hps_experiment.py', 'verify_hps.py',
        'H63_REGISTRATION.md', 'HPS_SOURCE_REVIEW.md', 'results/H63_precheck.json', 'srh_experiment.py')]
    sources += [REPO/'.agents/skills/literature-review/PROVENANCE.md']
    submitted = REPO.parent/'turn-in-assignment - Copy'/'BT2_ACF_best_no_energy_set.ipynb'
    audit.json_write(HERE/'H63_REGISTRY.json', dict(family='H63', options=OPTIONS,
        rollback=common.matrix.commit_id(), source_hashes={str(p.relative_to(REPO)):audit.digest(p) for p in sources},
        external_protected={str(submitted):audit.digest(submitted)}, test_enabled_only_if_eligible=True,
        random_training=False, selection='minimax_file_mape_then_mean_then_id'))
    print('PASS H63', len(rows), 'synthetic fixtures; registry written; no BT2 measurement')


def train():
    registry = check_registry()
    for path, digest in registry['external_protected'].items():
        from pathlib import Path
        assert audit.digest(Path(path)) == digest
    assert not (OUT/'H63_train_experiment.json').exists()
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
                        label=item['labels'][i], baseline_hz=pitch[i], hps_hz=f0[i],
                        cents_shift=1200*np.log2(f0[i]/pitch[i]), at_boundary=proof['at_boundary'],
                        silent_fallback=proof['silent_fallback'], score=proof['score']))
                values.append(f0)
                rows.append(dict(option_id=option['id'], **core.score_file(item, pred, f0)))
                boundaries.append(dict(file=path.name, option_id=option['id'], boundary_count=hits,
                    voiced_frames=int(pred.sum()), boundary_fraction=hits/max(int(pred.sum()), 1)))
                print('H63 measured', path.name, option['id'], flush=True)
            saved = OUT/f'H63_predictions_{path.stem}.npz'
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
    for filename, data in [('H63_fixed.csv', rows), ('H63_inner_traces.csv', inner), ('H63_metrics.csv', summary),
                           ('H63_changed_cases.csv', changes), ('H63_boundaries.csv', boundaries)]:
        p = OUT/filename; pd.DataFrame(data).to_csv(p, index=False); artifacts.append(p)
    audit.json_write(OUT/'H63_train_experiment.json', dict(family='H63', prereg_commit=head,
        registry_sha256=audit.digest(HERE/'H63_REGISTRY.json'), selections=selections, summaries=summaries,
        decision=decision, actual_fits=0, unique_measured_groups=len(rows), test_used=False,
        cv_note='No label/ML fit; deterministic pitch estimation; grouped file config selection; exploratory.',
        runtime=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__),
        wall_time_s=time.perf_counter()-started, artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in artifacts}))
    print(json.dumps(dict(selections=selections, decision=decision), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['precheck', 'train'])
    args = parser.parse_args(); precheck() if args.action == 'precheck' else train()
