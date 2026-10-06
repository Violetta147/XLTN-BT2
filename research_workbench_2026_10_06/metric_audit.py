import json
from pathlib import Path

import numpy as np
import pandas as pd

import audit

HERE = Path(__file__).resolve().parent


def main():
    profile = pd.read_csv(HERE / 'results/training_data_profile.csv')
    counts = profile[['file', 'v_frames', 'gt_count']].copy()
    counts['center_v_minus_3gt'] = counts.v_frames - counts.gt_count
    counts['count_mape_if_perfect_center_v_and_finite_f0'] = 100 * abs(counts.center_v_minus_3gt) / counts.gt_count
    p_counts = audit.csv_write('count_protocol_diagnostic.csv', counts)
    reference = np.array([100., 120., 160., 200., 240., 220.])
    reversed_pitch = reference[::-1].copy()
    assert np.isclose(reference.mean(), reversed_pitch.mean())
    assert np.isclose(reference.std(), reversed_pitch.std())
    assert len(reference) == len(reversed_pitch)
    frames = pd.DataFrame({'synthetic_index': np.arange(len(reference)), 'reference_hz': reference,
                           'permuted_estimate_hz': reversed_pitch,
                           'absolute_error_hz': abs(reference - reversed_pitch),
                           'frame_mape_percent': 100 * abs(reference - reversed_pitch) / reference,
                           'absolute_cents': abs(1200 * np.log2(reversed_pitch / reference))})
    p_example = audit.csv_write('synthetic_metric_counterexample.csv', frames)
    summary = {'scope': 'Synthetic conceptual counterexample; not an error measurement on recorded speech',
               'reference_mean_hz': float(reference.mean()), 'reference_std_hz_ddof0': float(reference.std()),
               'permuted_mean_hz': float(reversed_pitch.mean()), 'permuted_std_hz_ddof0': float(reversed_pitch.std()),
               'reference_count': len(reference), 'permuted_count': len(reversed_pitch),
               'file_stats_average_mape_percent': 0., 'synthetic_frame_mape_percent': float(frames.frame_mape_percent.mean()),
               'synthetic_frame_mae_hz': float(frames.absolute_error_hz.mean()),
               'synthetic_mean_absolute_cents': float(frames.absolute_cents.mean())}
    audit.json_write(HERE / 'results/metric_counterexample_summary.json', summary)
    fig, axes = audit.plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot(frames.synthetic_index, reference, 'o-', label='synthetic reference')
    axes[0].plot(frames.synthetic_index, reversed_pitch, 's--', label='reordered estimate')
    axes[0].set(xlabel='Synthetic frame index', ylabel='F0 (Hz)', title='Same mean/std/count, different trajectory')
    axes[0].legend(fontsize=8)
    axes[1].bar(['mean', 'std', 'count'], [0., 0., 0.], color='#178f72')
    axes[1].set(ylim=(0, 100), ylabel='Relative error (%)', title='File statistics cannot identify frame accuracy')
    axes[1].axhline(summary['synthetic_frame_mape_percent'], color='#c95847', ls='--', label='known synthetic frame MAPE')
    axes[1].legend(fontsize=8)
    audit.save_figure('15_metric_identifiability', fig, [p_example], 'Phản ví dụ tổng hợp: hoán vị F0 giữ mean/std/count nhưng đổi từng khung.', 'Không phải số đo frame error của WAV thật; metric chính giữ nguyên.')
    fig, axes = audit.plt.subplots(1, 2, figsize=(11, 4))
    x = np.arange(len(counts))
    axes[0].bar(x - .18, counts.v_frames, .36, label='manual center V labels')
    axes[0].bar(x + .18, counts.gt_count, .36, label='3GT reference count')
    axes[0].set_xticks(x, counts.file.str.replace('.wav', '', regex=False), rotation=30, ha='right')
    axes[0].set(ylabel='Frame count', title='Two reference counts have different protocols')
    axes[0].legend(fontsize=8)
    axes[1].bar(x, counts.count_mape_if_perfect_center_v_and_finite_f0, color='#c95847')
    axes[1].set_xticks(x, counts.file.str.replace('.wav', '', regex=False), rotation=30, ha='right')
    axes[1].set(ylabel='Count component MAPE (%)', title='Conditional count error under perfect center-V mask')
    audit.save_figure('16_count_protocol', fig, [p_counts], 'So sánh count3GT với số V theo center-labels.', 'Chỉ khi mỗi center-V đều có F0 hữu hạn; không phải bound cho mọi thuật toán, không chứng minh LAB sai.')
    for figure in audit.ARTIFACTS:
        figure['generator'] = 'metric_audit.py'
        figure['generator_sha256'] = audit.digest(__file__)
        figure['command'] = 'python research_workbench_2026_10_06/metric_audit.py'
    audit.json_write(HERE / 'results/metric_figure_manifest.json', {'figures': audit.ARTIFACTS})
    report = ['# H00b — đọc đúng metric và hai nguồn count', '',
              '## Kết quả có thể kiểm tra', '', audit.markdown_table(counts), '',
              'Nếu phân loại đúng mọi center-V và giữ F0 hữu hạn ở từng khung đó, count MAPE vẫn khác 0 vì count3GT dùng protocol chưa rõ. Đây không phải lower bound cho model nói chung: model có thể đổi count bằng FP/FN hoặc F0 không hữu hạn.', '',
              'Không sửa LAB, không thay metric chính. Cần biết cách tạo3GT: frame/hop/offset, điều kiện voiced/F0 hợp lệ, loại bỏ khung biên, nguồn annotation và quy tắc đếm. Hiện chưa có metadata để kết luận nguyên nhân.', '',
              '## Phản ví dụ tổng hợp', '', '~~~json', json.dumps(summary, indent=2, ensure_ascii=False), '~~~', '',
              'Hoán vị giữ nguyên tập giá trị, nên mean/std/count không đổi. F0 đúng từng thời điểm vẫn là câu hỏi khác. Giảm MAPE thống kê hữu ích cho yêu cầu bài này nhưng không thay thế đánh giá pitch từng khung.', '',
              'Frame error trong ví dụ này tính được vì chúng ta tự sinh reference; chưa có reference tương đương để tính trên WAV train thật.', '',
              '## Figures', '', '![Synthetic counterexample](figures/15_metric_identifiability.png)', '',
              '![Count protocols](figures/16_count_protocol.png)', '',
              '## Tái lập', '', '~~~powershell', 'python research_workbench_2026_10_06/metric_audit.py', '~~~']
    (HERE / 'H00B_METRIC_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
