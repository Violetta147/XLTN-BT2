import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import bounded_srh as api


def build():
    tables=[];changes=[];inputs=[]
    for stage in ('train','test'):
        receipt=api.OUT/f'H55_{stage}_verification.json';assert json.loads(receipt.read_text())['passed'];inputs.append(receipt)
        path=api.OUT/f'H55_{stage}_fixed.csv';inputs.append(path)
        table=pd.read_csv(path,float_precision='round_trip');table['stage']=stage;tables.append(table)
        for path in sorted(api.OUT.glob(f'H55_{stage}_predictions_*.npz')):
            inputs.append(path);output=dict(np.load(path,allow_pickle=False));stem=path.stem.replace(f'H55_{stage}_predictions_','')
            base=int(np.flatnonzero(output['option_id']=='hard170')[0])
            for k,identity in enumerate(output['option_id']):
                if identity=='hard170':continue
                pred=output['pred'][base];assert np.array_equal(pred,output['pred'][k])
                distance=abs(1200*np.log2(output['f0'][k,pred]/output['f0'][base,pred]))
                changes.append(dict(stage=stage,file=stem+'.wav',option_id=identity,voiced_count=int(sum(pred)),
                    changed_pitch_count=int(sum(output['f0'][k,pred]!=output['f0'][base,pred])),
                    median_abs_change_cents=float(np.median(distance)),largest_abs_change_cents=float(max(distance)),
                    same_mask_count_vuv_sil=True,frame_f0_truth_available=False))
    allrows=pd.concat(tables,ignore_index=True);allrows.to_csv(api.OUT/'H55_all_metrics.csv',index=False)
    pd.DataFrame(changes).to_csv(api.OUT/'H55_pitch_changes.csv',index=False)
    selected=json.loads((api.OUT/'H55_FROZEN_SELECTION.json').read_text())['option']['id']
    status=allrows[allrows.option_id==selected].copy();status['strict_below_2']=status.average_mape<2
    status.to_csv(api.OUT/'H55_selected_all_files.csv',index=False)
    comparison=[]
    for stage in ('train','test'):
        for family,identity,label in [('H54','hard170','baseline'),('H54','srh_w100_pitch_only','SRH unbounded'),('H55','srh_bound_200','SRH bound 200c')]:
            path=api.OUT/f'{family}_{stage}_fixed.csv';inputs.append(path);table=pd.read_csv(path,float_precision='round_trip')
            for _,row in table[table.option_id==identity].iterrows():comparison.append(dict(stage=stage,file=row['file'],method=label,average_mape=row.average_mape))
    comparison=pd.DataFrame(comparison);comparison.to_csv(api.OUT/'H54_H55_diagnostic_comparison.csv',index=False)
    matrix=comparison.pivot(index=['stage','file'],columns='method',values='average_mape')
    matrix=matrix.loc[[('train',f) for f in sorted(tables[0].file.unique())]+[('test',f) for f in sorted(tables[1].file.unique())],['baseline','SRH unbounded','SRH bound 200c']]
    figure,axis=plt.subplots(figsize=(8,6))
    axis.imshow(matrix.to_numpy(),aspect='auto',cmap='Blues',norm=LogNorm(vmin=.3,vmax=20))
    axis.set_xticks(range(3),matrix.columns);axis.set_yticks(range(8),[f'{s} {f.replace(".wav","")}' for s,f in matrix.index])
    for i in range(8):
        for j in range(3):axis.text(j,i,f'{matrix.iloc[i,j]:.3f}',ha='center',va='center',color='white' if matrix.iloc[i,j]>4 else 'black')
    axis.axhline(3.5,color='black',lw=1);axis.set_title('Average MAPE (%): fixed diagnostics, not selected models')
    figure.tight_layout();figures=api.HERE/'figures';figures.mkdir(exist_ok=True)
    for suffix in ('png','svg'):figure.savefig(figures/f'H55_bounded_comparison.{suffix}',dpi=160)
    plt.close(figure)
    columns=['option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','F0mean_abs_error','F0std_abs_error','macro_f1','recall_v','recall_uv','balanced_accuracy','false_voiced_sil']
    train=tables[0].pivot(index='option_id',columns='file',values='average_mape').loc[[o['id'] for o in api.OPTIONS]]
    report='''# H55 — giới hạn đỉnh SRH quanh baseline

**Chưa tìm được cấu hình chung vượt baseline.** Sau ba khoảng100/200/400cents, lựa chọn cuối và cả bốn outer pools đều giữ hard170. Bốn train của baseline vẫn <2%; cả bốn test còn >2%. Mục tiêu mỗi tám file <2% chưa đạt, pipeline và notebook đã nộp không đổi.

Vòng này kiểm tra đúng một thay đổi: thay chọn đỉnh SRH toàn range bằng chọn đỉnh trong vùng quanh F0 baseline.1200cents là tỉ lệ tần số2;200cents khoảng tỉ lệ1.122. Giữ source window100ms, reuse các proof H54 đã verified và hash-protected, không rerun estimator. Mask/count/VUV/SIL giữ nguyên; không mô hình fit hoặc seed. Tần số mới integer1Hz vì source SRH nên hầu hết khung thay nhẹ ngay cả khi chưa đổi peak đáng kể.

## Train và selection

'''+api.audit.markdown_table(train.reset_index())+'''

Bound200 giảm phone_F1 từ **13.903815%** ở SRH unbounded xuống **0.565616%**, nhưng baseline đã0.340080%. Bound100 giảm phone_M1 **0.776151→0.649398%**, song phone_F1/studio_F1/studio_M1 xấu hơn; studio_M1 của cả ba bound >2%. Không chọn width theo từng file. Minimax worst-file giữ baseline; ba gate yêu cầu giảm MAPE FAIL, năm guard khác PASS dưới selected control. Không promote.

## Test đã khóa trước

'''+api.audit.markdown_table(tables[1][columns])+'''

Bound200 là diagnostic cố định trước train, không được train chọn. Nó giảm phone_M2 **6.833750→4.602428%** và phone_F2 **4.197313→4.108902%**, nhưng tăng studio_F2 **5.063462→5.926086%**, studio_M2 **2.114791→2.747599%**; cả bốn vẫn >2%. Test đã có historical exposure, không chọn tham số từ test và không mô tả như xác nhận độc lập mới.

![So sánh](figures/H55_bounded_comparison.png)

## Cơ chế và đánh đổi

Giới hạn ứng viên chặn các thay đổi lớn trên train phone_F1 và phone_M1, nhưng đồng thời làm mất cải thiện thống kê của SRH unbounded trên phone_F2 (1.666665%→4.108902%). Baseline có thể sai ngoài khoảng bound; giữ gần baseline không đủ để sửa. Những bất đồng lớn vừa tăng vừa giảm trên phone_F2, nên không biết tất cả SRH unbounded đúng khi thiếu F0 chuẩn từng khung. Hai điểm train phone_F1 chuyển~235→389Hz nằm trong LAB **UV**; thay estimator giảm nhảy cao độ nhưng giữ nguyên mask chưa giải quyết việc dự đoán hữu thanh trên UV. Không dùng nhãn UV để loại chúng trong inference của vòng này.

Phân tích dựa trên whole-file MAPE và contour ước lượng, không claim xác định đúng/sai pitch từng khung. Count phone_M2 baseline lệch5.691057% đóng góp1.897019 điểm vào Average MAPE; pitch-only chỉ còn khoảng0.102981 điểm cho tổng mean/std contributions nếu muốn <2. Điều đó đặt yêu cầu rất chặt nhưng không chứng minh bất khả thi, nhãn sai hoặc dữ liệu ít là nguyên nhân duy nhất. Thay count phải là giả thuyết riêng, không tinh chỉnh theo test.

## Kiểm tra và tái lập

Prereg248d8be/freezeeeedd83 push/remoteverify trước train/test.16/8metric groups,64inner traces,24summary rows. Verifier scalar độc lập PASS1764bounded selections train và603test; displacement<=width, nearest mapping/fallback/tie/mask/metrics/selection/gates/hash. Reuse H54 cached verified LPC/FFT/SRH; H55 không đo native estimator mới.18synthetic near-truth biased-anchor casesPASS vàmask/fallback/tie checksPASS, không xóa ba failures của unboundedH54 và không chứng minh sửa octave anchor sai.

H55_REGISTRATION.md/H55_REGISTRY.json ghi grid, dữ liệu/code/version hashes, constraints và lựa chọn. Lệnh bounded_srh.py train/test;verify_bounded_srh.py train/test;report_bounded_srh.py. Không rerun measurement đã lưu. NoDrive/DL/PDF/Jev/prose skill. Original WAV/LAB/teacher3GT/frozen pipeline không thay; bài mới thầy giao vẫn sau ưu tiên cải thiệnBT2.
'''
    # Insert measured value rather than a manually rounded estimate.
    unbounded=comparison[(comparison.stage=='train')&(comparison.file=='phone_F1.wav')&(comparison.method=='SRH unbounded')].average_mape.iloc[0]
    report=report.replace('13.903815',f'{unbounded:.6f}')
    (api.HERE/'H55_REPORT.md').write_text(report,encoding='utf-8')
    outputs=[api.HERE/'H55_REPORT.md',api.OUT/'H55_all_metrics.csv',api.OUT/'H55_selected_all_files.csv',api.OUT/'H55_pitch_changes.csv',api.OUT/'H54_H55_diagnostic_comparison.csv']+list(figures.glob('H55_bounded_comparison.*'))
    api.audit.json_write(api.OUT/'H55_reporting.json',dict(passed=True,new_measurements=0,all_eight_strict_below_2=bool(status.strict_below_2.all()),
        selected=selected,qualified_counts=status.groupby('stage').strict_below_2.sum().to_dict(),
        input_hashes={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in inputs},
        outputs={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in outputs},source_sha256=api.audit.digest(__file__)))
    print('H55 report complete: baseline selected; all8 target FAIL')


if __name__=='__main__':build()
