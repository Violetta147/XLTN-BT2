# H26 — bổ sung ACF_score cho quyết định AMDF

Đăng ký trước đo; rollback2f5ef55, controlH24fixed gate25/pitch40. Không đổi baseline009fd2c hay frozen_config. Mục tiêu mỗifile AverageMAPE≤2%. Jev shortlist chưa chọn hướng rõ; agent chọn sau code chẩn đoán phoneM1 có40V bị loại chỉdopitch, không phải energygate. Không xem thiếu metadata là nguyên nhân phoneme/giới tính.

Giả thuyết: ACF25score, độ giống của tín hiệu với bản dịch, bổ sung cho NAMDF25score đo hiệu số; Logistic3D có thể phân biệt khung tuần hoàn yếu mà2Dscore/RMS bỏ sót. Đây là ý tưởng bổ sung đặc trưng cổ điển, không dùng ACF làm groundtruth hay thay ứng viênpitch. ACF_score có sẵn trong cùng core.frame_features canonical25; không thayACFmath hoặc preprocessing. C1 cố định, không tuneC mới.

Registry3options: rawcontrol; H25LR2DC1; LR3DC1 thêmACF_score. Chỉ thay một featureaxis giữa2D/3D. Training weights, scaler, energygate/probability.5 giữ đúngH25; fit bằng poolVUV khôngheld. Giữ25decision/10hop,40pitchsamecenters/fallback25, AMDFpathjump.35/octave0/median1/range70–400. Không đổiRMS/filters/frame/median/candidate cùngvòng.

FinalLOFO4file; nestedouterheldexcluded mọi innerfit/chọn. Inner eligible finiteMAPE,F1/recall≥rawcontrol−.01,SIL≤rawcontrol+1. Rank worstfileMAPE rồimean rồiID. Báo tấtcả3fixedLOFO, selectedLOFO vànested riêng. GatesgiữH25: train−10%; selected/nested−5%; nestedF1/recall−.01,SIL+1,nofileMAPEworse>2pp,phoneF1stdkhôngxấu. Mục tiêu≤2%mọifile báo riêng. Khôngauto-promote; giữfailures; rollbacklogic vềH24nếufail. Khôngtest/noDrive/noDL.

Checktrước chạy: rawcontrolH24 vàLR2DC1H25 mỗifile khớp1e-8; không đo3Dtrongcheck. Sau chạy verify3×16=48innertraces,24metrics,fitsdimensions/IDs, scalerweightedparity, labels/hash, poisoningheldGTinvariant, replayminimax/gates,PNG/SVG. Sốtrace là phép tính code, khôngJev.

Lệnh `python research_workbench_2026_10_07/amdf_joint_periodicity.py register/check/H26`. Không thêm feature/C sau khi xem kết quả.
