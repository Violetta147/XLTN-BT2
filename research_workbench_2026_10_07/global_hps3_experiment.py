import argparse
import json
import platform
import time
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
import recovery_pitch as common
from global_harmonic_product import refine
from verify_srh import independent_item
from voicing_recovery import gates

HERE, OUT, REPO, core, audit = common.HERE, common.OUT, common.REPO, common.core, common.audit
OPTIONS = [dict(id='hard170', order=0), dict(id='global_hps_3', order=3)]


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
    registry = json.loads((HERE/'H65_REGISTRY.json').read_text())
    assert registry['options'] == OPTIONS
    for path, digest in registry['source_hashes'].items():
        assert audit.digest(REPO/path) == digest, path
    return registry


def register():
    assert not (HERE/'H65_REGISTRY.json').exists()
    proof = json.loads((OUT/'H64_precheck.json').read_text())
    passed = [r for r in proof['tests'] if r['order'] == 3]
    assert proof['status'] == 'FAIL' and proof['synthetic_only'] and not proof['BT2_used']
    assert len(passed) == 18 and all(r['pass'] for r in passed) and proof['zero_input_fallback']
    old = json.loads((HERE/'H63_REGISTRY.json').read_text())
    sources = [REPO/p for p in old['source_hashes']]
    sources += [HERE/p for p in ('H63_REGISTRY.json', 'global_harmonic_product.py',
        'global_hps3_experiment.py', 'verify_global_hps3.py', 'H65_REGISTRATION.md',
        'H64_REGISTRATION.md', 'H64_REPORT.md', 'results/H64_precheck.json')]
    sources += [REPO/'docs/skills/ML_RESEARCH_SKILLS_2026-10-08.json']
    submitted = REPO.parent/'turn-in-assignment - Copy'/'BT2_ACF_best_no_energy_set.ipynb'
    audit.json_write(HERE/'H65_REGISTRY.json', dict(family='H65', options=OPTIONS,
        rollback=common.matrix.commit_id(), source_hashes={str(p.relative_to(REPO)):audit.digest(p) for p in sources},
        external_protected={str(submitted):audit.digest(submitted)}, test_enabled_only_if_eligible=True,
        random_training=False, selection='minimax_file_mape_then_mean_then_id',
        precheck_reused='results/H64_precheck.json: all 18 order3 fixtures, zero fallback; no rerun',
        H64_failure_retained=True, precheck_passed_fixtures=18))
    print('PASS H65 registration uses 18 cached order3 fixtures; no synthetic/BT2 inference executed')


def train():
    registry = check_registry()
    for path, digest in registry['external_protected'].items():
        from pathlib import Path
        assert audit.digest(Path(path)) == digest
    assert not (OUT/'H65_train_experiment.json').exists()
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
                print('H65 measured', path.name, option['id'], flush=True)
            saved = OUT/f'H65_predictions_{path.stem}.npz'
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
    for filename, data in [('H65_fixed.csv', rows), ('H65_inner_traces.csv', inner), ('H65_metrics.csv', summary),
                           ('H65_changed_cases.csv', changes), ('H65_boundaries.csv', boundaries)]:
        p = OUT/filename; pd.DataFrame(data).to_csv(p, index=False); artifacts.append(p)
    audit.json_write(OUT/'H65_train_experiment.json', dict(family='H65', prereg_commit=head,
        registry_sha256=audit.digest(HERE/'H65_REGISTRY.json'), selections=selections, summaries=summaries,
        decision=decision, actual_fits=0, unique_measured_groups=len(rows), test_used=False,
        cv_note='No label/ML fit; deterministic pitch estimation; grouped file config selection; exploratory.',
        runtime=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__),
        wall_time_s=time.perf_counter()-started, artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in artifacts}))
    print(json.dumps(dict(selections=selections, decision=decision), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['register', 'train'])
    args = parser.parse_args(); register() if args.action == 'register' else train()
