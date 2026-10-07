import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import verify_results
from verify_selection import summary

HERE = Path(__file__).resolve().parent


def verify(family, baseline):
    verify_results.verify(family)
    result = json.loads((HERE / f'results/{family}_experiment.json').read_text())
    trace = pd.read_csv(HERE / f'results/{family}_inner_traces.csv')
    for selection in result['selections']:
        pool = trace[trace.outer_held == selection['outer_held']]
        base = summary(pool[pool.option_id == baseline])
        ranking = []
        for identity, table in pool.groupby('option_id'):
            new = summary(table)
            valid = (np.isfinite(table.average_mape).all()
                     and new['macro_f1'] >= base['macro_f1'] - .01
                     and new['recall_v'] >= base['recall_v'] - .01
                     and new['false_voiced_sil'] <= base['false_voiced_sil'] + 1)
            if family in ('H25','H26','H27','H28','H29'):
                ranking.append((not valid, float(table.average_mape.max()) if valid else float('inf'), new['average_mape'] if valid else float('inf'), identity))
            else:
                ranking.append((not valid, new['average_mape'] if valid else float('inf'), identity))
        assert min(ranking)[-1] == selection['option']['id']
    metrics = pd.read_csv(HERE / f'results/{family}_metrics.csv')
    s = {(model, split): summary(table) for (model, split), table in metrics.groupby(['model', 'split'])}
    before = metrics[(metrics.split == 'nested') & (metrics.model == 'accepted')].set_index('file')
    after = metrics[(metrics.split == 'nested') & (metrics.model == 'candidate')].set_index('file')
    base, new = s['accepted', 'nested'], s['candidate', 'nested']
    checks = {
        'train_mape_relative_10_percent': s['candidate', 'train']['average_mape'] <= .9*s['accepted', 'train']['average_mape'],
        'lofo_mape_relative_5_percent': new['average_mape'] <= .95*base['average_mape'],
        'lofo_f1_drop_at_most_01': new['macro_f1'] >= base['macro_f1']-.01,
        'lofo_recall_v_drop_at_most_01': new['recall_v'] >= base['recall_v']-.01,
        'lofo_sil_increase_at_most_1': new['false_voiced_sil'] <= base['false_voiced_sil']+1,
        'lofo_no_file_mape_worse_by_over_2pp': ((after.average_mape-before.average_mape)<=2).all(),
        'lofo_phone_f1_std_not_worse': after.loc['phone_F1.wav','F0std_mape']<=before.loc['phone_F1.wav','F0std_mape'],
        'selected_lofo_mape_relative_5_percent': s['candidate','lofo']['average_mape']<=.95*s['accepted','lofo']['average_mape']}
    checks = {k: bool(v) for k,v in checks.items()}
    assert checks == result['decision']['checks']
    assert all(checks.values()) == result['decision']['eligible']
    fits = json.loads((HERE / f'results/{family}_fits.json').read_text())['fits']
    for fit in fits:
        classifier = fit['classifier']
        if classifier is not None:
            assert classifier['fit_files'] == fit['fit_files']
            assert min(classifier['scale']) > 0
            assert all(np.isfinite(classifier[key]).all() for key in ('mean','scale','coefficient'))
            assert len(classifier['feature_names']) == len(classifier['coefficient'])
    extra = {}
    if family == 'H27':
        praat_fits = [fit for fit in fits if fit['option_id'].startswith('praat_')]
        assert praat_fits
        for fit in praat_fits:
            assert fit['fitted']['requires_fit'] is False
            assert fit['fitted']['actual_fit_files'] == []
            assert fit['classifier'] is None
        nested = metrics[(metrics.split == 'nested') & (metrics.model == 'candidate')]
        assert result['goal_all_nested_files_le_2'] == bool((nested.average_mape <= 2).all())
        assert metrics.projection_coverage.between(0, 1).all()
        assert any(path.endswith('amdf_dual_window.py') for path in result['code_sha256'])
        extra['praat_no_training_fit_verified'] = True
    if family == 'H28':
        native_fits = [fit for fit in fits if fit['option_id'].startswith('harvest_')]
        assert native_fits
        for fit in native_fits:
            assert fit['fitted']['requires_fit'] is False
            assert fit['fitted']['actual_fit_files'] == []
            assert fit['classifier'] is None
        provenance = json.loads((HERE / 'results/pyworld_035_compatibility.json').read_text())
        assert verify_results.digest(provenance['native_module']) == provenance['native_module_sha256']
        assert result['environment']['native_module_sha256'] == provenance['native_module_sha256']
        nested = metrics[(metrics.split == 'nested') & (metrics.model == 'candidate')]
        assert result['goal_all_nested_files_le_2'] == bool((nested.average_mape <= 2).all())
        assert metrics.projection_coverage.between(0, 1).all()
        extra['harvest_no_training_fit_and_native_hash_verified'] = True
    if family == 'H29':
        for fit in fits:
            expected = fit['fit_files'] if fit['fitted']['requires_fit'] else []
            assert fit['fitted']['actual_fit_files'] == expected
            assert fit['classifier'] is None
        fixed = pd.read_csv(HERE / 'results/H29_fixed_lofo.csv')
        prior = pd.read_csv(HERE / 'results/H28_fixed_lofo.csv')
        raw = fixed[fixed.option_id == 'harvest_raw'].set_index('file').sort_index()
        original = prior[prior.option_id == 'harvest_h10'].set_index('file').sort_index()
        columns = ['F0mean','F0std','F0num','average_mape','macro_f1','recall_v','false_voiced_sil']
        assert np.allclose(raw[columns], original[columns], atol=1e-8)
        nested = metrics[(metrics.split == 'nested') & (metrics.model == 'candidate')]
        assert result['goal_all_nested_files_le_2'] == bool((nested.average_mape <= 2).all())
        extra['raw_harvest_reproduced_and_gate_fit_pool_verified'] = True
    if family == 'H24':
        contours = pd.read_csv(HERE / 'results/H24_nested_contours.csv')
        for file, group in contours.groupby('file'):
            a = group[group.model=='accepted'].reset_index(drop=True)
            b = group[group.model=='candidate'].reset_index(drop=True)
            assert np.array_equal(a.pred_voiced,b.pred_voiced)
            assert np.array_equal(a.f0_hz.notna(),b.f0_hz.notna())
        extra['voicing_and_valid_f0_count_unchanged'] = True
        fixed = pd.read_csv(HERE / 'results/H24_fixed_lofo.csv')
        for file, group in fixed.groupby('file'):
            for metric in ('TP','FN','FP','TN','false_voiced_sil','F0num','projection_coverage'):
                assert group[metric].nunique()==1
        assert (fixed.projection_coverage==1).all()
        extra['exact_canonical_support_all_frames'] = True
    receipt = {'family': family, 'selection_replayed': True, 'fits_checked':len(fits),
               'gates_recomputed': checks, **extra, 'verifier_sha256':verify_results.digest(__file__)}
    (HERE / f'results/{family}_selection_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('family')
    parser.add_argument('baseline')
    args = parser.parse_args()
    verify(args.family,args.baseline)
