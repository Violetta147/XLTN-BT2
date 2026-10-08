import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scipy
import sklearn
import mapped_rejection as api
from verify_srh import independent_item


def build():
    inputs = [api.OUT/'H58_mappings.json', api.OUT/'H56_models.json',
              api.OUT/'H57_train_proofs.json', api.OUT/'H57_test_proofs.json']
    models = json.loads((api.OUT/'H56_models.json').read_text())
    mappings = json.loads((api.OUT/'H58_mappings.json').read_text())
    bank = api.source.bank_train()
    names = sorted(bank)
    tables, audits, cases, quality = {}, [], [], []
    for stage in ('train', 'test'):
        verification = api.OUT/f'H58_{stage}_verification.json'
        assert json.loads(verification.read_text())['passed']
        fixed = api.OUT/f'H58_{stage}_fixed.csv'
        tables[stage] = pd.read_csv(fixed, float_precision='round_trip')
        proof_path = api.OUT/f'H58_{stage}_proofs.json'
        proofs = json.loads(proof_path.read_text())
        old = json.loads((api.OUT/f'H57_{stage}_proofs.json').read_text())
        original = json.loads((api.OUT/f'H56_{stage}_proofs.json').read_text())
        inputs += [verification, fixed, proof_path, api.OUT/f'H56_{stage}_proofs.json']
        for name in sorted(tables[stage].file.unique()):
            fit = [n for n in names if n != name] if stage == 'train' else names
            path = (api.core.TRAIN if stage == 'train' else api.REPO/'TinHieuKiemThu')/name
            item, _, _ = independent_item(path, stage)
            segments = api.core.read_segments(path.with_suffix('.lab'))
            boundaries = np.array([b for a, b, label in segments[:-1]])
            for seed in api.SEEDS:
                mid = next(i for i, m in enumerate(models) if m['fit_files'] == fit and m['seed'] == seed)
                base = next(p for p in proofs if p['file'] == name and p['model_id'] == mid and p['option_id'] == 'hard170')
                baseline = np.array(base['pred'], bool)
                selected = [p for p in proofs if p['file'] == name and p['model_id'] == mid and p['option_id'].startswith('mapped_rejection')]
                for p in selected:
                    mask = baseline & ~np.array(p['pred'], bool)
                    audits.append(dict(stage=stage, file=name, seed=seed, option_id=p['option_id'],
                        removed=int(mask.sum()), removed_v=int(sum(mask & (item['labels'] == 'v'))),
                        removed_uv=int(sum(mask & (item['labels'] == 'uv'))), removed_sil=int(sum(mask & (item['labels'] == 'sil')))))
                    if seed == 11 and p['option_id'] == 'mapped_rejection_025':
                        prior = next(o for o in old if o['file'] == name and o['model_id'] == mid and o['option_id'] == 'two_sided_025')
                        prior_mask = baseline & ~np.array(prior['pred'], bool)
                        audits.append(dict(stage=stage, file=name, seed=seed, option_id='H57_single_cluster_025',
                            removed=int(prior_mask.sum()), removed_v=int(sum(prior_mask & (item['labels'] == 'v'))),
                            removed_uv=int(sum(prior_mask & (item['labels'] == 'uv'))), removed_sil=int(sum(prior_mask & (item['labels'] == 'sil')))))
                        for i in np.flatnonzero(mask):
                            cases.append(dict(stage=stage, file=name, frame=int(i), time=float(item['times'][i]),
                                label=str(item['labels'][i]), score=float(p['prob'][i]),
                                removed_f0=float(base['f0'][i]),
                                nearest_boundary_ms=float(np.min(abs(boundaries-item['times'][i]))*1000)))
                if stage == 'train':
                    membership = next(p for p in original if p['file'] == name and p['model_id'] == mid and p['option_id'] == 'recovery_bound_200')['prob']
                    mapped = np.array(base['prob'])
                    target = (item['labels'] == 'v').astype(float)
                    assert np.isin(item['labels'], ['v', 'uv', 'sil']).all()
                    quality.append(dict(file=name, seed=seed, frames=len(target),
                        single_cluster_brier=float(np.mean((np.array(membership)-target)**2)),
                        mapped_brier=float(np.mean((mapped-target)**2)),
                        lab_v_mean_score=float(mapped[item['labels']=='v'].mean()),
                        baseline_v_min_score=float(mapped[baseline].min())))
    audits = pd.DataFrame(audits)
    audits.to_csv(api.OUT/'H58_removed_label_audit.csv', index=False)
    pd.DataFrame(cases).to_csv(api.OUT/'H58_removed_cases.csv', index=False)
    quality = pd.DataFrame(quality)
    quality.to_csv(api.OUT/'H58_held_train_score_quality.csv', index=False)
    components = []
    for mid, (model, mapping) in enumerate(zip(models, mappings)):
        for k in range(3):
            components.append(dict(model_id=mid, fit_pool='|'.join(model['fit_files']), seed=model['seed'],
                component=k, mass=mapping['mass'][k], voiced_mass=mapping['voiced_mass'][k],
                voiced_weight=mapping['weights'][k], originally_selected=k==model['component']))
    pd.DataFrame(components).to_csv(api.OUT/'H58_component_mappings.csv', index=False)
    fixed = tables['train'][tables['train'].fit_pool.str.count(r'\|') == 2]
    matrix = fixed.groupby(['option_id', 'file']).average_mape.mean().unstack().loc[list(api.BY_ID)]
    seed_summary = fixed.groupby(['option_id', 'seed']).agg(mean_mape=('average_mape', 'mean'),
        worst_mape=('average_mape', 'max'), removed=('removed', 'sum'), recall_v=('recall_v', 'mean')).reset_index()
    seed_summary.to_csv(api.OUT/'H58_seed_summary.csv', index=False)
    test_matrix = tables['test'].groupby(['option_id', 'file']).average_mape.mean().unstack()
    figures = api.HERE/'figures'
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.3))
    for axis, data, title in zip(axes, [matrix, test_matrix], ['Train fixed LOFO', 'Previously exposed test; frozen diagnostics']):
        axis.imshow(data.to_numpy(), aspect='auto', cmap='Blues', vmin=0, vmax=17)
        axis.set_xticks(range(4), [s.replace('.wav', '') for s in data.columns], rotation=25)
        axis.set_yticks(range(len(data)), data.index, fontsize=8)
        for i in range(len(data)):
            for j in range(4):
                axis.text(j, i, f'{data.iloc[i,j]:.2f}', ha='center', va='center', color='white' if data.iloc[i,j] > 7 else 'black')
        axis.set_title(title, fontsize=10)
    figure.suptitle('H58 Average MAPE (%) — mean of three seeds; all-file target <2%')
    figure.tight_layout()
    for suffix in ('png', 'svg'):
        figure.savefig(figures/f'H58_mapping_matrix.{suffix}', dpi=170)
    svg = figures/'H58_mapping_matrix.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n', encoding='utf-8')
    plt.close(figure)
    freeze = json.loads((api.OUT/'H58_FROZEN_SELECTION.json').read_text())
    selected = freeze['option']['id']
    full = '|'.join(names)
    status = []
    for stage, table in tables.items():
        for _, r in table[(table.fit_pool == full) & (table.option_id == selected)].iterrows():
            status.append(dict(stage=stage, file=r['file'], seed=int(r.seed), average_mape=float(r.average_mape), strict_below_2=bool(r.average_mape < 2)))
    pd.DataFrame(status).to_csv(api.OUT/'H58_selected_all_files.csv', index=False)
    measured = [json.loads((api.OUT/f'H58_{stage}_experiment.json').read_text()) for stage in ('train', 'test')]
    text = '''# H58 — mapping có giám sát giảm loại nhầm, chưa cải thiện cấu hình chung

**Chưa đạt mục tiêu mỗi file Average MAPE <2%.** Final vẫn chọn hard170. Baseline có 4/4 train và 0/4 test dưới 2%; không promote H58. Học ý nghĩa của cả ba cụm GMM đã giảm số khung hữu thanh bị loại so với H57, nhưng không đủ để cải thiện thống kê F0 trên mọi file.

## Thay đổi đã đo

GMM là mô hình hỗn hợp Gaussian, dùng ở đây để nhóm khung theo bốn đặc trưng tín hiệu. H57 lấy xác suất thuộc duy nhất cụm có tính chu kỳ cao nhất để loại khung. H58 học trọng số hữu thanh của cả ba cụm từ nhãn LAB trong từng fit pool, rồi cộng membership có trọng số. Clustering giữ nguyên; bước mapping **có giám sát**. Các file bị giữ ra để kiểm tra không cung cấp nhãn cho mapping.

Giữ nguyên recovery và F0 bound200 của H56; chỉ thay điểm rejection cho original baseline V. Vì vậy, so sánh H57/H58 cùng ngưỡng là ablation của mapping rejection. Ba ngưỡng cố định .1/.25/.5 được chọn trên train; không chọn từ test. Giữ đủ seed11/29/47 và 33 mapping ứng với đúng 33 GMM đã lưu, không fit lại optimizer.

## Train: ma trận và độ nhạy theo seed

'''+api.audit.markdown_table(matrix.reset_index())+'''

![Ma trận H58](figures/H58_mapping_matrix.png)

'''+api.audit.markdown_table(seed_summary)+'''

Với q=.1, phone_M1 còn dưới 2%, nhưng studio_F1/studio_M1 đều vượt 2%. Với q=.25, phone_M1 vẫn mất nhiều khung V; không đạt guard recall và không được chọn. Final hard170; outer phone_M1 chọn recovery_only, ba outer khác hard170. Nested bốn train dưới 2% qua cả ba seed, nhưng ba gate giảm MAPE không đạt. Đây không phải một cấu hình cuối cùng mới có kết quả tốt hơn baseline.

## Loại khung: so sánh trực tiếp H57/H58

'''+api.audit.markdown_table(audits[(audits.seed==11) & audits.option_id.isin(['mapped_rejection_025','H57_single_cluster_025'])])+'''

Các con số trên cùng file, fit pool, seed11, mask recovery, pitch và ngưỡng .25. Có ít khung bị loại nhầm hơn nhưng vẫn có LAB V bị loại. Việc giảm sai số count không bảo đảm giảm Average MAPE: chọn subset khác cũng thay mean và std. Mỗi khung bị loại, score và khoảng cách tới biên LAB lưu trong H58_removed_cases.csv; F0 trong bảng là ước lượng trước loại, không phải reference từng khung.

## Điểm dự đoán trên file train được giữ ra

'''+api.audit.markdown_table(quality.groupby('file').mean(numeric_only=True).drop(columns='seed').reset_index())+'''

Brier score là trung bình bình phương chênh lệch giữa điểm dự đoán và nhãn V=1, UV/SIL=0; thấp hơn là tốt hơn cho phép đối chiếu này. Chỉ tính trên fixed LOFO train. Bảng mô tả chất lượng điểm, không chứng minh calibration hay đảm bảo ngưỡng có thể chuyển sang file mới. So sánh với membership một cụm cũng không biến membership đó thành xác suất V đã hiệu chỉnh. H58_component_mappings.csv giữ 99 trọng số của 33 mô hình; ID cụm thuộc từng mô hình, không mặc nhiên tương ứng giữa các seed/pool.

## Test chẩn đoán đã khóa

'''+api.audit.markdown_table(tables['test'][tables['test'].seed==11][['file','option_id','average_mape','F0mean_mape','F0std_mape','F0num_mape','recall_v','removed']])+'''

Không nhánh nào đạt cả bốn test <2%. Recovery_only vẫn giảm studio_F2 xuống khoảng 3.44%, nhưng không được train chọn và chưa đạt 2%; mapping .25 làm file đó xấu hơn. Các nhánh chẩn đoán không phải kết quả promoted. Toàn bộ metric/seed lưu trong H58_test_fixed.csv, gồm mean/std MAE, F1, hai recall, balanced accuracy và SIL false positives. Test có lịch sử đã xem nhiều lần; freeze ngăn chọn tham số trong vòng H58, không biến test thành kiểm chứng độc lập mới.

## Kết luận và giới hạn

H57 cho thấy bỏ tất cả cụm ngoài cụm chu kỳ mạnh làm mất V. H58 kiểm tra được cách sửa lỗi mapping đó, nhưng ba cụm với một trọng số V cố định cho mỗi cụm vẫn không đủ cho quyết định F0 hợp lệ trên các file hiện có. Đây là giới hạn của cơ chế đã thử; chưa chứng minh mọi phương pháp ML thất bại, test/GT sai hay thiếu dữ liệu là nguyên nhân duy nhất. LAB V và số F0 hợp lệ trong 3GT mô tả hai mục tiêu khác nhau; không sửa nhãn để khớp điểm.

Ưu tiên tiếp theo là xác minh quy trình tạo F0mean/F0std/F0num (cửa sổ, bước khung, ngưỡng hữu thanh, bỏ biên và cách tính std) hoặc có reference từng khung đáng tin cậy trước khi thử thêm ngưỡng cùng cơ chế. Dữ liệu bổ sung có người nói khác và protocol cố định mới có thể cung cấp kiểm chứng độc lập; nhân bản cùng bản thu không tạo thêm người nói độc lập. Bài segmentation mới vẫn sau ưu tiên BT2.

## Kiểm tra và tái lập

Prereg `{prereg}` và freeze `{freeze}` đã push và xác minh SHA remote trước lần đo train/test tương ứng. Verifier PASS300 train/36 test groups,240 inner records,72 summary rows: scalar Gaussian/mapping, fold exclusion, selection/gates, mask/pitch, metrics và hashes. Synthetic precheck kiểm permutation cụm, poisoning nhãn held file, sensitivity nhãn fit, threshold ties và pitch giữ nguyên. Optimizer/PCM được reuse từ H56/H50 đã kiểm; không claim refit optimizer độc lập. Test không học mapping mới. Original notebook/WAV/LAB/teacher3GT/frozen config được giữ nguyên.

Lệnh: `mapped_rejection.py precheck/register/train/test`, `verify_mapped_rejection.py train/test`, `report_mapped_rejection.py`. No Drive, DL, PDF, Jev hoặc prose skill. Không chạy lại các vòng cũ; giữ toàn bộ thất bại và baseline.
'''
    text = text.replace('{prereg}', measured[0]['measured_commit']).replace('{freeze}', measured[1]['measured_commit'])
    (api.HERE/'H58_REPORT.md').write_text(text, encoding='utf-8')
    outputs = [api.HERE/'H58_REPORT.md'] + list(api.OUT.glob('H58_*audit.csv')) + [api.OUT/f'H58_{name}.csv' for name in ('removed_cases','held_train_score_quality','component_mappings','seed_summary','selected_all_files')] + list(figures.glob('H58_mapping_matrix.*'))
    api.audit.json_write(api.OUT/'H58_reporting.json', dict(passed=True, selected=selected,
        all_eight_target_met=all(r['strict_below_2'] for r in status), new_measurements=0,
        historical_test_exposure=True, source_sha256=api.audit.digest(__file__),
        runtime=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, sklearn=sklearn.__version__, pandas=pd.__version__),
        input_hashes={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in inputs},
        outputs={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in outputs}))
    print('H58 report and audits saved; all-eight target remains FAIL')


if __name__ == '__main__':
    build()
