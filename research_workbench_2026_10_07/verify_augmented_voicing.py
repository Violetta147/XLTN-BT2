import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import augmented_voicing as engine
import verify_amdf_loop

HERE = Path(__file__).resolve().parent


def main():
    verify_amdf_loop.verify('H47', 'praat7_filtered_v0.3')
    result = json.loads((HERE / 'results/H47_experiment.json').read_text())
    options = {o['id']: o for o in json.loads((HERE / 'H47_REGISTRY.json').read_text())['options']}
    items = {item['file']: item for item in engine.core.load_training()}
    raw = engine.evidence.RAW
    fits = json.loads((HERE / 'results/H47_fits.json').read_text())['fits']
    designs = {}
    manifest = json.loads((HERE / 'results/H46_augmentation_manifest.json').read_text())
    feature_hashes = {}
    for name, item in items.items():
        stem = Path(name).stem
        cases = [(stem + '__clean', engine.core.TRAIN / name)] + [
            (c['case_id'], HERE / c['path']) for c in manifest['cases'] if c['origin_file'] == name]
        for identity, path in cases:
            design_path = HERE / f'results/H47_design_{identity}.npz'
            data = dict(np.load(design_path))
            fs, audio = engine.core.load_audio(path)
            expected = engine.design(audio, fs, data['times'], data['gate'])
            np.testing.assert_allclose(expected, data['x'], atol=1e-12)
            assert np.array_equal(data['labels'], engine.labels_at(item, data['times']))
            assert np.array_equal(data['valid'], (data['gate'] >= 70) & (data['gate'] <= 400) & np.isin(data['labels'], ['v','uv','sil']))
            designs[identity] = data
            feature_hashes[design_path.name] = engine.audit.digest(design_path)
    rebuilt = {}
    unique_models = set()
    for entry in fits:
        name, option = entry['held_file'], options[entry['option_id']]
        classifier = entry['classifier']
        native = raw[(raw.file == name) & (raw.option_id == entry['fitted']['selected_members'][0])]
        times, frequency = native.time_s.to_numpy(), native.raw_f0_hz.to_numpy()
        pred = (frequency >= 70) & (frequency <= 400)
        if classifier is not None:
            pool = sorted(entry['fit_files'])
            expected_ids = {Path(n).stem + '__clean' for n in pool}
            if option['augmented']:
                expected_ids |= {c['case_id'] for c in manifest['cases'] if c['origin_file'] in pool}
            assert {c['case_id'] for c in classifier['fit_cases']} == expected_ids
            assert {c['origin_file'] for c in classifier['fit_cases']} == set(pool)
            if name not in pool:
                assert all(c['origin_file'] != name for c in classifier['fit_cases'])
            assert classifier['augmented'] == option['augmented'] and classifier['C'] == 1.
            key = (tuple(pool), option['augmented'])
            if key not in unique_models:
                count = sum(c['frames'] for c in classifier['fit_cases'])
                xs, ys, ws = [], [], []
                for case in classifier['fit_cases']:
                    data = designs[case['case_id']]
                    valid = data['valid']
                    assert valid.sum() == case['frames']
                    xs.append(data['x'][valid])
                    ys.append((data['labels'][valid] == 'v').astype(int))
                    ws.append(np.repeat(count / (len(pool) * (4 if option['augmented'] else 1) * valid.sum()), valid.sum()))
                x,y,w = np.vstack(xs),np.concatenate(ys),np.concatenate(ws)
                scale = StandardScaler().fit(x, sample_weight=w)
                model = LogisticRegression(C=1.,max_iter=1000).fit(scale.transform(x),y,sample_weight=w)
                np.testing.assert_allclose(scale.mean_, classifier['mean'], atol=1e-12)
                np.testing.assert_allclose(scale.scale_, classifier['scale'], atol=1e-12)
                np.testing.assert_allclose(model.coef_[0], classifier['coefficient'], atol=1e-10)
                np.testing.assert_allclose(model.intercept_[0], classifier['intercept'], atol=1e-10)
                unique_models.add(key)
            held_x = designs[Path(name).stem + '__clean']['x']
            logit = np.sum((held_x-np.array(classifier['mean'])) / np.array(classifier['scale']) * np.array(classifier['coefficient']), axis=1) + classifier['intercept']
            pred &= expit(logit) >= option['threshold']
        else:
            assert entry['fitted']['actual_fit_files'] == []
        canon = items[name]
        index = np.array([np.argmin(abs(times-t)) for t in canon['times']])
        support = abs(times[index]-canon['times']) <= .005+1/canon['fs']
        projected = pred[index] & support
        f0 = np.where(projected, frequency[index], np.nan)
        rebuilt[(option['id'],tuple(sorted(entry['fit_files'])),name)] = engine.core.score_file(canon,projected,f0)
    count = 0
    for filename in ('inner_traces','fixed_lofo','metrics'):
        for row in pd.read_csv(HERE / f'results/H47_{filename}.csv').to_dict('records'):
            name = row.get('inner_held',row.get('file'))
            pool = row['fit_files'].split('|') if filename == 'inner_traces' else (list(items) if row.get('split') == 'train' else [n for n in items if n != name])
            actual = rebuilt[(row['option_id'],tuple(sorted(pool)),name)]
            for metric in ('F0mean','F0std','F0num','F0mean_mape','F0std_mape','F0num_mape','average_mape','macro_f1','recall_v','recall_uv','balanced_accuracy','false_voiced_sil'):
                np.testing.assert_allclose(row[metric], actual[metric], atol=1e-8, rtol=1e-9)
            count += 1
    nested = pd.read_csv(HERE / 'results/H47_metrics.csv').query("split == 'nested' and model == 'candidate'")
    assert result['goal_all_nested_files_lt_2'] == bool((nested.average_mape < 2).all())
    receipt = dict(family='H47', fit_records_replayed=len(fits), independently_refitted_models=len(unique_models),
                  feature_groups_recomputed=len(designs), metric_rows_recomputed=count, origin_variant_exclusion=True,
                  target_strict_lt_2=result['goal_all_nested_files_lt_2'], feature_hashes=feature_hashes,
                  experiment_sha256=engine.audit.digest(HERE / 'results/H47_experiment.json'), verifier_sha256=engine.audit.digest(__file__))
    (HERE / 'results/H47_voicing_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k != 'feature_hashes'},indent=2))


if __name__ == '__main__':
    main()
