import base64
import datetime
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

os.environ['MPLBACKEND'] = 'Agg'
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from core import HERE, ROOT, RESULTS, TRAIN, TRAIN_GT, fit, infer, load_training, read_stats
from events import record

NAMES = {'ACF': 'ACF', 'AMDF_energy': 'AMDF có năng lượng', 'AMDF_no_energy': 'AMDF không năng lượng',
         'GMM_ACF': 'ACF + GMM', 'GMM_AMDF': 'AMDF + GMM'}
ORDER = ['ACF', 'AMDF_energy', 'AMDF_no_energy', 'GMM_ACF', 'GMM_AMDF']


def md_table(headers, rows):
    def value(x):
        if isinstance(x, (float, np.floating)):
            return f'{x:.2f}' if np.isfinite(x) else 'không xác định'
        return str(x).replace('|', '/')
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(value(v) for v in row) + ' |' for row in rows])


def grading(frame):
    rows = [[row.file, row.F0mean_mape, row.F0std_mape, row.F0num_mape, row.average_mape] for row in frame.itertuples()]
    rows.append(['TỔNG CỘNG', *[float(frame[key].mean()) for key in ('F0mean_mape', 'F0std_mape', 'F0num_mape', 'average_mape')]])
    return md_table(['File', 'MAPE F0mean (%)', 'MAPE F0std (%)', 'MAPE F0num (%)', 'Average MAPE (%)'], rows)


def figures(final, selection):
    directory = HERE / 'figures'
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout='constrained')
    x = np.arange(len(ORDER))
    for ax, split in zip(axes, ['train', 'test']):
        ax.bar(x - .18, [final['summary'][m]['baseline'][split]['average_mape'] for m in ORDER], .36, label='Baseline', color='#e07a5f')
        ax.bar(x + .18, [final['summary'][m]['improved'][split]['average_mape'] for m in ORDER], .36, label='Improved', color='#2a9d8f')
        if split == 'train':
            ax.scatter(x + .18, [selection[m]['nested_lofo']['average_mape'] for m in ORDER], c='black', marker='D', s=30, label='Nested LOFO')
        ax.set(xticks=x, xticklabels=['ACF', 'AMDF + E', 'AMDF no E', 'GMM ACF', 'GMM AMDF'], ylabel='Average MAPE (%)', title=split.upper())
        ax.tick_params(axis='x', labelrotation=20)
        ax.grid(axis='y', alpha=.2)
        ax.legend(fontsize=9)
    fig.savefig(directory / 'train_test_improvement.png', dpi=160)
    plt.close(fig)
    config = selection['ACF']['config']
    fitted = selection['ACF']['fitted']
    item = next(x for x in load_training(25) if x['file'] == 'phone_F1.wav')
    baseline_config = selection['ACF']['baseline']['config']
    baseline_fit = selection['ACF']['baseline']['fit']
    original = infer(item, baseline_config, baseline_fit)[1]
    improved = infer(item, config, fitted)[1]
    fig, axes = plt.subplots(2, 1, figsize=(13, 7), sharex=True, layout='constrained')
    for ax, values, name in zip(axes, [original, improved], ['Baseline ACF', 'Improved ACF (training selected)']):
        for label, color in [('v', '#1976d2'), ('uv', '#ef6c00'), ('sil', '#c62828')]:
            mask = item['labels'] == label
            ax.scatter(item['times'][mask], values[mask], s=12, color=color, label=label.upper())
        ax.axhline(item['stats']['F0mean'], color='black', ls='--', label='File GT mean')
        ax.axhspan(item['stats']['F0mean'] - item['stats']['F0std'], item['stats']['F0mean'] + item['stats']['F0std'], color='black', alpha=.08)
        ax.set(title=f'{name}: mean {np.nanmean(values):.2f} Hz, std {np.nanstd(values):.2f} Hz, n {np.isfinite(values).sum()}', ylim=(60, 410), ylabel='F0 (Hz)')
        ax.grid(alpha=.2)
        ax.legend(ncol=4, fontsize=9)
    axes[-1].set_xlabel('Time (s)')
    fig.savefig(directory / 'phone_F1_before_after.png', dpi=160)
    plt.close(fig)
    book = json.loads((ROOT / 'improved-training-only' / 'executed_local' / 'BT2_ACF_improved_train_only.ipynb').read_text(encoding='utf-8'))
    pngs = [o['data']['image/png'] for c in book['cells'] if c['cell_type'] == 'code'
            for o in c['outputs'] if 'image/png' in o.get('data', {})]
    for index, name in [(0, 'notebook_acf_train_distribution.png'), (4, 'notebook_acf_test_phone_F2.png'),
                        (2, 'notebook_acf_greedy_peak_evidence.png'), (3, 'notebook_acf_silence_evidence.png')]:
        (directory / name).write_bytes(base64.b64decode(pngs[index]))


def main():
    final = json.loads((RESULTS / 'final_evaluation.json').read_text(encoding='utf-8'))
    selection = json.loads((RESULTS / 'selection_summary.json').read_text(encoding='utf-8'))
    validation = json.loads((RESULTS / 'delivery_validation.json').read_text(encoding='utf-8'))
    frozen = json.loads((RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))
    access = json.loads((RESULTS / 'test_access.json').read_text(encoding='utf-8'))
    scores = pd.read_csv(RESULTS / 'final_train_test_per_file.csv')
    profile = pd.read_csv(RESULTS / 'final_dataset_profile.csv')
    nested = pd.read_csv(RESULTS / 'selected_train_and_nested_lofo.csv')
    baseline_frames = pd.read_csv(RESULTS / 'baseline_training_frames.csv')
    phone_frames = baseline_frames[(baseline_frames.model == 'ACF') & (baseline_frames.file == 'phone_F1.wav')]
    sil_frames = phone_frames[(phone_frames.label == 'sil') & phone_frames.f0.notna()]
    sil_frames.to_csv(RESULTS / 'phone_F1_false_silence_evidence.csv', index=False)
    silence_rows = []
    phone_gt_std = read_stats(TRAIN_GT / 'phone_F1.lab')['F0std']
    for label, mask in [('Mọi F0 hữu hạn: điểm chính thức', phone_frames.f0.notna()),
                        ('Bỏ riêng F0 trong SIL: chỉ chẩn đoán', phone_frames.f0.notna() & (phone_frames.label != 'sil'))]:
        values = phone_frames.loc[mask, 'f0'].to_numpy()
        silence_rows.append([label, len(values), values.mean(), values.std(), 100 * abs(values.std() - phone_gt_std) / phone_gt_std])
    silence_table = md_table(['Phép tính', 'F0num', 'Mean (Hz)', 'Std (Hz)', 'MAPE std (%)'], silence_rows)
    silence_frames_table = md_table(['Tâm khung (s)', 'Nhãn', 'ACF score', 'RMS tương đối', 'F0 (Hz)'],
                                   [[f'{r.time_s:.4f}', r.label.upper(), f'{r.score:.8f}', f'{r.relative_rms:.8f}', r.f0] for r in sil_frames.itertuples()])
    figures(final, selection)
    summary_rows, metric_rows = [], []
    for model in ORDER:
        s = final['summary'][model]
        summary_rows.append([NAMES[model], s['baseline']['train']['average_mape'], s['improved']['train']['average_mape'],
                             selection[model]['nested_lofo']['average_mape'], s['baseline']['test']['average_mape'],
                             s['improved']['test']['average_mape'], s['improved']['final_score'], s['improved']['grade_10']])
        for split in ('train', 'test'):
            before, after = s['baseline'][split], s['improved'][split]
            metric_rows.append({'model': model, 'split': split, 'version': 'baseline', **before})
            metric_rows.append({'model': model, 'split': split, 'version': 'improved', **after})
    pd.DataFrame(metric_rows).to_csv(RESULTS / 'final_tradeoffs_summary.csv', index=False)
    summary = md_table(['Phương pháp', 'Train cũ %', 'Train mới %', 'Nested LOFO %', 'Test cũ %', 'Test mới %', 'FINAL SCORE %', 'Điểm /10'], summary_rows)
    profile_table = md_table(['Tập', 'File', 'fs (Hz)', 'Dài (s)', 'GT mean (Hz)', 'GT std (Hz)', 'GT num', 'Khung V theo LAB', 'Năng lượng >1 kHz (%)', 'V/SIL RMS (dB, proxy)'],
                             [[r.split, r.file, r.fs, r.duration_s, r.GT_mean, r.GT_std, int(r.GT_num), r.v_frames,
                               100 * r.band_above_1000_fraction, r.V_to_SIL_rms_ratio_dB_proxy_not_SNR] for r in profile.itertuples()])
    gap = final['baseline_acf_gap_pp']
    contribution = final['gap_contribution_pp']
    root_figure = 'XLTN-BT2/research_3gt_2026_10_05/figures/'
    filename = 'PHAN_TICH_VA_CAI_TIEN_BT2_2026-10-05.md'
    lines = [f'''# Phân tích và cải tiến BT2: vì sao train gần 30% còn test khoảng 9%?

Ngày 05/10/2026. Số liệu được chạy lại local; giờ trong nhật ký là giờ Việt Nam (UTC+7).
Cập nhật 06/10/2026: thêm mục5.1 về score T/2T/3T và mục5.2 về nhận nhầm khoảng lặng,
tính bằng chứng trực tiếp từ WAV train trong mọi notebook mới.

## 1. Kết luận đọc trước

**Có nguyên nhân cụ thể trong thuật toán và dữ liệu; chưa thấy lỗi công thức MAPE hay ghép nhầm file.**
ACF bản cũ có train **29,83%**, test **9,33%**. Khác biệt không trái quy luật học máy:
bản cũ học ngưỡng phân biệt V/UV, không tối ưu trực tiếp ba thống kê F0. Chất lượng train không buộc
phải tốt hơn test trên mọi tập bốn file. Một vài file train kích hoạt lỗi mà test gặp ít hơn.

Hai nguyên nhân đã đo được:

1. **Chọn nhầm bội chu kỳ trong vùng hữu thanh của phone_F1.** Một khung có chu kỳ khoảng 4,6 ms,
   nhưng bản cũ chọn 13,9 ms. F0 xuống khoảng 72 Hz thay vì ứng viên khoảng 217 Hz.
   Một số giá trị thấp kéo mean xuống nhưng làm std tăng mạnh.
2. **Nhận nhầm UV/SIL là V.** Những F0 giả được tính đúng vào F0num và F0std theo quy tắc chấm.
   Ở studio_M1, chỉ giữ dự đoán nằm trong V thật để chẩn đoán cho std 25,94 Hz, rất gần GT 26,4 Hz;
   khi tính cả các dự đoán SIL sai, std tăng đáng kể.

Đã chạy các hướng riêng, đăng ký **234 cấu hình kết hợp**, kiểm tra giữ riêng file và nested LOFO,
sau đó khóa cấu hình trước khi đánh giá test. Tất cả năm pipeline giảm MAPE train và test:

{summary}

ACF có nested LOFO thấp nhất trong nhóm cải tiến (**8,55%**), nên là bản nên chạy trước nếu chọn theo
kiểm tra trên train. AMDF có năng lượng có train thấp nhất (**4,88%**); nested LOFO của nó là **10,01%**.
Sự chênh lệch đó cho thấy vẫn có rủi ro chọn cấu hình quá hợp với ít file train.

![So sánh train, validation và test]({root_figure}train_test_improvement.png)

## 2. Chính xác đã so sánh file nào?

Sáu file gốc trong `turn-in-assignment/` và `turn-in-assignment - Copy/` được giữ nguyên, đã đối chiếu SHA256 với snapshot.
Hai bản ACF giống nhau về toàn bộ file; hai bản GMM cũng giống nhau. AMDF khác ở cổng năng lượng.
Vì vậy sáu notebook gốc tạo ra năm pipeline khác nhau, và bốn notebook mới bao phủ đủ năm pipeline.

| Notebook mới trong `improved-training-only/` | Pipeline | Cổng năng lượng mới |
|---|---|---|
| BT2_ACF_improved_train_only.ipynb | ACF | Có |
| BT2_AMDF_improved_with_energy_train_only.ipynb | AMDF | Có |
| BT2_AMDF_improved_without_energy_train_only.ipynb | AMDF | Không |
| BT2_ACF_AMDF_GMM_improved_train_only.ipynb | ACF+GMM và AMDF+GMM | ACF không; AMDF có |

Tên `energy_set` của bản gốc chỉ là tên nhóm notebook; bản ACF/GMM gốc chưa có cổng năng lượng.
Không so sánh ngưỡng ACF với AMDF chỉ qua trị số: ACF score càng cao càng tuần hoàn, AMDF score càng thấp càng tuần hoàn.

## 3. Công thức chấm đã kiểm tra

Với một file: MAPE(X) = 100 × |X dự đoán − X chuẩn| / |X chuẩn|, X là F0mean, F0std, F0num.
Average MAPE file = (MAPE mean + MAPE std + MAPE num) / 3.
TỔNG CỘNG tập = trung bình Average MAPE của đúng bốn file.
**FINAL SCORE = 100 − TỔNG CỘNG MAPE TEST**; điểm thang 10 = FINAL SCORE / 10, làm tròn một chữ số.

Trong trao đổi đầu tiên, “Final Score” từng được dùng để chỉ sai số trung bình test; báo cáo này dùng
công thức cuối cùng trong mẫu của thầy: **100 trừ sai số**. Số 9,33% là MAPE, không phải điểm cuối cùng.
Không làm tròn các thành phần trước khi tính tổng. F0std dùng `ddof=0` như bản gốc; F0num đếm mọi F0 hữu hạn.
Không lọc dự đoán bằng nhãn thật, không bỏ MAPE num, không dùng mean/std chuẩn để sửa đầu ra.

Baseline ACF train được tái lập tới {selection['ACF']['baseline']['full_train']['average_mape']:.12f}%;
ngưỡng ACF là {selection['ACF']['baseline']['fit']['pitch_threshold']:.15f}.
Baseline test cũng khớp số liệu cũ tới sai số 1e-10. Kiểm tra này loại trừ nguyên nhân “bảng train/test tính hai công thức khác nhau”.

## 4. Vì sao chênh lệch 20,51 điểm phần trăm?

Gap = train MAPE − test MAPE = **{gap:.2f} điểm phần trăm**.
Do Average MAPE là trung bình ba đại lượng, có thể phân rã gap thành:

{md_table(['Thành phần', 'Đóng góp vào gap (điểm phần trăm)'], [[k, v] for k, v in contribution.items()])}

F0std giải thích khoảng **{100 * contribution['F0std'] / gap:.1f}%** gap; F0mean của test còn tệ hơn train một chút.
Vì thế “train kém mọi mặt” là cách đọc sai: train chủ yếu kém ở std và count.

### 4.1. phone_F1: một điểm lệch có thể làm std lớn ra sao?

GT std là 20,6 Hz; ACF cũ dự đoán std khoảng 48,94 Hz → MAPE std **137,56%**.
Ở khung tâm 0,5725 s, hai ứng viên là **72,1836 Hz** và **217,4165 Hz**.
Ứng viên 217 Hz chỉ kém đỉnh mạnh nhất khoảng **0,000493** điểm ACF.
Waveform lặp khoảng sáu chu kỳ trong 25 ms và có đỉnh ACF tại một, hai, ba chu kỳ.
Đây là bằng chứng trực tiếp về chọn **3T0**, không chỉ lỗi octave **2T0**.
Praat cũng mô tả việc ACF có đỉnh ở bội chu kỳ và phải giải quyết chọn ứng viên.
[Nguồn chính thức Praat](https://www.fon.hum.uva.nl/praat/manual/how_to_choose_a_pitch_analysis_method.html).

![Waveform và các đỉnh cạnh tranh]({root_figure}phone_F1_competing_periods.png)

Trong notebook mới, mục **5.1. Bằng chứng số liệu** hiện in độ cao từng đỉnh tới10 chữ số thập phân,
độ trễ, F0 sau nội suy, chênh với đỉnh cao nhất và lựa chọn của bản cũ ở ba khung liên tiếp.
Bảng và hình được tính khi chạy từ WAV, không dùng các score ghi sẵn. Output đã chạy lưu trong `executed_local/`.

![Minh chứng được chạy ngay trong notebook]({root_figure}notebook_acf_greedy_peak_evidence.png)

Chênh lệch score chứng minh lựa chọn `argmax` tại bội chu kỳ trong khung được kiểm tra.
Nó chưa chứng minh riêng rằng nhiễu gây ra thứ tự đỉnh này: chưa có tín hiệu sạch để đối chiếu,
và sóng tuần hoàn lý tưởng cũng có đỉnh ở bội chu kỳ. Nhiễu, biến đổi giọng nói, lấy mẫu và tính toán
đều có thể góp phần; không quy hết nguyên nhân cho nhiễu chỉ từ một waveform.

Chẩn đoán train thấy 14 dự đoán thấp hơn 60% GT mean ở phone_F1; 12 nằm trong V, không khung nào
ở vùng sát ranh giới nhãn theo tiêu chí nửa độ dài khung. Trong 9/14 khung có ứng viên gần 2/3/4 lần F0
với chênh strength <0,02. Con số này xác định các trường hợp nghi ngờ, không phải số lỗi F0 đã có GT từng khung.

Phân rã phương sai của phone_F1 theo nhóm nhãn: V góp **68,67%**, UV góp **10,26%**, SIL góp **21,07%**.
Đây là phần phương sai của mỗi nhóm quanh mean chung, gồm độ phân tán trong nhóm và độ lệch mean nhóm;
không phải tỷ lệ “lỗi có thể loại bỏ” tương ứng. Chỉ hai F0 SIL quanh 395 Hz đã góp hơn một phần năm phương sai.
Giữ V thật để chẩn đoán vẫn cho std **41,58 Hz**, nên cổng năng lượng một mình chưa giải quyết phone_F1.

#### Nhận nhầm khoảng lặng: bằng chứng mới trong mục 5.2 của notebook

{silence_frames_table}

Hai khung này có nhãn SIL trong LAB và không sát ranh giới theo tiêu chí nửa độ dài khung.
Score ACF vượt ngưỡng học trên train dù RMS tương đối chỉ khoảng 0,057–0,059.
ACF chuẩn hóa đo độ giống nhau khi dịch tín hiệu; biên độ nhỏ không tự bảo đảm score nhỏ.
Thuật toán gán V rồi đổi độ trễ thành F0, tạo hai dự đoán sai trong vùng khoảng lặng có nhãn.

{silence_table}

Phép bỏ riêng SIL thật cho thấy ảnh hưởng của hai giá trị xa mean lên std.
Đây là chẩn đoán bằng nhãn thật, không dùng để sửa đầu ra hoặc làm đẹp bảng chấm điểm.
Std vẫn cao sau khi bỏ SIL vì còn lỗi chọn bội chu kỳ và nhận nhầm UV.
Tỷ lệ 21,07% là phần phương sai quanh mean chung, không phải tỷ lệ std giảm khi bỏ hai điểm.

![Waveform khoảng lặng và ACF vượt ngưỡng]({root_figure}notebook_acf_silence_evidence.png)

Notebook cũng in số SIL nhận V và F0 hữu hạn trong SIL của baseline và cấu hình đang chạy,
kèm ngưỡng năng lượng nếu có. So sánh là giữa cả pipeline; chưa tách riêng hiệu quả cổng năng lượng.
Đã xác minh lỗi nhận SIL và tác động thống kê, nhưng chưa xác định nguồn vật lý của tín hiệu nền
hoặc chứng minh nó là nhiễu môi trường ngẫu nhiên. Câu giải thích về loại nhiễu đó được ghi là giả thuyết.

![phone_F1 trước và sau cải tiến]({root_figure}phone_F1_before_after.png)

Bản ACF mới trả std 26,55 Hz; MAPE std còn **28,89%**. Đây là cải thiện rõ nhưng chưa khớp hoàn toàn GT.
Dải mean ± std trên đồ thị là thống kê của file, không phải F0 chuẩn từng khung; điểm nằm ngoài dải không tự động là lỗi.

### 4.2. studio_M1: lỗi khác với phone_F1

Bản cũ nhận nhầm **22 khung SIL** là hữu thanh ở studio_M1. Chẩn đoán chỉ tính dự đoán thuộc V thật:
std **25,94 Hz** gần GT **26,4 Hz**. Cổng năng lượng có thể xử lý nguồn F0 giả này.
Không dùng phép lọc theo nhãn thật trong notebook cải tiến: khi chạy WAV mới chỉ có RMS và score.

### 4.3. Mẫu số MAPE và đặc trưng tập dữ liệu

{profile_table}

Phone_F1 có phần năng lượng trên 1 kHz chỉ **3,77%**; phone_F2 là **16,63%**.
Waveform phone_F1 ở khung đã kiểm tra gần hình sin, khiến các đỉnh bội chu kỳ gần ngang nhau.
Đây là dấu hiệu khác biệt phổ phù hợp với giả thuyết sai bội chu kỳ, chưa đủ xác định lỗi do microphone,
lọc của thiết bị hay nội dung người nói. Không có metadata thiết bị/chuỗi xử lý để kết luận nguồn gốc.

Phone_F2 có tỷ lệ RMS V/SIL cao hơn phone_F1 khoảng 5,49 dB trong phép đo này.
Đó là **proxy mức tách biệt năng lượng**, không phải SNR đo từ tín hiệu sạch và nhiễu tách riêng.
SIL median của studio_F2 bằng 0 nên tỷ lệ dB không xác định, được báo rõ thay vì chia cho 0.
Không file nào bị clipping theo tiêu chí |sample| >0,999.

GT std của phone_F1 20,6 thấp hơn phone_F2 30,7, nên cùng sai số Hz sẽ thành MAPE lớn hơn.
Nhưng nếu lấy lỗi std phone_F1 khoảng 28,34 Hz chia cho 30,7 thì vẫn khoảng **92,30%**, cao hơn nhiều
MAPE std phone_F2 **17,66%**. Mẫu số chỉ là một phần; sai chọn ứng viên là phần quan trọng.

F0num chuẩn không luôn bằng số khung có tâm rơi vào vùng V của LAB cũ. Ví dụ phone_F1: 148 so với 153;
studio_F1: 127 so với 123. Thầy chưa cung cấp chuỗi F0 chuẩn và quy trình tạo 3GT đủ để giải thích chính xác chênh lệch này.
Do đó không ép F0num bằng số nhãn V; sử dụng ba thống kê 3GT để chấm và nhãn LAB cũ cho V/UV riêng.

### 4.4. Những nguyên nhân đã loại trừ hoặc chưa có bằng chứng

- Đổi `ddof=0` sang `ddof=1` chỉ thay std khoảng 0,62% ở n=82; không thể giải thích sai số 137,56%.
- Không thấy ghép nhầm GT, lỗi công thức hoặc lỗi source/output cũ trong phép tái lập hiện tại.
- Phone dùng fs16 kHz, studio fs44,1 kHz; giữ đúng fs từng WAV và khung theo ms. Không đổi sample rate để làm đẹp kết quả.
- Lọc bỏ khung ranh giới theo nhãn thật không giải thích các F0 thấp đã tìm: chúng không nằm sát ranh giới.
- Chưa thể khẳng định toàn bộ sai khác đều do dataset hoặc toàn bộ test tốt đều do may mắn: chỉ có bốn file mỗi tập.

## 5. Loop thí nghiệm: đã thử gì, giữ gì?

| Hướng thử riêng | Kết quả tiêu biểu trên LOFO train | Kết luận |
|---|---|---|
| Cổng năng lượng | ACF 29,11→16,75%; AMDF 27,03→13,70%; GMM ACF lại 28,80→30,02% | Hữu ích cho SIL nhưng không dùng cho mọi pipeline |
| Ưu tiên chu kỳ ngắn khi strength gần bằng | ACF 22,76%; AMDF năng lượng 9,51%; GMM ACF 13,11% | Giảm sai bội chu kỳ; cần chọn margin bằng train |
| Chọn đường ứng viên theo thời gian | AMDF năng lượng tốt nhất 6,77%; GMM ACF 11,14% | Giữ làm thành phần chính, không làm phẳng F0 bằng GT |
| Trung vị 3/5 khung trong đoạn V dự đoán | ACF 24,89%; AMDF năng lượng 9,17% | Có ích vừa phải khi dùng riêng; kết hợp cho một số mô hình |
| Gaussian low-pass 800 Hz | ACF 30,34%; GMM ACF 33,64%; GMM AMDF 21,21% | Loại khỏi tập kết hợp; không mặc định lọc là tốt |
| Đổi cách chọn ngưỡng | AMDF histogram hai mode LOFO14,98% nhưng macro F1 tụt xuống0,820 so với0,869 | Không giữ chỉ vì giảm MAPE; kiểm tra đánh đổi V/UV |

Mỗi hướng có dữ liệu đầy đủ, cả cấu hình kém hơn, trong `results/experiment_*` và một commit riêng.
Tập kết hợp gồm ACF55, AMDF năng lượng55, GMM ACF46, GMM AMDF46, AMDF không năng lượng32 cấu hình.
Kết hợp được thực hiện sau khi đã đo từng thành phần; các kết quả riêng không được coi là cấu hình cuối.

### Quy tắc chọn và kiểm tra

1. Giữ bốn file train riêng; không chia khung gần nhau của cùng WAV vào train và validation.
2. Với mỗi cấu hình, LOFO học ngưỡng từ ba file và chấm file thứ tư; xếp theo MAPE trung bình file.
3. Chỉ chọn trong các cấu hình có macro F1 V/UV không thấp hơn baseline LOFO quá 0,03.
4. Nested LOFO giữ một file vòng ngoài; trên ba file còn lại chọn cấu hình bằng ba lần giữ riêng vòng trong;
   fit ngưỡng bằng ba file rồi chấm file vòng ngoài. Lặp đủ bốn vòng.
5. Điều kiện giữ: giảm MAPE train ít nhất20% tương đối; phone_F1 std cải thiện;
   fixed LOFO/nested MAPE không cao hơn baseline LOFO quá1 điểm; macro F1 không giảm quá0,03.

{md_table(['Phương pháp', 'Baseline LOFO %', 'Cấu hình cuối LOFO %', 'Nested LOFO %', 'Baseline LOFO F1', 'Nested F1'],
 [[NAMES[m], selection[m]['baseline']['lofo']['average_mape'], selection[m]['lofo']['average_mape'], selection[m]['nested_lofo']['average_mape'],
   f"{selection[m]['baseline']['lofo']['macro_f1']:.4f}", f"{selection[m]['nested_lofo']['macro_f1']:.4f}"] for m in ORDER])}

Nested LOFO ở đây giảm thiên lệch của bước chọn tham số trong registry, **chưa đánh giá độc lập toàn bộ quá trình nghiên cứu**:
các giả thuyết và tập cấu hình được xây dựng sau khi xem cả bốn file train. Các khung chồng lấn không phải quan sát độc lập;
không suy ra kích thước mẫu thống kê bằng số khung. Bốn file không đủ cho kết luận chắc chắn về người nói/thiết bị mới.
Baseline LOFO dùng cấu hình baseline cố định; nested mới kiểm tra cả bước chọn trong registry nên hai con số có quy trình khác nhau.

## 6. Cải tiến nằm ở đâu trong thuật toán?

Giữ nguyên chuẩn hóa ACF/AMDF, nội suy parabol, khung/bước trượt và dải70–400 Hz của từng baseline.
Đổi cách chọn F0 giữa các cực trị cạnh tranh; thêm cổng năng lượng vào pipeline nào được train/validation chấp nhận.
Không dùng deep learning, không thêm F0mean/F0std/F0num chuẩn vào suy luận.

| Pipeline | Khung (ms) | Chọn ứng viên | Jump cost | Octave cost / margin | Median | Năng lượng | Ngưỡng chu kỳ |
|---|---|---|---|---|---|---|---|
| ACF | 25 | Đường liên tục | 0,35 | octave0,03 | 3 | Có | Giao histogram V/UV được quy tắc gốc chọn |
| AMDF năng lượng | 25 | Đường liên tục | 0,35 | octave0 | 1 | Có | Gaussian được quy tắc gốc chọn |
| AMDF không năng lượng | 25 | Đường liên tục | 0,35 | octave0 | 1 | Không | Giao histogram V/UV |
| GMM ACF | 20 | Đường liên tục | 0,35 | octave0,01 | 3 | Không | GMM hai thành phần |
| GMM AMDF | 25 | F0 cao nhất trong ứng viên gần tốt nhất | — | margin0,05 | 3 | Có | GMM hai thành phần |

Strength của ACF là ACF score; strength của AMDF là 1−AMDF score.
Với cách chọn đường, chi phí khung là `(strength_max − strength_candidate) + octave_cost × log2(400/F0)`.
Chi phí chuyển khung là `jump_cost × abs(log2(F0_t/F0_previous))`; tìm tổng chi phí nhỏ nhất bằng quy hoạch động.
Chỉ nối trong một đoạn V **dự đoán** liên tục. Trung vị cũng chỉ áp dụng bên trong đoạn đó.
Log2 được dùng cho tỷ lệ giữa hai ứng viên để phạt bước nhảy, còn các thống kê và MAPE cuối vẫn dùng Hz.
Các bộ pitch cổ điển có cơ chế ứng viên, phạt octave và thay đổi pitch; đây là một biến thể đơn giản của ý tưởng này,
không phải bản sao đầy đủ Praat. [Tài liệu Praat về chi phí chọn đường](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_filtered_autocorrelation.html).

Cổng RMS học ngưỡng từ V/SIL train với balanced accuracy trung bình theo file. RMS tương đối được chuẩn hóa bằng
percentile95 của RMS trong chính WAV đang xử lý. Việc chuẩn hóa WAV test chỉ dùng dữ liệu WAV, không dùng GT và không học lại ngưỡng.
GMM fit trên score của vùng V/UV train, loại SIL theo LAB cũ; dù fit Gaussian không cần nhãn thành phần,
toàn bộ quy trình hiện tại vẫn dùng nhãn train để chọn vùng và kiểm tra mô hình.

Các thay đổi có đánh đổi: path/median có thể làm mất biến thiên pitch thật; near có thể chọn F0 quá cao;
cổng năng lượng có thể bỏ khung hữu thanh yếu. Vì vậy phải kiểm tra cả recall/F1 và F0num, không chỉ std.

## 7. Test độc lập được bảo vệ thế nào?

- Freeze cấu hình: **{frozen['frozen_at_vietnam']}**; hash registry, train manifest và mã inference đã lưu.
- Thư mục 3GT test trong nghiên cứu được tạo lần đầu lúc **{access['first_test_stats_directory_created_at']}**,
  mốc này lấy từ thời gian tạo thư mục trên Windows; sau freeze. Lượt đánh giá hoàn tất lúc22:56:56.
- Dự đoán tất cả WAV test được cố định trước khi gắn nhãn/thống kê test để chấm.
- Sau khi thấy test, không đổi thuật toán/siêu tham số. Lỗi chia0 ở phần profile RMS chỉ sửa phần báo cáo;
  không đổi prediction. Các notebook chạy lại test để kiểm chứng đúng cấu hình đã khóa, không tạo vòng chọn theo test.
- Test baseline đã được xem trong phiên trước. Vì vậy nói chính xác là **độc lập với việc chọn cải tiến lần này**,
  không phải test hoàn toàn chưa từng biết. Tên file và các thống kê tổng thể test trước đây đã có trong lịch sử.

Không có cơ sở cho câu “train30% thì test không thể9%”: đó không phải một định luật.
Train có trường hợp khó hơn đối với thuật toán cụ thể và hàm học ngưỡng cũ khác metric chấm cuối.
Sau cải tiến, ACF vẫn có train6,18% và test3,29% — test tiếp tục thấp hơn, nhưng cơ chế lỗi train đã giảm.
Có thể phần thuận lợi ngẫu nhiên của bốn file test góp vào kết quả; dữ liệu hiện tại không đủ định lượng phần đó
một cách đáng tin cậy. Cần bộ test mới chưa xem để xác nhận khả năng tổng quát.

## 8. Đánh đổi ngoài MAPE

Macro F1, recall V/UV và balanced accuracy ở dưới chỉ đánh giá khung có nhãn V/UV.
SIL→V báo riêng; F0num đếm toàn bộ F0 hữu hạn. MAE dưới đây là trung bình lỗi tuyệt đối theo file, đơn vị Hz.
Các cặp số có dạng **cũ → mới**; V/UV được macro trung bình theo file như MAPE.
''']
    for split in ('train', 'test'):
        metrics = []
        for model in ORDER:
            before, after = (final['summary'][model][version][split] for version in ('baseline', 'improved'))
            pair = lambda key, decimals=3: f'{before[key]:.{decimals}f} → {after[key]:.{decimals}f}'
            metrics.append([NAMES[model], pair('macro_f1'), pair('recall_v'), pair('recall_uv'), pair('balanced_accuracy'),
                            pair('F0mean_abs_error', 2), pair('F0std_abs_error', 2), pair('F0num', 0), pair('false_voiced_sil', 0)])
        lines += ['\n### ' + split.upper() + '\n', md_table(['Pipeline', 'Macro F1', 'Recall V', 'Recall UV', 'BA', 'MAE mean Hz', 'MAE std Hz', 'Tổng F0num', 'SIL→V'], metrics)]
    lines += ['''
GMM ACF vẫn bỏ nhiều khung V: nested recall V khoảng0,716, dù MAPE std tốt hơn. GMM AMDF thêm cổng năng lượng
làm F0num train giảm, MAPE num tăng từ9,48% lên15,24%; tổng MAPE vẫn giảm nhờ mean/std tốt hơn.
AMDF không năng lượng còn46 khung SIL→V train, nên std vẫn cao hơn các bản có năng lượng.
Đây là các hạn chế thực tế, không che bằng bảng tổng MAPE.

## 9. Bảng điền theo mẫu của thầy — các bản cải tiến
''']
    for model in ORDER:
        lines += ['\n### ' + NAMES[model] + '\n']
        for split in ('train', 'test'):
            subset = scores[(scores.model == model) & (scores.version == 'improved') & (scores.split == split)].sort_values('file')
            lines += ['\n**KẾT QUẢ TẬP ' + split.upper() + '**\n', grading(subset)]
        s = final['summary'][model]['improved']
        lines += [f'\nFINAL SCORE = 100 − {s["test"]["average_mape"]:.2f} = **{s["final_score"]:.2f}%**; điểm thang10 **{s["grade_10"]:.1f}**.\n']
    python_path = validation['python_executable']
    lines += [f'''
## 10. Cách dùng và tái lập

**Trên Colab:** upload bốn file `.ipynb` nằm trực tiếp trong `improved-training-only/`, mở từng file rồi Run all.
Không cần tải file Python nghiên cứu. Giữ các thư mục dữ liệu cũ và 3GT trong thư mục BT2 như trước.
Đường dẫn trong notebook vẫn bắt đầu `/content/drive/...`; không có ổG.
Nếu Colab mount tên `MyDrive` thay vì `My Drive`, notebook tự dùng tên tương đương khi đường dẫn gốc không tồn tại.
`SHOW_DETAILED_TEST_PLOTS=True` ở mọi notebook mới. Bản có output chạy local nằm ở `improved-training-only/executed_local/`.

**Trên local:** Python **{validation['python'].split()[0]}**; thư viện thực tế:
{', '.join(name + ' ' + version for name, version in validation['versions'].items())}.
File `results/delivery_validation.json` lưu đường dẫn interpreter, hash và kết quả kiểm chứng.
Để tái lập từ working folder này trong PowerShell (không cần Drive):

```powershell
$bt2Python = '{python_path}'
& $bt2Python 'XLTN-BT2/research_3gt_2026_10_05/baseline_audit.py'
& $bt2Python 'XLTN-BT2/research_3gt_2026_10_05/diagnose.py'
& $bt2Python 'XLTN-BT2/research_3gt_2026_10_05/experiments.py' energy
& $bt2Python 'XLTN-BT2/research_3gt_2026_10_05/experiments.py' near
& $bt2Python 'XLTN-BT2/research_3gt_2026_10_05/experiments.py' path
& $bt2Python 'XLTN-BT2/research_3gt_2026_10_05/experiments.py' median
& $bt2Python 'XLTN-BT2/research_3gt_2026_10_05/experiments.py' filter
& $bt2Python 'XLTN-BT2/research_3gt_2026_10_05/experiments.py' selection
& $bt2Python 'XLTN-BT2/research_3gt_2026_10_05/combined_selection.py'
& $bt2Python 'XLTN-BT2/research_3gt_2026_10_05/package_notebooks.py'
& $bt2Python 'XLTN-BT2/research_3gt_2026_10_05/final_evaluation.py'
& $bt2Python 'XLTN-BT2/research_3gt_2026_10_05/execute_notebook.py' 'BT2_ACF_improved_train_only.ipynb'
```

Nếu muốn bảo toàn nhật ký gốc, tái lập trong một bản copy thư mục nghiên cứu; các script ghi thêm sự kiện và ghi lại kết quả.
Không xem việc chạy lại selection sau khi đã biết test là một thí nghiệm mới có test chưa xem.

Kiểm chứng thực hiện: bốn notebook ×{validation['notebooks'][0]['code_cells_executed']} code cell,
tổng{sum(x['figures'] for x in validation['notebooks'])} hình; train/test khớp phép đánh giá độc lập tới1e-10;
bỏ labels/stats/segments vẫn cho prediction giống hệt; SHA256 sáu notebook gốc không đổi.
Đã xem hình waveform/ACF cạnh tranh, contour trước/sau, phân bố train và một hình test từ output notebook.
Các bảng còn lại được đối chiếu số liệu tự động; không khẳng định đã xem thủ công mọi hình.

## 11. Nhật ký, Git và cập nhật âm thanh

Nhật ký ngắn: **BAO_CAO_SU_KIEN_BT2_2026-10-05.md**, gồm thời gian, việc làm, bằng chứng và quyết định từng bước.
Dữ liệu chi tiết: `XLTN-BT2/research_3gt_2026_10_05/results/`.
Tất cả commit trên nhánh **codex/train-mape-investigation** là commit local; chưa push GitHub.
Mỗi hướng thí nghiệm được lưu riêng, baseline và kết quả thất bại vẫn có trong Git.

Đã dùng Google Dịch, nhập thông báo tiếng Việt và bấm loa nguồn nhiều lần. UI chuyển sang “Dừng nghe”,
nhưng người dùng báo chưa nghe ở lần đầu; chưa có xác nhận nghe được cho các lần sau.
Không xem việc bấm nút là bằng chứng âm thanh đã đến tai người dùng. Báo cáo file là bản ghi đáng tin cậy.
Không dùng Gemini để sinh kết quả thí nghiệm; toàn bộ con số trên được tính bằng mã local.

## 12. Việc còn hạn chế và bước tiếp theo hợp lý

1. Chạy bản Colab để xác nhận môi trường Colab của bạn cũng tái lập tương tự; local đã chạy xong.
2. Muốn kiểm tra F0 chính xác theo khung, cần chuỗi F0 chuẩn kèm quy tắc chia khung; 3GT chỉ chấm tổng thể.
3. Muốn biết có “ăn may” trên test hay không, cần thêm nhiều file/người nói và một bộ test mới giữ kín tới cuối.
4. Giữ các bản không năng lượng để đối chiếu, nhưng khi báo cáo phải nêu lỗi SIL và đánh đổi recall/count còn tồn tại.

Kết luận thực hành: cải tiến đã giảm sai số trên chính train như yêu cầu, và test hiện tại cũng tốt hơn sau khi khóa cấu hình.
Bằng chứng mạnh nhất là waveform và các ablation cùng dữ liệu, kèm validation theo file;
điểm test cao của tám WAV ngắn không đủ để tuyên bố hệ thống đã xử lý mọi tình huống pitch.
''']
    report = '\n'.join(lines).strip() + '\n'
    (ROOT / filename).write_text(report, encoding='utf-8')
    (HERE / filename).write_text(report.replace(root_figure, 'figures/'), encoding='utf-8')
    timeline = ROOT / 'BAO_CAO_SU_KIEN_BT2_2026-10-05.md'
    shutil.copy2(timeline, HERE / timeline.name)
    outputs_dir = HERE / 'deliverables' / 'executed_local'
    outputs_dir.mkdir(exist_ok=True)
    for path in (ROOT / 'improved-training-only' / 'executed_local').glob('*.ipynb'):
        shutil.copy2(path, outputs_dir / path.name)
    record('Hoàn thành phân tích chuyên sâu và bảng báo cáo', 'Đã viết báo cáo nguyên nhân, 234 cấu hình, validation, bảng train/test từng pipeline và mọi đánh đổi.',
           'Chuẩn bị kiểm tra hình cuối cùng và lưu checkpoint bàn giao; không tiếp tục tối ưu theo test.')
    print(ROOT / filename)


if __name__ == '__main__':
    main()
