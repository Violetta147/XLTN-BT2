import json
import shutil
import sys
from pathlib import Path

from core import BASELINES, HERE, ROOT, TRAIN, TRAIN_GT, RESULTS, sha256
from events import record

BASELINES.mkdir(exist_ok=True)
TRAIN_GT.mkdir(exist_ok=True)
names = {'ACF.ipynb': 'BT2_ACF_best_energy_set.ipynb', 'AMDF.ipynb': 'BT2_AMDF_best_energy_set.ipynb',
         'GMM.ipynb': 'BT2_ACF_AMDF_GMM_best_energy_set.ipynb'}
for name, original in names.items():
    shutil.copy2(ROOT / 'turn-in-assignment' / original, BASELINES / name)
shutil.copy2(ROOT / 'turn-in-assignment - Copy' / 'BT2_AMDF_best_no_energy_set.ipynb', BASELINES / 'AMDF_no_energy.ipynb')
for path in (ROOT / '.validation-3gt').glob('*.lab'):
    shutil.copy2(path, TRAIN_GT / path.name)
manifest = []
for path in sorted(TRAIN.glob('*.wav')):
    local_original = ROOT / 'TinHieuHuanLuyen' / path.name
    assert sha256(path) == sha256(local_original)
    manifest.append({'file': path.name, 'wav_sha256': sha256(path),
                     'segments_sha256': sha256(path.with_suffix('.lab')),
                     'three_gt_sha256': sha256(TRAIN_GT / path.with_suffix('.lab').name)})
manifest.append({'baseline_notebooks': {name: sha256(BASELINES / name) for name in (*names, 'AMDF_no_energy.ipynb')},
                 'python': sys.version, 'python_executable': sys.executable, 'test_accessed': False})
(RESULTS / 'training_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
record('Lưu baseline, manifest SHA-256 và ba ground truth train', '4 WAV local khớp các bản đã dùng; snapshot 4 pipeline ACF/AMDF/GMM. Chưa mở test mới.', 'Giữ nguyên sáu notebook đã giao; mọi thí nghiệm có file kết quả riêng')
