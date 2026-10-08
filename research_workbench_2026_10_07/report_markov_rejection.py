import json
import platform
import numpy as np
import pandas as pd
import scipy
import sklearn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import markov_rejection as api
from verify_srh import independent_item


def longest_run(mask):
    longest = current = 0
    for value in mask:
        current = current+1 if value else 0
        longest = max(longest, current)
    return longest


def save_figure(figure, stem):
    for suffix in ('png', 'svg'):
        path = api.HERE/'figures'/f'{stem}.{suffix}'
        figure.savefig(path, dpi=160)
        if suffix == 'svg':
            path.write_text('\n'.join(line.rstrip() for line in path.read_text(encoding='utf-8').splitlines())+'\n', encoding='utf-8')
    plt.close(figure)


def build():
    models = json.loads((api.OUT/'H56_models.json').read_text())
    transitions = json.loads((api.OUT/'H59_transitions.json').read_text())
    names = sorted(api.source.bank_train())
    tables, audits, quality, cases, trace_rows = {}, [], [], [], []
    inputs = [api.OUT/'H56_models.json', api.OUT/'H58_mappings.json', api.OUT/'H59_transitions.json']
    figure, axes = plt.subplots(2, 2, figsize=(12, 7), sharey=True)
    for stage in ('train', 'test'):
        verification = api.OUT/f'H59_{stage}_verification.json'
        assert json.loads(verification.read_text())['passed']
        table_path = api.OUT/f'H59_{stage}_fixed.csv'
        proof_path = api.OUT/f'H59_{stage}_proofs.json'
        proofs = json.loads(proof_path.read_text())
        tables[stage] = pd.read_csv(table_path, float_precision='round_trip')
        inputs += [verification, table_path, proof_path, api.OUT/f'H59_{stage}_experiment.json']
        for number, name in enumerate(sorted(tables[stage].file.unique())):
            fit = [n for n in names if n != name] if stage == 'train' else names
            path = (api.core.TRAIN if stage == 'train' else api.REPO/'TinHieuKiemThu')/name
            item, _, _ = independent_item(path, stage)
            segments = api.core.read_segments(path.with_suffix('.lab'))
            boundaries = np.array([b for a, b, label in segments[:-1]])
            for seed in api.SEEDS:
                mid = next(i for i, m in enumerate(models) if m['fit_files'] == fit and m['seed'] == seed)
                group = [p for p in proofs if p['file'] == name and p['model_id'] == mid]
                base = next(p for p in group if p['option_id'] == 'hard170')
                baseline = np.array(base['pred'], bool)
                for proof in group:
                    if proof['option_id'] in ('hard170', 'recovery_only'):
                        continue
                    removed = baseline & ~np.array(proof['pred'], bool)
                    removed_v = removed & (item['labels'] == 'v')
                    audits.append(dict(stage=stage, file=name, seed=seed, option_id=proof['option_id'],
                        removed=int(removed.sum()), removed_v=int(removed_v.sum()),
                        removed_uv=int(sum(removed & (item['labels'] == 'uv'))),
                        removed_sil=int(sum(removed & (item['labels'] == 'sil'))),
                        longest_consecutive_removed_v=longest_run(removed_v)))
                static = next(p for p in group if p['option_id'] == 'mapped_rejection_025')
                temporal = next(p for p in group if p['option_id'] == 'markov_rejection_025')
                if stage == 'train':
                    target = (item['labels'] == 'v').astype(float)
                    assert np.isin(item['labels'], ['v', 'uv', 'sil']).all()
                    quality.append(dict(file=name, seed=seed,
                        mapped_brier=float(np.mean((np.array(static['prob'])-target)**2)),
                        markov_brier=float(np.mean((np.array(temporal['prob'])-target)**2)),
                        mapped_mean_lab_v=float(np.mean(np.array(static['prob'])[target==1])),
                        markov_mean_lab_v=float(np.mean(np.array(temporal['prob'])[target==1]))))
                if seed != 11:
                    continue
                changed = np.array(static['pred']) != np.array(temporal['pred'])
                for i in np.flatnonzero(changed):
                    cases.append(dict(stage=stage, file=name, frame=int(i), time=float(item['times'][i]),
                        label=str(item['labels'][i]), static_score=float(static['prob'][i]), markov_score=float(temporal['prob'][i]),
                        static_kept=bool(static['pred'][i]), markov_kept=bool(temporal['pred'][i]),
                        baseline_f0=float(base['f0'][i]), nearest_boundary_ms=float(np.min(abs(boundaries-item['times'][i]))*1000)))
                for i in range(len(item['times'])):
                    trace_rows.append(dict(stage=stage, file=name, frame=i, time=float(item['times'][i]), label=str(item['labels'][i]),
                        baseline_voiced=bool(baseline[i]), static_score=float(static['prob'][i]), markov_score=float(temporal['prob'][i]),
                        static_kept=bool(static['pred'][i]), markov_kept=bool(temporal['pred'][i])))
                if stage == 'train':
                    axis = axes.flat[number]
                    for a, b, label in segments:
                        if label == 'v':
                            axis.axvspan(a, b, color='green', alpha=.10)
                    axis.plot(item['times'], static['prob'], color='#1870a8', linewidth=1, label='H58 per-frame score')
                    axis.plot(item['times'], temporal['prob'], color='#dc6a22', linewidth=1, label='H59 chain marginal')
                    axis.axhline(.25, color='black', linestyle=':', linewidth=.7, label='Frozen q=0.25')
                    axis.set_title(name.replace('.wav','')+' — held out of fit pool')
                    axis.set_xlabel('Time (s)')
                    axis.set_ylim(-.02, 1.02)
                    axis.set_ylabel('Score; not calibrated P(valid F0)')
    handles, labels = axes.flat[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc='lower center', ncol=3, fontsize=9)
    figure.suptitle('H59 qualitative train LOFO, seed11 — green spans: LAB V')
    figure.tight_layout(rect=(0,.045,1,.95))
    save_figure(figure, 'H59_context_scores')
    audits, quality = pd.DataFrame(audits), pd.DataFrame(quality)
    audits.to_csv(api.OUT/'H59_removed_label_audit.csv', index=False)
    quality.to_csv(api.OUT/'H59_held_train_score_quality.csv', index=False)
    pd.DataFrame(cases).to_csv(api.OUT/'H59_changed_cases.csv', index=False)
    pd.DataFrame(trace_rows).to_csv(api.OUT/'H59_score_traces.csv', index=False)
    transition_rows = []
    for mid, fitted in enumerate(transitions):
        row = dict(model_id=mid, fit_pool='|'.join(fitted['fit_files']), seed=fitted['seed'], initial_v=fitted['initial'][1])
        for a in (0,1):
            for b in (0,1):
                row[f'count_{a}{b}'] = fitted['transition_counts'][a][b]
                row[f'p_{a}{b}'] = fitted['transition'][a][b]
        transition_rows.append(row)
    transition_table = pd.DataFrame(transition_rows)
    transition_table.to_csv(api.OUT/'H59_transition_audit.csv', index=False)
    fixed = tables['train'][tables['train'].fit_pool.str.count(r'\|') == 2]
    matrix = fixed.groupby(['option_id', 'file']).average_mape.mean().unstack().loc[list(api.BY_ID)]
    seeds = fixed.groupby(['option_id', 'seed']).agg(mean_mape=('average_mape', 'mean'),
        worst_mape=('average_mape', 'max'), removed=('removed', 'sum'), recall_v=('recall_v', 'mean')).reset_index()
    seeds.to_csv(api.OUT/'H59_seed_summary.csv', index=False)
    figure, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    test_matrix = tables['test'].groupby(['option_id','file']).average_mape.mean().unstack()
    for axis, data, title in zip(axes, [matrix, test_matrix], ['Train fixed LOFO', 'Previously exposed test; frozen diagnostics']):
        axis.imshow(data.to_numpy(), aspect='auto', cmap='Blues', vmin=0, vmax=15)
        axis.set_xticks(range(4), [s.replace('.wav','') for s in data.columns], rotation=25)
        axis.set_yticks(range(len(data)), data.index, fontsize=8)
        for i in range(len(data)):
            for j in range(4):
                axis.text(j,i,f'{data.iloc[i,j]:.3f}',ha='center',va='center',color='white' if data.iloc[i,j]>7 else 'black')
        axis.set_title(title, fontsize=10)
    figure.suptitle('H59 Average MAPE (%) — mean of three seeds; all-file target <2%')
    figure.tight_layout()
    save_figure(figure, 'H59_context_matrix')
    freeze = json.loads((api.OUT/'H59_FROZEN_SELECTION.json').read_text())
    selected = freeze['option']['id']
    full = '|'.join(names)
    status = []
    for stage, table in tables.items():
        for _, r in table[(table.fit_pool==full) & (table.option_id==selected)].iterrows():
            status.append(dict(stage=stage,file=r['file'],seed=int(r.seed),average_mape=float(r.average_mape),strict_below_2=bool(r.average_mape<2)))
    pd.DataFrame(status).to_csv(api.OUT/'H59_selected_all_files.csv', index=False)
    train_receipt = json.loads((api.OUT/'H59_train_experiment.json').read_text())
    test_receipt = json.loads((api.OUT/'H59_test_experiment.json').read_text())
    test = tables['test'][tables['test'].seed==11]
    transitions_display = transition_table[(transition_table.seed==11) & (transition_table.fit_pool.str.count(r'\|')>=2)]
    text = '''# H59 — thêm ngữ cảnh thời gian, chưa cải thiện cấu hình chung

**Mục tiêu cả tám file Average MAPE <2% vẫn chưa đạt.** Final giữ hard170: 4/4 train,0/4 test dưới 2%. Không promote H59. Nhánh Markov .25 chẩn đoán đạt studio_M2 dưới 2%, nhưng các file khác và recall V không đáp ứng yêu cầu; không dùng kết quả test này để chọn cấu hình.

## H59 kiểm tra điều gì?

H58 học trọng số hữu thanh của ba cụm GMM nhưng chấm từng khung riêng. H59 giữ các trọng số đó, thêm quy luật chuyển trạng thái giữa khung liền kề để thử giữ đoạn V yếu gần V mạnh. N là UV hoặc SIL; V là hữu thanh theo LAB. Counts chuyển trạng thái học từ đúng các file train của từng fit pool, không nối hai file, không dùng nhãn held/test. Điểm chuỗi tính bằng forward-backward.

Chỉ đổi điểm dùng để loại original baseline V. Recovery mask, F0 bound200, framing, GMM và mapping H58 giữ nguyên. Static .25 là control trực tiếp; ba ngưỡng Markov .1/.25/.5 đăng ký trước đo. H58 score được dùng như unary potential, chưa chứng minh là emission likelihood hay calibrated probability. Đây là chuỗi custom suy luận offline có dùng khung tương lai, không phải chứng nhận một HMM generative hoặc streaming implementation.

## Ma trận train và seed

'''+api.audit.markdown_table(matrix.reset_index())+'''

![Ma trận](figures/H59_context_matrix.png)

'''+api.audit.markdown_table(seeds)+'''

Mọi cấu hình Markov đều có ít nhất một file train vượt 2%; không nhánh nào được chọn. Riêng phone_F1 ở q=.1 đạt 2.00385%, vẫn vượt mục tiêu dù làm tròn hai chữ số có thể hiện 2.00. Final chọn hard170; outer giữ phone_M1 chọn recovery_only, ba outer khác chọn control. Nested bốn file train <2% qua ba seed nhưng ba gate giảm MAPE FAIL, không promote. Kết quả này không biến thành một pipeline mới tốt hơn baseline chỉ vì nested giữ fallback tốt.

## Khung bị loại và ngữ cảnh

'''+api.audit.markdown_table(audits[(audits.seed==11) & audits.option_id.isin(['mapped_rejection_025','markov_rejection_025'])])+'''

`longest_consecutive_removed_v` là số khung LAB V bị loại liền nhau, không phải số đoạn độc lập hay số cao độ được xác minh sai. Các khung25ms/hop10ms chồng nhau. H59 giảm loại ở phone nhưng có thể kéo dài quyết định N ở các chuỗi V với điểm GMM yếu, làm hai studio train xấu hơn. Không diễn giải mọi frame bị loại là UV thật hoặc reference F0 không hợp lệ.

![Điểm theo thời gian](figures/H59_context_scores.png)

Hình fixedLOFO seed11 tô xanh LAB V; đường xanh là điểm H58, cam là marginal H59. H59_score_traces.csv giữ toàn bộ khung của tám file cho so sánh .25, H59_changed_cases.csv giữ mọi khung đổi quyết định, điểm trước/sau và khoảng cách tới biên. F0 ở case là baseline estimate, không phải ground truth từng khung. Audit giữ cả tác động tốt và xấu.

## Điểm dự đoán và transition

'''+api.audit.markdown_table(quality.groupby('file').mean(numeric_only=True).drop(columns='seed').reset_index())+'''

Brier là trung bình bình phương chênh lệch với nhãn LAB V=1,UV/SIL=0 trên held train; nhỏ hơn tốt hơn cho tiêu chí này. Đây là mô tả, không chứng nhận calibration hoặc valid-F0 count. Ngữ cảnh không sửa được sai lệch kéo dài của unary score; một score yếu liên tục có thể khiến chuỗi tự tin hơn vào N và làm mất V. Bảng/hình cho phép kiểm tra cơ chế này, không suy ra toàn bộ temporal models đều thất bại.

Ví dụ studio_F1: Brier giảm khoảng .1183→.1053 nhưng q=.25 loại LAB V tăng từ 3 lên 25 khung và Average MAPE tăng 2.30425→8.43208%. Điểm tổng hợp tốt hơn không bảo đảm subset F0 tốt hơn ở ngưỡng đã chọn. Trên studio_M1, số LAB V bị loại tăng 0→19; bảng case giữ cả những đoạn bị kéo về N dù thuộc LAB V. Các cửa sổ chồng nhau làm bằng chứng giữa khung có tương quan; việc nhân unary potentials trong chuỗi này chưa được kiểm chứng như các emission độc lập.

'''+api.audit.markdown_table(transitions_display[['fit_pool','initial_v','p_00','p_01','p_10','p_11']])+'''

H59_transition_audit.csv có đủ33records tương ứng33model IDs nhưng chỉ11fit pools; transition deterministic không đổi theo seed. GMM/mapping có seed variation như H56/H58. Mọi counts và smoothing1 đều lưu để kiểm tra.

## Test đã khóa trước

'''+api.audit.markdown_table(test[['file','option_id','average_mape','F0mean_mape','F0std_mape','F0num_mape','recall_v','removed']])+'''

Markov .25 giảm studio_M2 xuống khoảng0.73% và phone_M2 xuống khoảng5.71%, nhưng phone_F2/studio_F2 xấu hơn. Recall V studio_M2 từbaseline .921875 xuống .875, phone_M2 từ .970149 xuống .925373. Vì vậy không gọi đây là cải thiện được chấp nhận; .25 không được train chọn và không đạt cả bốn test. Không ghép nhánh tốt theo file hoặc chọn seed từ test. Thống kê count gần reference hơn cũng không chứng minh đã chọn đúng frame F0, vì BT2 chỉ có LAB theo đoạn và 3GT cả file.

Toàn bộ metric mean/std/count, mean/std MAE,F1/recallV/recallUV/balancedaccuracy/SIL và ba seed có trong H59_test_fixed.csv. Test có lịch sử exposure; freeze ngăn chọn tham số trong vòng H59 nhưng không tạo ra independent test mới.

## Kiểm tra và kết luận

Prereg `{prereg}` và freeze `{freeze}` đã push và remote-SHA verified trước train/test tương ứng. Verifier PASS360 train/48test groups,288inner records/72summary rows; scalar Gaussian/mapping, transition poolcounts, scaled forward-backward, static parity H58, pitch/mask, metrics/folds/selection/gates/hashes. Synthetic enumeration2^N kiểm chuỗi1/2/5/6; uniform-transition parity, chuỗi2000frames finite, held-label poisoning và file-boundary counts PASS. Không refit optimizer/native pipeline và không fit gì trên test. Giữ notebook nộp,WAV/LAB,3GT và frozen baseline.

H59 bổ sung một hướng chưa có ở H58: temporal context riêng cho rejection. Đo cho thấy smoothing này có thể làm mất nhiều V khi unary score yếu kéo dài. Chưa đủ bằng chứng để đổ lỗi cho test, số lượng data hoặc nhãn thầy; cũng không nên tiếp tục tăng độ mượt trên cùng score mà coi đó là sửa được cơ chế. Muốn kiểm nghiệm hướng mới cần thay score/đặc trưng bằng giả thuyết riêng, hoặc xác minh quy trình/reference F0 hợp lệ để tách mục tiêu LAB V khỏi thống kê3GT. Reference từng khung hoặc corpus độc lập mới giúp xác nhận, không lấy estimated contour làm truth.

Lệnh markov_rejection.py precheck/register/train/test; verify_markov_rejection.py train/test; report_markov_rejection.py. Source/registry/rawresults/failures giữ nguyên; no Drive/DL/PDF/Jev/prose skill, không rerun các vòng cũ. BT2 vẫn trước bài segmentation mới.
'''
    text = text.replace('{prereg}',train_receipt['measured_commit']).replace('{freeze}',test_receipt['measured_commit'])
    (api.HERE/'H59_REPORT.md').write_text(text, encoding='utf-8')
    outputs = [api.HERE/'H59_REPORT.md'] + [api.OUT/f'H59_{name}.csv' for name in ('removed_label_audit','held_train_score_quality','changed_cases','score_traces','transition_audit','seed_summary','selected_all_files')] + list((api.HERE/'figures').glob('H59_context_*'))
    api.audit.json_write(api.OUT/'H59_reporting.json',dict(passed=True,selected=selected,
        all_eight_target_met=all(r['strict_below_2'] for r in status),new_measurements=0,historical_test_exposure=True,
        source_sha256=api.audit.digest(__file__),runtime=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__,pandas=pd.__version__),
        input_hashes={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in inputs},
        outputs={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in outputs}))
    print('H59 report/audits saved; all-eight target FAIL; baseline preserved')


if __name__ == '__main__':
    build()
