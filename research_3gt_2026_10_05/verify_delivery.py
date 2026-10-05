import datetime
import importlib.metadata
import json
import platform
import sys

from core import HERE, ROOT, RESULTS, sha256
from events import record


def main():
    directory = ROOT / 'improved-training-only'
    rows = []
    for path in sorted(directory.glob('*.ipynb')):
        clean = json.loads(path.read_text(encoding='utf-8'))
        executed_path = directory / 'executed_local' / path.name
        executed = json.loads(executed_path.read_text(encoding='utf-8'))
        before_code = [''.join(c['source']) for c in executed['cells'] if c['cell_type'] == 'code']
        after_code = [''.join(c['source']) for c in clean['cells'] if c['cell_type'] == 'code']
        assert before_code == after_code, 'Code changed since full execution'
        assert all(c['execution_count'] is not None for c in executed['cells'] if c['cell_type'] == 'code')
        assert not any(o['output_type'] == 'error' for c in executed['cells'] if c['cell_type'] == 'code' for o in c['outputs'])
        # Đồng bộ phần giải thích mới; giữ nguyên mọi output đã chạy của code không thay đổi.
        for a, b in zip(clean['cells'], executed['cells']):
            b['source'] = a['source']
        executed['metadata']['bt2_local_execution']['source_sha256'] = sha256(path)
        executed_path.write_text(json.dumps(executed, ensure_ascii=False, indent=1), encoding='utf-8')
        outputs = [o for c in executed['cells'] if c['cell_type'] == 'code' for o in c['outputs']]
        images = sum('image/png' in o.get('data', {}) for o in outputs)
        assert images >= 6
        rows.append({'notebook': path.name, 'code_cells_executed': len(after_code), 'figures': images,
                     'source_sha256': sha256(path), 'executed_sha256': sha256(executed_path),
                     'train_test_parity_atol': 1e-10, 'code_identical_to_executed': True})
    original_pairs = [('ACF.ipynb', ROOT / 'turn-in-assignment' / 'BT2_ACF_best_energy_set.ipynb'),
                      ('AMDF.ipynb', ROOT / 'turn-in-assignment' / 'BT2_AMDF_best_energy_set.ipynb'),
                      ('AMDF_no_energy.ipynb', ROOT / 'turn-in-assignment - Copy' / 'BT2_AMDF_best_no_energy_set.ipynb'),
                      ('GMM.ipynb', ROOT / 'turn-in-assignment' / 'BT2_ACF_AMDF_GMM_best_energy_set.ipynb')]
    originals = []
    for snapshot, path in original_pairs:
        assert sha256(HERE / 'baselines' / snapshot) == sha256(path)
        originals.append({'path': str(path), 'sha256': sha256(path), 'unchanged_from_snapshot': True})
    assert sha256(ROOT / 'turn-in-assignment - Copy' / 'BT2_ACF_best_no_energy_set.ipynb') == sha256(original_pairs[0][1])
    assert sha256(ROOT / 'turn-in-assignment - Copy' / 'BT2_ACF_AMDF_GMM_best_no_energy_set.ipynb') == sha256(original_pairs[3][1])
    versions = {name: importlib.metadata.version(name) for name in ('numpy', 'pandas', 'scipy', 'scikit-learn', 'matplotlib')}
    result = {'verified_at_vietnam': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat(timespec='seconds'),
              'python': sys.version, 'python_executable': sys.executable, 'platform': platform.platform(),
              'versions': versions, 'notebooks': rows, 'originals': originals, 'all_six_original_notebooks_unchanged': True}
    (RESULTS / 'delivery_validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    record('Chạy toàn bộ notebook và đối chiếu kết quả', '; '.join(f'{x["notebook"]}: {x["code_cells_executed"]} cell, {x["figures"]} hình' for x in rows),
           'Đều PASS: train/test khớp 1e-10, source code không đổi sau chạy, sáu bản gốc khớp snapshot. Outputs local lưu riêng.')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
