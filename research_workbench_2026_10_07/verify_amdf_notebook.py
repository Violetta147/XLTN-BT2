import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

import verify_results
from verify_selection import summary

HERE = Path(__file__).resolve().parent


def main():
    verify_results.verify('H23')
    result = json.loads((HERE / 'results/H23_experiment.json').read_text(encoding='utf-8'))
    traces = pd.read_csv(HERE / 'results/H23_inner_traces.csv')
    for choice in result['selections']:
        pool = traces[traces.outer_held == choice['outer_held']]
        baseline = summary(pool[pool.option_id == 'amdf_f25_h10'])
        ranked = []
        for identity, part in pool.groupby('option_id'):
            measured = summary(part)
            eligible = bool(np.isfinite(part.average_mape).all()
                            and measured['macro_f1'] >= baseline['macro_f1'] - .01
                            and measured['recall_v'] >= baseline['recall_v'] - .01
                            and measured['false_voiced_sil'] <= baseline['false_voiced_sil'] + 1)
            ranked.append((not eligible, measured['average_mape'] if eligible else float('inf'), identity))
        assert min(ranked)[2] == choice['option']['id']
    fits = json.loads((HERE / 'results/H23_fits.json').read_text(encoding='utf-8'))['fits']
    names = set(result['data_sha256'])
    for fit in fits:
        assert set(fit['fit_files']) in (names, names - {fit['held_file']}) or len(fit['fit_files']) == 2
        assert fit['classifier'] is None
    book = json.loads((HERE / 'AMDF_LOCAL_TRAIN.ipynb').read_text(encoding='utf-8'))
    encoded = json.dumps([cell['source'] for cell in book['cells']], ensure_ascii=False).encode('utf-8')
    source_hash = hashlib.sha256(encoded).hexdigest()
    assert source_hash == book['metadata']['bt2_local_execution']['source_cells_sha256']
    code_cells = [cell for cell in book['cells'] if cell['cell_type'] == 'code']
    for cell in code_cells:
        compile(cell['source'], 'AMDF_LOCAL_TRAIN.ipynb', 'exec')
        assert cell['execution_count'] is not None
        assert not any(output['output_type'] == 'error' for output in cell['outputs'])
        assert 'drive.mount' not in cell['source'] and 'TEST_DIR' not in cell['source']
    assert not book['metadata']['bt2_local_execution']['source_rewritten']
    assert book['metadata']['bt2_local_execution']['all_code_cells_executed']
    detail = pd.read_csv(HERE / 'results/AMDF_notebook_per_file.csv')
    assert len(detail) == 32 and not detail.duplicated(['model', 'split', 'file']).any()
    saved = pd.read_csv(HERE / 'results/AMDF_notebook_summary.csv')
    for (model, split), part in detail.groupby(['model', 'split']):
        expected = saved[(saved.model == model) & (saved.split == split)].iloc[0]
        for metric, value in summary(part).items():
            assert np.isclose(expected[metric], value, atol=1e-8)
    manifest = json.loads((HERE / 'results/AMDF_notebook_figure_manifest.json').read_text(encoding='utf-8'))
    assert manifest['builder_sha256'] == verify_results.digest(HERE / 'build_amdf_notebook.py')
    for figure in manifest['figures']:
        assert figure['generator_sha256'] == verify_results.digest(HERE / figure['generator'])
        for source in figure['sources']:
            assert source['sha256'] == verify_results.digest(HERE / source['path'])
        png = (HERE / figure['png']).read_bytes()
        assert png[:8] == b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II', png[16:24])) > 200
        ET.parse(HERE / figure['svg'])
    receipt = {'notebook_code_cells': len(code_cells), 'exact_sources_hash_valid': True,
               'all_cells_executed_without_error': True, 'execution_method': 'exact Python cells with display adapter; not Jupyter kernel',
               'notebook_tables_recomputed': True, 'H23_selection_replayed': True,
               'notebook_figure_sources_verified': True, 'verifier_sha256': verify_results.digest(__file__)}
    (HERE / 'results/AMDF_notebook_verification.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
