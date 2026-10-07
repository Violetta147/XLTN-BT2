import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

import zcr_logistic as runner

audit, core = runner.audit, runner.core
HERE = Path(__file__).resolve().parent


def main():
    options = runner.registry('H22')
    items = core.load_training()
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['ACF']['config']
    features = {}
    for item in items:
        _, audio = core.load_audio(core.TRAIN / item['file'])
        features[item['file']] = runner.extract(item, audio, options[0])
    fixed = pd.read_csv(HERE / 'results/H22_fixed_lofo_metrics.csv')
    rows, coefficient_rows, transition_rows = [], [], []
    for held in features.values():
        training = [x for x in features.values() if x['file'] != held['file']]
        values = {}
        for option in options[1:]:
            pred, f0, fitted, model = runner.infer(held, training, option, config)
            reference = fixed[(fixed.file == held['file']) & (fixed.option_id == option['id'])].iloc[0]
            score = core.score_file(held, pred, f0)
            for metric in ('average_mape', 'macro_f1', 'recall_v', 'false_voiced_sil'):
                assert np.isclose(score[metric], reference[metric], atol=1e-8)
            matrix = (runner.design(held, option['use_zcr']) - model['mean']) / model['scale']
            terms = matrix * model['coefficient']
            logit = terms.sum(axis=1) + model['intercept']
            expected = (expit(logit) >= .5) & (held['relative_rms'] >= fitted['energy_threshold'])
            assert np.array_equal(pred, expected)
            values[option['id']] = (pred, f0, logit, terms)
            coefficient_rows.append({'held_file': held['file'], 'option_id': option['id'],
                                     'fit_files': '|'.join(model['fit_files']), 'intercept': model['intercept'],
                                     **{f'coef_{name}': coefficient for name, coefficient in zip(model['feature_names'], model['coefficient'])}})
        two, three = values['raw_lr1_2d'], values['raw_lr1_3d_zcr']
        for i, time in enumerate(held['times']):
            rows.append({'file': held['file'], 'time_s': time, 'label': held['labels'][i],
                         'boundary': bool(held['boundary'][i]), 'acf_score': held['ACF_score'][i],
                         'relative_rms': held['relative_rms'][i], 'zcr_crossings_per_s': held['zcr'][i],
                         'pred_2d': bool(two[0][i]), 'pred_3d': bool(three[0][i]),
                         'f0_2d_hz': two[1][i], 'f0_3d_hz': three[1][i],
                         'logit_2d': two[2][i], 'logit_3d': three[2][i],
                         'logit_3d_zcr_term': three[3][i, 2],
                         'logit_3d_other_terms': three[3][i, :2].sum()})
        for label in ('v', 'uv', 'sil'):
            mask = held['labels'] == label
            transition_rows.append({'file': held['file'], 'label': label, 'frames': int(mask.sum()),
                                    'voiced_2d': int((two[0] & mask).sum()), 'voiced_3d': int((three[0] & mask).sum()),
                                    'lost_voiced': int((two[0] & ~three[0] & mask).sum()),
                                    'gained_voiced': int((~two[0] & three[0] & mask).sum())})
    frame_table = pd.DataFrame(rows)
    p_frames = audit.csv_write('H22_diagnostic_frames.csv', frame_table)
    audit.csv_write('H22_coefficients.csv', coefficient_rows)
    transitions = pd.DataFrame(transition_rows)
    audit.csv_write('H22_decision_transitions.csv', transitions)
    profile = frame_table.groupby(['file', 'label']).zcr_crossings_per_s.agg(['count', 'mean', 'std', 'median']).reset_index()
    audit.csv_write('H22_zcr_by_file_label.csv', profile)
    fig, axes = audit.plt.subplots(1, 2, figsize=(12, 4.5))
    edges = np.linspace(0, 12000, 41)
    for file, group in frame_table[frame_table.label == 'v'].groupby('file'):
        axes[0].hist(group.zcr_crossings_per_s, bins=edges, density=True, histtype='step', label=file[:-4])
    axes[0].set(xlabel='Raw frame ZCR (crossings/s)', ylabel='Density', title='V frames: file variation')
    axes[0].legend(fontsize=8)
    part = frame_table[(frame_table.file == 'phone_M1.wav') & (frame_table.label == 'v')]
    lost = part.pred_2d & ~part.pred_3d
    axes[1].scatter(part.loc[~lost, 'logit_2d'], part.loc[~lost, 'logit_3d'], s=12, alpha=.5, label='Other V frames')
    axes[1].scatter(part.loc[lost, 'logit_2d'], part.loc[lost, 'logit_3d'], s=24, color='#d44', label='V lost after ZCR')
    axes[1].axhline(0, color='#888', linewidth=1)
    axes[1].axvline(0, color='#888', linewidth=1)
    axes[1].set(xlabel='2D logit before energy gate', ylabel='3D logit before energy gate', title='phone_M1 V frames')
    axes[1].legend(fontsize=8)
    audit.save_figure('H22_zcr_diagnostics', fig, [p_frames],
                      'Fixed LOFO đặc trưng raw và quyết định2D/3D; logit0 là probability0.5 trước energy gate.',
                      'Thêm đặc trưng cũng refit các hệ số khác; ZCR term đơn lẻ không là tác động nhân quả. Histogram train4file, không quy luật giới tính.')
    for figure in audit.ARTIFACTS:
        figure.update(generator='zcr_diagnostics.py', generator_sha256=audit.digest(__file__),
                      command='python research_workbench_2026_10_07/zcr_diagnostics.py')
    audit.json_write(HERE / 'results/H22_diagnostic_manifest.json', {
        'figures': audit.ARTIFACTS, 'fixed_scores_reproduced': True,
        'sources': {name: audit.digest(HERE / f'results/{name}') for name in
                    ('H22_fixed_lofo_metrics.csv', 'H22_diagnostic_frames.csv', 'H22_coefficients.csv',
                     'H22_decision_transitions.csv', 'H22_zcr_by_file_label.csv')},
        'runner_sha256': audit.digest(Path(runner.__file__))})
    report = ['# H22 — vì sao thêm ZCR có đánh đổi?', '',
              'ZCR là tần suất đổi dấu sau trừ mean khung; không là tần số cơ bản F0. Báo cáo này tái dựng fixed LOFO2D/3D, không thay lựa chọn hoặc chạy thêm grid.', '',
              '## Các khung đổi quyết định', '', audit.markdown_table(transitions), '',
              'lost_voiced ở nhãn V là tăng bỏ sót; ở UV/SIL là bớt dự đoán hữu thanh sai. gained_voiced có ý nghĩa ngược lại. Đây là khung chồng lấn, không phải các sự kiện độc lập.', '',
              '## Hệ số sau chuẩn hóa', '', audit.markdown_table(pd.DataFrame(coefficient_rows)), '',
              'Hệ số gắn với đơn vị sau StandardScaler, không dùng hệ số lớn nhỏ như causal feature importance. Thêm ZCR làm refit cả hệ số ACF/RMS và intercept; tác động không chỉ là cộng một ZCR term vào mô hình2D đã cố định.', '',
              '## Phân bố theo file và nhãn', '', audit.markdown_table(profile), '',
              'Sự khác nhau về phân bố là quan sát. Chưa cô lập speaker, thiết bị, utterance hoặc sampling rate; không khẳng định domain shift là nguyên nhân đã chứng minh. Mỗi ô device×F/M chỉ1file, không suy rộng thành giọng nam/nữ.', '',
              '![Diagnostics](figures/H22_zcr_diagnostics.png)', '',
              'Đã tái lập fixed scores trong1e-8 và kiểm tra pred từ logit+energy gate. Các file CSV giữ đầy đủ khung để đối chiếu. Không có F0 reference từng khung nên các contour chỉ là dự đoán, không phép xác minh pitch đúng.']
    (HERE / 'H22_ERROR_ANALYSIS.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(transitions.to_string(index=False))
    print(pd.DataFrame(coefficient_rows).to_string(index=False))


if __name__ == '__main__':
    main()
