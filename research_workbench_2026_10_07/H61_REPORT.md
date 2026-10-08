# H61 — harmonic least-squares chưa cải thiện chung

Prereg `079cbad1b9dcbf1e22e2b7ab927133fc72993c31` đã commit/pushremoteverify trước đo. Custom dense harmonic regression trong25ms, tìm±100cents quanhbaseline, giữmask/count và mọiV/UV/SIL. **Finalhard170, ba gates giảmMAPE FAIL, không promote và không đo test mới.** Verifier independentQR/basis/Hann/grid/localbracket/PCMmetrics/selection/hash PASS12groups. Đây không phải reference fastF0Nls hoặc xác minhoptimizer độc lập.

| File train | baseline | 3 họa âm | 5 họa âm |
|---|---:|---:|---:|
| phone_F1.wav | 0.340080 | 0.443094 | 0.303953 |
| phone_M1.wav | 0.776151 | 1.034688 | 0.816033 |
| studio_F1.wav | 1.473576 | 1.254701 | 1.370408 |
| studio_M1.wav | 1.909923 | 2.193784 | 2.173975 |

AverageMAPE(%) so teacher3GT. phone_F1 nls5 .340080→.303953, studio_F1 nls3 1.473576→1.254701 có cải thiện riêng, nhưng studio_M1 1.909923→2.193784(nls3)/2.173975(nls5). Không chọnorder riêng theo tênfile. Outerheldstudio_M1 chọnnls3 trênbafilekhác, heldscore2.193784>2; baouterkhác chọncontrol. Nestedtrain3/4<2 trong khiaccepted4/4; không gọi thấpresidual làpitchđúng. LAB không cóframeF0GT.

12unique metricgroups,48innertraces,24summaryrows. Zero trainlabel/model fits: linearcoefficients fit trênWAV mỗi khung đang suy luận, configselection theofiletrain. Three seeds11/29/47 chỉ dùngsyntheticnoise,36fixtures ở16k/44.1k vớiF090/200/320Hz vàgainDCinvariance; không là3modelseeds. Nativecanonical25ms/10ms khôngresample/framingchange, populationstd. Tất cảF0numMAPE/VUV/SIL bằngbaseline; estimator-only không thể sửa count. Đủmean/std/countMAPE, MAE/F1/recall/balancedaccuracy ởH61_fixed.csv; boundhits vàpairedcases trongH61_bound_audit.csv/H61_changed_cases.csv. Phiên này chưa chạybenchmarkquốc tế mới/robustnessBT2noise, khôngsuydiễn từsynthetic.

H61támgates vànested vẫnexploratory sauhistoricalexposure. Baseline vẫn4/4train,0/4test lịch sử; mục tiêu8file<2 chưađạt. Khôngđo test đểchọnorder. Hướng mới: dùng harmonic explained-energy nhưfeature cho voicing, cóablation so logisticbase4 vàbase4+coherence, preregriêng trướcđo. Khôngquylỗi test/data/GT. Originalnotebook/LAB/3GT/frozen giữ nguyên, noDrive/DL/PDF/Jev/proseskill.
