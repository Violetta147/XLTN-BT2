# H52 — kết quả mở rộng YAAPT

**Không có cải thiện đủ để thay baseline.** Final và cả bốn outer folds chọn hard170. YAAPT đã được thử ở H40; H52 mở rộng ngưỡng hữu thanh, dùng riêng cao độ dưới mask hiện tại và bỏ transition cost ở bước DP cuối.

Default35ms được replay để lưu candidate/merit/NLFER evidence; raw/native/canonical parity với H40_f35 đã kiểm. Đây không phải bằng chứng độc lập mới. Hồ sơ H40 và các probe sine/rich173 lỗi octave giữ nguyên; bộ probe mới không phủ định lỗi cũ.

## Train

| option_id | file | average_mape | F0mean_mape | F0std_mape | F0num_mape | macro_f1 | recall_v | false_voiced_sil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hard170 | phone_F1.wav | 0.34008 | 0.254931 | 0.0896324 | 0.675676 | 0.938333 | 0.941176 | 0 |
| yaapt_default | phone_F1.wav | 1.61251 | 1.02293 | 2.46326 | 1.35135 | 0.933433 | 0.934641 | 0 |
| yaapt_nlfer050 | phone_F1.wav | 1.9399 | 0.848297 | 4.29574 | 0.675676 | 0.938333 | 0.941176 | 0 |
| yaapt_nlfer100 | phone_F1.wav | 1.81837 | 1.07757 | 3.0262 | 1.35135 | 0.933433 | 0.934641 | 0 |
| yaapt_pitch_only | phone_F1.wav | 0.938348 | 0.624652 | 1.51472 | 0.675676 | 0.938333 | 0.941176 | 0 |
| yaapt_no_final_dp | phone_F1.wav | 0.574154 | 1.08584 | 0.636619 | 0 | 0.922636 | 0.934641 | 0 |
| hard170 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| yaapt_default | phone_M1.wav | 2.04954 | 2.54467 | 1.87981 | 1.72414 | 0.908738 | 0.942623 | 1 |
| yaapt_nlfer050 | phone_M1.wav | 2.09738 | 2.435 | 1.70196 | 2.15517 | 0.913068 | 0.946721 | 1 |
| yaapt_nlfer100 | phone_M1.wav | 0.89405 | 2.09741 | 0.584743 | 0 | 0.891848 | 0.92623 | 1 |
| yaapt_pitch_only | phone_M1.wav | 0.810006 | 1.77583 | 0.223153 | 0.431034 | 0.928721 | 0.946721 | 0 |
| yaapt_no_final_dp | phone_M1.wav | 2.47853 | 1.5729 | 0.690269 | 5.17241 | 0.862496 | 0.885246 | 1 |
| hard170 | studio_F1.wav | 1.47358 | 1.08487 | 0.186249 | 3.14961 | 0.900407 | 0.96748 | 0 |
| yaapt_default | studio_F1.wav | 1.98456 | 0.247004 | 4.13187 | 1.5748 | 0.886037 | 0.96748 | 1 |
| yaapt_nlfer050 | studio_F1.wav | 1.61574 | 0.432331 | 3.62748 | 0.787402 | 0.896914 | 0.97561 | 1 |
| yaapt_nlfer100 | studio_F1.wav | 2.36441 | 0.0903668 | 4.64066 | 2.3622 | 0.875508 | 0.95935 | 1 |
| yaapt_pitch_only | studio_F1.wav | 2.78667 | 0.0531629 | 5.15725 | 3.14961 | 0.900407 | 0.96748 | 0 |
| yaapt_no_final_dp | studio_F1.wav | 1.80689 | 0.537108 | 4.09615 | 0.787402 | 0.896914 | 0.97561 | 1 |
| hard170 | studio_M1.wav | 1.90992 | 0.0161649 | 2.05507 | 3.65854 | 0.808446 | 0.861702 | 0 |
| yaapt_default | studio_M1.wav | 8.66448 | 2.60249 | 9.9763 | 13.4146 | 0.83779 | 0.925532 | 0 |
| yaapt_nlfer050 | studio_M1.wav | 9.12659 | 2.79072 | 9.95489 | 14.6341 | 0.822766 | 0.925532 | 0 |
| yaapt_nlfer100 | studio_M1.wav | 8.1873 | 2.48673 | 8.66053 | 13.4146 | 0.83779 | 0.925532 | 0 |
| yaapt_pitch_only | studio_M1.wav | 5.67825 | 2.59815 | 10.7781 | 3.65854 | 0.808446 | 0.861702 | 0 |
| yaapt_no_final_dp | studio_M1.wav | 7.80887 | 3.10284 | 10.5677 | 9.7561 | 0.832327 | 0.904255 | 0 |

## Test đã chốt trước

| option_id | file | average_mape | F0mean_mape | F0std_mape | F0num_mape | macro_f1 | recall_v | false_voiced_sil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hard170 | phone_F2.wav | 4.19731 | 1.51635 | 10.619 | 0.456621 | 0.870816 | 0.906383 | 0 |
| yaapt_default | phone_F2.wav | 4.29656 | 2.83768 | 4.11593 | 5.93607 | 0.815908 | 0.910638 | 0 |
| hard170 | phone_M2.wav | 6.83375 | 0.884189 | 13.926 | 5.69106 | 0.977499 | 0.970149 | 0 |
| yaapt_default | phone_M2.wav | 4.63873 | 2.20859 | 3.57753 | 8.13008 | 0.937416 | 0.955224 | 0 |
| hard170 | studio_F2.wav | 5.06346 | 0.0266886 | 10.8471 | 4.31655 | 0.881481 | 0.948905 | 0 |
| yaapt_default | studio_F2.wav | 1.85319 | 1.07636 | 3.04437 | 1.43885 | 0.91778 | 0.992701 | 0 |
| hard170 | studio_M2.wav | 2.11479 | 0.32909 | 2.56701 | 3.44828 | 0.850806 | 0.921875 | 0 |
| yaapt_default | studio_M2.wav | 4.05093 | 0.356653 | 0.589231 | 11.2069 | 0.808042 | 0.953125 | 0 |

Selected hard170 giữ0/4test <2%,4/4train <2%; mục tiêu8file FAIL. YAAPTdefault chẩn đoán có studio_F2=1.85319%, nhưng ba test khác >2% và không được chọn trên train. Không dùng kết quả test để ghép pipeline theo file.

v2 verifier PASS5148train và1301test frames,32metric groups tổng cộng, final DP scalar và PCM NLFER fullFFT độc lập; không reimplement toàn bộ spectral candidate generation. V1 sai thứ tự phép tính float khi các chi phí gần hòa; chỉ checker v2 sửa, source đo/outputs giữ nguyên. Xem H52_VERIFICATION_NOTE.md.

Prereg đầu51f05a9 dùng trùng tên source H40. Đã phục hồi ba file H40 từ56ee7d8, đổi tên source H52 và đăng ký amendedc09574e **trước bất kỳ đo BT2 H52**; testfreeze390a533. H40 source diff so56ee7d8 hiện bằng0. Không sửa notebook đã nộp, WAV/LAB hoặc frozen baseline.

Nguồn/phiên bản, mức đọc HTML/abstract/code và lỗi discovery ở H52_YAAPT_SOURCE_NOTE.md. Không đọc PDF. Lệnh: yaapt_extension.py train/external; verify_yaapt_extension_v2.py train/test. Không có stochastic fit/seed; không rerun kết quả đã lưu. Không đủ bằng chứng quy nguyên nhân cho dữ liệu ít hoặc GT sai.
