import argparse
import json

import tuning
from tuning import HERE, audit, pd, np


def main(family):
    registry = pd.DataFrame(json.loads((HERE / f'{family}_REGISTRY.json').read_text(encoding='utf-8'))['options']).rename(columns={'id': 'option_id'})
    traces = pd.read_csv(HERE / f'results/{family}_inner_traces.csv')
    final = traces[traces.outer_held == 'final']
    per_option = final.groupby('option_id').agg(average_mape=('average_mape', 'mean'), F0std_mape=('F0std_mape', 'mean'),
                 macro_f1=('macro_f1', 'mean'), recall_v=('recall_v', 'mean'), recall_uv=('recall_uv', 'mean'),
                 false_voiced_sil=('false_voiced_sil', 'sum'), files=('file', 'size'),
                 projection_coverage=('projection_coverage', 'mean'), native_f0_count=('native_f0_count', 'sum')).reset_index()
    per_option = per_option.merge(registry, on='option_id', validate='one_to_one')
    assert len(per_option) == len(registry) and (per_option.files == 4).all()
    p_options = audit.csv_write(f'{family}_full_grid_summary.csv', per_option)
    control = per_option[per_option.option_id == 'raw_0_0_f25_h10'].iloc[0]
    per_option['inner_class_guards'] = ((per_option.macro_f1 >= control.macro_f1 - .01)
                    & (per_option.recall_v >= control.recall_v - .01)
                    & (per_option.false_voiced_sil <= control.false_voiced_sil + 1))
    per_option['average_mape_delta_vs_control'] = per_option.average_mape - control.average_mape
    audit.csv_write(f'{family}_grid_guard_summary.csv', per_option.sort_values('average_mape'))
    fixed = per_option[(per_option.frame_ms == 25) & (per_option.hop_ms == 10)]
    fixed = fixed[fixed.C.isna()] if family == 'H18' else fixed[(fixed.C == 1) | (fixed.option_id == 'raw_0_0_f25_h10')]
    p_fixed = audit.csv_write(f'{family}_fixed_geometry_filter_control.csv', fixed)
    fig, axes = audit.plt.subplots(1, 3, figsize=(15, 4))
    x = np.arange(len(fixed))
    labels = [f'{r.kind}:{r.low_hz:g}/{r.high_hz:g}' + (' ACF' if pd.isna(r.C) else ' LR') for r in fixed.itertuples(index=False)]
    for ax, metric in zip(axes, ('average_mape', 'macro_f1', 'false_voiced_sil')):
        ax.bar(x, fixed[metric])
        ax.axhline(control[metric], ls='--', color='black', label='accepted ACF')
        ax.set_xticks(x, labels, rotation=60, ha='right')
        ax.set(title=metric)
    axes[0].legend(fontsize=7)
    audit.save_figure(f'{family}_filter_controls', fig, [p_fixed], 'Tách slice25/10 để đọc riêng ảnh hưởng filter; H19 giữC1 trong slice.', 'Điểm LOFO đã dùng để lựa chọn registry, không phải đánh giá độc lập. Gate nested của toàn quy trình vẫn quyết định giữ/bỏ.')
    best = per_option.groupby(['frame_ms', 'hop_ms']).average_mape.min().unstack('hop_ms')
    p_best = audit.csv_write(f'{family}_geometry_optimistic.csv', best.reset_index())
    fig, ax = audit.plt.subplots(figsize=(6, 4))
    image = ax.imshow(best.to_numpy(), aspect='auto', cmap='viridis_r')
    ax.set_xticks(range(len(best.columns)), best.columns)
    ax.set_yticks(range(len(best.index)), best.index)
    ax.set(xlabel='Native hop (ms)', ylabel='Frame length (ms)', title=family + ': minimum selection-LOFO within each geometry')
    for row in range(len(best.index)):
        for col in range(len(best.columns)):
            ax.text(col, row, f'{best.iloc[row, col]:.2f}', ha='center', va='center', color='white')
    fig.colorbar(image, ax=ax, label='Optimistic selected file-stat AvgMAPE (%)')
    audit.save_figure(f'{family}_geometry_grid', fig, [p_best, p_options], 'Heatmap minimum theo filters/C trong từng geometry của training selection.', 'Minimum chịu selection bias, không thay nested. Native hop thay đổi thật; các output chấm cùng canonical grid.')
    for figure in audit.ARTIFACTS:
        figure.update(generator='grid_analysis.py', generator_sha256=audit.digest(__file__), command=f'python research_workbench_2026_10_07/grid_analysis.py {family}')
    audit.json_write(HERE / f'results/{family}_grid_figure_manifest.json', {'figures': audit.ARTIFACTS})
    (HERE / f'{family}_GRID_EXPLANATION.md').write_text('\n'.join([
        '# ' + family + ' — đọc từng bộ lọc và geometry trong grid', '',
        'Slice25/10 là phép đối chiếu để đọc một biến, không khóa thuật toán ở25/10. Toàn grid đã có20/25/40ms vàhop5/10/20ms. Các slice dùng threshold/scaler fit other3, cùng canonical grid chấm.', '',
        audit.markdown_table(fixed[['option_id', 'average_mape', 'F0std_mape', 'macro_f1', 'recall_v', 'recall_uv', 'false_voiced_sil']]), '',
        f'![Filters](figures/{family}_filter_controls.png)', '',
        f'![Geometry](figures/{family}_geometry_grid.png)', '',
        'Bảng toàn grid và guards trong results. Không lấy configuration đẹp nhất từ bảng để gọi là generalization đã xác minh; so báo cáo nested của family. Không tune bằngtest. Tên F/M không dùng chọnrange.'
    ]) + '\n', encoding='utf-8')
    print(fixed[['option_id', 'average_mape', 'macro_f1', 'false_voiced_sil']].to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('family', choices=['H18', 'H19'])
    main(parser.parse_args().family)
