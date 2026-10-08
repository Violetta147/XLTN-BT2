import json
import numpy as np
import pandas as pd
import nls_experiment as api

receipt=json.loads((api.OUT/'H61_train_experiment.json').read_text())
assert json.loads((api.OUT/'H61_verification.json').read_text())['status']=='PASS'
table=pd.read_csv(api.OUT/'H61_fixed.csv');audit=[];cases=[]
for path in sorted(api.core.TRAIN.glob('*.wav')):
    item,fs,audio=api.independent_item(path,'train');saved=dict(np.load(api.OUT/f'H61_predictions_{path.stem}.npz'))
    for k,option in enumerate(api.OPTIONS[1:],1):
        proof=dict(np.load(api.OUT/f'H61_{option["id"]}_{path.stem}.npz'))
        ids=proof['indices'];cents=1200*np.log2(saved['f0'][k,ids]/saved['f0'][0,ids])
        audit.append(dict(file=path.name,option_id=option['id'],voiced_frames=len(ids),
            bound_hits=int(proof['at_boundary'].sum()),mean_absolute_change_cents=float(np.mean(abs(cents))),
            unchanged_mask=True,unchanged_count=True))
        for j in np.argsort(-abs(cents))[:4]:
            i=ids[j];cases.append(dict(file=path.name,option_id=option['id'],time_s=item['times'][i],
                center_lab=item['labels'][i],baseline_hz=saved['f0'][0,i],nls_hz=saved['f0'][k,i],
                relative_cents=cents[j],bound_hit=bool(proof['at_boundary'][j]),
                frame_f0_ground_truth_available=False))
pd.DataFrame(audit).to_csv(api.OUT/'H61_bound_audit.csv',index=False)
pd.DataFrame(cases).to_csv(api.OUT/'H61_changed_cases.csv',index=False)
matrix=table.pivot(index='file',columns='option_id',values='average_mape').reset_index()
text=f'''# H61 — harmonic least-squares chưa cải thiện chung

Prereg `{receipt['prereg_commit']}` đã commit/pushremoteverify trước đo. Custom dense harmonic regression trong25ms, tìm±100cents quanhbaseline, giữmask/count và mọiV/UV/SIL. **Finalhard170, ba gates giảmMAPE FAIL, không promote và không đo test mới.** Verifier independentQR/basis/Hann/grid/localbracket/PCMmetrics/selection/hash PASS12groups. Đây không phải reference fastF0Nls hoặc xác minhoptimizer độc lập.

| File train | baseline | 3 họa âm | 5 họa âm |
|---|---:|---:|---:|
'''
for _,r in matrix.iterrows():text+='| '+r['file']+' | '+' | '.join(f"{r[c]:.6f}" for c in ('hard170','nls_3','nls_5'))+' |\n'
text+='''
AverageMAPE(%) so teacher3GT. phone_F1 nls5 .340080→.303953, studio_F1 nls3 1.473576→1.254701 có cải thiện riêng, nhưng studio_M1 1.909923→2.193784(nls3)/2.173975(nls5). Không chọnorder riêng theo tênfile. Outerheldstudio_M1 chọnnls3 trênbafilekhác, heldscore2.193784>2; baouterkhác chọncontrol. Nestedtrain3/4<2 trong khiaccepted4/4; không gọi thấpresidual làpitchđúng. LAB không cóframeF0GT.

12unique metricgroups,48innertraces,24summaryrows. Zero trainlabel/model fits: linearcoefficients fit trênWAV mỗi khung đang suy luận, configselection theofiletrain. Three seeds11/29/47 chỉ dùngsyntheticnoise,36fixtures ở16k/44.1k vớiF090/200/320Hz vàgainDCinvariance; không là3modelseeds. Nativecanonical25ms/10ms khôngresample/framingchange, populationstd. Tất cảF0numMAPE/VUV/SIL bằngbaseline; estimator-only không thể sửa count. Đủmean/std/countMAPE, MAE/F1/recall/balancedaccuracy ởH61_fixed.csv; boundhits vàpairedcases trongH61_bound_audit.csv/H61_changed_cases.csv. Phiên này chưa chạybenchmarkquốc tế mới/robustnessBT2noise, khôngsuydiễn từsynthetic.

H61támgates vànested vẫnexploratory sauhistoricalexposure. Baseline vẫn4/4train,0/4test lịch sử; mục tiêu8file<2 chưađạt. Khôngđo test đểchọnorder. Hướng mới: dùng harmonic explained-energy nhưfeature cho voicing, cóablation so logisticbase4 vàbase4+coherence, preregriêng trướcđo. Khôngquylỗi test/data/GT. Originalnotebook/LAB/3GT/frozen giữ nguyên, noDrive/DL/PDF/Jev/proseskill.
'''
(api.HERE/'H61_REPORT.md').write_text(text,encoding='utf-8')
print('H61 report/audit/cases saved')
