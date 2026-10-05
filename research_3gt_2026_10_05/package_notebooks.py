import ast
import json
import textwrap
from pathlib import Path

from core import HERE, ROOT, RESULTS, sha256
from events import record


def nodes_from_notebook(name, names):
    nodes = []
    book = json.loads((HERE / 'baselines' / name).read_text(encoding='utf-8'))
    for cell in book['cells']:
        if cell['cell_type'] == 'code':
            nodes.extend(node for node in ast.parse(''.join(cell['source'])).body
                         if isinstance(node, ast.FunctionDef) and node.name in names)
    assert {node.name for node in nodes} == set(names)
    return nodes


def standalone_source():
    source = '''import math
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal import correlate
from sklearn.mixture import GaussianMixture
EPS = 1e-12
F0_MIN, F0_MAX, HOP_MS = 70., 400., 10
HIST_BINS, HIST_SMOOTH_WINDOW, HIST_W = 20, 5, 1.
NEAR_ZERO_MEAN_ABS = 1e-8
FIT_CACHE = {}
'''
    groups = {'ACF': ('ACF.ipynb', ['normalized_acf', 'detect_pitch_acf', 'lag_to_f0',
                                  'gaussian_intersection', 'histogram_threshold', 'class_histogram_threshold']),
              'AMDF': ('AMDF.ipynb', ['lag_search_range', 'normalized_amdf', 'deepest_local_dip',
                                    'f0_from_lag', 'gaussian_threshold', 'histogram_threshold', 'two_mode_histogram_threshold']),
              'GMM': ('GMM.ipynb', ['normal_pdf', 'fit_gmm_threshold'])}
    for group, (filename, names) in groups.items():
        body = '\n\n'.join(ast.unparse(node) for node in nodes_from_notebook(filename, names))
        returned = 'return {' + ', '.join(repr(name) + ': ' + name for name in names) + '}'
        source += '\ndef build_' + group.lower() + '():\n' + textwrap.indent(body + '\n' + returned, '    ') + '\n'
        source += group + ' = build_' + group.lower() + '()\n'
    source += '\ndef init_functions():\n    return\n'
    tree = ast.parse((HERE / 'core.py').read_text(encoding='utf-8'))
    names = {'read_stats', 'read_segments', 'load_audio', 'refine_lag', 'classification', 'threshold_options',
             'fit_pitch_threshold', 'fit_energy', 'fit', 'voiced_runs', 'infer', 'score_file', 'evaluate', 'lofo', 'summarize'}
    source += '\n\n' + '\n\n'.join(ast.unparse(node) for node in tree.body
                                      if isinstance(node, ast.FunctionDef) and node.name in names)
    original = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'frame_features')
    cache_if = next(node for node in original.body if isinstance(node, ast.If) and ast.unparse(node.test) == 'cache.exists()')
    algorithm_loop = cache_if.orelse[0]
    features = '''def signal_features(path, frame_ms=25):
    path = Path(path)
    fs, original = load_audio(path)
    frame_len, hop_len = round(fs * frame_ms / 1000), round(fs * .010)
    frames = np.lib.stride_tricks.sliding_window_view(original, frame_len)[::hop_len]
    times = (np.arange(len(frames)) * hop_len + frame_len / 2) / fs
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    relative_rms = rms / max(np.quantile(rms, .95), EPS)
    arrays = {'times': times, 'rms': rms, 'relative_rms': relative_rms}
'''
    features += textwrap.indent(ast.unparse(algorithm_loop), '    ')
    features += "\n    return {'file': path.name, 'fs': fs, 'duration_s': len(original) / fs, 'frame_ms': frame_ms, 'preprocess': 'raw', **arrays}\n"
    source += '\n\n' + features
    ast.parse(source)
    return source


def cell(kind, source):
    obj = {'cell_type': kind, 'metadata': {}, 'source': source.splitlines(keepends=True)}
    if kind == 'code':
        obj.update(execution_count=None, outputs=[])
    return obj


def main():
    frozen = json.loads((RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))
    selection = json.loads((RESULTS / 'selection_summary.json').read_text(encoding='utf-8'))
    shared = standalone_source()
    (HERE / 'standalone_pipeline.py').write_text(shared, encoding='utf-8')
    helpers = (HERE / 'notebook_helpers.py').read_text(encoding='utf-8')
    specs = [('BT2_ACF_improved_train_only.ipynb', ['ACF'], 'MyDrive'),
             ('BT2_AMDF_improved_with_energy_train_only.ipynb', ['AMDF_energy'], 'My Drive'),
             ('BT2_AMDF_improved_without_energy_train_only.ipynb', ['AMDF_no_energy'], 'My Drive'),
             ('BT2_ACF_AMDF_GMM_improved_train_only.ipynb', ['GMM_ACF', 'GMM_AMDF'], 'My Drive')]
    local_dir = ROOT / 'improved-training-only'
    committed_dir = HERE / 'deliverables'
    local_dir.mkdir(exist_ok=True)
    committed_dir.mkdir(exist_ok=True)
    hashes = {}
    for filename, models, alias in specs:
        configs = {model: frozen['models'][model]['config'] for model in models}
        reference = {model: {key: selection[model][key] for key in ('train', 'lofo', 'nested_lofo')} for model in models}
        cells = [cell('markdown', f'''# BT2: {' / '.join(models)} — cải tiến chọn bằng TRAIN

## 1. Bạn sẽ chạy gì?
Chạy **Runtime → Run all** trên Colab. Notebook tự học ngưỡng từ bốn file train, in bảng train,
kiểm tra giữ riêng từng file train, rồi áp dụng cùng cấu hình lên bốn file test.
Các notebook gốc vẫn được giữ để so sánh. Đây là phiên bản cải tiến sau điều tra ngày 05/10/2026.

**Cấu hình đã chốt lúc {frozen['frozen_at_vietnam']} bằng train.** Test không tham gia chọn cải tiến.
Kết quả test baseline đã được xem trong phiên trước, nên không gọi test là dữ liệu chưa từng xem.

## 2. Vì sao F0std của bản cũ cao?
F0 là số lần dây thanh rung trong một giây. Một chu kỳ dài T giây thì F0 = 1/T.
ACF có các đỉnh tại T, 2T, 3T; AMDF có các đáy tương ứng. Đỉnh mạnh nhất có thể là 3T.
Ở một khung `phone_F1`, T khoảng 4,6 ms nhưng bản cũ chọn 13,9 ms: F0 xuống khoảng 72 Hz thay vì 217 Hz.
Vài điểm lệch xa làm độ lệch chuẩn tăng mạnh, dù trung bình vẫn gần đúng.
Nhận nhầm im lặng thành hữu thanh cũng làm tăng F0std và F0num.

## 3. Dữ liệu và cách chấm
Hai thư mục cũ có WAV và LAB theo thời gian với nhãn `v`, `uv`, `sil`.
Hai thư mục `*-3groundtruth` có LAB chứa **F0mean, F0std, F0num của cả file**.
Không có F0 chuẩn cho từng khung. Không dùng ba thống kê chuẩn để sửa trực tiếp giá trị dự đoán.

- MAPE từng đại lượng = 100 × |dự đoán − chuẩn| / |chuẩn|.
- Average MAPE của file = trung bình ba MAPE.
- TỔNG CỘNG của mỗi tập = trung bình Average MAPE của bốn file.
- **FINAL SCORE = 100 − TỔNG CỘNG MAPE TEST**; điểm thang 10 = FINAL SCORE / 10, làm tròn một chữ số.

F0std dùng độ lệch chuẩn của toàn bộ F0 hữu hạn (`ddof=0`). F0num đếm toàn bộ F0 hữu hạn,
kể cả dự đoán nhầm ở UV/SIL; không lọc bằng nhãn thật để làm đẹp điểm.
''')]
        cells.append(cell('code', f'''from google.colab import drive
drive.mount('/content/drive')
from pathlib import Path
import matplotlib.pyplot as plt
from IPython.display import display

PROJECT_DIR = Path('/content/drive/{alias}/Seventh Semester/Spoken Language Processing/BT2')
# Colab có thể hiển thị cùng Drive dưới tên MyDrive thay vì My Drive.
if not PROJECT_DIR.exists():
    drive_alias = Path(str(PROJECT_DIR).replace('/My Drive/', '/MyDrive/'))
    if drive_alias.exists():
        PROJECT_DIR = drive_alias
TRAIN_DIR = PROJECT_DIR / 'TinHieuHuanLuyen'
TEST_DIR = PROJECT_DIR / 'TinHieuKiemThu'
TRAIN_STATS_DIR = PROJECT_DIR / 'TinHieuHuanLuyen-3groundtruth'
TEST_STATS_DIR = PROJECT_DIR / 'TinHieuKiemThu-3groundtruth'
SHOW_DETAILED_TEST_PLOTS = True
MODEL_CONFIGS = {repr(configs)}
REFERENCE_TRAIN_VALIDATION = {repr(reference)}
assert TRAIN_DIR.exists() and TRAIN_STATS_DIR.exists(), 'Thiếu thư mục train hoặc train-3groundtruth'
print('Thư mục dữ liệu:', PROJECT_DIR)
'''))
        cells.append(cell('markdown', '''## 4. Tính đặc trưng từ WAV
Khung dài 20 hoặc 25 ms theo cấu hình của từng thuật toán; bước trượt 10 ms; giữ nguyên tần số lấy mẫu.
Trừ trung bình khung, tính ACF chuẩn hóa hoặc AMDF chuẩn hóa, tìm cực trị trong dải 70–400 Hz,
nội suy parabol để có độ trễ không nguyên. Giữ tối đa 12 ứng viên mạnh nhất mỗi khung.
RMS tương đối = RMS khung / percentile 95 của RMS trong chính file WAV; không dùng nhãn hay 3GT.

Các hàm dưới đây tự chứa toàn bộ thuật toán, không cần tải thêm file Python.
'''))
        # Tách các hàm thành cell theo phần để đọc dễ hơn, vẫn giữ nguyên thứ tự phụ thuộc.
        source_tree = ast.parse(shared)
        parts, current = [], []
        for node in source_tree.body:
            current.append(ast.unparse(node))
            if isinstance(node, ast.FunctionDef) and node.name in ('build_amdf', 'read_segments', 'signal_features'):
                parts.append('\n\n'.join(current)); current = []
        if current:
            parts.append('\n\n'.join(current))
        cells.extend(cell('code', part) for part in parts)
        cells.append(cell('markdown', '''## 5. Học ngưỡng và chọn đường F0
ACF score lớn hơn ngưỡng → hữu thanh; AMDF score nhỏ hơn ngưỡng → hữu thanh.
`original` tính ba ngưỡng: giao Gaussian V/UV, hai mode histogram gộp, giao hai histogram theo nhãn;
chọn theo balanced accuracy trên train. `hist_classes` dùng giao histogram V/UV.
`gmm` fit hai Gaussian trên score train, dùng giao mật độ có trọng số; không đổi thành histogram.
Histogram giao của **hai lớp V/UV** cần nhãn lớp. Histogram hai mode và GMM tự tìm nhóm,
nhưng phân biệt V/UV để chọn mô hình và cổng V/SIL vẫn sử dụng nhãn train cũ.

Nếu `energy=True`, học ngưỡng RMS từ V/SIL của train bằng balanced accuracy trung bình theo file.
Một khung chỉ được chấp nhận khi vượt cả ngưỡng chu kỳ và ngưỡng năng lượng.

### Chọn ứng viên
- `path`: trong từng đoạn hữu thanh dự đoán liên tục, tìm đường có tổng chi phí thấp nhất bằng quy hoạch động.
  Chi phí khung = (score mạnh nhất − score ứng viên) + `octave_cost × log2(400/F0)`.
  Chi phí chuyển khung = `jump_cost × |log2(F0 mới / F0 trước)|`.
  Với AMDF, strength = 1 − AMDF score. Những bước nhảy F0 lớn bị phạt.
- `near`: chọn F0 cao nhất trong các ứng viên có strength cách ứng viên mạnh nhất không quá `margin`.
- `median=3`: lọc trung vị ba khung ở bên trong đoạn hữu thanh dự đoán; không nối qua khoảng vô thanh.

Đây là cách chọn đường đơn giản lấy ý tưởng từ các bộ phân tích pitch cổ điển,
không phải triển khai đầy đủ Praat. Không gán F0mean/F0std chuẩn vào đầu ra.
'''))
        cells.append(cell('code', helpers))
        cells.append(cell('code', '''train_paths = sorted(TRAIN_DIR.glob('*.wav'))
assert len(train_paths) == 4, 'Bài yêu cầu đúng bốn file train'
train_by_frame = {}
for frame_ms in sorted({config['frame_ms'] for config in MODEL_CONFIGS.values()}):
    train_by_frame[frame_ms] = [attach_truth(signal_features(path, frame_ms), path.with_suffix('.lab'),
                                            TRAIN_STATS_DIR / path.with_suffix('.lab').name) for path in train_paths]
FITTED, TRAIN_ROWS, LOFO_ROWS = {}, {}, {}
for name, config in MODEL_CONFIGS.items():
    items = train_by_frame[config['frame_ms']]
    FITTED[name] = fit(items, config)
    print(name, '— cấu hình:', config, '— ngưỡng học từ TRAIN:', FITTED[name])
    threshold_plot(items, config, FITTED[name], name)
    curve_examples(items, config)
    TRAIN_ROWS[name] = evaluate(items, config, FITTED[name])
    show_results(TRAIN_ROWS[name], 'KẾT QUẢ TẬP TRAIN — ' + name)
'''))
        cells.append(cell('markdown', '''## 6. Train cao/thấp chưa đủ: kiểm tra giữ riêng file
Train ở trên là chẩn đoán trên dữ liệu đã học ngưỡng. LOFO (leave one file out) giữ riêng một file,
học ngưỡng từ ba file còn lại rồi chấm file giữ riêng; lặp đủ bốn lần.
LOFO trong notebook giữ cố định cấu hình đã chọn, nên vẫn có thiên lệch do chọn cấu hình.
Nghiên cứu local đã làm **nested LOFO**: ba file vòng ngoài chọn cấu hình bằng LOFO vòng trong,
sau đó chấm file vòng ngoài chưa dùng để chọn. Bảng tham chiếu phía dưới là kết quả đó,
không phải phép kiểm tra nested đang chạy lại trong notebook này.
Các hướng thuật toán và tập cấu hình được xây dựng sau khi phân tích cả bốn file train;
nested LOFO kiểm tra việc chọn tham số trong tập cấu hình đó, chưa đánh giá độc lập toàn bộ quá trình nghiên cứu.
Chỉ có bốn file train nên validation vẫn biến động mạnh; cần thêm dữ liệu để khẳng định tổng quát.
'''))
        cells.append(cell('code', '''validation_summary = []
for name, config in MODEL_CONFIGS.items():
    LOFO_ROWS[name] = lofo(train_by_frame[config['frame_ms']], config)
    show_results(LOFO_ROWS[name], 'VALIDATION GIỮ RIÊNG TỪNG FILE TRAIN — ' + name)
    ref = REFERENCE_TRAIN_VALIDATION[name]
    validation_summary.append({'Model': name, 'Train MAPE local (%)': ref['train']['average_mape'],
                               'LOFO MAPE local (%)': ref['lofo']['average_mape'],
                               'Nested LOFO MAPE local (%)': ref['nested_lofo']['average_mape'],
                               'Nested macro F1 V/UV': ref['nested_lofo']['macro_f1']})
display(pd.DataFrame(validation_summary).round(4))
'''))
        cells.append(cell('markdown', '''## 7. Áp dụng lên TEST độc lập với chọn cải tiến
Đọc WAV test và dự đoán **trước** khi đọc nhãn/thống kê test. Ngưỡng giữ nguyên từ train.
Sau đó mới đọc LAB để chấm và vẽ. Không fit GMM, không chọn ngưỡng, không sửa tham số bằng test.
Kết quả có thể kém bản cũ trên một số file test dù train và validation tốt hơn; vẫn báo cáo đúng.
'''))
        cells.append(cell('code', '''assert TEST_DIR.exists() and TEST_STATS_DIR.exists(), 'Thiếu thư mục test hoặc test-3groundtruth'
test_paths = sorted(TEST_DIR.glob('*.wav'))
assert len(test_paths) == 4, 'Bài yêu cầu đúng bốn file test'
test_by_frame = {frame_ms: [signal_features(path, frame_ms) for path in test_paths]
                 for frame_ms in sorted({config['frame_ms'] for config in MODEL_CONFIGS.values()})}
TEST_ROWS, TEST_PREDICTIONS, TEST_LABELED = {}, {}, {}
for name, config in MODEL_CONFIGS.items():
    predictions = [infer(item, config, FITTED[name]) for item in test_by_frame[config['frame_ms']]]
    # Nhãn và thống kê test chỉ được gắn sau khi đã dự đoán xong.
    items = [attach_truth(item, TEST_DIR / Path(item['file']).with_suffix('.lab'),
                          TEST_STATS_DIR / Path(item['file']).with_suffix('.lab'))
             for item in test_by_frame[config['frame_ms']]]
    TEST_ROWS[name] = pd.DataFrame([score_file(item, *prediction) for item, prediction in zip(items, predictions)])
    TEST_PREDICTIONS[name], TEST_LABELED[name] = predictions, items
    show_results(TEST_ROWS[name], 'KẾT QUẢ TẬP TEST — ' + name)
    average_mape = float(TEST_ROWS[name].average_mape.mean())
    final_score = 100 - average_mape
    print(f'FINAL SCORE = 100 − {average_mape:.2f} = {final_score:.2f}%')
    print(f'Điểm thang 10 (1 chữ số thập phân): {final_score / 10:.1f}')
    if SHOW_DETAILED_TEST_PLOTS:
        for item in items:
            detailed_plot(item, config, FITTED[name], TEST_DIR / item['file'], name)
'''))
        cells.append(cell('markdown', '''## 8. Đọc kết quả và điền bảng của thầy
Lấy bảng **KẾT QUẢ TẬP TRAIN** và **KẾT QUẢ TẬP TEST**, gồm bốn dòng file và dòng TỔNG CỘNG.
Notebook GMM in riêng hai thuật toán ACF và AMDF để so sánh.
Macro F1/recall V/recall UV chỉ chấm khung có nhãn V/UV; lỗi nhận SIL là V được báo riêng.
Các đường GT mean ± std trên đồ thị là thống kê của file, không phải đường F0 chuẩn theo thời gian.

Muốn giữ test độc lập, không đổi cấu hình theo bảng test rồi dùng lại test để tuyên bố cải thiện.

Tham khảo: [Praat: chọn phương pháp pitch](https://www.fon.hum.uva.nl/praat/manual/how_to_choose_a_pitch_analysis_method.html),
[Praat: các ứng viên và chi phí chọn đường](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_filtered_autocorrelation.html).
'''))
        book = {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                'language_info': {'name': 'python', 'version': '3.11'}, 'bt2_frozen': frozen['frozen_at_vietnam'],
                'bt2_models': models}, 'nbformat': 4, 'nbformat_minor': 4}
        for directory in (local_dir, committed_dir):
            (directory / filename).write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding='utf-8')
        hashes[filename] = sha256(local_dir / filename)
    (RESULTS / 'notebook_source_manifest.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    record('Đóng gói notebook Colab tự chứa thuật toán đã chốt', '4 notebook mới cho 5 pipeline; giữ nguyên sáu bản gốc, đường dẫn /content/drive và SHOW_DETAILED_TEST_PLOTS=True.',
           'Chưa coi notebook đã kiểm chứng cho tới khi chạy toàn bộ cell local và đối chiếu số liệu.')
    print(json.dumps(hashes, indent=2))


if __name__ == '__main__':
    main()
