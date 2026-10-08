"""Independent QR nuisance-AR, whitening, objective/grid/bracket and scalar metrics."""
import json
import math
import numpy as np
import pandas as pd


from scipy.linalg import qr

def independent_design(length,fs,frequency,order):
    t=np.array([(i-(length-1)/2)/fs for i in range(length)])
    columns=[np.ones(length)]
    columns += [np.cos(2*np.pi*h*frequency*t) for h in range(1,order+1)]
    columns += [np.sin(2*np.pi*h*frequency*t) for h in range(1,order+1)]
    return np.column_stack(columns)

def independent_certificate(segment,fs,anchor,order,frequency):
    length=len(segment)
    design=independent_design(length,fs,anchor,order)
    weights=np.sqrt(.5-.5*np.cos(2*np.pi*np.arange(length)/(length-1)))
    q,r=qr(design*weights[:,None],mode='economic')
    beta=np.linalg.solve(r,q.T@(segment*weights))
    errors=segment-design@beta
    denominator=sum(float(x)*float(x) for x in errors[:-1])
    raw=sum(float(errors[i])*float(errors[i-1]) for i in range(1,length))/denominator if denominator else 0.
    rho=max(-.95,min(.95,raw))
    def objective(f):
        matrix=independent_design(length,fs,f,order)
        transformed=np.empty_like(matrix); target=np.empty(length)
        transformed[0]=matrix[0]*math.sqrt(1-rho*rho)
        target[0]=segment[0]*math.sqrt(1-rho*rho)
        for i in range(1,length):
            transformed[i]=matrix[i]-rho*matrix[i-1]
            target[i]=segment[i]-rho*segment[i-1]
        transformed *= weights[:,None]; target *= weights
        orthogonal,_=qr(transformed,mode='economic')
        error=target-orthogonal@(orthogonal.T@target)
        return float(error@error)
    lower=max(70.,anchor*math.pow(2,-1/12));upper=min(400.,anchor*math.pow(2,1/12))
    grid=np.array(sorted(set(min(upper,max(lower,anchor*math.pow(2,k/1200))) for k in range(-100,101,5))))
    if not np.any(segment-segment[0]):
        return dict(cost=0.,rho=0.,rho_raw=0.,grid_cost=np.zeros(len(grid)),bracket=np.array([anchor,anchor]),boundary=False,silent=True)
    costs=np.array([objective(f) for f in grid]);best=int(np.argmin(costs))
    bracket=np.array([grid[max(0,best-1)],grid[min(len(grid)-1,best+1)]])
    cost=objective(frequency)
    assert bracket[0]-1e-8<=frequency<=bracket[1]+1e-8
    assert cost<=min(costs)+1e-9
    return dict(cost=cost,rho=rho,rho_raw=raw,grid_cost=costs,bracket=bracket,
        boundary=bool(np.isclose(frequency,lower,atol=1e-4) or np.isclose(frequency,upper,atol=1e-4)),silent=False)


def independent_choose(records):
    identities = sorted({r['option_id'] for r in records})
    baseline = [r for r in records if r['option_id'] == 'hard170']
    ranking = []
    for identity in identities:
        group = [r for r in records if r['option_id'] == identity]
        valid = all(math.isfinite(r['average_mape']) for r in group)
        valid = valid and all(sum(r[k] for r in group)/len(group) >= sum(r[k] for r in baseline)/len(baseline)-.01 for k in ('macro_f1', 'recall_v'))
        valid = valid and sum(r['false_voiced_sil'] for r in group) <= sum(r['false_voiced_sil'] for r in baseline)+1
        ranking.append((not valid, max(r['average_mape'] for r in group) if valid else math.inf,
                        sum(r['average_mape'] for r in group)/len(group) if valid else math.inf, identity))
    return min(ranking)[-1]


def verify():
    import ar_nls_experiment as api
    from verify_srh import independent_item, independent_score
    from voicing_recovery import gates
    from threadpoolctl import threadpool_limits
    registry = api.check_registry()
    receipt = json.loads((api.OUT/'H66_train_experiment.json').read_text())
    for p, digest in receipt['artifacts'].items():
        assert api.audit.digest(api.REPO/p) == digest, p
    from pathlib import Path
    for p, digest in registry['external_protected'].items():
        assert api.audit.digest(Path(p)) == digest, p
    fixed = pd.read_csv(api.OUT/'H66_fixed.csv', float_precision='round_trip')
    old = pd.read_csv(api.OUT/'H47_nested_contours.csv', float_precision='round_trip')
    cases = pd.read_csv(api.OUT/'H66_changed_cases.csv', float_precision='round_trip')
    bounds = pd.read_csv(api.OUT/'H66_boundaries.csv', float_precision='round_trip')
    checks = []; verified_frames = 0
    with threadpool_limits(limits=1):
        for path in sorted(api.core.TRAIN.glob('*.wav')):
            item, fs, audio = independent_item(path, 'train')
            length, hop = round(fs*.025), round(fs*.01)
            saved = dict(np.load(api.OUT/f'H66_predictions_{path.stem}.npz'))
            baseline = old[(old.file == path.name) & (old.model == 'candidate')]
            pred, base = baseline.pred_voiced.to_numpy(bool), baseline.f0_hz.to_numpy()
            assert np.array_equal(pred, saved['pred']) and np.array_equal(item['times'], saved['times'])
            for k, option in enumerate(api.OPTIONS):
                f0 = saved['f0'][k]; hits = 0
                assert np.array_equal(np.isfinite(f0), pred)
                if not option['order']:
                    assert np.allclose(f0, base, equal_nan=True, rtol=0, atol=0)
                else:
                    group = cases[(cases.file == path.name) & (cases.option_id == option['id'])].set_index('frame')
                    assert np.array_equal(group.index, np.flatnonzero(pred))
                    for i in np.flatnonzero(pred):
                        p = independent_certificate(audio[i*hop:i*hop+length], fs, base[i], option['order'], f0[i])
                        row = group.loc[i]
                        assert row.label == item['labels'][i] and row.time_s == item['times'][i]
                        assert row.baseline_hz == base[i] and row.candidate_hz == f0[i]
                        assert np.isclose(row.score, -p['cost'], atol=1e-9, rtol=1e-9)
                        assert np.isclose(row.cost, p['cost'], atol=1e-9, rtol=1e-9)
                        assert np.isclose(row.rho, p['rho'], atol=1e-8) and np.isclose(row.rho_raw, p['rho_raw'], atol=1e-8)
                        assert np.allclose([row.left_hz,row.right_hz],p['bracket'],atol=1e-8)
                        assert bool(row.at_boundary) == p['boundary'] and bool(row.silent_fallback) == p['silent']
                        hits += p['boundary']; verified_frames += 1
                bound = bounds[(bounds.file == path.name) & (bounds.option_id == option['id'])].iloc[0]
                assert bound.boundary_count == hits and bound.voiced_frames == pred.sum()
                assert np.isclose(bound.boundary_fraction, hits/pred.sum(), atol=1e-12)
                metrics = independent_score(item, pred, f0)
                row = fixed[(fixed.file == path.name) & (fixed.option_id == option['id'])].iloc[0]
                for key, value in metrics.items():
                    assert np.isclose(value, row[key], rtol=1e-9, atol=1e-9), (path, key)
                checks.append(dict(file=path.name, option_id=option['id'], voiced_frames=int(pred.sum())))
            print('H66 verified', path.name, flush=True)
    records = fixed.to_dict('records'); names = sorted(fixed.file.unique()); selections = []
    inner = pd.read_csv(api.OUT/'H66_inner_traces.csv', float_precision='round_trip', keep_default_na=False)
    for held in ['final']+names:
        pool = [n for n in names if n != held]
        selections.append(dict(outer_held=held, selection_files=pool,
            option_id=independent_choose([r for r in records if r['file'] in pool])))
        group = inner[inner.outer_held == held]
        assert len(group) == len(pool)*len(api.OPTIONS) and set(group.inner_held) == set(pool)
        assert (group.actual_fit_files == '').all()
        for _, row in group.iterrows():
            original = next(r for r in records if r['file'] == row['file'] and r['option_id'] == row.option_id)
            assert row.inner_held == row['file']
            for key, value in original.items():
                assert row[key] == value, (held, key)
    assert selections == receipt['selections']
    selection = {r['outer_held']:r['option_id'] for r in selections}
    summary = pd.read_csv(api.OUT/'H66_metrics.csv', float_precision='round_trip')
    for _, row in summary.iterrows():
        identity = 'hard170' if row.model == 'accepted' else selection[row['file']] if row.split == 'nested' else selection['final']
        assert row.option_id == identity
        original = next(r for r in records if r['file'] == row['file'] and r['option_id'] == identity)
        for key, value in original.items():
            assert row[key] == value
    _, decision = gates(summary)
    assert decision == receipt['decision']
    api.audit.json_write(api.OUT/'H66_verification.json', dict(status='PASS', groups=len(checks), checks=checks,
        verified_voiced_frame_options=verified_frames, independent_anchor_qr_rho_whitening_grid_objective_bracket=True,
        independent_scalar_metrics_selection=True, inner_summary_membership=True, mask_count_invariant=True,
        protected_hashes=True, limitation='Independent QR certifies nuisance rho, whitening, objective/grid/local bracket; optimizer not independently rerun; gate code unchanged.'))
    print('PASS H66', len(checks), 'groups;', verified_frames, 'frame options')


if __name__ == '__main__':
    verify()
