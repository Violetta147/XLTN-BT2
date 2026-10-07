import json
import time
from pathlib import Path

import tuning
from tuning import HERE, REPO, audit, core, np, pd
import robustness_analysis


def main():
    started = time.perf_counter()
    items = core.load_training()
    names = sorted(x['file'] for x in items)
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['ACF']['config']
    experiments = {h: json.loads((HERE / f'results/{h}_experiment.json').read_text(encoding='utf-8')) for h in ('H18', 'H19')}
    choices = {h: {x['outer_held']: x['option'] for x in data['selections'] if x['outer_held'] != 'final'} for h, data in experiments.items()}
    baseline = next(x for x in tuning.registry('H18') if x['id'] == 'raw_0_0_f25_h10')
    clean = {}
    audio = {}
    for item in items:
        _, audio[item['file']] = core.load_audio(core.TRAIN / item['file'])
        for option in [baseline] + [o for h in choices.values() for o in h.values()]:
            key = (tuning.feature_key(option), item['file'])
            if key not in clean:
                clean[key] = tuning.extract(item, audio[item['file']], option)
    rows, clipping = [], []
    for item in items:
        name = item['file']
        conditions = [{'file': name, 'kind': kind, 'level': float(level), 'seed': seed}
                      for kind, level, seed in __import__('itertools').product(('white', 'pink', 'brown'), (20, 10, 0), range(3))]
        conditions += [{'file': name, 'kind': 'clip_peak', 'level': level, 'seed': 0} for level in (.8, .5, .25)]
        for condition in conditions:
            transformed, seed, snr = robustness_analysis.perturb(audio[name], condition)
            case = '|'.join(str(condition[x]) for x in ('file', 'kind', 'level', 'seed'))
            if condition['kind'] == 'clip_peak':
                changed = abs(audio[name]) > abs(audio[name]).max() * condition['level']
                windows = np.lib.stride_tricks.sliding_window_view(changed, round(item['fs'] * .025))[::round(item['fs'] * .01)]
                clipping.append({'file': name, 'ratio': condition['level'], 'threshold': float(abs(audio[name]).max() * condition['level']),
                                 'sample_clipped_fraction': float(changed.mean()), 'canonical_frames_with_clipping': float(windows.any(axis=1).mean()),
                                 'original_peak': float(abs(audio[name]).max()), 'original_rms': float(np.sqrt(np.mean(audio[name] ** 2))),
                                 'clipped_rms': float(np.sqrt(np.mean(transformed ** 2)))})
            for model, option in [('accepted', baseline), ('H18_nested', choices['H18'][name]), ('H19_nested', choices['H19'][name])]:
                native = tuning.extract(item, transformed, option)
                training = [clean[(tuning.feature_key(option), other)] for other in names if other != name]
                pred, f0, fitted, classifier = tuning.infer(native, training, option, config)
                if classifier is not None:
                    assert name not in classifier['fit_files']
                pp, ff, support = tuning.project(native, item, pred, f0, option['hop_ms'])
                rows.append({**condition, 'case_id': case, 'model': model, 'option_id': option['id'],
                             'actual_rng_seed': seed, 'achieved_snr_db': snr, 'projection_coverage': float(support.mean()),
                             **core.score_file(item, pp, ff)})
        print(f'H20: completed {name}', flush=True)
    frame = pd.DataFrame(rows)
    assert len(frame) == 360 and not frame.duplicated(['case_id', 'model']).any()
    p_cases = audit.csv_write('H20_stress_cases.csv', frame)
    p_clip = audit.csv_write('H20_clipping_fraction.csv', clipping)
    previous = pd.read_csv(REPO / 'research_workbench_2026_10_06/results/robustness_cases.csv')
    matched = frame[frame.model == 'accepted'].merge(previous[previous.model == 'accepted'], on='case_id', suffixes=('_new', '_old'), validate='one_to_one')
    assert len(matched) == 120
    for metric in ('average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil'):
        assert np.allclose(matched[metric + '_new'], matched[metric + '_old'], atol=1e-8, equal_nan=True), metric
    groups = frame.groupby(['file', 'kind', 'level', 'model']).agg(average_mape=('average_mape', 'mean'),
                 macro_f1=('macro_f1', 'mean'), recall_v=('recall_v', 'mean'), recall_uv=('recall_uv', 'mean'),
                 false_voiced_sil=('false_voiced_sil', 'mean'), cases=('average_mape', 'size'), finite=('average_mape', 'count')).reset_index()
    groups['file_group'] = groups.file.str.split('_').str[1].str[0]
    groups['device'] = groups.file.str.split('_').str[0]
    p_groups = audit.csv_write('H20_stress_per_file.csv', groups)
    aggregate = groups.groupby(['kind', 'level', 'model']).agg(conditional_average_mape=('average_mape', 'mean'),
                 macro_f1=('macro_f1', 'mean'), recall_v=('recall_v', 'mean'), false_voiced_sil=('false_voiced_sil', 'sum'),
                 cases=('cases', 'sum'), finite=('finite', 'sum')).reset_index()
    aggregate['coverage'] = aggregate.finite / aggregate.cases
    p_summary = audit.csv_write('H20_stress_summary.csv', aggregate)
    clean_rows = []
    for family in ('H18', 'H19'):
        data = pd.read_csv(HERE / f'results/{family}_metrics.csv')
        data = data[data.split == 'nested'].copy()
        for row in data.to_dict('records'):
            if row['model'] == 'accepted' and family == 'H19':
                continue
            row['model'] = 'accepted' if row['model'] == 'accepted' else family + '_nested'
            row['file_group'] = row['file'].split('_')[1][0]
            row['device'] = row['file'].split('_')[0]
            row['gt_mean_hz'] = next(x['stats']['F0mean'] for x in items if x['file'] == row['file'])
            row['gt_std_hz'] = next(x['stats']['F0std'] for x in items if x['file'] == row['file'])
            clean_rows.append(row)
    clean_frame = pd.DataFrame(clean_rows)
    p_clean = audit.csv_write('H20_clean_per_file.csv', clean_frame)
    descriptions = []
    for factor in ('file_group', 'device'):
        for (group, model), data in clean_frame.groupby([factor, 'model']):
            descriptions.append({'factor': factor, 'group': group, 'model': model, 'files': len(data),
                                 **core.summarize(data)})
    p_descriptions = audit.csv_write('H20_FM_device_summary.csv', descriptions)
    boundary_rows = []
    for family in ('H18', 'H19'):
        contours = pd.read_csv(HERE / f'results/{family}_nested_contours.csv')
        for (file, model, boundary), data in contours.groupby(['file', 'model', 'boundary']):
            if model == 'accepted' and family == 'H19':
                continue
            boundary_rows.append({'file': file, 'model': 'accepted' if model == 'accepted' else family + '_nested',
                                  'boundary': bool(boundary), 'frames': len(data),
                                  **core.classification(data.label.to_numpy(), data.pred_voiced.to_numpy(dtype=bool))})
    audit.csv_write('H20_boundary_metrics.csv', boundary_rows)
    fig, axes = audit.plt.subplots(1, 3, figsize=(13, 4))
    for ax, metric in zip(axes, ('average_mape', 'macro_f1', 'recall_v')):
        for model, data in clean_frame.groupby('model'):
            ax.plot(data.file.str.replace('.wav', '', regex=False), data[metric], 'o-', label=model)
        ax.set(title=metric)
        ax.tick_params(axis='x', rotation=30)
    axes[0].legend(fontsize=7)
    audit.save_figure('H20_FM_device', fig, [p_clean, p_descriptions], 'Bốn file cho thấy tương tác tên nhóm và thiết bị; mỗi ô chỉ một file.', 'F/M theo tên, không xác minh danh tính hoặc tổng quát cho giới; sample rate/domain đi cùng thiết bị.')
    fig, axes = audit.plt.subplots(2, 3, figsize=(13, 7))
    for col, kind in enumerate(('white', 'pink', 'brown')):
        for model in ('accepted', 'H18_nested', 'H19_nested'):
            data = aggregate[(aggregate.kind == kind) & (aggregate.model == model)].sort_values('level')
            axes[0, col].plot(data.level, data.macro_f1, 'o-', label=model)
            axes[1, col].plot(data.level, data.false_voiced_sil, 'o-', label=model)
        axes[0, col].set(title=kind, ylabel='File-average macro F1', ylim=(0, 1))
        axes[1, col].set(xlabel='Injected full-file SNR (dB)', ylabel='Expected total SIL false voiced')
    axes[0, 0].legend(fontsize=7)
    audit.save_figure('H20_noise', fig, [p_summary, p_groups], 'Noise được đưa vào sau clean selection, không fit lại.', 'Ba seed mô phỏng/cell, chỉ bốn WAV; không chứng minh độ bền trên corpus nhiễu thật.')
    fig, axes = audit.plt.subplots(2, 4, figsize=(15, 7))
    for col, name in enumerate(names):
        for model in ('accepted', 'H18_nested', 'H19_nested'):
            data = groups[(groups.kind == 'clip_peak') & (groups.file == name) & (groups.model == model)].sort_values('level')
            axes[0, col].plot(data.level, data.average_mape, 'o-', label=model)
            axes[1, col].plot(data.level, data.macro_f1, 'o-', label=model)
        axes[0, col].set(title=name.replace('.wav', ''), ylabel='File-stat AvgMAPE (%)')
        axes[1, col].set(xlabel='Hard-clipping peak ratio', ylabel='Macro F1', ylim=(0, 1))
    axes[0, 0].legend(fontsize=7)
    audit.save_figure('H20_clipping', fig, [p_groups, p_clip], 'Clipping cắt đỉnh tại tỷ lệ peak raw; giảm ratio làm clip mạnh hơn.', 'Synthetic clipping không chứng minh file phone đã bị clip vật lý; số phần trăm sample/frames bị cắt báo riêng.')
    first = items[0]
    signal = audio[first['file']]
    peak = int(np.argmax(abs(signal)))
    lo, hi = max(0, peak - round(first['fs'] * .01)), min(len(signal), peak + round(first['fs'] * .01))
    limit = .25 * abs(signal).max()
    example = pd.DataFrame({'time_s': np.arange(lo, hi) / first['fs'], 'raw': signal[lo:hi], 'clipped': np.clip(signal[lo:hi], -limit, limit)})
    p_example = audit.csv_write('H20_clipping_example.csv', example)
    fig, ax = audit.plt.subplots(figsize=(10, 3.5))
    ax.plot(example.time_s, example.raw, label='raw')
    ax.plot(example.time_s, example.clipped, label='hard clip at .25 peak')
    ax.axhline(limit, ls='--', color='grey')
    ax.axhline(-limit, ls='--', color='grey')
    ax.set(xlabel='Time (s)', ylabel='Normalized amplitude', title=first['file'] + ': clipping near the largest peak')
    ax.legend()
    audit.save_figure('H20_clipping_waveform', fig, [p_example], 'Ví dụ waveform bị cắt đỉnh, lấy quanh peak lớn nhất trước clip.', 'Đây là minh họa hard clipping, khác center clipping là xóa biên độ nhỏ quanh zero.')
    for figure in audit.ARTIFACTS:
        figure.update(generator='stress.py', generator_sha256=audit.digest(__file__), command='python research_workbench_2026_10_07/stress.py')
    audit.json_write(HERE / 'results/H20_figure_manifest.json', {'figures': audit.ARTIFACTS})
    audit.json_write(HERE / 'results/H20_validation.json', {'cases': 120, 'rows': len(frame), 'previous_H15_control_cases_matched': len(matched),
                'no_stress_tuning': True, 'train_only': True, 'wall_time_s': time.perf_counter() - started,
                'code_sha256': {str(p.relative_to(REPO)): audit.digest(p) for p in (Path(__file__), Path(tuning.__file__), Path(robustness_analysis.__file__))},
                'clean_selection_sha256': {h: audit.digest(HERE / f'results/{h}_experiment.json') for h in experiments},
                'data_sha256': {n: audit.digest(core.TRAIN / n) for n in names}})
    report = ['# H20 — nhóm F/M, phone/studio và clipping/noise sau freeze', '',
              'F/M chỉ là tên file, mỗi nhóm2file, mỗi ô F/M × thiết bị1file. Không đủ phân biệt ảnh hưởng người nói, giới, thiết bị và sample rate. Không fit threshold theo nhãn giới.', '',
              '## Clean outer results', '', audit.markdown_table(clean_frame[['file', 'model', 'gt_mean_hz', 'F0mean', 'gt_std_hz', 'F0std', 'average_mape', 'macro_f1', 'recall_v', 'recall_uv', 'false_voiced_sil']]), '',
              '## Tỷ lệ clipping thật được tạo trong mô phỏng', '', audit.markdown_table(pd.DataFrame(clipping)), '',
              'Hard clipping là cắt phần đỉnh vượt ±threshold, tạo waveform plateau và có thể thêm harmonics; center clipping là bỏ biên độ nhỏ gần zero trước ACF, sẽ cần thí nghiệm riêng. Dataset audit không thấy sample ở native int16 rails, nhưng không loại trừ analog clipping trước ghi hoặc compression.', '',
              '## Stress tổng hợp', '', audit.markdown_table(aggregate), '',
              'Mean seeds trong từng file trước khi gộp; AvgMAPE có điều kiện và coverage cùng được báo. Không chấm undefined như0. H18/H19 dùng outer selection từ clean other3; không tune trên noise/clipping. Accepted khớp120case H15 cũ trong tolerance1e-8.', '',
              '![Nhóm](figures/H20_FM_device.png)', '', '![Noise](figures/H20_noise.png)', '',
              '![Clipping](figures/H20_clipping.png)', '', '![Waveform](figures/H20_clipping_waveform.png)', '',
              'Lệnh: `python research_workbench_2026_10_07/stress.py`. CSV/manifest/selection hashes trong results. Test không mở trong vòng này.']
    (HERE / 'H20_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(aggregate.to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
