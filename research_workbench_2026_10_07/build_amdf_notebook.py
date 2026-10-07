import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def main():
    cells = []

    def add(kind, source):
        cell = {'cell_type': kind, 'metadata': {}, 'source': source.strip() + '\n'}
        if kind == 'code':
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)

    add('markdown', '''# AMDF local: trước/sau và thí nghiệm độ dài khung

AMDF (average magnitude difference function) đo mức khác nhau giữa tín hiệu và bản dịch theo độ trễ. Đáy thấp gợi ý chu kỳ lặp; F0 = tần số lấy mẫu / độ trễ. F0 là tần số cơ bản, đơn vị Hz.

Notebook này tính lại AMDF thực trên bốn WAV train local. Có hai nhánh: không cổng năng lượng và có cổng năng lượng. So sánh baseline với bản đã sửa từ ngày05/10, rồi chạy vòng mới H23 cho frame20/25/40ms. Không đọc test, không mount Drive. Các cải thiện cũ và thí nghiệm mới được ghi riêng.

Nhãn V/UV/SIL là hữu thanh/vô thanh/khoảng lặng. LAB còn có mean/std/count F0 cả file; chúng không phải cao độ chuẩn theo từng thời điểm.''')
    add('code', f'''from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd

REPO = Path({str(REPO)!r})
WORKBENCH = REPO / 'research_workbench_2026_10_07'
assert (REPO / 'TinHieuHuanLuyen').is_dir()
sys.path.insert(0, str(WORKBENCH))
import amdf_frames as experiment
core, audit = experiment.core, experiment.audit
plt = audit.plt
print('WAV train:', core.TRAIN)
print('LAB thống kê:', core.TRAIN_GT)
print('Notebook chỉ sử dụng train local.')''')
    add('markdown', '''## 1. Đọc dữ liệu và đối chiếu cấu hình

Ngưỡng pitch quyết định dip AMDF có đủ thấp để coi khung là hữu thanh. Cổng năng lượng còn yêu cầu relative RMS lớn hơn ngưỡng: RMS của khung chia phân vị95% RMS trong chính file.

Baseline chọn đáy mạnh nhất riêng từng khung. Bản cải tiến giữ nhiều đáy làm ứng viên và chọn một đường F0 với phạt bước nhảy, để giảm việc nhảy giữa chu kỳ và bội chu kỳ. Nhánh không energy còn đổi phương pháp học ngưỡng; không quy mọi cải thiện của nhánh đó cho riêng chọn đường.''')
    add('code', '''items = core.load_training()
frozen = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))
history = json.loads((core.RESULTS / 'selection_summary.json').read_text(encoding='utf-8'))
models = {}
for family in ('AMDF_no_energy', 'AMDF_energy'):
    models[family + '_baseline'] = history[family]['baseline']['config']
    models[family + '_improved'] = frozen['models'][family]['config']
display(pd.DataFrame([{'model': name, **config} for name, config in models.items()]).fillna('không áp dụng'))
display(pd.DataFrame([{'file': item['file'], 'fs': item['fs'], 'frames': len(item['times']), **item['stats']} for item in items]))''')
    add('markdown', '''## 2. Tính lại kết quả trước/sau

Train dùng cả bốn file để học ngưỡng rồi chấm chính các file đó. LOFO (leave one file out) giữ một file để chấm, học ngưỡng bằng ba file còn lại và lặp đủ bốn lần. LOFO ở đây giữ cố định các cấu hình đã chọn trước đó; vẫn có ảnh hưởng của việc nghiên cứu nhiều lần trên cùng dữ liệu.

Average MAPE là trung bình ba lỗi phần trăm mean/std/count trong mỗi file, rồi trung bình bốn file. Macro F1 và recall chỉ chấm V/UV; số SIL dự đoán hữu thanh được báo riêng. Không gộp SIL vào FP V/UV.''')
    add('code', '''all_rows, summaries = [], []
saved_train = pd.read_csv(core.RESULTS / 'final_train_test_per_file.csv')
for name, config in models.items():
    family, version = name.rsplit('_', 1)
    for split in ('train', 'lofo'):
        rows = core.evaluate(items, config) if split == 'train' else core.lofo(items, config)
        summary = core.summarize(rows)
        reference = history[family]['baseline']['full_train' if split == 'train' else 'lofo'] if version == 'baseline' else history[family][split]
        for metric in ('average_mape', 'F0std_mape', 'macro_f1', 'recall_v', 'false_voiced_sil'):
            assert np.isclose(summary[metric], reference[metric], atol=1e-8), (name, split, metric)
        if split == 'train':
            reference_rows = saved_train[(saved_train.model == family) & (saved_train.version == version) & (saved_train.split == 'train')].sort_values('file')
            columns = ['F0mean', 'F0std', 'F0num', 'average_mape', 'macro_f1', 'false_voiced_sil']
            assert np.allclose(rows.sort_values('file')[columns], reference_rows[columns], atol=1e-8)
        summaries.append({'model': name, 'split': split, **summary})
        all_rows.extend({'model': name, 'split': split, **row} for row in rows.to_dict('records'))
summary_table = pd.DataFrame(summaries)
detail_table = pd.DataFrame(all_rows)
display(summary_table[['model', 'split', 'average_mape', 'F0std_mape', 'macro_f1', 'recall_v', 'recall_uv', 'balanced_accuracy', 'false_voiced_sil', 'F0num']].round(6))
display(detail_table[['model', 'split', 'file', 'average_mape', 'F0std_mape', 'macro_f1', 'false_voiced_sil']].round(6))
summary_table.to_csv(WORKBENCH / 'results/AMDF_notebook_summary.csv', index=False)
detail_table.to_csv(WORKBENCH / 'results/AMDF_notebook_per_file.csv', index=False)
print('PASS: tất cả số liệu AMDF trước/sau khớp kết quả đã lưu trong1e-8.')''')
    add('code', '''fig, axes = plt.subplots(1, 2, figsize=(12, 4))
for ax, split in zip(axes, ('train', 'lofo')):
    table = summary_table[summary_table.split == split]
    for family in ('AMDF_no_energy', 'AMDF_energy'):
        before = table[table.model == family + '_baseline'].iloc[0]
        after = table[table.model == family + '_improved'].iloc[0]
        ax.plot(['baseline', 'improved'], [before.average_mape, after.average_mape], 'o-', label=family)
    ax.set(title=split + ' — fixed configurations', ylabel='Mean file-stat AvgMAPE (%)')
    ax.legend()
source = WORKBENCH / 'results/AMDF_notebook_summary.csv'
audit.save_figure('AMDF_before_after', fig, [source], 'AMDF trước/sau, tính lại trên train local; LOFO giữ cố định cấu hình.', 'Cấu hình đã chọn trên dữ liệu này trước đó; không phải nested mới hoặc pitch error từng khung.')
artifact = dict(audit.ARTIFACTS[-1])
artifact.update(generator='execute_amdf_notebook.py', generator_sha256=audit.digest(WORKBENCH / 'execute_amdf_notebook.py'), command='python research_workbench_2026_10_07/execute_amdf_notebook.py')
audit.json_write(WORKBENCH / 'results/AMDF_notebook_figure_manifest.json', {'figures': [artifact], 'builder_sha256': audit.digest(WORKBENCH / 'build_amdf_notebook.py')})
audit.ARTIFACTS.clear()
from PIL import Image
display(Image.open(WORKBENCH / 'figures/AMDF_before_after.png'))''')
    add('markdown', '''## 3. Xem một đường AMDF thực

Normalized AMDF chia tổng sai khác tuyệt đối cho tổng biên độ tuyệt đối của hai đoạn chồng lấn. Trong mã này mỗi lag dùng số mẫu chồng lấn tương ứng; không mặc định công thức giống mọi bài AMDF khác.

Ví dụ chọn khung V nội bộ ở giữa danh sách khung của phone_F1, không chọn theo lỗi nhỏ nhất. Đáy đánh dấu là ứng viên riêng khung. Path có thể chọn một đáy khác khi xét cả chuỗi; chưa có reference F0 từng khung để xác minh đáy nào đúng.''')
    add('code', '''item = next(x for x in items if x['file'] == 'phone_F1.wav')
fs, audio = core.load_audio(core.TRAIN / item['file'])
indices = np.flatnonzero((item['labels'] == 'v') & ~item['boundary'])
index = int(indices[len(indices) // 2])
length, hop = round(fs * .025), round(fs * .010)
frame = audio[index * hop:index * hop + length]
score, lag_integer, lag_refined, lag_grid, curve = core.AMDF['deepest_local_dip'](frame, fs)
print('File/tâm khung:', item['file'], item['times'][index], 's')
print('NAMDF dip:', score, 'lag:', lag_refined, 'candidate F0:', fs / lag_refined, 'Hz')
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(np.arange(length) * 1000 / fs, frame)
axes[0].set(xlabel='Time within frame (ms)', ylabel='Raw amplitude')
axes[1].plot(lag_grid * 1000 / fs, curve)
axes[1].axvline(lag_refined * 1000 / fs, ls='--', color='red', label='Deepest local dip')
axes[1].set(xlabel='Lag (ms)', ylabel='Normalized AMDF')
axes[1].legend()
fig.tight_layout()
display(fig)
plt.close(fig)''')
    add('markdown', '''## 4. H23: chọn độ dài khung riêng cho AMDF

Vòng mới chỉ mở frame20/25/40ms, giữ hop10ms và mọi thành phần khác của AMDF có energy đã sửa. Registry và tiêu chí đã commit trước chạy. File vòng ngoài bị loại khỏi cả chọn cấu hình và học ngưỡng; inner LOFO chỉ dùng ba file khác.

Chấm trên lưới thời điểm25/10 chung để count không đổi thước đo. Bảng ghi native count và coverage riêng. Những điểm ngoài hỗ trợ là bỏ dự đoán; không nội suy xuyên UV hay sửa count cho khớp GT.

Cell sau chỉ chạy H23 nếu chưa có kết quả; khi chạy lại notebook, nó xác minh kết quả và source hash hiện có thay vì ghi đè thí nghiệm đã lưu.''')
    add('code', '''result_path = WORKBENCH / 'results/H23_experiment.json'
if not result_path.exists():
    experiment.run('H23')
else:
    print('H23 đã có kết quả; đọc và xác minh source, không ghi đè.')
import verify_results
verify_results.verify('H23')
result = json.loads(result_path.read_text(encoding='utf-8'))
display(pd.DataFrame([{'model': model, 'split': split, **values} for model, splits in result['summaries'].items() for split, values in splits.items()])[['model', 'split', 'average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil']].round(6))
display(pd.DataFrame([{'outer_held': choice['outer_held'], **choice['option']} for choice in result['selections']]))
display(pd.read_csv(WORKBENCH / 'results/H23_fixed_frame_lofo.csv')[['option_id', 'file', 'average_mape', 'F0std_mape', 'macro_f1', 'recall_v', 'projection_coverage', 'native_frames', 'native_f0_count']].round(6))
print('Gate:', result['decision'])
display(Image.open(WORKBENCH / 'figures/H23_nested.png'))''')
    add('markdown', '''## 5. Đọc kết luận đúng phạm vi

Có cải thiện AMDF so baseline cũ không đồng nghĩa mọi cấu hình thử thêm sẽ cải thiện tiếp. Train, fixed LOFO và nested selection trả lời các câu hỏi khác nhau; không thay điểm nested xấu bằng điểm selected LOFO đẹp.

Bốn file đã xem nhiều lần không đủ tách ảnh hưởng giới tính, người nói, thiết bị và nội dung nói. Nếu H23 không đạt, giữ cải tiến AMDF đã có, lưu kết quả thất bại và phân tích trước chọn cơ chế tiếp theo. Không tuyên bố mọi F0 đúng chỉ vì mean/std/count gần LAB.

Tất cả code cells được chạy nguyên source bởi execute_amdf_notebook.py; chỉ bộ hiển thị bảng/hình được thay cho chế độ headless. Đây không phải lần chạy bằng Jupyter kernel. Source không được thay đường dẫn trong bộ nhớ; notebook chạy lại trên môi trường local có các thư viện đã dùng.''')
    for cell in cells:
        if cell['cell_type'] == 'code':
            compile(cell['source'], 'AMDF_LOCAL_TRAIN.ipynb', 'exec')
    book = {'nbformat': 4, 'nbformat_minor': 4, 'metadata': {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python', 'version': '3.13.11'},
        'bt2_models': ['AMDF_no_energy', 'AMDF_energy'], 'train_only': True}, 'cells': cells}
    destination = HERE / 'AMDF_LOCAL_TRAIN.ipynb'
    assert not destination.exists(), 'Do not overwrite an existing notebook'
    destination.write_text(json.dumps(book, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('Created', destination)


if __name__ == '__main__':
    main()
