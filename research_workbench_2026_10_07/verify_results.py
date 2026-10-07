import argparse
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(family):
    result = json.loads((HERE / f'results/{family}_experiment.json').read_text(encoding='utf-8'))
    registry = json.loads((HERE / f'{family}_REGISTRY.json').read_text(encoding='utf-8'))
    identities = {x['id'] for x in registry['options']}
    assert result['registry_sha256'] == digest(HERE / f'{family}_REGISTRY.json')
    for p, value in result['code_sha256'].items():
        assert digest(REPO / p) == value, p
    for p, value in result['data_sha256'].items():
        assert digest(REPO / 'TinHieuHuanLuyen' / p) == value, p
    names = set(result['data_sha256'])
    traces = pd.read_csv(HERE / f'results/{family}_inner_traces.csv')
    assert len(traces) == len(identities) * 16
    assert not traces.duplicated(['outer_held', 'option_id', 'inner_held']).any()
    assert set(traces.option_id) == identities
    for row in traces.itertuples(index=False):
        fitted = set(row.fit_files.split('|'))
        expected = names - {row.inner_held} - ({row.outer_held} if row.outer_held != 'final' else set())
        assert fitted == expected
    for selection in result['selections']:
        assert selection['option']['id'] in identities
        expected = names - ({selection['outer_held']} if selection['outer_held'] != 'final' else set())
        assert set(selection['selection_files']) == expected
    metrics = pd.read_csv(HERE / f'results/{family}_metrics.csv')
    contours = pd.read_csv(HERE / f'results/{family}_nested_contours.csv')
    assert len(metrics) == 24 and not metrics.duplicated(['split', 'model', 'file']).any()
    for (file, model), group in contours.groupby(['file', 'model']):
        saved = metrics[(metrics.split == 'nested') & (metrics.file == file) & (metrics.model == model)].iloc[0]
        valid = group.f0_hz.dropna().to_numpy()
        statistics = {'F0mean': valid.mean(), 'F0std': valid.std(), 'F0num': len(valid)}
        gt = {}
        for line in (REPO / 'research_3gt_2026_10_05/train_3gt' / file.replace('.wav', '.lab')).read_text(encoding='utf-8').splitlines():
            key, value = line.split()[:2]
            if key in statistics:
                gt[key] = float(value)
        errors = []
        for key, value in statistics.items():
            assert np.isclose(saved[key], value, atol=1e-8)
            errors.append(100 * abs(value - gt[key]) / gt[key])
        assert np.isclose(saved.average_mape, np.mean(errors), atol=1e-8)
        counts = {'TP': ((group.label == 'v') & group.pred_voiced).sum(),
                  'FN': ((group.label == 'v') & ~group.pred_voiced).sum(),
                  'FP': ((group.label == 'uv') & group.pred_voiced).sum(),
                  'TN': ((group.label == 'uv') & ~group.pred_voiced).sum(),
                  'false_voiced_sil': ((group.label == 'sil') & group.pred_voiced).sum()}
        assert all(saved[k] == v for k, v in counts.items())
        tp, tn, fp, fn = [counts[k] for k in ('TP', 'TN', 'FP', 'FN')]
        f1 = (2 * tp / max(2 * tp + fp + fn, 1) + 2 * tn / max(2 * tn + fp + fn, 1)) / 2
        assert np.isclose(saved.macro_f1, f1, atol=1e-10)
    manifest = json.loads((HERE / f'results/{family}_figure_manifest.json').read_text(encoding='utf-8'))
    for figure in manifest['figures']:
        assert figure['generator_sha256'] == digest(HERE / figure['generator'])
        for source in figure['sources']:
            assert source['sha256'] == digest(HERE / source['path'])
        png = (HERE / figure['png']).read_bytes()
        assert png[:8] == b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II', png[16:24])) > 200
        ET.parse(HERE / figure['svg'])
    checks = {'family': family, 'registry_options': len(identities), 'inner_trace_rows': len(traces),
              'outer_contour_stats_and_labels_recomputed': True, 'fit_selection_exclusions_verified': True,
              'hashes_and_figures_verified': True, 'raw_baseline_reproduced_by_runner': result['baseline_reproduced'],
              'eligible': result['decision']['eligible'], 'champion_promoted': result['decision']['champion_promoted']}
    (HERE / f'results/{family}_verification.json').write_text(json.dumps(checks, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('family', choices=['H18', 'H19'])
    verify(parser.parse_args().family)
