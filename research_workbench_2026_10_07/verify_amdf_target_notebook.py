import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    notebook = HERE / 'AMDF_TARGET_2PCT.ipynb'
    book = json.loads(notebook.read_text(encoding='utf-8'))
    source = json.dumps([cell['source'] for cell in book['cells']], ensure_ascii=False).encode('utf-8')
    meta = book['metadata']['bt2_local_execution']
    assert meta['source_cells_sha256'] == hashlib.sha256(source).hexdigest()
    assert meta['all_code_cells_executed'] and not meta['source_rewritten'] and not meta['test_wav_read']
    code = [cell for cell in book['cells'] if cell['cell_type'] == 'code']
    assert len(code) == 4 and [cell['execution_count'] for cell in code] == [1, 2, 3, 4]
    for cell in code:
        assert cell['outputs'] and not any(x['output_type'] == 'error' for x in cell['outputs'])
    assert any('image/png' in x.get('data', {}) for cell in code for x in cell['outputs'])
    table = pd.read_csv(HERE / 'results/AMDF_target_notebook_per_file.csv')
    assert len(table) == 24 and not table.duplicated(['method', 'file']).any()
    metrics = ['F0mean', 'F0std', 'F0num', 'average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil']
    for row in table.to_dict('records'):
        saved = pd.read_csv(HERE / f'results/{row["family"]}_fixed_lofo.csv')
        ref = saved[(saved.option_id == row['option_id']) & (saved.file == row['file'])].iloc[0]
        assert np.allclose([row[key] for key in metrics], ref[metrics].astype(float), atol=1e-8)
        assert np.isclose(row['average_mape'], sum(row[k] for k in ('F0mean_mape', 'F0std_mape', 'F0num_mape')) / 3)
    status = pd.read_csv(HERE / 'results/AMDF_target_notebook_status.csv').set_index('family')
    for family in ('H24', 'H25', 'H26'):
        measured = pd.read_csv(HERE / f'results/{family}_metrics.csv')
        values = measured[(measured.split == 'nested') & (measured.model == 'candidate')].average_mape
        assert np.isclose(status.loc[family, 'mean'], values.mean())
        assert np.isclose(status.loc[family, 'worst'], values.max())
        assert status.loc[family, 'all_files_le_2'] == bool((values <= 2).all())
    manifest = json.loads((HERE / 'results/AMDF_target_notebook_figure_manifest.json').read_text(encoding='utf-8'))
    for figure in manifest['figures']:
        assert digest(HERE / figure['generator']) == figure['generator_sha256']
        for source in figure['sources']:
            assert digest(HERE / source['path']) == source['sha256']
        png = (HERE / figure['png']).read_bytes()
        assert png[:8] == b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II', png[16:24])) > 200
        ET.parse(HERE / figure['svg'])
    receipt = {'notebook_sha256': digest(notebook), 'source_cells_sha256': meta['source_cells_sha256'],
               'exact_source_cells_executed': 4, 'measurement_rows_recomputed_and_matched': 24,
               'status_and_figures_verified': True, 'execution_method': meta['execution_method'],
               'verifier_sha256': digest(__file__), 'all_files_target_met': bool(status.all_files_le_2.any())}
    (HERE / 'results/AMDF_target_notebook_verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
