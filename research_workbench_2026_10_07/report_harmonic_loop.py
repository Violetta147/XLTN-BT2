"""Reports measured H60-H62 only. No training, inference, test or model calls."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import harmonic_voicing as api

receipt=json.loads((api.OUT/'H62_train_experiment.json').read_text())
assert json.loads((api.OUT/'H62_verification.json').read_text())['status']=='PASS'
assert not receipt['decision']['eligible']
table=pd.read_csv(api.OUT/'H62_fixed_lofo.csv');rows=[];scores=[];cases=[]
names=sorted(table.file.unique())
for held in names:
    feature=dict(np.load(api.OUT/f'H62_design_{Path(held).stem}.npz'))
    evidence=next(p for p in receipt['proofs'] if p['held_file']==held and len(p['fit_files'])==3)
    saved=dict(np.load(api.REPO/evidence['path']));labels=feature['labels']
    for k,option in enumerate(api.OPTIONS):
        pred=saved['pred'][k];base=feature['base_pred'];removed=base&~pred;recovered=~base&pred
        rows.append(dict(file=held,option_id=option['id'],
            **{f'{action}_{label}':int((mask&(labels==label)).sum())
                for action,mask in [('removed',removed),('recovered',recovered)] for label in ('v','uv','sil')}))
        if option['dimensions'] and option['reject']==.25:
            for i in np.flatnonzero(removed|recovered)[:6]:
                cases.append(dict(file=held,option_id=option['id'],time_s=feature['times'][i],
                    center_lab=labels[i],probability_v=saved['probability'][k,i],
                    action='removed' if removed[i] else 'recovered',r2_h3=feature['x'][i,4],extra_r2_h5=feature['x'][i,5],
                    frame_f0_ground_truth_available=False))
        if option['dimensions'] and option['reject']==0:
            scores.append(dict(file=held,dimensions=option['dimensions'],
                brier=float(np.mean((saved['probability'][k]-(labels=='v').astype(int))**2))))
pd.DataFrame(rows).to_csv(api.OUT/'H62_fixed_label_audit.csv',index=False)
pd.DataFrame(scores).to_csv(api.OUT/'H62_held_score_quality.csv',index=False)
pd.DataFrame(cases).to_csv(api.OUT/'H62_changed_cases.csv',index=False)
matrix=table.pivot(index='file',columns='option_id',values='average_mape').reset_index()
text=f'''# H62 — đặc trưng khớp họa âm chưa cải thiện chung

H62 so sánh cùng learner logistic với bốn đặc trưng cũ và sáu đặc trưng có thêm mức khớp họa âm. Prereg `{receipt['prereg_commit']}` đã push và xác minh SHA remote trước đo. **Final và bốn outer folds đều chọn hard170. Ba gate giảm MAPE không đạt; không promote và không đo test mới.** Baseline giữ 4/4 train dưới 2%; kết quả test đã lưu vẫn 0/4. Mục tiêu cả tám file chưa đạt.

| File train held-out | baseline | base4 recovery | base4 reject .1 | base4 reject .25 | coherence6 recovery | coherence6 reject .1 | coherence6 reject .25 |
|---|---:|---:|---:|---:|---:|---:|---:|
'''
order=[o['id'] for o in api.OPTIONS]
for _,r in matrix.iterrows():text+='| '+r['file']+' | '+' | '.join(f"{r[c]:.6f}" for c in order)+' |\n'
text+='''
Các giá trị là Average MAPE (%) so với teacher3GT. Thêm coherence giúp giảm một số lỗi trên hai file phone và ở studio_F1 khi chỉ recovery, nhưng studio_M1 tăng 4.149865→4.454627%. Với rejection .25, studio_F1 dùng base4 đạt 0.502753%, tốt hơn coherence6 0.768353%; cả hai đều không thắng trên toàn bộ file. Đây là ablation trực tiếp cho thấy thêm đặc trưng không tạo lợi ích nhất quán. Không chọn mô hình theo tên file hoặc môi trường thu âm.

Hai đặc trưng mới đo phần năng lượng được mô hình ba họa âm giải thích và phần tăng thêm khi dùng năm họa âm. Mô hình khớp từ WAV tại anchor hiện có, không dùng LAB để tạo đặc trưng. Logistic học LAB V so với UV/SIL của đúng fit pool; điểm này không phải xác suất chắc chắn rằng một khung có F0 chuẩn của thầy. Khung V giữ lại vẫn dùng pitch baseline; recovery dùng ACF bound200 của H56. Thay đổi count có thể đồng thời đổi mean/std. H62_fixed_label_audit.csv ghi rõ recovered/removed V/UV/SIL; H62_changed_cases.csv lưu các khung đổi quyết định, không gọi pitch ước lượng là frame ground truth.

Điểm Brier giảm trên cả bốn file khi thêm coherence: phone_F1 .034816→.032672; phone_M1 .044968→.037172; studio_F1 .019251→.018575; studio_M1 .028807→.024395. Vì vậy đặc trưng mới có thông tin hữu ích theo nhãn LAB, nhưng chưa tạo pipeline đạt thống kê F0. Ở q=.25, phone_M1 giảm recovery nhầm UV từ3 xuống0, vẫn hồi phục5V và loại4V; Average MAPE vẫn8.118297%, cao hơn baseline. studio_M1 hồi phục5V→6V nhưng count/mean/std chung xấu hơn. Những đánh đổi này giải thích vì sao không promote dù Brier cải thiện.

Đã đo 140 nhóm train, 22 logistic fits từ 11 fit pools ×2 bộ đặc trưng, 112 inner traces, 28 fixed LOFO và 24 summary rows. Chọn cấu hình theo minimax lỗi file trong inner folds, rồi mean và ID; có guard F1/recallV/SIL và tám gate hiện hành. Grouped nested dùng bốn outer files và ba inner files; không random split các khung. Solver LBFGS là deterministic, không giả ba seed thành ba lần học độc lập. Ba seed11/29/47 chỉ dùng cho18 synthetic noise fixtures trước đo.

Verifier PASS: QR độc lập đối chiếu đặc trưng từ PCM; kiểm grid/LAB/3GT, scalar response, scaler, đúng membership và hash của fit design; gradient logistic trên các mô hình đã serialize; masks, pitch, metric, inner traces, selection và gate. Không refit optimizer độc lập; PEZS cũ được dùng lại từ cache H50 đã xác minh. Điểm Brier theo file ở H62_held_score_quality.csv, không thay metric chính bằng Brier để gọi thành công.

H60/H61/H62 đều chưa thắng nên baseline và notebook đã nộp giữ nguyên. Không đo thêm test sau các vòng fail này, không sửa nhãn hoặc reference. Test đã có lịch sử exposure, nested cũng exploratory; chưa có bằng chứng quy toàn bộ nguyên nhân cho thiếu data, GT hoặc test. Hình LOOP_H60_H62_train_matrix.png và bảng tổng hợp LOOP_H60_H62_SUMMARY.csv chỉ chứa số đã đo, không có số test mới.

Theo yêu cầu cuối của người dùng, hoàn tất kiểm tra và bàn giao rồi dừng loop tại H62. Không khởi động H63, không schedule hay retry Jev. Chat mới đọc START_NEXT_CHAT.md; tiếp tục chỉ theo yêu cầu mới của người dùng. Bài phân đoạn mới vẫn đứng sau cải thiện BT2, chưa chuyển bài.
'''
(api.HERE/'H62_REPORT.md').write_text(text,encoding='utf-8')
summaries=[]
for family,filename,verifier in [('H60','H60_fixed.csv','H60_verification.json'),
                                 ('H61','H61_fixed.csv','H61_verification.json'),
                                 ('H62','H62_fixed_lofo.csv','H62_verification.json')]:
    t=pd.read_csv(api.OUT/filename);v=json.loads((api.OUT/verifier).read_text())
    for identity,group in t.groupby('option_id'):
        summaries.append(dict(family=family,option_id=identity,measured_split='BT2 training files',
            below_2_count=int((group.average_mape<2).sum()),file_count=4,
            worst_file_mape=float(group.average_mape.max()),mean_file_mape=float(group.average_mape.mean()),
            verifier_status=v['status'],test_newly_measured=False,selected_final=(identity=='hard170')))
pd.DataFrame(summaries).to_csv(api.OUT/'LOOP_H60_H62_SUMMARY.csv',index=False)
fig,axes=plt.subplots(3,1,figsize=(15,10),constrained_layout=True)
labels=[('H60 — MAPS', 'H60_fixed.csv', ['hard170','maps_pitch','maps_whole_20','maps_whole_50','maps_whole_80'],
         ['baseline','MAPS pitch','whole .2','whole .5','whole .8']),
        ('H61 — harmonic regression','H61_fixed.csv',['hard170','nls_3','nls_5'],['baseline','3 harmonics','5 harmonics']),
        ('H62 — voicing feature ablation','H62_fixed_lofo.csv',order,
         ['baseline','base4 rec','base4 q.1','base4 q.25','coherence rec','coherence q.1','coherence q.25'])]
for ax,(title,filename,identities,display) in zip(axes,labels):
    t=pd.read_csv(api.OUT/filename).pivot(index='file',columns='option_id',values='average_mape').loc[names,identities]
    ax.imshow(t.to_numpy(),norm=LogNorm(vmin=.2,vmax=40),cmap='YlOrRd',aspect='auto')
    ax.set_xticks(range(len(identities)),display);ax.set_yticks(range(4),names);ax.set_title(title,loc='left')
    for i in range(4):
        for j in range(len(identities)):
            value=float(t.iloc[i,j]);ax.text(j,i,f'{value:.3f}%',ha='center',va='center',color='white' if value>15 else 'black')
            if value<2:ax.add_patch(plt.Rectangle((j-.48,i-.48),.96,.96,fill=False,edgecolor='green',linewidth=2))
fig.suptitle('Training-file Average MAPE: green border <2%; baseline remains selected; no new test evaluation')
figure_dir=api.HERE/'figures';figure_dir.mkdir(exist_ok=True)
fig.savefig(figure_dir/'LOOP_H60_H62_train_matrix.png',dpi=150)
plt.close(fig)
print('Saved H62 report, label audit, score audit, cases and three-round matrix')
