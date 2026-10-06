import json
from pathlib import Path

import numpy as np
import pandas as pd

import audit
import core
from estimator_experiment import eligibility

HERE = Path(__file__).resolve().parent


def majority_mask(raw, energy):
    windows = np.lib.stride_tricks.sliding_window_view(np.pad(raw.astype(int), (1, 1)), 3)
    return (windows.sum(axis=1) >= 2) & energy


def infer(item, config, fitted):
    energy = item['relative_rms'] >= fitted['energy_threshold']
    raw = (item['ACF_score'] >= fitted['pitch_threshold']) & energy
    mask = majority_mask(raw, energy)
    adapter = dict(item, ACF_score=np.where(mask, 1., -1.))
    pred, f0 = core.infer(adapter, config, dict(fitted, pitch_threshold=.5))
    assert np.array_equal(pred, mask)
    return pred, f0


def main():
    assert np.array_equal(majority_mask(np.array([0, 1, 1, 0, 1, 1, 0], bool), np.ones(7, bool)), [0, 1, 1, 1, 1, 1, 0])
    assert not majority_mask(np.array([0, 0, 1, 0, 0], bool), np.ones(5, bool)).any()
    assert not majority_mask(np.array([1, 0, 1], bool), np.array([1, 0, 1], bool))[1]
    items = core.load_training()
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['ACF']['config']
    rows, changes = [], []
    for split in ('train', 'lofo'):
        for item in items:
            training = items if split == 'train' else [x for x in items if x is not item]
            fitted = core.fit(training, config)
            original_pred, original_f0 = core.infer(item, config, fitted)
            new_pred, new_f0 = infer(item, config, fitted)
            for model, pred, f0 in [('accepted', original_pred, original_f0), ('candidate', new_pred, new_f0)]:
                rows.append({'split': split, 'model': model, **core.score_file(item, pred, f0)})
            for i in np.flatnonzero(original_pred != new_pred):
                changes.append({'split': split, 'file': item['file'], 'time_s': item['times'][i], 'label': item['labels'][i],
                                'boundary': bool(item['boundary'][i]), 'before_voiced': bool(original_pred[i]), 'after_voiced': bool(new_pred[i]),
                                'change': 'added' if new_pred[i] else 'removed'})
    frame = pd.DataFrame(rows)
    change_frame = pd.DataFrame(changes)
    p_metrics = audit.csv_write('mask_vote_metrics.csv', frame)
    p_changes = audit.csv_write('mask_vote_changed_frames.csv', change_frame)
    change_counts = change_frame.groupby(['split', 'label', 'boundary', 'change']).size().reset_index(name='frames')
    p_counts = audit.csv_write('mask_vote_changes_summary.csv', change_counts)
    summaries = {model: {split: core.summarize(frame[(frame.model == model) & (frame.split == split)]) for split in ('train', 'lofo')} for model in ('accepted', 'candidate')}
    decision = eligibility(frame, summaries)
    poisoned = dict(items[0], labels=np.full(len(items[0]['labels']), 'unknown'), stats={'F0mean': -1, 'F0std': -1, 'F0num': -1})
    original = infer(items[0], config, core.fit(items, config))
    actual = infer(poisoned, config, core.fit(items, config))
    assert np.array_equal(original[0], actual[0]) and np.allclose(original[1], actual[1], equal_nan=True)
    audit.json_write(HERE / 'results/mask_vote_experiment.json', {'decision': decision, 'summaries': summaries,
                     'toy_assertions_pass': True, 'poisoned_gt_inference_invariant': True, 'train_only': True,
                     'code_sha256': audit.digest(__file__)})
    fig, axes = audit.plt.subplots(1, 2, figsize=(11, 4))
    for ax, split in zip(axes, ('train', 'lofo')):
        group = change_frame[change_frame.split == split].groupby(['label', 'change']).size().unstack(fill_value=0)
        x = np.arange(len(group))
        for j, change in enumerate(('added', 'removed')):
            ax.bar(x + (j - .5) * .35, group.get(change, pd.Series(0, index=group.index)), .35, label=change)
        ax.set_xticks(x, group.index)
        ax.set(ylabel='Changed mask frames', title=split + ': minority gaps versus short events')
    axes[0].legend(fontsize=8)
    audit.save_figure('mask_vote_changes', fig, [p_changes, p_counts], 'Khung hữu thanh được thêm/bỏ bởi majority3, báo theo nhãn thật.', 'Các frame chồng nhau; đây là thay đổi decision, không chứng minh cao độ các khung thêm đã đúng.')
    for figure in audit.ARTIFACTS:
        figure['generator'] = 'mask_vote_experiment.py'
        figure['generator_sha256'] = audit.digest(__file__)
        figure['command'] = 'python research_workbench_2026_10_06/mask_vote_experiment.py'
    audit.json_write(HERE / 'results/mask_vote_figure_manifest.json', {'figures': audit.ARTIFACTS})
    summary = pd.DataFrame([{'split': split, 'model': model, **value} for model, parts in summaries.items() for split, value in parts.items()])
    report = ['# H14 — majority3 voiced mask', '', audit.markdown_table(summary), '',
              '## Thay đổi frame', '', audit.markdown_table(change_counts), '',
              '## Gate', '', '~~~json', json.dumps(decision, indent=2), '~~~', '',
              '![Mask changes](figures/mask_vote_changes.png)', '',
              'Median mask thay quyết định V/UV, khác median pitch giữ mask. Thêm frame có thể làm path nối và đổi F0 trong run; không sửa theo GTstats. Giữ champion nếu fail.', '',
              '~~~powershell', 'python research_workbench_2026_10_06/mask_vote_experiment.py', '~~~']
    (HERE / 'MASK_VOTE_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps(decision, indent=2), flush=True)
    print(summary[['split','model','average_mape','F0std_mape','recall_v','macro_f1','false_voiced_sil']].to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
