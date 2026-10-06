import json
from pathlib import Path

import numpy as np
import pandas as pd

import audit
import core
import hysteresis_experiment as hysteresis

HERE = Path(__file__).resolve().parent


def main():
    items = core.load_training()
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['ACF']['config']
    choices = pd.read_csv(HERE / 'results/hysteresis_outer_selections.csv')
    expected = pd.read_csv(HERE / 'results/hysteresis_metrics.csv')
    metrics, frames, effects, label_rows = [], [], [], []
    for split in ('train', 'lofo', 'nested'):
        for item in items:
            training = items if split == 'train' else [x for x in items if x is not item]
            fitted = core.fit(training, config)
            margin = choices[(choices.split == split) & (choices.held_file == item['file'])].margin.iloc[0]
            old_pred, old_f0 = core.infer(item, config, fitted)
            new_pred, new_f0 = hysteresis.infer(item, config, fitted, margin)
            assert np.all(new_pred[old_pred])
            hybrid = old_f0.copy()
            added = new_pred & ~old_pred
            hybrid[added] = new_f0[added]
            variants = {'accepted': (old_pred, old_f0), 'append_only_diagnostic': (new_pred, hybrid),
                        'hysteresis': (new_pred, new_f0),
                        'accepted_without_pitch_median': core.infer(item, dict(config, median=1), fitted),
                        'hysteresis_without_pitch_median': hysteresis.infer(item, dict(config, median=1), fitted, margin)}
            scored = {}
            for variant, (pred, f0) in variants.items():
                row = core.score_file(item, pred, f0)
                metrics.append({'split': split, 'variant': variant, 'margin': margin, **row})
                scored[variant] = row
            saved = expected[(expected.split == split) & (expected.file == item['file'])]
            assert np.isclose(scored['accepted']['average_mape'], saved[saved.model == 'accepted'].average_mape.iloc[0], atol=1e-8)
            assert np.isclose(scored['hysteresis']['average_mape'], saved[saved.model == 'candidate'].average_mape.iloc[0], atol=1e-8)
            shared = np.isfinite(old_f0) & np.isfinite(new_f0)
            changed = shared & (abs(new_f0 - old_f0) > 1e-6)
            effects.append({'split': split, 'file': item['file'], 'margin': margin,
                            'added_mask_frames': int(added.sum()), 'removed_mask_frames': int((old_pred & ~new_pred).sum()),
                            'shared_finite_frames': int(shared.sum()), 'shared_f0_changed_frames': int(changed.sum()),
                            'shared_estimate_change_mae_hz': float(np.mean(abs(new_f0[shared] - old_f0[shared]))),
                            'accepted_std_hz': scored['accepted']['F0std'], 'append_only_std_hz': scored['append_only_diagnostic']['F0std'],
                            'full_hysteresis_std_hz': scored['hysteresis']['F0std'],
                            'gt_std_hz': item['stats']['F0std']})
            for label in ('v', 'uv', 'sil'):
                label_rows.append({'split': split, 'file': item['file'], 'label': label,
                                   'added_mask_frames': int((added & (item['labels'] == label)).sum()),
                                   'shared_f0_changed_frames': int((changed & (item['labels'] == label)).sum())})
            for i in range(len(old_f0)):
                frames.append({'split': split, 'file': item['file'], 'time_s': item['times'][i], 'label': item['labels'][i],
                               'boundary': bool(item['boundary'][i]), 'acf_score': item['ACF_score'][i],
                               'relative_rms': item['relative_rms'][i], 'onset_threshold': fitted['pitch_threshold'],
                               'offset_threshold': fitted['pitch_threshold'] - margin,
                               'old_pred': bool(old_pred[i]), 'new_pred': bool(new_pred[i]),
                               'added_frame': bool(added[i]), 'shared_estimate_changed': bool(changed[i]),
                               'old_f0_hz': old_f0[i], 'new_f0_hz': new_f0[i], 'append_only_diagnostic_hz': hybrid[i]})
    p_metrics = audit.csv_write('hysteresis_influence_metrics.csv', metrics)
    p_frames = audit.csv_write('hysteresis_influence_frames.csv', frames)
    p_effects = audit.csv_write('hysteresis_influence_effects.csv', effects)
    p_labels = audit.csv_write('hysteresis_influence_labels.csv', label_rows)
    effects_df, frame_df = pd.DataFrame(effects), pd.DataFrame(frames)
    fig, axes = audit.plt.subplots(1, 3, figsize=(13, 4))
    for ax, split in zip(axes, ('train', 'lofo', 'nested')):
        data = effects_df[effects_df.split == split]
        x = np.arange(len(data))
        for j, (column, title) in enumerate([('accepted_std_hz', 'accepted'), ('append_only_std_hz', 'append-only diagnostic'), ('full_hysteresis_std_hz', 'full hysteresis')]):
            ax.bar(x + (j - 1) * .23, data[column], .23, label=title)
        ax.plot(x, data.gt_std_hz, 'kx', ms=7, label='3GT std')
        ax.set_xticks(x, data.file.str.replace('.wav', '', regex=False), rotation=35, ha='right')
        ax.set(title=split, ylabel='File F0 std (Hz)')
    axes[0].legend(fontsize=7)
    audit.save_figure('hysteresis_influence_std', fig, [p_effects], 'Tách thêm khung và tái tính F0 trong voiced run.', 'Append-only là counterfactual diagnostic dùng estimate, không deploy và không biết pitch thật từng frame.')
    fig, axes = audit.plt.subplots(4, 1, figsize=(11, 9))
    for ax, item in zip(axes, items):
        data = frame_df[(frame_df.split == 'train') & (frame_df.file == item['file'])]
        ax.plot(data.time_s, data.acf_score, color='#344b69', label='ACF score')
        ax.plot(data.time_s, data.onset_threshold, '--', color='gray', label='onset threshold')
        ax.plot(data.time_s, data.offset_threshold, '--', color='#c95847', label='offset threshold')
        for i in data[data.added_frame].index:
            row = data.loc[i]
            ax.axvspan(row.time_s - .005, row.time_s + .005, color='#178f72' if row.label == 'v' else '#dd9c22', alpha=.25)
        ax.set(title=item['file'] + ': train decisions (green added V; orange added non-V)', ylabel='ACF score')
    axes[0].legend(fontsize=7)
    axes[-1].set_xlabel('Time (s)')
    audit.save_figure('hysteresis_threshold_events', fig, [p_frames], 'Các khung được thêm khi score ở giữa onset/offset và run còn active.', 'Score curve không phải probability; RMSfail vẫn reset, không cứu mọi onsetFN.')
    fig, axes = audit.plt.subplots(1, 2, figsize=(11, 4))
    label_counts = pd.DataFrame(label_rows).groupby(['split', 'label']).added_mask_frames.sum().unstack(fill_value=0)
    x = np.arange(len(label_counts))
    bottom = np.zeros(len(x))
    for label in ('v', 'uv', 'sil'):
        axes[0].bar(x, label_counts[label], bottom=bottom, label=label, color=audit.PALETTE[label])
        bottom += label_counts[label].to_numpy()
    axes[0].set_xticks(x, label_counts.index)
    axes[0].set(title='New mask frames: true segment labels', ylabel='Frame count')
    axes[0].legend(fontsize=8)
    for split, group in effects_df.groupby('split'):
        axes[1].plot(group.file.str.replace('.wav', '', regex=False), group.shared_f0_changed_frames, 'o-', label=split)
    axes[1].set(title='Old voiced frames with recomputed F0', ylabel='Changed estimate frames')
    axes[1].tick_params(axis='x', rotation=30)
    axes[1].legend(fontsize=8)
    audit.save_figure('hysteresis_added_and_context', fig, [p_labels, p_effects], 'Hysteresis thêm frame và đổi context F0 ở frame cũ.', 'Estimate thay đổi không đồng nghĩa error đã sửa đúng; chỉ V/UV/SIL được xác minh từ LAB.')
    for figure in audit.ARTIFACTS:
        figure['generator'] = 'hysteresis_influence.py'
        figure['generator_sha256'] = audit.digest(__file__)
        figure['command'] = 'python research_workbench_2026_10_06/hysteresis_influence.py'
    audit.json_write(HERE / 'results/hysteresis_influence_manifest.json', {'figures': audit.ARTIFACTS,
                     'reproduced_h12_metrics': True, 'selection_repeated': False, 'test_read': False})
    report = ['# H12 — vì sao thay mask còn làm F0std đổi?', '',
              'Đọc lại đúng margin đã chọn và fold fit H12, không chọn tham số mới. Reproduce MAPE train/selectedLOFO/nested khớp1e-8. Không đọctest.', '',
              '## Hai tác động cần tách', '',
              '1. Thêm frame: append-only diagnostic giữ F0 accepted ở frame cũ, thêm F0 từ candidate ở frame vừa có mask. Count/distribution đổi chỉ vì tập estimate thay đổi.',
              '2. Đổi context: full hysteresis tái chạy path và median trên voiced runs dài/nối lại. F0 ở cả những frame cũ có thể đổi. Chênh so với append-only cho thấy phần này.', '',
              'Append-only không phải algorithm cạnh tranh; không sử dụng để chọn/push model, không chứng minh ground-truth pitch. Hai hiệu ứng không phải các đại lượng additive đơn giản vì std/MAPE là nonlinear.', '',
              audit.markdown_table(effects_df), '',
              '## Nhãn của frame được thêm', '', audit.markdown_table(pd.DataFrame(label_rows)), '',
              'Giảm std error có thể do sửa candidate path hoặc do distribution vô tình khớp3GT; thiếu frameF0truth nên chưa phân biệt chắc chắn. LAB xác minh được lớpV/UV/SIL của các frame thêm, không xác minh pitchHz.', '',
              '## Figures', '', '![Std influence](figures/hysteresis_influence_std.png)', '',
              '![Threshold events](figures/hysteresis_threshold_events.png)', '',
              '![Added/context](figures/hysteresis_added_and_context.png)', '',
              '~~~powershell', 'python research_workbench_2026_10_06/hysteresis_influence.py', '~~~']
    (HERE / 'HYSTERESIS_MECHANISM_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(effects_df.to_string(index=False))
    print(label_counts.to_string())


if __name__ == '__main__':
    main()
