import json
from pathlib import Path

import numpy as np
import pandas as pd

import audit
import core

HERE = Path(__file__).resolve().parent


def main():
    items = core.load_training()
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['ACF']['config']
    rows = []
    for split in ('train', 'lofo'):
        for item in items:
            training = items if split == 'train' else [x for x in items if x is not item]
            fitted = core.fit(training, config)
            pred, _ = core.infer(item, config, fitted)
            pitch_pass = item['ACF_score'] >= fitted['pitch_threshold']
            energy_pass = item['relative_rms'] >= fitted['energy_threshold']
            assert np.array_equal(pred, pitch_pass & energy_pass)
            previous = np.r_[False, pred[:-1]]
            following = np.r_[pred[1:], False]
            width = item['frame_ms'] / 1000
            for i, center in enumerate(item['times']):
                a, b = center - width / 2, center + width / 2
                fractions = {label: sum(max(0., min(b, right) - max(a, left)) for left, right, value in item['segments'] if value == label) / width for label in ('v', 'uv', 'sil')}
                reason = 'both_fail' if not pitch_pass[i] and not energy_pass[i] else ('pitch_only_fail' if not pitch_pass[i] else ('energy_only_fail' if not energy_pass[i] else 'both_pass'))
                rows.append({'split': split, 'file': item['file'], 'time_s': center, 'label': item['labels'][i],
                             'boundary': bool(item['boundary'][i]), 'pred_voiced': bool(pred[i]), 'reason': reason,
                             'pitch_margin': item['ACF_score'][i] - fitted['pitch_threshold'],
                             'energy_margin': item['relative_rms'][i] - fitted['energy_threshold'],
                             'previous_voiced': bool(previous[i]), 'following_voiced': bool(following[i]),
                             'isolated_mask_gap': bool(not pred[i] and previous[i] and following[i]),
                             'v_overlap_fraction': fractions['v'], 'uv_overlap_fraction': fractions['uv'],
                             'sil_overlap_fraction': fractions['sil']})
    frame = pd.DataFrame(rows)
    p_frames = audit.csv_write('voicing_failure_reasons.csv', frame)
    misses = frame[(frame.label == 'v') & ~frame.pred_voiced]
    reasons = misses.groupby(['split', 'boundary', 'reason']).size().reset_index(name='false_negative_frames')
    p_reasons = audit.csv_write('voicing_fn_reason_summary.csv', reasons)
    neighbors = misses.groupby(['split', 'boundary']).agg(fn=('time_s', 'size'), isolated_mask_gaps=('isolated_mask_gap', 'sum'), previous_voiced=('previous_voiced', 'sum'), following_voiced=('following_voiced', 'sum')).reset_index()
    p_neighbors = audit.csv_write('voicing_fn_neighbors.csv', neighbors)
    mixtures = frame.groupby(['split', 'label', 'boundary']).agg(frames=('time_s', 'size'), mean_v_fraction=('v_overlap_fraction', 'mean'), mean_uv_fraction=('uv_overlap_fraction', 'mean'), mean_sil_fraction=('sil_overlap_fraction', 'mean')).reset_index()
    p_mixtures = audit.csv_write('window_label_overlap.csv', mixtures)
    fig, axes = audit.plt.subplots(1, 2, figsize=(11, 4))
    for ax, split in zip(axes, ('train', 'lofo')):
        table = reasons[reasons.split == split].pivot(index='boundary', columns='reason', values='false_negative_frames').fillna(0)
        bottom = np.zeros(len(table))
        for reason in table.columns:
            ax.bar(np.arange(len(table)), table[reason], bottom=bottom, label=reason)
            bottom += table[reason].to_numpy()
        ax.set_xticks(np.arange(len(table)), ['boundary' if x else 'interior' for x in table.index])
        ax.set(title=split + ': which decision conditions fail?', ylabel='V frames predicted UV')
    axes[0].legend(fontsize=8)
    audit.save_figure('17_voicing_failure_reasons', fig, [p_reasons], 'Tách FN hữu thanh theo điều kiện ACF/RMS thất bại.', 'Điều kiện logic trực tiếp; không suy diễn nguyên nhân sinh lý/phoneme.')
    fig, axes = audit.plt.subplots(1, 2, figsize=(11, 4))
    for ax, split in zip(axes, ('train', 'lofo')):
        data = frame[(frame.split == split) & (frame.label == 'v')]
        for pred, label, color in [(True, 'V detected', '#178f72'), (False, 'V missed', '#c95847')]:
            subset = data[data.pred_voiced == pred]
            ax.scatter(subset.v_overlap_fraction, subset.pitch_margin, s=12, alpha=.55, label=label, color=color)
        ax.axhline(0, color='black', lw=.8)
        ax.set(xlabel='Actual V overlap fraction within frame', ylabel='ACF score minus fold threshold', title=split + ': mixed frames and score')
    axes[0].legend(fontsize=8)
    audit.save_figure('18_overlap_vs_voicing', fig, [p_frames], 'Tỷ lệ V trong cửa sổ và khoảng cách ngưỡng ACF.', 'Nhãn chính vẫn center-label; chỉ chẩn đoán window mixing, không đổi label để tăng score.')
    for figure in audit.ARTIFACTS:
        figure['generator'] = 'voicing_diagnostic.py'
        figure['generator_sha256'] = audit.digest(__file__)
        figure['command'] = 'python research_workbench_2026_10_06/voicing_diagnostic.py'
    audit.json_write(HERE / 'results/voicing_diagnostic_manifest.json', {'figures': audit.ARTIFACTS})
    report = ['# Chẩn đoán V bị bỏ sót trước H12', '',
              'Cùng accepted ACF và fold fit. Chỉ đọc train. Không đổi nhãn hoặc metric. Boundary là tâm cách endpoint nhỏ hơn half-window.', '',
              '## Điều kiện thất bại', '', audit.markdown_table(reasons), '',
              '## Hàng xóm thời gian', '', audit.markdown_table(neighbors), '',
              '## Cửa sổ trộn nhãn', '', audit.markdown_table(mixtures), '',
              'Đây là logical failure attribution: score thấp, RMS thấp hoặc cả hai. Nó không xác định phoneme, không chứng minh label sai, không có frame pitch GT. Hysteresis chỉ cứu được một số score thấp gần voiced run nếu vẫn pass RMS; không cứu mọi FN.', '',
              '![Failure conditions](figures/17_voicing_failure_reasons.png)', '',
              '![Mixed windows](figures/18_overlap_vs_voicing.png)', '',
              '~~~powershell', 'python research_workbench_2026_10_06/voicing_diagnostic.py', '~~~']
    (HERE / 'VOICING_DIAGNOSTIC_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(reasons.to_string(index=False))
    print(neighbors.to_string(index=False))


if __name__ == '__main__':
    main()
