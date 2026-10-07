import base64
import contextlib
import hashlib
import io
import json
import sys
import traceback
from pathlib import Path

import matplotlib.figure
import pandas as pd
from PIL import Image

HERE = Path(__file__).resolve().parent


def main():
    path = HERE / 'AMDF_TARGET_2PCT.ipynb'
    book = json.loads(path.read_text(encoding='utf-8'))
    source = json.dumps([cell['source'] for cell in book['cells']], ensure_ascii=False).encode('utf-8')
    source_hash = hashlib.sha256(source).hexdigest()
    namespace = {'__name__': '__main__'}
    execution_count = 0
    failed = False
    for index, cell in enumerate(book['cells']):
        if cell['cell_type'] != 'code':
            continue
        execution_count += 1
        outputs = []

        def display_local(*objects):
            for obj in objects:
                data = {'text/plain': str(obj)}
                if isinstance(obj, pd.DataFrame):
                    data['text/html'] = obj.to_html(index=False)
                elif isinstance(obj, (matplotlib.figure.Figure, Image.Image)):
                    buffer = io.BytesIO()
                    if isinstance(obj, Image.Image):
                        obj.save(buffer, format='PNG')
                    else:
                        obj.savefig(buffer, format='png', dpi=110, bbox_inches='tight')
                    data['image/png'] = base64.b64encode(buffer.getvalue()).decode('ascii')
                outputs.append({'output_type': 'display_data', 'metadata': {}, 'data': data})

        namespace['display'] = display_local
        stdout, stderr = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec(compile(cell['source'], f'{path}:cell{index}', 'exec'), namespace)
        except Exception as error:
            failed = True
            outputs.append({'output_type': 'error', 'ename': type(error).__name__,
                            'evalue': str(error), 'traceback': traceback.format_exc().splitlines()})
        if stdout.getvalue():
            outputs.insert(0, {'output_type': 'stream', 'name': 'stdout', 'text': stdout.getvalue()})
        if stderr.getvalue():
            outputs.append({'output_type': 'stream', 'name': 'stderr', 'text': stderr.getvalue()})
        cell['execution_count'], cell['outputs'] = execution_count, outputs
        print(f'AMDF notebook cell{index}: {"ERROR" if failed else "OK"}', flush=True)
        if failed:
            break
    assert hashlib.sha256(json.dumps([cell['source'] for cell in book['cells']], ensure_ascii=False).encode('utf-8')).hexdigest() == source_hash
    book['metadata']['bt2_local_execution'] = {
        'source_cells_sha256': source_hash, 'source_rewritten': False,
        'execution_method': 'Python exec of each exact code cell; headless display adapter; not Jupyter kernel',
        'python_executable': sys.executable, 'all_code_cells_executed': not failed,
        'test_wav_read': False, 'data_root': str(HERE.parent)}
    path.write_text(json.dumps(book, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    if failed:
        raise RuntimeError(f'Notebook error preserved in {path}')
    print('PASS exact source execution:', execution_count, 'code cells', flush=True)


if __name__ == '__main__':
    main()
