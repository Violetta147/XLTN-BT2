import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import srh_experiment as api


def build():
    tables=[];checks={};cases=[];deviations=[]
    for stage in ('train','test'):
        checks[stage]=json.loads((api.OUT/f'H54_{stage}_verification.json').read_text())
        assert checks[stage]['passed']
        table=pd.read_csv(api.OUT/f'H54_{stage}_fixed.csv',float_precision='round_trip');table['stage']=stage;tables.append(table)
        for path in sorted(api.OUT.glob(f'H54_{stage}_predictions_*.npz')):
            saved=dict(np.load(path,allow_pickle=False));stem=path.stem.replace(f'H54_{stage}_predictions_','')
            base=int(np.flatnonzero(saved['option_id']=='hard170')[0]);new=int(np.flatnonzero(saved['option_id']=='srh_w100_pitch_only')[0])
            ix=np.flatnonzero(saved['pred'][base]);delta=1200*np.log2(saved['f0'][new,ix]/saved['f0'][base,ix])
            deviations.append(dict(stage=stage,file=stem+'.wav',voiced_frames=len(ix),abs_change_over_600cents=int(sum(abs(delta)>600)),
                median_abs_change_cents=float(np.median(abs(delta))),largest_abs_change_cents=float(max(abs(delta))),frame_f0_truth_available=False))
            directory=api.core.TRAIN if stage=='train' else api.REPO/'TinHieuKiemThu'
            item=api.core.frame_features(directory/(stem+'.wav'),split=stage)
            for i in ix[np.argsort(-abs(delta),kind='stable')[:5]]:
                cases.append(dict(stage=stage,file=stem+'.wav',time_s=saved['times'][i],label=item['labels'][i],
                    estimated_baseline_f0_hz=saved['f0'][base,i],estimated_srh_f0_hz=saved['f0'][new,i],
                    delta_cents=1200*np.log2(saved['f0'][new,i]/saved['f0'][base,i]),frame_f0_truth_available=False))
    allrows=pd.concat(tables,ignore_index=True)
    allrows.to_csv(api.OUT/'H54_all_metrics.csv',index=False)
    pd.DataFrame(cases).to_csv(api.OUT/'H54_largest_pitch_changes.csv',index=False)
    pd.DataFrame(deviations).to_csv(api.OUT/'H54_pitch_disagreement.csv',index=False)
    selected=json.loads((api.OUT/'H54_FROZEN_SELECTION.json').read_text())['option']['id']
    status=allrows[allrows.option_id==selected].copy();status['strict_below_2']=status.average_mape<2
    status.to_csv(api.OUT/'H54_selected_all_files.csv',index=False)
    figures=api.HERE/'figures';figures.mkdir(exist_ok=True)
    figure,axes=plt.subplots(1,2,figsize=(12,5),gridspec_kw={'width_ratios':[1.35,1]})
    for axis,table,stage in zip(axes,tables,('train','test')):
        matrix=table.pivot(index='option_id',columns='file',values='average_mape')
        matrix=matrix.loc[[o['id'] for o in api.OPTIONS if o['id'] in matrix.index]]
        plot=axis.imshow(matrix.to_numpy(),aspect='auto',cmap='Blues',norm=LogNorm(vmin=.3,vmax=100))
        axis.set_xticks(range(4),[s.replace('.wav','') for s in matrix.columns],rotation=25,ha='right')
        axis.set_yticks(range(len(matrix)),matrix.index)
        for i in range(len(matrix)):
            for j in range(4):axis.text(j,i,f'{matrix.iloc[i,j]:.2f}',ha='center',va='center',color='white' if matrix.iloc[i,j]>7 else 'black')
        axis.set_title(f'H54 {stage}: Average MAPE (%)')
    figure.tight_layout()
    for suffix in ('png','svg'):figure.savefig(figures/f'H54_srh_matrix.{suffix}',dpi=160)
    plt.close(figure)
    figure,axes=plt.subplots(2,1,figsize=(11,6),sharex=False)
    for axis,stage,stem in zip(axes,('train','test'),('phone_F1','phone_F2')):
        output=dict(np.load(api.OUT/f'H54_{stage}_predictions_{stem}.npz',allow_pickle=False))
        directory=api.core.TRAIN if stage=='train' else api.REPO/'TinHieuKiemThu'
        for start,end,label in api.core.read_segments(directory/(stem+'.lab')):
            axis.axvspan(start,end,color={'v':'green','uv':'orange','sil':'gray'}[label],alpha=.1)
        for identity,color in [('hard170','black'),('srh_w100_pitch_only','tab:blue')]:
            k=int(np.flatnonzero(output['option_id']==identity)[0]);axis.plot(output['times'],output['f0'][k],color=color,lw=1,label=identity)
        axis.set_title(f'{stage} {stem}: estimated F0; LAB shading V=green, UV=orange, SIL=gray')
        axis.set_ylabel('F0 estimate (Hz)');axis.set_xlabel('Time (s)');axis.legend(loc='upper right',fontsize=8)
    figure.suptitle('No frame-level F0 ground truth on BT2',fontsize=11);figure.tight_layout()
    for suffix in ('png','svg'):figure.savefig(figures/f'H54_srh_qualitative.{suffix}',dpi=160)
    plt.close(figure)
    columns=['option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','macro_f1','recall_v','recall_uv','balanced_accuracy','false_voiced_sil']
    train=tables[0].pivot(index='option_id',columns='file',values='average_mape').loc[[o['id'] for o in api.OPTIONS]]
    report='''# H54 — SRH: kết quả và giới hạn

**Chưa có cấu hình chung tốt hơn baseline.** Sáu cấu hình mới và control đã đo trên bốn train; cả lựa chọn cuối và bốn outer pools giữ hard170. Mục tiêu mỗi một trong tám file Average MAPE <2% chưa đạt: baseline có4/4train và0/4test đạt. Không sửa notebook đã nộp hoặc pipeline được giữ lại.

SRH dùng residual sau dự đoán tuyến tính, cộng năng lượng họa âm và trừ giữa họa âm. Vòng này có ba cửa sổ60/80/100ms và hai nhánh: thay cả voicing/pitch, hoặc chỉ thay pitch dưới mặt nạ hữu thanh baseline. Nhánh pitch-only giữ count, V/UV/SIL; whole có thể đổi chúng. Không mô hình học hoặc seed ngẫu nhiên.

## Ma trận train

'''+api.audit.markdown_table(train.reset_index())+'''

![Ma trận](figures/H54_srh_matrix.png)

SRH toàn pipeline gây nhiều SIL false positives: tổng99/128/154khung lần lượt ở cửa sổ60/80/100ms, so baseline0. Đây là số khung có LAB SIL mà vẫn được dự đoán hữu thanh, không phải số cao độ đã được xác nhận sai. Pitch-only80 giảm studio_F1 rất nhỏ1.473576→1.431750%, nhưng ba train khác xấu hơn; không chọn cấu hình riêng cho file. Worst-file minimax và guard VUV đều dẫn về control. Trong tám gate, ba điều kiện yêu cầu giảm MAPE FAIL, năm guard khác PASS vì giữ baseline; eligibility FAIL, không promote.

## Test cấu hình đã chốt

'''+api.audit.markdown_table(tables[1][columns])+'''

Selected vẫn là baseline. Hai nhánh100ms là diagnostics đã đăng ký trước đo train và khóa trước test. Pitch-only giảm phone_F2 **4.197313→1.666665%**, studio_F2 **5.063462→3.012553%**; nhưng phone_M2 **6.833750→7.960597%**, studio_M2 **2.114791→3.042067%**. Không dùng test để route theo giới tính/file, ghép kết quả tốt nhất hoặc promote. Whole làm F0std phone_F2 gần thống kê chuẩn hơn nhưng count lệch15.525114% và F1 giảm, Average MAPE5.829442%. Điều này cho thấy cần báo cùng pitch/voicing/count thay vì chỉ chọn một thành phần đẹp.

## Phân tích thay đổi cao độ

![Contour](figures/H54_srh_qualitative.png)

'''+api.audit.markdown_table(pd.DataFrame(deviations))+'''

Cent là đơn vị logarit:1200cents tương ứng tỉ lệ tần số2. Ở train phone_F1, chỉ2khung lệch hơn600cents so baseline, ở1.6025/1.6125s SRH~389/388Hz so baseline~235Hz; các điểm này có thể làm std nhạy dù đa số thay đổi nhỏ. Ở phone_M1, có4khung hơn600cents, ba khung quanh2.02–2.04s chuyển~102Hz sang~199–210Hz. Đây là **bất đồng hai ước lượng**, không bằng chứng ground truth từng khung. File `H54_largest_pitch_changes.csv` giữ5thay đổi lớn nhất mỗi file, không dùng chọn lại cấu hình.

Test phone_F2 có14khung lệch hơn600cents, gồm cả hướng tăng và giảm. MAPE thống kê cải thiện không bảo đảm tất cả14khung SRH đúng. Một giới hạn quanh baseline có thể chặn thay đổi gây lệch std trên train nhưng cũng chặn sửa octave nếu baseline sai; đó chỉ là giả thuyết cho vòng mới, chưa được đo ởH54. Không kết luận dữ liệu ít hoặc GT sai là nguyên nhân duy nhất.

## Kiểm tra và tái lập

Prereg45f489e và freeze4527180 đều push/remoteverify trước train/test.12native analyses train/4test;28/12metric groups,112inner records,24summary rows. Verifier PASS7740/2607LPC frames và3813/1276spectral frames. Mọi LPC frame BT2 cócondition<=1e8 nên đã so dense coefficients; equation residual, convolution/energy/overlap-add/fullFFT/scalarSRH/projection/metrics/hash và lựa chọn train đã đối chiếu. Resampling dùng cùng SciPy, không reference MATLAB/Octave execution hoặc bit-parity claim.

Precheck tổng hợp15/18accuracyPASS,3FAIL100→300Hz/fs44100 giữ nguyên. Math qualificationPASS cho phép benchmark exploratory, không biến accuracyFAIL thànhPASS. Verifier đầu đã lỗi coefficient comparison ở synthetic condition~3.09e10; hồ sơ và sửa trước measurement lưu riêng. Không sửa thuật toán theo BT2. Source/license/phạm vi đọc abstract/code tạiSRH_SOURCE_NOTE.md, registry/H54_REGISTRATION.md. Test có historical exposure nên không đánh giá như corpus mới độc lập.

Lệnh đo `srh_experiment.py train/test`, kiểm tra `verify_srh.py train/test`, báo cáo `report_srh.py`; không chạy lại phép đo đã lưu. Dùng Python3.13.11/numpy2.4.3/scipy1.17.1, seedNone. LAB/teacher3GT không F0 chuẩn từng khung. Jev không tham gia. NoDrive/DL/PDF; bài phân đoạn mới vẫn sau ưu tiên cải thiệnBT2.
'''
    (api.HERE/'H54_REPORT.md').write_text(report,encoding='utf-8')
    inputs=[api.OUT/f'H54_{s}_fixed.csv' for s in ('train','test')]+[api.OUT/f'H54_{s}_verification.json' for s in ('train','test')]
    inputs+=list(api.OUT.glob('H54_*_predictions_*.npz'))
    outputs=[api.HERE/'H54_REPORT.md',api.OUT/'H54_all_metrics.csv',api.OUT/'H54_selected_all_files.csv',api.OUT/'H54_pitch_disagreement.csv',api.OUT/'H54_largest_pitch_changes.csv']
    outputs+=list(figures.glob('H54_srh_*'))
    api.audit.json_write(api.OUT/'H54_reporting.json',dict(passed=True,new_measurements=0,selected=selected,
        all_eight_strict_below_2=bool(status.strict_below_2.all()),qualified_counts=status.groupby('stage').strict_below_2.sum().to_dict(),
        input_hashes={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in inputs},
        outputs={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in outputs},source_sha256=api.audit.digest(__file__)))
    print('H54 report complete: all8 target FAIL, baseline retained')


if __name__=='__main__':build()
