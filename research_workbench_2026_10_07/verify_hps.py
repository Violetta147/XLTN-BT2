"""Direct DFT at needed FFT bins, independent interpolation/product/grid and scalar metrics."""
import json
import math
import numpy as np
import pandas as pd


def independent_refine(segment, fs, anchor, order):
    length = len(segment)
    nfft = 2**math.ceil(math.log2(16*length))
    lower = max(70., anchor*math.pow(2., -1/12))
    upper = min(400., anchor*math.pow(2., 1/12))
    grid = np.array(sorted(set([lower, upper, anchor]+[k/10 for k in range(math.ceil(lower*10), math.floor(upper*10)+1)])))
    indices = np.arange(length)
    window = .5-.5*np.cos(2*np.pi*indices/(length-1))
    centered = segment-np.mean(segment)
    weighted = centered*window
    if not np.any(weighted):
        return dict(f0=float(anchor), grid=grid, scores=np.zeros(len(grid)), boundary=False, silent=True)
    # Common normalizer does not change argmax, but floor does; obtain FFT max
    # independently with scipy FFT, then compute needed spectral samples with DFT.
    from scipy.fft import rfft
    scale = np.abs(rfft(weighted, nfft)).max()
    positions = grid[:, None]*np.arange(1, order+1)[None, :]*nfft/fs
    left = np.floor(positions).astype(int)
    needed = np.unique(np.r_[left.ravel(), (left+1).ravel()])
    magnitudes = {}
    for offset in range(0, len(needed), 64):
        bins = needed[offset:offset+64]
        dft = np.exp((-2j*np.pi/nfft)*bins[:, None]*indices[None, :])@weighted
        magnitudes.update(zip(bins, np.abs(dft)/scale))
    scores = []
    for row, bins in zip(positions, left):
        total = 0.
        for p, k in zip(row, bins):
            amplitude = magnitudes[k]*(1-(p-k))+magnitudes[k+1]*(p-k)
            total += math.log(max(float(amplitude), 1e-12))
        scores.append(total)
    best = max(range(len(grid)), key=lambda i:(scores[i], -grid[i]))
    return dict(f0=float(grid[best]), grid=grid, scores=np.array(scores), boundary=best in (0, len(grid)-1), silent=False)


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
    import hps_experiment as api
    from verify_srh import independent_item, independent_score
    from voicing_recovery import gates
    from threadpoolctl import threadpool_limits
    registry = api.check_registry()
    receipt = json.loads((api.OUT/'H63_train_experiment.json').read_text())
    for p, digest in receipt['artifacts'].items():
        assert api.audit.digest(api.REPO/p) == digest, p
    from pathlib import Path
    for p, digest in registry['external_protected'].items():
        assert api.audit.digest(Path(p)) == digest, p
    fixed = pd.read_csv(api.OUT/'H63_fixed.csv', float_precision='round_trip')
    old = pd.read_csv(api.OUT/'H47_nested_contours.csv', float_precision='round_trip')
    cases = pd.read_csv(api.OUT/'H63_changed_cases.csv', float_precision='round_trip')
    bounds = pd.read_csv(api.OUT/'H63_boundaries.csv', float_precision='round_trip')
    checks = []; verified_frames = 0
    with threadpool_limits(limits=1):
        for path in sorted(api.core.TRAIN.glob('*.wav')):
            item, fs, audio = independent_item(path, 'train')
            length, hop = round(fs*.025), round(fs*.01)
            saved = dict(np.load(api.OUT/f'H63_predictions_{path.stem}.npz'))
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
                        p = independent_refine(audio[i*hop:i*hop+length], fs, base[i], option['order'])
                        assert p['f0'] == f0[i], (path.name, option['id'], i, p['f0'], f0[i])
                        row = group.loc[i]
                        assert row.label == item['labels'][i] and row.time_s == item['times'][i]
                        assert row.baseline_hz == base[i] and row.hps_hz == f0[i]
                        assert np.isclose(row.score, max(p['scores']), atol=1e-9, rtol=1e-9)
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
            print('H63 verified', path.name, flush=True)
    records = fixed.to_dict('records'); names = sorted(fixed.file.unique()); selections = []
    inner = pd.read_csv(api.OUT/'H63_inner_traces.csv', float_precision='round_trip', keep_default_na=False)
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
    summary = pd.read_csv(api.OUT/'H63_metrics.csv', float_precision='round_trip')
    for _, row in summary.iterrows():
        identity = 'hard170' if row.model == 'accepted' else selection[row['file']] if row.split == 'nested' else selection['final']
        assert row.option_id == identity
        original = next(r for r in records if r['file'] == row['file'] and r['option_id'] == identity)
        for key, value in original.items():
            assert row[key] == value
    _, decision = gates(summary)
    assert decision == receipt['decision']
    api.audit.json_write(api.OUT/'H63_verification.json', dict(status='PASS', groups=len(checks), checks=checks,
        verified_voiced_frame_options=verified_frames, independent_dft_interpolation_argmax=True,
        independent_scalar_metrics_selection=True, inner_summary_membership=True, mask_count_invariant=True,
        protected_hashes=True, limitation='DFT samples independent; scipy FFT reused only for spectrum-wide normalization; gate code unchanged.'))
    print('PASS H63', len(checks), 'groups;', verified_frames, 'frame options')


if __name__ == '__main__':
    verify()
