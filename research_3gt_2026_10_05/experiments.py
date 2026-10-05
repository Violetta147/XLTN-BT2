import argparse
import json
import time

import pandas as pd

from baseline_audit import CONFIGS
from core import RESULTS, evaluate, fit, load_training, lofo, summarize
from events import record


def variants(stage):
    if stage == 'energy':
        return [('energy', {'energy': True})]
    if stage == 'near':
        return [(f'near_{margin:g}', {'candidate': 'near', 'margin': margin}) for margin in (.01, .02, .05, .10)]
    if stage == 'path':
        return [(f'path_j{jump:g}_o{octave:g}', {'candidate': 'path', 'jump_cost': jump, 'octave_cost': octave})
                for jump in (.05, .15, .35) for octave in (0., .01, .03)]
    if stage == 'median':
        return [(f'median{width}', {'median': width}) for width in (3, 5)]
    if stage == 'filter':
        return [('gaussian800', {'preprocess': 'gaussian800'})]
    if stage == 'selection':
        return [(method, {'threshold_method': method}) for method in ('gaussian', 'hist_modes', 'hist_classes')]
    raise ValueError(stage)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('energy', 'near', 'path', 'median', 'filter', 'selection'))
    args = parser.parse_args()
    stage = args.stage
    start = time.perf_counter()
    rows, all_files = [], []
    for model, baseline in CONFIGS.items():
        if stage == 'selection' and model.startswith('GMM'):
            continue
        for name, changes in variants(stage):
            config = {**baseline, **changes}
            items = load_training(config['frame_ms'], config.get('preprocess', 'raw'))
            fitted = fit(items, config)
            training = evaluate(items, config, fitted)
            validation = lofo(items, config)
            rows.append({'model': model, 'variant': name, 'config': json.dumps(config, sort_keys=True),
                         **{'train_' + key: value for key, value in summarize(training).items()},
                         **{'lofo_' + key: value for key, value in summarize(validation).items()},
                         **fitted})
            for kind, frame in [('train', training), ('lofo', validation)]:
                frame = frame.copy()
                frame['model'], frame['variant'], frame['kind'] = model, name, kind
                all_files.append(frame)
    results = pd.DataFrame(rows)
    results.to_csv(RESULTS / f'experiment_{stage}_summary.csv', index=False)
    pd.concat(all_files, ignore_index=True).to_csv(RESULTS / f'experiment_{stage}_per_file.csv', index=False)
    baseline = json.loads((RESULTS / 'baseline_summary.json').read_text(encoding='utf-8'))
    best = {}
    for model, group in results.groupby('model', sort=False):
        chosen = group.sort_values(['lofo_average_mape', 'lofo_macro_f1'], ascending=[True, False]).iloc[0]
        best[model] = {'variant': chosen['variant'], 'train_mape': float(chosen['train_average_mape']),
                       'lofo_mape': float(chosen['lofo_average_mape']),
                       'baseline_lofo_mape': baseline[model]['lofo']['average_mape'],
                       'lofo_f1_delta': float(chosen['lofo_macro_f1']) - baseline[model]['lofo']['macro_f1']}
    (RESULTS / f'experiment_{stage}_conclusions.json').write_text(json.dumps(best, indent=2), encoding='utf-8')
    brief = '; '.join(f'{model}: {value["variant"]}, LOFO {value["lofo_mape"]:.2f}% vs {value["baseline_lofo_mape"]:.2f}%' for model, value in best.items())
    record('Thí nghiệm riêng: ' + stage, brief + f' ({time.perf_counter() - start:.1f}s)',
           'Chỉ là ablation train; chưa chốt và chưa chạy test. Mọi cấu hình, kể cả kém hơn, được lưu.')
    print(results[['model', 'variant', 'train_average_mape', 'lofo_average_mape', 'lofo_macro_f1']].to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
