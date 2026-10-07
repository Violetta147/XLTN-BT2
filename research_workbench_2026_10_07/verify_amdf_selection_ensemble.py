import json
from pathlib import Path

import numpy as np
import pandas as pd
import verify_amdf_loop
from verify_results import digest

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def main():
    verify_amdf_loop.verify('H45', 'praat7_filtered_v0.3')
    result = json.loads((HERE / 'results/H45_experiment.json').read_text())
    options = {o['id']: o for o in json.loads((HERE / 'H45_REGISTRY.json').read_text())['options']}
    members = [o['id'] for o in json.loads((HERE / 'H44_REGISTRY.json').read_text())['options']]
    member_metrics = pd.read_csv(HERE / 'results/H44_fixed_lofo.csv')
    raw = pd.read_csv(HERE / 'results/H44_raw_native_frames.csv', float_precision='round_trip')
    contours = pd.read_csv(HERE / 'results/H45_nested_contours.csv')
    metrics = pd.read_csv(HERE / 'results/H45_metrics.csv')
    fixed = pd.read_csv(HERE / 'results/H45_fixed_lofo.csv')
    traces = pd.read_csv(HERE / 'results/H45_inner_traces.csv')
    fits = json.loads((HERE / 'results/H45_fits.json').read_text())['fits']
    names = set(result['data_sha256'])
    recalculated = {}
    for fit in fits:
        held, identity = fit['held_file'], fit['option_id']
        option, proof = options[identity], fit['fitted']
        selected = []
        if option['method'] == 'ensemble':
            pool = set(fit['fit_files'])
            assert pool and pool <= names and proof['actual_fit_files'] == sorted(pool) and proof['requires_fit']
            ranked = []
            for member in members:
                data = member_metrics[(member_metrics.option_id == member) & member_metrics.file.isin(pool)]
                ref = member_metrics[(member_metrics.option_id == 'praat7_filtered_v0.3') & member_metrics.file.isin(pool)]
                assert set(data.file) == pool
                valid = bool(np.isfinite(data.average_mape).all() and data.macro_f1.mean() >= ref.macro_f1.mean() - .01
                             and data.recall_v.mean() >= ref.recall_v.mean() - .01 and data.false_voiced_sil.sum() <= ref.false_voiced_sil.sum() + 1)
                ranked.append((not valid, data.average_mape.max() if valid else np.inf, data.average_mape.mean() if valid else np.inf, member))
            ranked.sort()
            selected = [r[3] for r in ranked if not r[0]][:option['top_k']]
            assert [r[3] for r in proof['member_ranking']] == [r[3] for r in ranked]
        else:
            assert proof['actual_fit_files'] == [] and not proof['requires_fit']
            selected = ['praat7_filtered_v0.3' if option['method'] == 'control' else 'amdf_pitch_spectral_p170']
        assert selected == proof['selected_members'] and fit['classifier'] is None
        native = [raw[(raw.option_id == member) & (raw.file == held)] for member in selected]
        nt = native[0].time_s.to_numpy()
        assert all(np.array_equal(group.time_s, nt) for group in native)
        f0 = native[0].raw_f0_hz.to_numpy().copy()
        mask = (f0 >= 70) & (f0 <= 400)
        array = np.stack([group.raw_f0_hz.to_numpy()[mask] for group in native])
        f0[mask] = array[0] if len(selected) == 1 else np.prod(array, axis=0) ** (1 / len(selected))
        canonical = contours[(contours.file == held) & (contours.model == 'accepted')]
        times = canonical.time_s.to_numpy()
        from scipy.io import wavfile
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', wavfile.WavFileWarning)
            fs, pcm = wavfile.read(REPO / 'TinHieuHuanLuyen' / held)
        index = np.array([int(np.argmin(np.abs(nt - t))) for t in times])
        support = abs(nt[index] - times) <= .005 + 1 / fs
        pred = support & (f0[index] >= 70) & (f0[index] <= 400)
        valid_f0 = f0[index][pred]
        labels = canonical.label.to_numpy()
        gt = dict(line.split()[:2] for line in (REPO / 'research_3gt_2026_10_05/train_3gt' / held.replace('.wav', '.lab')).read_text().splitlines())
        calculated = dict(F0mean=valid_f0.mean(), F0std=valid_f0.std(ddof=0), F0num=len(valid_f0))
        for key in ('F0mean', 'F0std', 'F0num'):
            calculated[key + '_mape'] = 100 * abs(calculated[key] - float(gt[key])) / float(gt[key])
        calculated['average_mape'] = np.mean([calculated[key + '_mape'] for key in ('F0mean', 'F0std', 'F0num')])
        calculated.update(TP=int(((labels == 'v') & pred).sum()), FN=int(((labels == 'v') & ~pred).sum()),
                          FP=int(((labels == 'uv') & pred).sum()), TN=int(((labels == 'uv') & ~pred).sum()),
                          false_voiced_sil=int(((labels == 'sil') & pred).sum()))
        recalculated[(identity, tuple(sorted(fit['fit_files'])), held)] = calculated
    checks = 0

    def compare(row, pool, held):
        nonlocal checks
        fresh = recalculated[(row['option_id'], tuple(sorted(pool)), held)]
        for key, value in fresh.items():
            np.testing.assert_allclose(row[key], value, atol=1e-8, rtol=1e-9)
        checks += 1

    for row in traces.to_dict('records'):
        compare(row, row['fit_files'].split('|'), row['inner_held'])
    for row in fixed.to_dict('records'):
        compare(row, names - {row['file']}, row['file'])
    for row in metrics.to_dict('records'):
        compare(row, names if row['split'] == 'train' else names - {row['file']}, row['file'])
    nested = metrics[(metrics.model == 'candidate') & (metrics.split == 'nested')]
    assert result['goal_all_nested_files_le_2'] == bool((nested.average_mape <= 2).all())
    receipt = dict(family='H45', fits_replayed=len(fits), metric_rows_recomputed=checks,
                   aggregation_verification='product and kth-root; independent from log2 mean',
                   membership_fit_pool_only=True, new_native_calls=0, target_met=result['goal_all_nested_files_le_2'],
                   experiment_sha256=digest(HERE / 'results/H45_experiment.json'), verifier_sha256=digest(__file__))
    (HERE / 'results/H45_ensemble_verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
