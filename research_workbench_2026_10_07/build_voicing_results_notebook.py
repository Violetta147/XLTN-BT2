import contextlib
import io
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def markdown(text):
    return dict(cell_type='markdown',metadata={},source=text.splitlines(keepends=True))


def code(text):
    return dict(cell_type='code',metadata={},source=text.splitlines(keepends=True),execution_count=None,outputs=[])


def main():
    path=HERE/'H51_RESULTS_LOCAL.ipynb'
    assert not path.exists(),'Preserve existing notebook'
    cells=[markdown('''# H51: đọc ma trận hữu thanh và kết quả F0

Notebook này đọc dữ liệu đã kiểm tra; không tự chạy lại 2.793 lượt học. Để tái lập toàn bộ thí nghiệm, dùng các lệnh trong `H51_RUNBOOK.md`. Các notebook gốc và file đã nộp giữ nguyên.

`Center` là cách gán nhãn chuẩn của khung bằng nhãn LAB tại điểm giữa cửa sổ. Nó không phải thuật toán nhận hữu thanh khi chạy trên file mới. Logistic/SVM/kNN/RF học nhãn V so với UV/SIL trong file train. GMM phân cụm không đọc LAB khi học hoặc gán nghĩa cụm; bước chọn pipeline qua validation vẫn dùng nhãn và ba thống kê chuẩn.

Năm nhóm: P=độ tuần hoàn; E=năng lượng; Z=ZCR; S=tỷ lệ phổ tần số cao; M=13 MFCC. Ma trận gồm 31 tổ hợp × 5 mô hình, seed 11/29/47. Điều kiện khôi phục và pitch dùng chung. Chỉ có bốn file train; seed không tạo thêm người nói.
'''),code(r'''from pathlib import Path
import hashlib
import json
import pandas as pd

cwd = Path.cwd()
candidates = [cwd, cwd / 'research_workbench_2026_10_07', cwd / 'XLTN-BT2' / 'research_workbench_2026_10_07']
workbench = next((p for p in candidates if (p / 'results/H51_external_verification.json').is_file()), None)
assert workbench is not None, 'Mở notebook từ folder workbench, repo XLTN-BT2 hoặc workspace XLTN local'
repo = workbench.parent
results = workbench / 'results'
for phase in ('train', 'external'):
    receipt = json.loads((results / f'H51_{phase}_verification.json').read_text(encoding='utf-8'))
    experiment_path = results / f'H51_{phase}_experiment.json'
    assert receipt['passed']
    assert hashlib.sha256(experiment_path.read_bytes()).hexdigest() == receipt['experiment_sha256']
    experiment = json.loads(experiment_path.read_text(encoding='utf-8'))
    for relative, digest in experiment['artifacts'].items():
        assert hashlib.sha256((repo / relative).read_bytes()).hexdigest() == digest, relative
freeze = json.loads((results / 'H51_FROZEN_SELECTION.json').read_text(encoding='utf-8'))
print('Verified train/external evidence. Final recipe:', freeze['recipe']['id'])
print('Grouped outer 4 folds / inner 3 folds; no random frame split; exploratory after repeated train use.')
'''),markdown('''## Mục tiêu và kết quả kiểm định chéo

Mục tiêu là **mỗi file Average MAPE <2%**. MAPE là trung bình ba lỗi tương đối mean/std/count. Tập train đã được nghiên cứu nhiều vòng; test và KEELE cũng có lịch sử được xem. Không coi các kết quả này là đánh giá trên dữ liệu hoàn toàn mới.
'''),code(r'''metrics = pd.read_csv(results / 'H51_metrics.csv')
print(metrics[(metrics['split'] == 'nested') & (metrics['model'] == 'candidate')][['seed', 'file', 'option_id', 'average_mape', 'macro_f1', 'recall_v']].to_string(index=False))
print('\nFixed final recipe on 4 train + 4 descriptive test files:')
print(pd.read_csv(results / 'H51_all8_target.csv').to_string(index=False))
'''),markdown('''## Ma trận và seed

Ba seed thực sự đổi phép học của RF/GMM. Logistic/SVM/kNN cho kết quả xác định nên các seed chỉ lặp cùng kết quả. Độ lệch chuẩn qua seed không phải mức bất định về toàn bộ người nói.

![Ma trận MAPE và F1](figures/H51_matrix.png)
'''),code(r'''summary = pd.read_csv(results / 'H51_seed_summary.csv')
full = ['logistic_PEZSM', 'svm_PEZSM', 'knn_PEZSM', 'rf_PEZSM', 'gmm_PEZSM', 'hard170']
print(summary[summary['recipe_id'].isin(full)].to_string(index=False))
print('\nFull matrix rows:', len(summary), '; non-control recipes:', len(summary) - 1)
'''),markdown('''## Ablation, tương tác và permutation

Leave-one-block-out bỏ một nhóm khỏi mô hình dùng toàn bộ đặc trưng. Tương tác dùng f(A+B)−f(A)−f(B)+f(control), là phép so sánh hiệu ứng cộng, không chứng minh nhân quả. Permutation đảo đầu vào của classifier, giữ nguyên điều kiện khôi phục và pitch.
'''),code(r'''removed = pd.read_csv(results / 'H51_leave_one_block_out.csv')
print(removed.groupby(['method', 'removed_block'])[['delta_mape', 'delta_f1']].mean().to_string())
permuted = pd.read_csv(results / 'H51_permutation.csv')
print('\nPermutation groups:', len(permuted))
print(permuted.groupby(['recipe_id', 'block'])[['delta_average_mape', 'delta_macro_f1']].mean().to_string())
'''),markdown('''## Lỗi cần phân biệt

Một khung có nhãn V đúng chưa xác nhận F0 ước lượng của nó đúng. Khi thêm một cao độ xa mean cũ, std có thể tăng mạnh. F0num chuẩn và số khung tâm V cũng khác nhau; chưa biết protocol tạo ba thống kê của thầy.
'''),code(r'''print(pd.read_csv(results / 'H51_selected_recovery_cases.csv').to_string(index=False))
print('\nConditional count tradeoff, not a lower bound for all models:')
print(pd.read_csv(results / 'H51_label_count_tradeoff.csv').to_string(index=False))
print('\nSee H51_INTERPRETATION.md for variance decomposition and limits.')
'''),markdown('''## Robustness và chuyển dữ liệu

Noise kế thừa nhãn và thống kê của file sạch là mục tiêu tiềm ẩn, không có F0 chuẩn mới sau thêm nhiễu. Phone↔studio chỉ có hai file mỗi điều kiện và bị trộn với khác biệt người nói. KEELE có reference từng khung nhưng cửa sổ và độ trễ khác pipeline; đây là kiểm tra chuyển dữ liệu để chẩn đoán, không đủ kết luận lỗi chỉ do BT2 ít dữ liệu.
'''),code(r'''noise = pd.read_csv(results / 'H51_robustness.csv')
print(noise.groupby(['condition', 'recipe_id'])[['average_mape', 'macro_f1', 'recall_v']].mean().to_string())
transfer = pd.read_csv(results / 'H51_keele_pooled.csv')
print('\nKEELE pooled per seed, keeping GPE/VDE/FFE/RPA together:')
print(transfer[['recipe_id', 'seed', 'gpe20_pct', 'vde_pct', 'ffe20_pct', 'rpa50_pct', 'file_mean_average_mape']].to_string(index=False))
'''),markdown('''## Đồ thị định trước cho bốn file

Logistic dùng toàn bộ đặc trưng, seed 11. Xanh lá=V, cam=UV, xanh nhạt=SIL theo LAB. Điểm F0 là ước lượng, không phải ground truth.

![phone_F1](figures/H51_qualitative_phone_F1.png)
![phone_M1](figures/H51_qualitative_phone_M1.png)
![studio_F1](figures/H51_qualitative_studio_F1.png)
![studio_M1](figures/H51_qualitative_studio_M1.png)

Đọc `H51_REPORT.md`, `H51_INTERPRETATION.md`, `EXPERIMENT_COVERAGE.md` để xem đầy đủ các cell, kết quả không đạt và hướng chưa thử. Không thay nhãn, tham số hoặc chọn seed từ notebook đọc kết quả này.
''')]
    for number,cell in enumerate(cells):cell['id']=f'h51-{number:02d}'
    scope={};executed=0
    previous=Path.cwd()
    import os
    os.chdir(HERE)
    try:
        for cell in cells:
            if cell['cell_type']!='code':continue
            source=''.join(cell['source']);compiled=compile(source,str(path),'exec');stream=io.StringIO()
            with contextlib.redirect_stdout(stream):exec(compiled,scope)
            executed+=1;cell['execution_count']=executed
            cell['outputs']=[dict(output_type='stream',name='stdout',text=stream.getvalue().splitlines(keepends=True))]
    finally:os.chdir(previous)
    notebook=dict(nbformat=4,nbformat_minor=5,cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3 (local)',language='python',name='python3'),
        language_info=dict(name='python',version='3.13.11')))
    path.write_text(json.dumps(notebook,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    import hashlib
    receipt=dict(exact_code_cells_executed=executed,execution='Python exec with captured stdout, not a Jupyter kernel',
                 new_training_or_native_calls=0,notebook_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                 source_builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (HERE/'results/H51_notebook_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('Created and executed',executed,'exact analysis code cells; no experiment rerun')


if __name__=='__main__':main()

