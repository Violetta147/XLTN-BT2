import json
import numpy as np
import pandas as pd
import maps_experiment as api

receipt=json.loads((api.OUT/'H60_train_experiment.json').read_text())
verify=json.loads((api.OUT/'H60_verification.json').read_text())
assert verify['status']=='PASS' and not receipt['decision']['eligible']
table=pd.read_csv(api.OUT/'H60_fixed.csv')
matrix=table.pivot(index='file',columns='option_id',values='average_mape').reset_index()
cases=[]
for path in sorted(api.core.TRAIN.glob('*.wav')):
    item,fs,audio=api.independent_item(path,'train')
    saved=dict(np.load(api.OUT/f'H60_predictions_{path.stem}.npz'))
    a,b=saved['f0'][0],saved['f0'][1]
    cents=np.where(saved['pred'][0],1200*np.log2(b/a),np.nan)
    indices=np.flatnonzero(saved['pred'][0])
    for i in sorted(indices,key=lambda i:abs(cents[i]),reverse=True)[:5]:
        cases.append(dict(file=path.name,time_s=item['times'][i],center_lab=item['labels'][i],
            baseline_hz=a[i],maps_hz=b[i],relative_cents=cents[i],
            interpretation='Two estimator outputs; neither is frame F0 ground truth.'))
pd.DataFrame(cases).to_csv(api.OUT/'H60_changed_cases.csv',index=False)
text=f'''# H60 — MAPS không cải thiện BT2

Đã chạy một reference-derived pipeline MAPS với mã tác giả và adapter được ghi trước đo. Prereg commit `{receipt['prereg_commit']}` đã push/remote-SHA verified trước train. **Final selection hard170; tám gates không đạt; không promote và không đo test mới.** Baseline giữ4/4train<2%, kết quả test lịch sử0/4<2%, all8 vẫn chưa đạt.

| File train | hard170 | MAPS pitch-only | whole q=.2 | whole q=.5 | whole q=.8 |
|---|---:|---:|---:|---:|---:|
'''
for _,r in matrix.iterrows():
    text+='| '+r['file']+' | '+' | '.join(f"{r[c]:.6f}" for c in ('hard170','maps_pitch','maps_whole_20','maps_whole_50','maps_whole_80'))+' |\n'
text+='''
Các số trên là Average MAPE(%) của F0mean/F0std/F0num so teacher3GT; toàn bộ V/UV/SIL, mean/std MAE ở results/H60_fixed.csv. MAPS pitch-only giữ nguyên mask/count và metrics phân loại, cho thấy đổi estimator riêng chưa tốt hơn. studio_M1 tăng1.909923→37.506279%; các trường hợp chênh lệch lớn nằm trong H60_changed_cases.csv. Độ lệch giữa hai estimator không chứng minh bên nào sai về pitch vật lý vì BT2 không có frameF0GT.

Whole q=.2 trênphone_M1 đạt2.451146%, nhưng không dưới2 và F1 giảm. Trênphone_F1 q=.2 recallV tăng nhưng có4falseVoicedSIL, vượt guard. Không chọn cấu hình riêng theofile/recordingtype. Outer/final đều chọn hard170. Có20unique measured groups và80inner selection records;24train/LOFO/nested summary rows. Deterministic pretrained likelihood table: zero model fits, không giả3seeds tạo3lần fit. Nested chỉ chọn config trênfile train khác, vẫn exploratory sau lịch sử exposure; không chứng nhận unseen-speaker generalization.

Native2048sample ở48kHz=42.667ms, hop10ms; canonical evaluation25ms/10ms, original70–400 output, centerLAB/populationstd. Internal framing khácbaseline, không gọi đây là so sánh chỉfilter. Initial25ms integration fail90Hz synthetic2582.404cents được lưu; theo cấu hình tác giả six fixtures median14.62–48.84cents pass100cents. Synthetic pass không bảo đảm speech pass. Nguồn MAPS/giấy phépGPLv3/version/calibration và ba compatibility corrections được ghi tại MAPS_SOURCE_REVIEW.md/H60_REGISTRATION.md. Không sửa vendorbytes hay calibrationtables.

Verifier v1 yêu cầu exacttrajectory và FAIL: product/log-space Viterbi tie khác67/30/0/5frames nhưng independent log-objective của bốnfile đều khớp0gap. H60_path_tie_audit.json giữ discrepancy. Verifier v2 chỉ sửa yêu cầu kiểm chứng sang optimum-objective parity1e-9, ghi rõ postmeasurement; inference/config/source prereg không đổi, dữ liệu không rerun. IndependentPCM grid, logpath objective, scalar nearestprojection, metrics/configselection PASS20groups. Magnitude/phase/spline dùng chung nguồn author, không claim independentfullpipeline. Source+artifacthashes được kiểm. Fallback biên và splineclipping nằm trong H60_verification.json. Không gộp verifier correction vào accuracygain.

H60 không đạt nên bước tiếp theo kiểm một estimator khác theo harmonic least-squares, giữvoicing/count. Đây là giả thuyết riêng, cần prereg riêng, chưa đo dữ liệu ở H60. Chưa quy nguyên nhân cho ít dữ liệu, GT hoặc test. NoDrive/DL/PDF/Jev/proseskill; originalnotebook/LAB/3GT/frozen giữ nguyên.
'''
(api.HERE/'H60_REPORT.md').write_text(text,encoding='utf-8')
print('H60 report and changed cases saved')
