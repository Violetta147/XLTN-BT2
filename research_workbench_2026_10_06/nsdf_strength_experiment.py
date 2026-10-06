import json
from pathlib import Path

import numpy as np
import pandas as pd

import audit
import core
import mpm_estimator
from estimator_experiment import eligibility

HERE = Path(__file__).resolve().parent


def replacement(item):
    fs, audio = core.load_audio(core.TRAIN / item['file'])
    frames = np.lib.stride_tricks.sliding_window_view(audio, round(fs * .025))[::round(fs * .010)]
    strengths = item['ACF_candidate_strength'].copy()
    rows = []
    for i, frame in enumerate(frames):
        valid = np.isfinite(item['ACF_candidate_f0'][i])
        candidates = item['ACF_candidate_f0'][i, valid]
        indices = np.rint(fs / candidates).astype(int)
        acf = core.ACF['normalized_acf'](frame)
        nsdf = mpm_estimator.nsdf_curve(frame)
        assert np.allclose(acf[indices], strengths[i, valid], atol=1e-8)
        original = strengths[i, valid].copy()
        strengths[i, valid] = nsdf[indices]
        for pitch, index, before, after in zip(candidates, indices, original, strengths[i, valid]):
            rows.append({'file': item['file'], 'time_s': item['times'][i], 'label': item['labels'][i],
                         'boundary': bool(item['boundary'][i]), 'candidate_f0_hz': pitch, 'integer_lag': int(index),
                         'acf_strength': before, 'nsdf_strength': after})
    result = dict(item, ACF_candidate_strength=strengths)
    assert np.array_equal(result['ACF_candidate_f0'], item['ACF_candidate_f0'], equal_nan=True)
    return result, rows


def main():
    items = core.load_training()
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['ACF']['config']
    transformed, quality_rows = {}, []
    for item in items:
        new, rows = replacement(item)
        transformed[item['file']] = new
        quality_rows += rows
    p_quality = audit.csv_write('nsdf_candidate_strengths.csv', quality_rows)
    rows, contour_rows = [], []
    for split in ('train', 'lofo'):
        for item in items:
            training = items if split == 'train' else [x for x in items if x is not item]
            fitted = core.fit(training, config)
            baseline_pred, _ = core.infer(item, config, fitted)
            for model in ('accepted', 'candidate'):
                source = item if model == 'accepted' else transformed[item['file']]
                pred, pitch = core.infer(source, config, fitted)
                assert np.array_equal(pred, baseline_pred)
                rows.append({'split': split, 'model': model, **core.score_file(item, pred, pitch)})
                if split == 'lofo':
                    for center, label, value in zip(item['times'], item['labels'], pitch):
                        contour_rows.append({'file': item['file'], 'time_s': center, 'label': label, 'model': model, 'estimated_hz': value})
    frame = pd.DataFrame(rows)
    p_metrics = audit.csv_write('nsdf_strength_metrics.csv', frame)
    p_contours = audit.csv_write('nsdf_strength_contours.csv', contour_rows)
    summaries = {model: {split: core.summarize(frame[(frame.model == model) & (frame.split == split)]) for split in ('train', 'lofo')} for model in ('accepted', 'candidate')}
    decision = eligibility(frame, summaries)
    poisoned = dict(transformed[items[0]['file']], labels=np.full(len(items[0]['labels']), 'unknown'), stats={'F0mean': -1, 'F0std': -1, 'F0num': -1})
    before = core.infer(transformed[items[0]['file']], config, core.fit(items, config))
    after = core.infer(poisoned, config, core.fit(items, config))
    assert np.array_equal(before[0], after[0]) and np.allclose(before[1], after[1], equal_nan=True)
    audit.json_write(HERE / 'results/nsdf_strength_experiment.json', {'summaries': summaries, 'decision': decision,
                     'candidate_f0_unchanged': True, 'voiced_mask_unchanged': True, 'cached_acf_strength_verified': True,
                     'poisoned_gt_inference_invariant': True, 'train_only': True,
                     'code_sha256': {name: audit.digest(HERE / name) for name in ('nsdf_strength_experiment.py', 'mpm_estimator.py')}})
    quality = pd.DataFrame(quality_rows)
    fig, axes = audit.plt.subplots(1, 2, figsize=(11, 4))
    positive = quality[(quality.acf_strength > 0) & (quality.label == 'v')]
    for boundary, color in [(False, '#178f72'), (True, '#c95847')]:
        group = positive[positive.boundary == boundary]
        axes[0].scatter(group.acf_strength, group.nsdf_strength, alpha=.3, s=8, color=color, label='boundary' if boundary else 'interior')
    axes[0].plot([0, 1], [0, 1], '--', color='gray')
    axes[0].set(xlabel='Normalized ACF candidate score', ylabel='Same-lag NSDF score', title='Arithmetic energy penalty on same candidates')
    axes[0].legend(fontsize=8)
    for model in ('accepted', 'candidate'):
        table = frame[(frame.model == model) & (frame.split == 'lofo')].set_index('file')
        axes[1].plot(table.index.str.replace('.wav', '', regex=False), table.average_mape, 'o-', label=model)
    axes[1].set(title='Held-file file-stat MAPE', ylabel='Average MAPE (%)')
    axes[1].tick_params(axis='x', rotation=30)
    axes[1].legend(fontsize=8)
    audit.save_figure('nsdf_strength_diagnostic', fig, [p_quality, p_metrics], 'Cùng lag candidates: thay energy normalization của strength và đo LOFO.', 'Không có F0 truth từng khung; score khác nhau không chứng minh pitch đúng.')
    fig, axes = audit.plt.subplots(4, 1, figsize=(11, 9))
    contours = pd.DataFrame(contour_rows)
    for ax, item in zip(axes, items):
        for model in ('accepted', 'candidate'):
            data = contours[(contours.file == item['file']) & (contours.model == model)]
            ax.plot(data.time_s, data.estimated_hz, '.', ms=3, label=model)
        ax.set(title=item['file'], ylabel='Estimated F0 (Hz)', ylim=(50, 430))
    axes[0].legend(fontsize=8)
    axes[-1].set_xlabel('Time (s)')
    audit.save_figure('nsdf_strength_contours', fig, [p_contours], 'Ảnh hưởng candidate strength tới path giữ cùng mask.', 'Đường F0 là estimate; tính đúng chỉ được kiểm tra trên file statistics.')
    for figure in audit.ARTIFACTS:
        figure['generator'] = 'nsdf_strength_experiment.py'
        figure['generator_sha256'] = audit.digest(__file__)
        figure['command'] = 'python research_workbench_2026_10_06/nsdf_strength_experiment.py'
    audit.json_write(HERE / 'results/nsdf_strength_figure_manifest.json', {'figures': audit.ARTIFACTS})
    table = pd.DataFrame([{'split': split, 'model': model, **summary} for model, parts in summaries.items() for split, summary in parts.items()])
    report = ['# H13 — strength NSDF trên cùng ACF candidates/path', '', audit.markdown_table(table), '',
              '~~~json', json.dumps(decision, indent=2), '~~~', '',
              'Giữ nguyên candidates/mask/threshold/path costs/median3; chỉ energy normalization strength thay đổi. Không gộp H12 hysteresis vào thí nghiệm này. Giữ champion và log failure nếu gates chưa đạt.', '',
              '![Quality](figures/nsdf_strength_diagnostic.png)', '', '![Contours](figures/nsdf_strength_contours.png)', '',
              '~~~powershell', 'python research_workbench_2026_10_06/nsdf_strength_experiment.py', '~~~']
    (HERE / 'NSDF_STRENGTH_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps({'decision': decision, 'summaries': summaries}, indent=2), flush=True)


if __name__ == '__main__':
    main()
