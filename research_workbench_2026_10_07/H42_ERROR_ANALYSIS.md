# H42 — Đánh đổi và lựa chọn giữ riêng file

Giả thuyết phổ có ích ở cấu hình fixed5%, nhưng chưa giải quyết mục tiêu cả4file/nested vàphone_F1stdgate. Không promote hoặc đổi H41.

FixedHF05 phone_F1 AverageMAPE0.340080%/stdMAPE0.089632%, soH41fixed25/b200 1.080551%/2.332506%. Studio_F1stdMAPE0.050159% so0.554161%; studio_M1Average2.380001%/std3.289457% so1.940495%/2.158397%. Tốt lên ởfile này không đủ để chọn riêng theoGT lúcinfer.

Final vàouterphone_F1/phone_M1/studio_F1 chọnH41fixed25/b200. Outer studio_M1 chọnHF05 từ3file còn lại; heldfileAvg2.380001% làm targetFAIL. Nestedmean1.442494% soH41 1.332617%; worst2.380001% so1.940495%. Phone_F1nestedstd vẫn2.332506%,gateFAIL. Támgate giữ nguyên, bảyPASS mộtFAIL.

| file | option_id | F0mean | F0std | F0num | F0mean_mape | F0std_mape | F0num_mape | average_mape | macro_f1 | recall_v | recall_uv | balanced_accuracy | false_voiced_sil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phone_F1.wav | amdf_anchor_w25_b200 | 216.103 | 21.0805 | 147 | 0.23347 | 2.33251 | 0.675676 | 1.08055 | 0.938333 | 0.941176 | 0.956522 | 0.948849 | 0 |
| phone_M1.wav | amdf_anchor_w25_b200 | 122.477 | 16.9527 | 233 | 0.988737 | 0.908681 | 0.431034 | 0.776151 | 0.928721 | 0.946721 | 0.967742 | 0.957232 | 0 |
| studio_F1.wav | amdf_anchor_w25_b200 | 231.657 | 37.0039 | 123 | 0.896051 | 0.554161 | 3.14961 | 1.53327 | 0.900407 | 0.96748 | 0.833333 | 0.900407 | 0 |
| studio_M1.wav | amdf_spectral_hf05 | 116.676 | 25.5316 | 85 | 0.192009 | 3.28946 | 3.65854 | 2.38 | 0.808446 | 0.861702 | 0.84 | 0.850851 | 0 |

## Route tại native frames

| option_id | file | native_voiced_frames | routed_25ms | routed_40ms | AMDF_candidates_used | Praat_fallback |
| --- | --- | --- | --- | --- | --- | --- |
| praat7_filtered_v0.3 | phone_F1.wav | 147 | 0 | 0 | 0 | 147 |
| amdf_anchor_w25_b200 | phone_F1.wav | 147 | 147 | 0 | 145 | 2 |
| amdf_anchor_w40_b200 | phone_F1.wav | 147 | 0 | 147 | 147 | 0 |
| amdf_spectral_hf05 | phone_F1.wav | 147 | 44 | 103 | 146 | 1 |
| amdf_spectral_hf10 | phone_F1.wav | 147 | 21 | 126 | 147 | 0 |
| amdf_spectral_hf20 | phone_F1.wav | 147 | 6 | 141 | 147 | 0 |
| amdf_spectral_hf35 | phone_F1.wav | 147 | 0 | 147 | 147 | 0 |
| praat7_filtered_v0.3 | phone_M1.wav | 235 | 0 | 0 | 0 | 235 |
| amdf_anchor_w25_b200 | phone_M1.wav | 235 | 233 | 0 | 233 | 2 |
| amdf_anchor_w40_b200 | phone_M1.wav | 235 | 0 | 233 | 233 | 2 |
| amdf_spectral_hf05 | phone_M1.wav | 235 | 112 | 121 | 233 | 2 |
| amdf_spectral_hf10 | phone_M1.wav | 235 | 93 | 140 | 233 | 2 |
| amdf_spectral_hf20 | phone_M1.wav | 235 | 59 | 174 | 233 | 2 |
| amdf_spectral_hf35 | phone_M1.wav | 235 | 23 | 210 | 233 | 2 |
| praat7_filtered_v0.3 | studio_F1.wav | 123 | 0 | 0 | 0 | 123 |
| amdf_anchor_w25_b200 | studio_F1.wav | 123 | 123 | 0 | 123 | 0 |
| amdf_anchor_w40_b200 | studio_F1.wav | 123 | 0 | 123 | 123 | 0 |
| amdf_spectral_hf05 | studio_F1.wav | 123 | 66 | 57 | 123 | 0 |
| amdf_spectral_hf10 | studio_F1.wav | 123 | 50 | 73 | 123 | 0 |
| amdf_spectral_hf20 | studio_F1.wav | 123 | 32 | 91 | 123 | 0 |
| amdf_spectral_hf35 | studio_F1.wav | 123 | 16 | 107 | 123 | 0 |
| praat7_filtered_v0.3 | studio_M1.wav | 85 | 0 | 0 | 0 | 85 |
| amdf_anchor_w25_b200 | studio_M1.wav | 85 | 85 | 0 | 85 | 0 |
| amdf_anchor_w40_b200 | studio_M1.wav | 85 | 0 | 85 | 85 | 0 |
| amdf_spectral_hf05 | studio_M1.wav | 85 | 41 | 44 | 85 | 0 |
| amdf_spectral_hf10 | studio_M1.wav | 85 | 28 | 57 | 85 | 0 |
| amdf_spectral_hf20 | studio_M1.wav | 85 | 16 | 69 | 85 | 0 |
| amdf_spectral_hf35 | studio_M1.wav | 85 | 2 | 83 | 85 | 0 |

Route-count là native frame, không phải F0num của canonical grid; không coi mọi AMDFcandidate dùng là sửa pitch đúng. Curve/ratio đúng phép tính cũng không chứng nhận nội dung nhãn. Fourfile nested vẫnexploratory sau lịch sử đã xem nhiều vòng.

Độc lập fullFFT/Hann/PCM/NAMDF/parabola/band/tie/fallback/route kiểm tra588spectralframes và1176curveframes trên8curvegroups;28fixedgroups/112traces/120fits, labels/hash/gates/H41controls/PNGSVG đãcheck. H42 tái sử dụng4historicalPraatcalls,0newnativecalls; no test inference.

H42 không được promote. H41 vẫn là mốc per-fileAverage≤2%, nhưngphone_F1stdregression chưa giải quyết. Nếu thử feature/controller/band/selection mới, phải đăng ký vòng khác trước đo; không thaymetric/gate củaH42 hoặc lấybest mỗifile.
