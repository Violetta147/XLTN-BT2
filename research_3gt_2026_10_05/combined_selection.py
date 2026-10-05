import argparse
import datetime
import json
import time

import numpy as np
import pandas as pd

from baseline_audit import CONFIGS
from core import HERE, RESULTS, evaluate, fit, infer, load_training, lofo, score_file, sha256, summarize
from events import record

MODELS = {name: CONFIGS[name] for name in ('ACF', 'AMDF_energy', 'GMM_ACF', 'GMM_AMDF')}
MODELS['AMDF_no_energy'] = CONFIGS['AMDF']


def registry():
    candidates = {}
    transforms = [{'candidate': 'best', 'median': width} for width in (1, 3, 5)]
    transforms += [{'candidate': 'near', 'margin': margin, 'median': width}
                   for margin in (.01, .02, .05, .10) for width in (1, 3)]
    transforms += [{'candidate': 'path', 'jump_cost': jump, 'octave_cost': octave, 'median': width}
                   for jump in (.15, .35) for octave in (0., .01, .03) for width in (1, 3)]
    for model, base in MODELS.items():
        energy_options = (False,) if model == 'AMDF_no_energy' else (False, True)
        configs = [{**base, **transform, 'energy': energy, 'preprocess': 'raw'}
                   for energy in energy_options for transform in transforms]
        if not model.startswith('GMM'):
            energy = model != 'AMDF_no_energy'
            for method in ('gaussian', 'hist_modes', 'hist_classes'):
                for transform in ({'candidate': 'best', 'median': 1},
                                  {'candidate': 'near', 'margin': .05, 'median': 1},
                                  {'candidate': 'path', 'jump_cost': .35, 'octave_cost': 0., 'median': 1}):
                    configs.append({**base, **transform, 'energy': energy, 'threshold_method': method,
                                    'preprocess': 'raw'})
        unique = {json.dumps(config, sort_keys=True): config for config in configs}
        candidates[model] = [{'id': f'{model}_{i:03d}', 'config': config}
                             for i, config in enumerate(unique.values())]
    return candidates


def choose(items, choices, baseline):
    baseline_f1 = summarize(lofo(items, baseline))['macro_f1']
    rows = []
    for candidate in choices:
        stats = summarize(lofo(items, candidate['config']))
        rows.append({'id': candidate['id'], **stats, 'allowed_f1': stats['macro_f1'] >= baseline_f1 - .03})
    frame = pd.DataFrame(rows)
    eligible = frame[frame.allowed_f1 & np.isfinite(frame.average_mape)]
    assert len(eligible), 'Baseline candidate must remain eligible'
    row = eligible.sort_values(['average_mape', 'macro_f1', 'id'], ascending=[True, False, True]).iloc[0]
    selected = next(choice for choice in choices if choice['id'] == row.id)
    return selected, frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--register', action='store_true')
    args = parser.parse_args()
    registry_path = RESULTS / 'candidate_registry.json'
    if args.register:
        registry_path.write_text(json.dumps(registry(), indent=2), encoding='utf-8')
        record('Đăng ký tập cấu hình kết hợp trước validation lồng nhau',
               '; '.join(f'{name}: {len(choices)} cấu hình' for name, choices in registry().items()),
               'Không dùng low-pass đã thất bại; chỉ kết hợp các hướng đã đo riêng. GMM giữ ngưỡng GMM.')
        return
    choices = json.loads(registry_path.read_text(encoding='utf-8'))
    baseline = json.loads((RESULTS / 'baseline_summary.json').read_text(encoding='utf-8'))
    start = time.perf_counter()
    frozen, summaries, nested_rows, train_rows, selection_rows, fold_choices = {}, {}, [], [], [], []
    for model, base in MODELS.items():
        print('Selecting', model, flush=True)
        items = load_training(base['frame_ms'])
        selected, grid = choose(items, choices[model], base)
        grid['model'] = model
        selection_rows.append(grid)
        config = selected['config']
        fitted = fit(items, config)
        train = evaluate(items, config, fitted)
        cv = lofo(items, config)
        nested = []
        for held in items:
            outer_train = [item for item in items if item is not held]
            inner_choice, inner_grid = choose(outer_train, choices[model], base)
            inner_config = inner_choice['config']
            inner_fit = fit(outer_train, inner_config)
            row = score_file(held, *infer(held, inner_config, inner_fit))
            nested.append(row)
            fold_choices.append({'model': model, 'outer_held_out': held['file'], 'inner_selected_id': inner_choice['id'],
                                 'inner_config': inner_config, 'outer_fit': inner_fit,
                                 'held_out_average_mape': row['average_mape'],
                                 'inner_validation_mape': float(inner_grid.loc[inner_grid.id == inner_choice['id'], 'average_mape'].iloc[0])})
        nested = pd.DataFrame(nested)
        reference_name = 'AMDF' if model == 'AMDF_no_energy' else model
        ref = baseline[reference_name]
        train_metrics, cv_metrics, nested_metrics = summarize(train), summarize(cv), summarize(nested)
        baseline_table = pd.read_csv(RESULTS / 'baseline_train.csv')
        old_phone = baseline_table[(baseline_table.model == reference_name) & (baseline_table.file == 'phone_F1.wav')].F0std_mape.iloc[0]
        new_phone = train.loc[train.file == 'phone_F1.wav', 'F0std_mape'].iloc[0]
        gates = {
            'train_20pct_relative_reduction': train_metrics['average_mape'] <= .8 * ref['full_train']['average_mape'],
            'phone_F1_std_improved': bool(new_phone < old_phone),
            'lofo_not_worse_by_more_than_1pp': cv_metrics['average_mape'] <= ref['lofo']['average_mape'] + 1,
            'nested_not_worse_by_more_than_1pp': nested_metrics['average_mape'] <= ref['lofo']['average_mape'] + 1,
            'lofo_F1_not_worse_by_more_than_0_03': cv_metrics['macro_f1'] >= ref['lofo']['macro_f1'] - .03,
            'nested_F1_not_worse_by_more_than_0_03': nested_metrics['macro_f1'] >= ref['lofo']['macro_f1'] - .03,
        }
        keep = all(gates.values())
        summaries[model] = {'selected_id': selected['id'], 'config': config, 'fitted': fitted,
                            'train': train_metrics, 'lofo': cv_metrics, 'nested_lofo': nested_metrics,
                            'baseline': ref, 'phone_F1_std_mape_before': float(old_phone),
                            'phone_F1_std_mape_after': float(new_phone), 'gates': gates, 'keep': keep}
        frozen[model] = {'config': config if keep else base, 'fitted': fitted if keep else fit(items, base),
                         'accepted_improvement': keep, 'selected_id': selected['id']}
        for kind, frame in [('train', train), ('lofo_selected', cv), ('nested_lofo', nested)]:
            frame = frame.copy()
            frame['model'], frame['kind'] = model, kind
            train_rows.append(frame)
        record('Validation lồng nhau: ' + model,
               f'Train {train_metrics["average_mape"]:.2f}%, LOFO {cv_metrics["average_mape"]:.2f}%, nested LOFO {nested_metrics["average_mape"]:.2f}%; phone_F1 stdMAPE {old_phone:.2f}→{new_phone:.2f}%.',
               ('Giữ: đạt toàn bộ tiêu chí train/validation/F1.' if keep else 'Không giữ: ' + ', '.join(key for key, value in gates.items() if not value)))
    pd.concat(selection_rows, ignore_index=True).to_csv(RESULTS / 'combined_grid_lofo.csv', index=False)
    pd.concat(train_rows, ignore_index=True).to_csv(RESULTS / 'selected_train_and_nested_lofo.csv', index=False)
    (RESULTS / 'nested_fold_choices.json').write_text(json.dumps(fold_choices, indent=2), encoding='utf-8')
    (RESULTS / 'selection_summary.json').write_text(json.dumps(summaries, indent=2), encoding='utf-8')
    freeze = {'frozen_at_vietnam': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat(timespec='seconds'),
              'test_opened_during_selection': False, 'models': frozen,
              'candidate_registry_sha256': sha256(registry_path),
              'training_manifest_sha256': sha256(RESULTS / 'training_manifest.json'),
              'selection_summary_sha256': sha256(RESULTS / 'selection_summary.json'),
              'inference_code_sha256': sha256(HERE / 'core.py')}
    if all(value['accepted_improvement'] for value in frozen.values()):
        (RESULTS / 'frozen_config.json').write_text(json.dumps(freeze, indent=2), encoding='utf-8')
        record('Chốt cấu hình bằng train; mở khóa một lượt đánh giá test cuối',
               f'5 pipeline đều đạt gate; tổng thời gian chọn/nested {time.perf_counter() - start:.1f}s. Đã lưu hash và thời gian freeze.',
               'Từ đây không sửa thuật toán hay tham số theo test; notebook phải tái lập đúng cấu hình này.')
    else:
        (RESULTS / 'provisional_config.json').write_text(json.dumps(freeze, indent=2), encoding='utf-8')
        record('Chưa chốt cấu hình', 'Có pipeline chưa qua gate; test vẫn khóa.', 'Tiếp tục xử lý nguyên nhân dựa trên train')
    print(json.dumps(summaries, indent=2), flush=True)


if __name__ == '__main__':
    main()
