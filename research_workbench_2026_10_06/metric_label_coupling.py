from pathlib import Path

import numpy as np
import pandas as pd

import audit

HERE = Path(__file__).resolve().parent


def main():
    frame = pd.read_csv(HERE / 'results/hysteresis_influence_frames.csv')
    diagnostic = pd.read_csv(HERE / 'results/voicing_failure_reasons.csv')
    stats, changes = [], []
    for (split, file), group in frame.groupby(['split', 'file']):
        for model, column in [('accepted', 'old_f0_hz'), ('hysteresis', 'new_f0_hz')]:
            all_values = group[column].dropna().to_numpy()
            mean, variance = all_values.mean(), all_values.var()
            contribution_sum = 0.
            for label in ('v', 'uv', 'sil'):
                values = group.loc[group.label == label, column].dropna().to_numpy()
                n = len(values)
                within = n / len(all_values) * values.var() if n else 0.
                between = n / len(all_values) * (values.mean() - mean) ** 2 if n else 0.
                contribution_sum += within + between
                stats.append({'split': split, 'file': file, 'model': model, 'center_label': label,
                              'finite_estimate_count': n, 'group_mean_hz': float(values.mean()) if n else np.nan,
                              'group_std_hz': float(values.std()) if n else np.nan,
                              'within_variance_contribution_hz2': within, 'between_variance_contribution_hz2': between,
                              'total_variance_contribution_hz2': within + between,
                              'all_estimates_std_hz': float(all_values.std()),
                              'contribution_fraction': (within + between) / variance if variance else np.nan,
                              'oracle_label_filter': True})
            assert np.isclose(contribution_sum, variance, rtol=1e-9, atol=1e-9)
        changed_nonv = group[(group.label != 'v') & group.shared_estimate_changed]
        for _, row in changed_nonv.iterrows():
            source_split = 'lofo' if split == 'nested' else split
            reference = diagnostic[(diagnostic.split == source_split) & (diagnostic.file == file) & np.isclose(diagnostic.time_s, row.time_s, atol=1e-9)]
            assert len(reference) == 1
            changes.append({'split': split, 'file': file, 'time_s': row.time_s, 'center_label': row.label,
                            'old_estimated_hz': row.old_f0_hz, 'new_estimated_hz': row.new_f0_hz,
                            'v_overlap_fraction_in_window': reference.v_overlap_fraction.iloc[0],
                            'old_mask': row.old_pred, 'new_mask': row.new_pred,
                            'pitch_truth_known': False})
    p_stats = audit.csv_write('label_variance_hysteresis.csv', stats)
    p_changes = audit.csv_write('nonv_estimate_context_changes.csv', changes)
    stats_df = pd.DataFrame(stats)
    data = stats_df[(stats_df.split == 'train') & (stats_df.file == 'phone_F1.wav')]
    fig, axes = audit.plt.subplots(1, 2, figsize=(11, 4))
    models = ['accepted', 'hysteresis']
    bottom = np.zeros(2)
    for label in ('v', 'uv', 'sil'):
        plot = data[data.center_label == label].set_index('model').reindex(models)
        axes[0].bar(models, plot.total_variance_contribution_hz2, bottom=bottom, color=audit.PALETTE[label], label=label)
        bottom += plot.total_variance_contribution_hz2.to_numpy()
    axes[0].set(title='phone_F1 train: all-estimate variance by center label', ylabel='Contribution (Hz²)')
    axes[0].legend(fontsize=8)
    v = stats_df[(stats_df.center_label == 'v') & (stats_df.file == 'phone_F1.wav')]
    for model in models:
        plot = v[v.model == model].set_index('split').reindex(['train', 'lofo', 'nested'])
        axes[1].plot(plot.index, plot.group_std_hz, 'o-', label=model)
    axes[1].set(title='Oracle true-center-V subset (diagnostic only)', ylabel='Estimated F0 std within V frames (Hz)')
    axes[1].legend(fontsize=8)
    audit.save_figure('metric_label_coupling', fig, [p_stats, p_changes], 'Variance contribution và true-center-V subset tách metric gain do non-V estimates.', 'Oracle dùng nhãn để phân tích, không triển khai; không có frameF0truth. Mixed boundary windows có thể chứa một phầnV.')
    for figure in audit.ARTIFACTS:
        figure['generator'] = 'metric_label_coupling.py'
        figure['generator_sha256'] = audit.digest(__file__)
        figure['command'] = 'python research_workbench_2026_10_06/metric_label_coupling.py'
    audit.json_write(HERE / 'results/metric_label_coupling_manifest.json', {'figures': audit.ARTIFACTS, 'variance_identity_verified': True})
    report = ['# Metric gain có thể chứa tác động từ khung không phải V', '',
              '## Phát hiện quan trọng', '',
              'Trên phone_F1 train, hai center-UV vẫn bị dự đoán V nhưng estimate đổi từ khoảng71.608/82.785Hz lên247.050/240.541Hz. Chúng không trở thành true-positive V; error class vẫn làUV→V. Đổi context làm distribution gần file3GT, giảm stdMAPE, nhưng không chứng minh các F0 ấy đúng.', '',
              'Center-UV không đồng nghĩa toàn bộ25ms chứa0%V. Bảng dưới báo overlap đúng theo LAB; không suy diễn mỗi trường hợp là một âm vô thanh thuần hoặc có F0 chuẩn đã biết.', '',
              audit.markdown_table(pd.DataFrame(changes)), '',
              '## Variance theo nhãn', '', audit.markdown_table(data), '',
              '## Cách diễn giải H12', '',
              '- Gates đăng ký trước vẫn PASS trên metric và V/UV; không đổi kết quả hoặc criterion sau khi xem dữ liệu.',
              '- Hysteresis train thêm18V+2UV, nested thêm17V+2UV, SIL không tăng. Đây là gain classification có nhãn xác minh và tradeoff còn lại.',
              '- Không gọi phần giảm std chủ yếu ở train phone_F1 là sửa F0 ở khung V: phần đó chịu ảnh hưởng mạnh từ estimates trênUV false positives.',
              '- H12 vẫn provisional; không thay champion chỉ vì metric cực thấp. Cần báo phân loại, distribution và giới hạn reference cùng nhau.',
              '- Oracle true-V subset là diagnostic dùng nhãn, không là pipeline deploy hay label adjustment. Count/stat3GT protocol chưa rõ, không thay metric chính.', '',
              '![Metric and labels](figures/metric_label_coupling.png)', '',
              '~~~powershell', 'python research_workbench_2026_10_06/metric_label_coupling.py', '~~~']
    (HERE / 'METRIC_LABEL_COUPLING_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(pd.DataFrame(changes).to_string(index=False))
    print(data[['model','center_label','group_std_hz','total_variance_contribution_hz2','contribution_fraction']].to_string(index=False))


if __name__ == '__main__':
    main()
