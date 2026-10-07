import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import verify_results

HERE = Path(__file__).resolve().parent


def summary(table):
    return {name: float(table[name].mean()) for name in ('average_mape', 'macro_f1', 'recall_v')} | {
        'false_voiced_sil': int(table.false_voiced_sil.sum())}


def verify(family):
    verify_results.verify(family)
    result = json.loads((HERE / f'results/{family}_experiment.json').read_text(encoding='utf-8'))
    registry = json.loads((HERE / f'{family}_REGISTRY.json').read_text(encoding='utf-8'))
    options = {x['id']: x for x in registry['options']}
    trace = pd.read_csv(HERE / f'results/{family}_inner_traces.csv')
    for selection in result['selections']:
        pool = trace[trace.outer_held == selection['outer_held']]
        base = summary(pool[pool.option_id == 'raw_0_0_f25_h10'])
        ranked = []
        for option_id, table in pool.groupby('option_id'):
            s = summary(table)
            valid = bool(np.isfinite(table.average_mape).all()
                         and s['macro_f1'] >= base['macro_f1'] - .01
                         and s['recall_v'] >= base['recall_v'] - .01
                         and s['false_voiced_sil'] <= base['false_voiced_sil'] + 1)
            ranked.append((not valid, s['average_mape'] if valid else float('inf'), option_id))
        assert min(ranked)[2] == selection['option']['id'], selection
    fits = json.loads((HERE / f'results/{family}_fits.json').read_text(encoding='utf-8'))['fits']
    for entry in fits:
        classifier = entry['classifier']
        if classifier is not None:
            assert classifier['fit_files'] == entry['fit_files']
            dimension = 3 if options[entry['option_id']].get('use_zcr') else 2
            for key in ('coefficient', 'mean', 'scale', 'feature_names'):
                assert len(classifier[key]) == dimension
            assert all(np.isfinite(classifier[key]).all() for key in ('coefficient', 'mean', 'scale'))
            assert min(classifier['scale']) > 0
    metrics = pd.read_csv(HERE / f'results/{family}_metrics.csv')
    s = {(model, split): summary(table) for (model, split), table in metrics.groupby(['model', 'split'])}
    before = metrics[(metrics.split == 'nested') & (metrics.model == 'accepted')].set_index('file')
    after = metrics[(metrics.split == 'nested') & (metrics.model == 'candidate')].set_index('file')
    base, new = s['accepted', 'nested'], s['candidate', 'nested']
    checks = {
        'train_mape_relative_10_percent': s['candidate', 'train']['average_mape'] <= .9 * s['accepted', 'train']['average_mape'],
        'lofo_mape_relative_5_percent': new['average_mape'] <= .95 * base['average_mape'],
        'lofo_f1_drop_at_most_01': new['macro_f1'] >= base['macro_f1'] - .01,
        'lofo_recall_v_drop_at_most_01': new['recall_v'] >= base['recall_v'] - .01,
        'lofo_sil_increase_at_most_1': new['false_voiced_sil'] <= base['false_voiced_sil'] + 1,
        'lofo_no_file_mape_worse_by_over_2pp': ((after.average_mape - before.average_mape) <= 2).all(),
        'lofo_phone_f1_std_not_worse': after.loc['phone_F1.wav', 'F0std_mape'] <= before.loc['phone_F1.wav', 'F0std_mape'],
        'selected_lofo_mape_relative_5_percent': s['candidate', 'lofo']['average_mape'] <= .95 * s['accepted', 'lofo']['average_mape']}
    checks = {key: bool(value) for key, value in checks.items()}
    assert checks == result['decision']['checks']
    assert all(checks.values()) == result['decision']['eligible']
    receipt = {'family': family, 'selection_replayed_from_all_inner_traces': True,
               'fits_checked': len(fits), 'classifier_dimensions_and_fit_ids_valid': True,
               'all_decision_gates_recomputed_from_csv': checks,
               'verifier_sha256': verify_results.digest(__file__),
               'command': f'python research_workbench_2026_10_07/verify_selection.py {family}'}
    (HERE / f'results/{family}_selection_verification.json').write_text(
        json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('family', choices=['H21', 'H22'])
    verify(parser.parse_args().family)
