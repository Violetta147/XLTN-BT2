import json
from pathlib import Path

import numpy as np
import pandas as pd
import voicing_matrix as api


def main():
    receipt=json.loads((api.OUT/'H51_train_verification.json').read_text())
    assert receipt['passed'] and receipt['experiment_sha256']==api.audit.digest(api.OUT/'H51_train_experiment.json')
    experiment=json.loads((api.OUT/'H51_train_experiment.json').read_text())
    for path,digest in experiment['artifacts'].items():assert api.audit.digest(api.REPO/path)==digest
    selections={row['outer_held']:row['recipe_id'] for row in experiment['selections']}
    items=api.core.load_training();rows=[];cases=[];counts=[]
    for item in items:
        name=item['file'];bank=dict(np.load(api.OUT/f'H50_design_{Path(name).stem}.npz',allow_pickle=False))
        data=dict(np.load(api.OUT/f'H51_predictions_{Path(name).stem}.npz',allow_pickle=False))
        count=int((item['labels']=='v').sum());gt=item['stats']['F0num'];count_error=100*abs(count-gt)/gt
        counts.append(dict(file=name,center_v_frames=count,reference_F0num=gt,count_mape_if_exact_v_and_all_finite=count_error,
                           average_mape_contribution_if_other_components_zero=count_error/3))
        for seed in api.SEEDS:
            idx=int(np.flatnonzero((data['recipe_id']==selections[name])&(data['seed']==seed))[0])
            new=data['recover'][idx];before=bank['base_f0'];after=data['f0'][idx]
            old=before[np.isfinite(before)];added=after[new]
            row=dict(seed=seed,file=name,recipe_id=selections[name],old_count=len(old),new_count=int(np.isfinite(after).sum()),reference_count=gt,
                     old_mean=float(old.mean()),new_mean=float(np.nanmean(after)),old_std=float(old.std()),new_std=float(np.nanstd(after)),
                     added_frames=len(added),added_v=int((new&(item['labels']=='v')).sum()),added_non_v=int((new&(item['labels']!='v')).sum()))
            if len(added):
                w0,w1=len(old)/(len(old)+len(added)),len(added)/(len(old)+len(added))
                between=w0*w1*(old.mean()-added.mean())**2
                within=w0*old.var()+w1*added.var()
                assert np.isclose(within+between,np.nanvar(after),atol=1e-10)
                row.update(added_mean=float(added.mean()),added_std=float(added.std()),within_variance_hz2=float(within),between_variance_hz2=float(between))
            else:row.update(added_mean=np.nan,added_std=np.nan,within_variance_hz2=float(old.var()),between_variance_hz2=0.)
            for key,estimate0,estimate1 in [('F0mean',old.mean(),np.nanmean(after)),('F0std',old.std(),np.nanstd(after)),('F0num',len(old),int(np.isfinite(after).sum()))]:
                reference=item['stats'][key];row[key+'_mape_before']=100*abs(estimate0-reference)/reference;row[key+'_mape_after']=100*abs(estimate1-reference)/reference
            rows.append(row)
            if seed==11:
                for i in np.flatnonzero(new):
                    voiced=np.flatnonzero(bank['base_pred']);distance=abs(bank['times'][voiced]-bank['times'][i]);j=voiced[np.argmin(distance)]
                    cases.append(dict(file=name,recipe_id=selections[name],time_s=bank['times'][i],center_label=item['labels'][i],boundary=bool(item['boundary'][i]),
                        added_estimated_f0_hz=after[i],periodicity=bank['x'][i,0],relative_rms=float(np.exp(bank['x'][i,1])),zcr_per_second=bank['x'][i,2],
                        high_frequency_ratio=bank['x'][i,3],nearest_baseline_time_s=bank['times'][j],nearest_baseline_estimated_f0_hz=before[j],
                        distance_ms=distance.min()*1000,per_frame_pitch_truth_available=False))
    api.write_csv('H51_selected_recovery_decomposition.csv',rows);api.write_csv('H51_selected_recovery_cases.csv',cases);api.write_csv('H51_label_count_tradeoff.csv',counts)
    fixed=pd.read_csv(api.OUT/'H51_fixed_lofo.csv')
    final=selections['final'];control=fixed[fixed.recipe_id=='hard170'];candidate=fixed[fixed.recipe_id==final]
    identical=all(np.allclose(control.sort_values(['file','seed'])[key],candidate.sort_values(['file','seed'])[key],atol=1e-10)
                  for key in ('average_mape','F0mean','F0std','F0num','macro_f1','recall_v','recovered'))
    text=['# Diễn giải cơ chế và lỗi H51','',
          f'Cấu hình final là {final}. Fixed LOFO của nó bằng control hard170 ở mọi file và seed: **{identical}**. Khi hòa điểm, quy tắc chọn ID đã đăng ký quyết định cấu hình; đây không phải cải thiện pipeline. Các outer folds vẫn đánh giá recipe riêng do bước chọn bên trong quyết định.','',
          'Bảng dưới phân rã những khung mới của cấu hình được chọn ở từng outer fold. Chỉ trình bày seed 11 cho gọn; CSV lưu đủ ba seed. V/UV/SIL là nhãn tại tâm khung, không xác nhận F0 của khung đó.','',
          api.audit.markdown_table(pd.DataFrame(rows).query('seed == 11')[['file','recipe_id','added_frames','added_v','added_non_v','old_count','new_count','old_std','new_std','added_mean','between_variance_hz2']]),'',
          'Chi tiết khung mới và F0 ước lượng gần nhất của baseline:','',api.audit.markdown_table(pd.DataFrame(cases)),'',
          'Khi thêm một nhóm F0 có mean xa mean cũ, phương sai tăng qua thành phần giữa hai nhóm: w0×w1×(mean0−mean1)². Đã kiểm độc lập rằng phương sai trong nhóm cộng thành phần này khớp phương sai toàn bộ output. Vì vậy một khung có nhãn V đúng vẫn có thể làm F0std MAPE tăng mạnh nếu cao độ ước lượng của nó lệch xa phần còn lại. Cần tách hai câu hỏi: khung có hữu thanh không, và cao độ được ước lượng có đúng không.','',
          'Ma trận H51 cô lập các đầu vào/mô hình phân loại nhưng dùng chung ACF để lấy pitch của khung khôi phục. Nó chưa cô lập được chất lượng pitch này với quyết định khôi phục. Kết quả thất bại không chứng minh ML, MFCC hoặc miền tần số nói chung không hữu ích. Các estimated pitch gần nhau cũng chưa thay thế ground truth.','',
          'ML ở đây học quyết định V so với UV/SIL, không học hồi quy F0 từng khung: BT2 chưa có nhãn cao độ chuẩn theo thời gian. Ba thống kê mean/std/count của cả file chỉ dùng đánh giá và chọn cấu hình trên train. Chúng không xác định duy nhất contour; đảo thứ tự cùng các giá trị F0 vẫn giữ ba thống kê nhưng có thể sai ở từng timestamp. Vì vậy không thể lấy một MAPE nhỏ để kết luận toàn bộ cao độ đã đúng.','',
          'LAB và F0num đo những thứ khác nhau:','',api.audit.markdown_table(pd.DataFrame(counts)),'',
          'Ví dụ studio_M1 có 94 khung tâm V, F0num chuẩn là 82. Nếu phát F0 hữu hạn đúng ở mọi tâm V và không phát ngoài V, count MAPE sẽ là 14,63%; riêng phần count đã đóng góp 4,88 điểm phần trăm vào Average MAPE. Đây là kết quả có điều kiện của giả thuyết trên, không phải cận dưới cho mọi mô hình. Mô hình có thể không phát F0 ở một số khung V. V theo đoạn ngữ âm cũng không nhất thiết đồng nghĩa mọi cửa sổ đều có F0 ước lượng hợp lệ.','',
          'Chưa biết cách thầy tạo mean/std/count: độ dài, độ dịch và tâm khung, điều kiện giữ F0, xử lý biên, engine và ngưỡng. Không đủ bằng chứng kết luận thầy ghi nhầm hoặc sửa sai. Không đổi LAB để đạt điểm. Cần cùng lúc giữ các lỗi MAPE, F1/recall và SIL để thấy sự đánh đổi.','',
          'Phạm vi đã chạy và những hướng chưa thuộc ma trận này được ghi trong EXPERIMENT_COVERAGE.md. Lỗi parser của verifier v1 và bản kiểm tra v2 nằm ở H51_VERIFICATION_REPAIR.md; mọi source đăng ký và output đo được giữ nguyên.']
    path=api.HERE/'H51_INTERPRETATION.md';path.write_text('\n'.join(text)+'\n',encoding='utf-8')
    api.audit.json_write(api.OUT/'H51_interpretation_receipt.json',dict(verified_input_only=True,variance_decomposition_verified=True,
        final_equals_control_fixed_lofo=identical,artifacts={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in
        [path,api.OUT/'H51_selected_recovery_decomposition.csv',api.OUT/'H51_selected_recovery_cases.csv',api.OUT/'H51_label_count_tradeoff.csv']}))
    print('Wrote verified recovery and label/count interpretation; final-control equality:',identical)


if __name__=='__main__':main()
