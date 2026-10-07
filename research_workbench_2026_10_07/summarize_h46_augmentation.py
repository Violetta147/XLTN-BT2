import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results'
columns = ['average_mape', 'F0mean_mape', 'F0std_mape', 'F0num_mape', 'F0mean_abs_error', 'F0std_abs_error',
           'F0num', 'macro_f1', 'balanced_accuracy', 'recall_v', 'recall_uv', 'false_voiced_sil']
tables = {}
for family in ('H45', 'H46'):
    data = pd.read_csv(OUT / f'{family}_metrics.csv')
    tables[family] = data[(data.model == 'candidate') & (data.split == 'nested')].set_index('file')[columns]
    assert len(tables[family]) == 4
comparison = tables['H45'].add_prefix('clean_fit_').join(tables['H46'].add_prefix('augmented_fit_'))
comparison['average_mape_delta_pp'] = comparison.augmented_fit_average_mape - comparison.clean_fit_average_mape
comparison.reset_index().to_csv(OUT / 'H46_clean_vs_augmented_fit.csv', index=False)
manifest = json.loads((OUT / 'H46_augmentation_manifest.json').read_text())
result = json.loads((OUT / 'H46_experiment.json').read_text())
short = comparison[['clean_fit_average_mape', 'augmented_fit_average_mape', 'average_mape_delta_pp']].round(6)
markdown = ['| File | Clean-fit MAPE (%) | Augmented-fit MAPE (%) | Delta (pp) |', '| --- | ---: | ---: | ---: |']
markdown += [f'| {name} | {row.iloc[0]:.6f} | {row.iloc[1]:.6f} | {row.iloc[2]:.6f} |' for name, row in short.iterrows()]
lines = ['# Augmentation có giúp BT2 không?', '',
         'So H45 clean-fit với H46 augmented-fit trên cùng bốn WAV train gốc được giữ riêng theo origin. Mỗi origin có ba noise variants; cả bản gốc và biến thể đều bị loại khỏi fit khi origin là held. K và memberbank giữ nguyên, chỉ thêm augmentation vào ranking fit pool.', '',
         '\n'.join(markdown), '',
         f"Mean Average MAPE H45: {tables['H45'].average_mape.mean():.6f}%; H46: {tables['H46'].average_mape.mean():.6f}%. Worst H45: {tables['H45'].average_mape.max():.6f}%; H46: {tables['H46'].average_mape.max():.6f}%.", '',
         f"Mục tiêu mỗi nested file≤2% H46: {result['goal_all_nested_files_le_2']}. Tám gate H46: {result['decision']['eligible']}.", '',
         f"Đã sinh {manifest['augmented_files']} WAV từ {manifest['origins']} file gốc, với {manifest['native_calls']} lần gọi Praat mới. Vẫn chỉ có bốn nhóm nguồn; chưa có thêm người đọc hoặc câu nói mới, cũng chưa xác minh tính độc lập giữa các bản thu gốc. Dùng nhiễu trắng 30/20 dB và nhiễu hồng 20 dB với seed cố định; giữ tần số lấy mẫu và thời lượng, không đổi cao độ, tốc độ hoặc cắt đỉnh.", '',
         'Nhãn V/UV/SIL và F0mean/std/count kế thừa được xem là latent targets của speech ban đầu dưới noise. Chưa có ground truth pitch từng khung mới; không gọi bản augment là dữ liệu chuẩn được giảng viên xác nhận. SNR ở đây so toàn waveform gốc với noise thêm, không phải SNR speech sạch.', '',
         'Chỉ augmentation train; không mở test, không chỉnh reference/frozen/original, không đổi threshold/grid/gate sauđo. Nested vẫnexploratory vì nhiều vòng trên4train. Augmentation có thể kiểmtra độbền với biến đổi đã biết, không bù được người nói/nội dung/phiên thu mới.', '',
         'Đọc H46_REPORT.md/H46_REGISTRATION.md và results/H46_augmentation_manifest.json. Các componentMAPE/MAE/count/F1/BA/recall/SIL trước/sau giữ tại results/H46_clean_vs_augmented_fit.csv.']
(HERE / 'AUGMENTATION_RESULT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(short.to_string())
