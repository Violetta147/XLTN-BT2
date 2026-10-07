# H43 — Qua gate control nhưng nested target chưa đạt

Finalngưỡng170Hz cố định trên4file đạtAverage≤2%: 0.340080/0.776151/1.473576/1.909923%. Nhưngouterstudio_M1 chọn140Hz từ3filekhác vàheldAverage2.523880%; nestedtargetFAIL. Không coi fixedtarget lànestedtarget, khôngpromote tự động.

Phone_F1nestedstdMAPE.089632% soH31.851866% vàH41 2.332506%; tất cả8gate soH31PASS. Nestedmean1.278422% nhưngworst2.523880%; mean nhỏ không đủ. VUV/count/SIL giữcontrol, count147/233/123/85. Khôngkhẳngđịnh F0 từngkhung đúng vìGT chỉfile-stat/segment.

| file | option_id | F0mean | F0std | F0num | F0mean_mape | F0std_mape | F0num_mape | average_mape | macro_f1 | recall_v | recall_uv | balanced_accuracy | false_voiced_sil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phone_F1.wav | amdf_pitch_spectral_p170 | 216.15 | 20.5815 | 147 | 0.254931 | 0.0896324 | 0.675676 | 0.34008 | 0.938333 | 0.941176 | 0.956522 | 0.948849 | 0 |
| phone_M1.wav | amdf_pitch_spectral_p170 | 122.477 | 16.9527 | 233 | 0.988737 | 0.908681 | 0.431034 | 0.776151 | 0.928721 | 0.946721 | 0.967742 | 0.957232 | 0 |
| studio_F1.wav | amdf_pitch_spectral_p170 | 232.091 | 36.8685 | 123 | 1.08487 | 0.186249 | 3.14961 | 1.47358 | 0.900407 | 0.96748 | 0.833333 | 0.900407 | 0 |
| studio_M1.wav | amdf_pitch_spectral_p140 | 116.585 | 25.4382 | 85 | 0.269847 | 3.64326 | 3.65854 | 2.52388 | 0.808446 | 0.861702 | 0.84 | 0.850851 | 0 |

## Vì sao studio_M1 chọn140?

| outer_held | option_id | selection_files | worst_average_mape | mean_average_mape | selected |
| --- | --- | --- | --- | --- | --- |
| studio_M1.wav | amdf_pitch_spectral_p140 | phone_F1.wav\|phone_M1.wav\|studio_F1.wav | 1.43556 | 0.849423 | True |
| studio_M1.wav | amdf_pitch_spectral_p000 | phone_F1.wav\|phone_M1.wav\|studio_F1.wav | 1.43556 | 0.861714 | False |
| studio_M1.wav | amdf_pitch_spectral_p170 | phone_F1.wav\|phone_M1.wav\|studio_F1.wav | 1.47358 | 0.863269 | False |
| studio_M1.wav | amdf_anchor_w25_b200 | phone_F1.wav\|phone_M1.wav\|studio_F1.wav | 1.53327 | 1.12999 | False |
| studio_M1.wav | amdf_pitch_spectral_p200 | phone_F1.wav\|phone_M1.wav\|studio_F1.wav | 1.62955 | 1.05367 | False |
| studio_M1.wav | praat7_filtered_v0.3 | phone_F1.wav\|phone_M1.wav\|studio_F1.wav | 1.70384 | 1.1047 | False |
| studio_M1.wav | amdf_anchor_w40_b200 | phone_F1.wav\|phone_M1.wav\|studio_F1.wav | 1.87103 | 1.15965 | False |

So sánh chỉ trong3filecòn lại:140Hz cóworst/mean nhỏ hơn170Hz; quy tắcminimax làm đúngregistry nhưngheldstudio_M1 xấu. Đây là bằng chứng limitedselectionstability trênn4, khôngcode bỏqua cấuhình170 hoặc leakheldfile. Khôngsửaselection/gateH43 sauđo.

## Routecounts

| option_id | file | raw_native_voiced | range_excluded | in_range_native_voiced | route25 | route40 | AMDF_used | Praat_fallback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| praat7_filtered_v0.3 | phone_F1.wav | 147 | 0 | 147 | 0 | 0 | 0 | 147 |
| amdf_anchor_w25_b200 | phone_F1.wav | 147 | 0 | 147 | 147 | 0 | 145 | 2 |
| amdf_anchor_w40_b200 | phone_F1.wav | 147 | 0 | 147 | 0 | 147 | 147 | 0 |
| amdf_pitch_spectral_p000 | phone_F1.wav | 147 | 0 | 147 | 44 | 103 | 146 | 1 |
| amdf_pitch_spectral_p140 | phone_F1.wav | 147 | 0 | 147 | 44 | 103 | 146 | 1 |
| amdf_pitch_spectral_p170 | phone_F1.wav | 147 | 0 | 147 | 44 | 103 | 146 | 1 |
| amdf_pitch_spectral_p200 | phone_F1.wav | 147 | 0 | 147 | 84 | 63 | 146 | 1 |
| praat7_filtered_v0.3 | phone_M1.wav | 235 | 2 | 233 | 0 | 0 | 0 | 235 |
| amdf_anchor_w25_b200 | phone_M1.wav | 235 | 2 | 233 | 233 | 0 | 233 | 2 |
| amdf_anchor_w40_b200 | phone_M1.wav | 235 | 2 | 233 | 0 | 233 | 233 | 2 |
| amdf_pitch_spectral_p000 | phone_M1.wav | 235 | 2 | 233 | 112 | 121 | 233 | 2 |
| amdf_pitch_spectral_p140 | phone_M1.wav | 235 | 2 | 233 | 205 | 28 | 233 | 2 |
| amdf_pitch_spectral_p170 | phone_M1.wav | 235 | 2 | 233 | 233 | 0 | 233 | 2 |
| amdf_pitch_spectral_p200 | phone_M1.wav | 235 | 2 | 233 | 233 | 0 | 233 | 2 |
| praat7_filtered_v0.3 | studio_F1.wav | 123 | 0 | 123 | 0 | 0 | 0 | 123 |
| amdf_anchor_w25_b200 | studio_F1.wav | 123 | 0 | 123 | 123 | 0 | 123 | 0 |
| amdf_anchor_w40_b200 | studio_F1.wav | 123 | 0 | 123 | 0 | 123 | 123 | 0 |
| amdf_pitch_spectral_p000 | studio_F1.wav | 123 | 0 | 123 | 66 | 57 | 123 | 0 |
| amdf_pitch_spectral_p140 | studio_F1.wav | 123 | 0 | 123 | 66 | 57 | 123 | 0 |
| amdf_pitch_spectral_p170 | studio_F1.wav | 123 | 0 | 123 | 67 | 56 | 123 | 0 |
| amdf_pitch_spectral_p200 | studio_F1.wav | 123 | 0 | 123 | 87 | 36 | 123 | 0 |
| praat7_filtered_v0.3 | studio_M1.wav | 85 | 0 | 85 | 0 | 0 | 0 | 85 |
| amdf_anchor_w25_b200 | studio_M1.wav | 85 | 0 | 85 | 85 | 0 | 85 | 0 |
| amdf_anchor_w40_b200 | studio_M1.wav | 85 | 0 | 85 | 0 | 85 | 85 | 0 |
| amdf_pitch_spectral_p000 | studio_M1.wav | 85 | 0 | 85 | 41 | 44 | 85 | 0 |
| amdf_pitch_spectral_p140 | studio_M1.wav | 85 | 0 | 85 | 74 | 11 | 85 | 0 |
| amdf_pitch_spectral_p170 | studio_M1.wav | 85 | 0 | 85 | 80 | 5 | 85 | 0 |
| amdf_pitch_spectral_p200 | studio_M1.wav | 85 | 0 | 85 | 85 | 0 | 85 | 0 |

Route chỉnativeF0∈70–400; phone_M1 có2rawPraatframes khoảng473Hz bị rangeexclude, canonicalcount233 khôngđổi. Không tínhhai frame này làAMDFroute hoặcnhãnsai đãxácnhận.

H43 verifier independentlyreplayed fullFFT/Hann/PCM/NAMDF/band/refine/tie/routepitchcondition/sourcenativehash/labels/std/MAPE/count/VUV/support và112traces/120fits/28fixedgroups. H42p0parity/H41controls kiểm tra. 0newnativecalls,4historicalPraatgroups; no testinference/tuning. Giữfailures, original/frozen/notebooks cũ.

Tiếp theo notebook riêng replayregisteredH42/H43 từWAV đểcósource/figures/receipts thực; hypothesis mới cầnprereg trước đo. H41 targetnested vẫn làmốc, H43 cònselectiontarget chưađạt; không đổi mục tiêu thành mean≤2%.
