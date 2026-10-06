import json
from pathlib import Path

import numpy as np
import pandas as pd

import audit
import core
from estimator_experiment import eligibility

HERE = Path(__file__).resolve().parent
MARGINS = [0., .02, .04, .06, .08, .12]


def hysteresis_mask(scores, energy_pass, threshold, margin):
    pred = np.zeros(len(scores), dtype=bool)
    previous = False
    for i, score in enumerate(scores):
        active_threshold = threshold - margin if previous else threshold
        previous = bool(energy_pass[i] and score >= active_threshold)
        pred[i] = previous
    return pred


def infer(item, config, fitted, margin):
    pred = hysteresis_mask(item['ACF_score'], item['relative_rms'] >= fitted['energy_threshold'], fitted['pitch_threshold'], margin)
    adapter = dict(item, ACF_score=np.where(pred, 1., -1.))
    actual, f0 = core.infer(adapter, config, dict(fitted, pitch_threshold=.5))
    assert np.array_equal(actual, pred)
    return actual, f0


def metrics(item, config, fitted, margin):
    return core.score_file(item, *infer(item, config, fitted, margin))


def acceptable(candidate, baseline):
    c, b = core.summarize(candidate), core.summarize(baseline)
    new, old = candidate.set_index('file'), baseline.set_index('file')
    guard = c['macro_f1'] >= b['macro_f1'] - .01 and c['recall_v'] >= b['recall_v'] - .01 and c['false_voiced_sil'] <= b['false_voiced_sil'] + 1
    guard &= bool(((new.average_mape - old.average_mape) <= 2).all())
    if 'phone_F1.wav' in new.index:
        guard &= bool(new.loc['phone_F1.wav', 'F0std_mape'] <= old.loc['phone_F1.wav', 'F0std_mape'])
    return bool(guard)


def select_margin(items, config, context):
    candidates = {margin: [] for margin in MARGINS}
    traces = []
    for held in items:
        training = [x for x in items if x is not held]
        fitted = core.fit(training, config)
        for margin in MARGINS:
            row = metrics(held, config, fitted, margin)
            candidates[margin].append(row)
            traces.append({'context': context, 'inner_held': held['file'], 'fit_files': '|'.join(x['file'] for x in training), 'margin': margin, **row, **fitted})
    tables = {margin: pd.DataFrame(rows) for margin, rows in candidates.items()}
    choices = []
    for margin, table in tables.items():
        summary = core.summarize(table)
        choices.append({'context': context, 'selection_files': '|'.join(x['file'] for x in items), 'margin': margin,
                        'guard_pass': acceptable(table, tables[0.]), **summary})
    feasible = [row for row in choices if row['guard_pass']]
    selected = min(feasible, key=lambda row: (row['average_mape'], row['margin']))['margin'] if feasible else 0.
    return selected, traces, choices


def gate(per_file, split):
    frame = per_file[(per_file.split == 'train') | (per_file.split == split)].copy()
    frame.loc[frame.split == split, 'split'] = 'lofo'
    summaries = {model: {part: core.summarize(frame[(frame.model == model) & (frame.split == part)]) for part in ('train', 'lofo')} for model in ('accepted', 'candidate')}
    return eligibility(frame, summaries), summaries


def main():
    items = core.load_training()
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['ACF']['config']
    toy = hysteresis_mask(np.array([.2, .8, .68, .64, .69, .8, .64]), np.ones(7, dtype=bool), .7, .05)
    assert np.array_equal(toy, [False, True, True, False, False, True, False])
    all_fit = core.fit(items, config)
    for item in items:
        base = core.infer(item, config, all_fit)
        zero = infer(item, config, all_fit, 0.)
        assert np.array_equal(base[0], zero[0]) and np.allclose(base[1], zero[1], atol=1e-10, equal_nan=True)
        for margin in MARGINS:
            candidate = infer(item, config, all_fit, margin)
            assert np.all(candidate[0][base[0]])
    selected, inner, choices = select_margin(items, config, 'final_all_train')
    rows, fitted_rows, selections = [], [], []
    for split in ('train', 'lofo', 'nested'):
        for item in items:
            training = items if split == 'train' else [x for x in items if x is not item]
            fitted = core.fit(training, config)
            margin = selected
            if split == 'nested':
                margin, fold_inner, fold_choices = select_margin(training, config, 'outer_' + item['file'])
                inner.extend(fold_inner)
                choices.extend(fold_choices)
                assert all(item['file'] not in trace['fit_files'].split('|') and trace['inner_held'] != item['file'] for trace in fold_inner)
            fitted_rows.append({'split': split, 'held_file': item['file'], 'fit_files': '|'.join(x['file'] for x in training), **fitted})
            selections.append({'split': split, 'held_file': item['file'], 'margin': margin, 'selection_files': '|'.join(x['file'] for x in training) if split == 'nested' else '|'.join(x['file'] for x in items)})
            for model in ('accepted', 'candidate'):
                rows.append({'split': split, 'model': model, 'margin': 0. if model == 'accepted' else margin,
                             **metrics(item, config, fitted, 0. if model == 'accepted' else margin)})
    for fit in fitted_rows:
        assert fit['split'] == 'train' or fit['held_file'] not in fit['fit_files'].split('|')
    for trace in inner:
        assert trace['inner_held'] not in trace['fit_files'].split('|')
    poison = dict(items[0], labels=np.full(len(items[0]['labels']), 'unknown'), stats={'F0mean': -1., 'F0std': -1., 'F0num': -1})
    expected = infer(items[0], config, all_fit, selected)
    actual = infer(poison, config, all_fit, selected)
    assert np.array_equal(expected[0], actual[0]) and np.allclose(expected[1], actual[1], equal_nan=True)
    per_file = pd.DataFrame(rows)
    p_metrics = audit.csv_write('hysteresis_metrics.csv', per_file)
    p_inner = audit.csv_write('hysteresis_inner_validation.csv', inner)
    p_choices = audit.csv_write('hysteresis_margin_choices.csv', choices)
    audit.csv_write('hysteresis_fold_fits.csv', fitted_rows)
    audit.csv_write('hysteresis_outer_selections.csv', selections)
    final_gate, final_summaries = gate(per_file, 'lofo')
    nested_gate, nested_summaries = gate(per_file, 'nested')
    final_gate['nested_status'] = 'Final selected LOFO reused for selection; nested score reported separately.'
    nested_gate['nested_status'] = 'Outer held file excluded from margin selection; inner held-file fits only other two.'
    decision = {'final_margin': selected, 'registry': MARGINS, 'final_gate': final_gate, 'nested_gate': nested_gate,
                'eligible': final_gate['eligible'] and nested_gate['eligible'] and selected != 0.,
                'promoted': False, 'test_read': False, 'toy_transition_pass': True, 'zero_margin_matches_champion': True,
                'poisoned_gt_inference_invariant': True, 'nested_leakage_assertions_pass': True,
                'summaries': {'final': final_summaries, 'nested': nested_summaries},
                'code_sha256': audit.digest(__file__)}
    audit.json_write(HERE / 'results/hysteresis_experiment.json', decision)
    fig, axes = audit.plt.subplots(1, 2, figsize=(11, 4))
    choice_table = pd.DataFrame(choices)
    for context, group in choice_table.groupby('context'):
        axes[0].plot(group.margin, group.average_mape, 'o-', label=context.replace('outer_', ''))
    axes[0].set(xlabel='Offset threshold reduction', ylabel='Inner LOFO Average MAPE (%)', title='Pre-registered hysteresis margin grid')
    axes[0].legend(fontsize=7)
    for j, model in enumerate(('accepted', 'candidate')):
        values = [final_summaries[model]['train']['average_mape'], final_summaries[model]['lofo']['average_mape'], nested_summaries[model]['lofo']['average_mape']]
        axes[1].bar(np.arange(3) + (j - .5) * .35, values, width=.35, label=model)
    axes[1].set_xticks(np.arange(3), ['train', 'selected LOFO', 'nested'])
    axes[1].set(ylabel='Average MAPE (%)', title='Selection versus held-file procedure')
    axes[1].legend(fontsize=8)
    audit.save_figure('hysteresis_selection', fig, [p_choices, p_metrics], 'Margin sensitivity và nested evaluation của hysteresis.', 'Selected LOFO dùng chọn margin; chỉ nested loại outerheld khỏi lựa chọn mới, n=4 vẫn exploratory.')
    fig, axes = audit.plt.subplots(1, 3, figsize=(12, 4))
    for ax, metric in zip(axes, ('recall_v', 'macro_f1', 'false_voiced_sil')):
        for model in ('accepted', 'candidate'):
            table = per_file[(per_file.model == model) & (per_file.split == 'nested')].set_index('file')
            ax.plot(table.index.str.replace('.wav', '', regex=False), table[metric], 'o-', label=model)
        ax.set(title=metric, ylabel='Rate' if metric != 'false_voiced_sil' else 'Frame count')
        ax.tick_params(axis='x', rotation=35)
    axes[0].legend(fontsize=8)
    audit.save_figure('hysteresis_nested_tradeoffs', fig, [p_metrics], 'Recall/F1/SIL theo outerheld file.', 'Không đánh đổi SIL/UV chỉ để đạt count3GT; raw labels và scoring giữ nguyên.')
    for figure in audit.ARTIFACTS:
        figure['generator'] = 'hysteresis_experiment.py'
        figure['generator_sha256'] = audit.digest(__file__)
        figure['command'] = 'python research_workbench_2026_10_06/hysteresis_experiment.py'
    audit.json_write(HERE / 'results/hysteresis_figure_manifest.json', {'figures': audit.ARTIFACTS})
    table = pd.DataFrame([{'split': split, 'model': model, **core.summarize(per_file[(per_file.split == split) & (per_file.model == model)])} for split in ('train', 'lofo', 'nested') for model in ('accepted', 'candidate')])
    report = ['# H12 — hysteresis một yếu tố và nested lựa chọn margin', '', audit.markdown_table(table), '',
              '## Quyết định', '', '~~~json', json.dumps({k:v for k,v in decision.items() if k != 'summaries'}, indent=2), '~~~', '',
              '## Margin mỗi outerfold', '', audit.markdown_table(pd.DataFrame(selections)), '',
              '## Figures', '', '![Selection](figures/hysteresis_selection.png)', '', '![Tradeoffs](figures/hysteresis_nested_tradeoffs.png)', '',
              'Giữ accepted champion. Hysteresis thay voiced mask nên có thể thay run/context của path và median; không khẳng định F0 mới từng khung đúng khi chưa có frameGT. Test chưa đọc trong vòng này.', '',
              '~~~powershell', 'python research_workbench_2026_10_06/hysteresis_experiment.py', '~~~']
    (HERE / 'HYSTERESIS_EXPERIMENT_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in decision.items() if k != 'summaries'}, indent=2), flush=True)
    print(table[['split','model','average_mape','F0std_mape','recall_v','macro_f1','false_voiced_sil']].to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
