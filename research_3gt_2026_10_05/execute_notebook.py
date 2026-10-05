import base64
import contextlib
import io
import json
import os
import sys
import traceback
from pathlib import Path

os.environ['MPLBACKEND'] = 'Agg'
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from core import HERE, ROOT, TRAIN, sha256


def run(filename):
    path = ROOT / 'improved-training-only' / filename
    book = json.loads(path.read_text(encoding='utf-8'))
    expected = pd.read_csv(HERE / 'results' / 'final_train_test_per_file.csv')
    scope = {'__name__': '__main__'}
    execution_count = 0
    for cell in book['cells']:
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(cell['source'])
        # Chỉ thay mount/đường dẫn trong bộ nhớ chạy local; source Colab không thay đổi.
        if 'from google.colab import drive' in source:
            source = source.replace('from google.colab import drive', '')
            source = source.replace("drive.mount('/content/drive')", '')
            source = '\n'.join("PROJECT_DIR = Path(" + repr(str(TRAIN.parent)) + ")"
                               if line.startswith('PROJECT_DIR = Path(') else line for line in source.splitlines())
            source = source.replace("TRAIN_STATS_DIR = PROJECT_DIR / 'TinHieuHuanLuyen-3groundtruth'",
                                    'TRAIN_STATS_DIR = Path(' + repr(str(HERE / 'train_3gt')) + ')')
            source = source.replace("TEST_STATS_DIR = PROJECT_DIR / 'TinHieuKiemThu-3groundtruth'",
                                    'TEST_STATS_DIR = Path(' + repr(str(HERE / 'test_3gt')) + ')')
        outputs = []
        def display_local(*objects, **kwargs):
            for obj in objects:
                data = {'text/plain': str(obj)}
                if isinstance(obj, pd.DataFrame):
                    data['text/html'] = obj.to_html(index=False)
                outputs.append({'output_type': 'display_data', 'metadata': {}, 'data': data})
        def show_local(*args, **kwargs):
            for number in plt.get_fignums():
                fig = plt.figure(number)
                stream = io.BytesIO()
                fig.savefig(stream, format='png', dpi=110, bbox_inches='tight')
                outputs.append({'output_type': 'display_data', 'metadata': {},
                                'data': {'image/png': base64.b64encode(stream.getvalue()).decode(), 'text/plain': 'Figure'}})
                plt.close(fig)
        plt.show = show_local
        execution_count += 1
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(compile(source, str(path) + ':cell' + str(execution_count), 'exec'), scope)
        scope['display'] = display_local
        # Cell mount import lại display, thay sau cell đầu cho các cell hiển thị tiếp theo.
        if stdout.getvalue():
            outputs.insert(0, {'output_type': 'stream', 'name': 'stdout', 'text': stdout.getvalue()})
        if stderr.getvalue():
            outputs.append({'output_type': 'stream', 'name': 'stderr', 'text': stderr.getvalue()})
        cell['execution_count'], cell['outputs'] = execution_count, outputs
        print(filename, 'cell', execution_count, 'OK', flush=True)
    for model in book['metadata']['bt2_models']:
        for split, collection in [('train', 'TRAIN_ROWS'), ('test', 'TEST_ROWS')]:
            actual = scope[collection][model].sort_values('file').reset_index(drop=True)
            reference = expected[(expected.model == model) & (expected.version == 'improved') & (expected.split == split)]
            reference = reference.sort_values('file').reset_index(drop=True)
            columns = ['F0mean', 'F0std', 'F0num', 'F0mean_mape', 'F0std_mape', 'F0num_mape', 'average_mape', 'macro_f1']
            assert actual.file.tolist() == reference.file.tolist()
            assert np.allclose(actual[columns], reference[columns], atol=1e-10, rtol=1e-10), (model, split)
    directory = ROOT / 'improved-training-only' / 'executed_local'
    directory.mkdir(exist_ok=True)
    destination = directory / filename
    book['metadata']['bt2_local_execution'] = {'data_root': str(TRAIN.parent), 'source_sha256': sha256(path),
                                             'all_cells_executed': True, 'numerical_parity': 'train/test absolute tolerance 1e-10',
                                             'note': 'Outputs chạy local; source giữ đường dẫn Colab'}
    destination.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding='utf-8')
    print('PASS', filename, '—', execution_count, 'code cells; all train/test metrics match 1e-10', flush=True)


if __name__ == '__main__':
    run(sys.argv[1])
