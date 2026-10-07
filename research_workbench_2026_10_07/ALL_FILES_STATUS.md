# Cấu hình hard170 cố định — kiểm tra toàn bộ 8 file

Cấu hình chốt từ train trước phép đo test, chỉ một cấu hình; không chọn best trên test. Bốn train tái sử dụng kết quả H47 đã replay, bốn test tính mới từ WAV. Test đã được xem trong lịch sử nên không gọi đây là held-out độc lập hoàn toàn.

| split | file | F0mean_mape | F0std_mape | F0num_mape | average_mape | F0mean_abs_error | F0std_abs_error | F0num | macro_f1 | recall_v | recall_uv | balanced_accuracy | false_voiced_sil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | phone_F1.wav | 0.254931 | 0.0896324 | 0.675676 | 0.34008 | 0.549631 | 0.0184643 | 147 | 0.938333 | 0.941176 | 0.956522 | 0.948849 | 0 |
| train | phone_M1.wav | 0.988737 | 0.908681 | 0.431034 | 0.776151 | 1.22307 | 0.152658 | 233 | 0.928721 | 0.946721 | 0.967742 | 0.957232 | 0 |
| train | studio_F1.wav | 1.08487 | 0.186249 | 3.14961 | 1.47358 | 2.49087 | 0.0685396 | 123 | 0.900407 | 0.96748 | 0.833333 | 0.900407 | 0 |
| train | studio_M1.wav | 0.0161649 | 2.05507 | 3.65854 | 1.90992 | 0.0188967 | 0.542538 | 85 | 0.808446 | 0.861702 | 0.84 | 0.850851 | 0 |
| test | phone_F2.wav | 1.51635 | 10.619 | 0.456621 | 4.19731 | 2.27755 | 3.26003 | 220 | 0.870816 | 0.906383 | 0.895522 | 0.900953 | 0 |
| test | phone_M2.wav | 0.884189 | 13.926 | 5.69106 | 6.83375 | 1.15121 | 2.1446 | 130 | 0.977499 | 0.970149 | 1 | 0.985075 | 0 |
| test | studio_F2.wav | 0.0266886 | 10.8471 | 4.31655 | 5.06346 | 0.0530035 | 5.18494 | 133 | 0.881481 | 0.948905 | 0.869565 | 0.909235 | 0 |
| test | studio_M2.wav | 0.32909 | 2.56701 | 3.44828 | 2.11479 | 0.509102 | 0.777803 | 120 | 0.850806 | 0.921875 | 0.9 | 0.910937 | 0 |

Mỗi file <2%: **False**. Mỗi test <2%: **False**.

## Test so với Praat control

| split | model | file | F0mean | F0std | F0num | F0mean_mape | F0std_mape | F0num_mape | average_mape | F0mean_abs_error | F0std_abs_error | TP | TN | FP | FN | recall_v | recall_uv | balanced_accuracy | macro_f1 | accuracy_vu | false_voiced_sil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | accepted | phone_F2.wav | 147.449 | 33.8253 | 220 | 1.83145 | 10.1803 | 0.456621 | 4.15612 | 2.75084 | 3.12535 | 213 | 60 | 7 | 22 | 0.906383 | 0.895522 | 0.900953 | 0.870816 | 0.903974 | 0 |
| test | candidate | phone_F2.wav | 147.922 | 33.96 | 220 | 1.51635 | 10.619 | 0.456621 | 4.19731 | 2.27755 | 3.26003 | 213 | 60 | 7 | 22 | 0.906383 | 0.895522 | 0.900953 | 0.870816 | 0.903974 | 0 |
| test | accepted | phone_M2.wav | 128.899 | 17.3712 | 130 | 0.999398 | 12.7999 | 5.69106 | 6.49677 | 1.30122 | 1.97118 | 130 | 65 | 0 | 4 | 0.970149 | 1 | 0.985075 | 0.977499 | 0.979899 | 0 |
| test | candidate | phone_M2.wav | 129.049 | 17.5446 | 130 | 0.884189 | 13.926 | 5.69106 | 6.83375 | 1.15121 | 2.1446 | 130 | 65 | 0 | 4 | 0.970149 | 1 | 0.985075 | 0.977499 | 0.979899 | 0 |
| test | accepted | studio_F2.wav | 198.455 | 42.3308 | 133 | 0.0728118 | 11.4419 | 4.31655 | 5.2771 | 0.144604 | 5.46925 | 130 | 20 | 3 | 7 | 0.948905 | 0.869565 | 0.909235 | 0.881481 | 0.9375 | 0 |
| test | candidate | studio_F2.wav | 198.547 | 42.6151 | 133 | 0.0266886 | 10.8471 | 4.31655 | 5.06346 | 0.0530035 | 5.18494 | 130 | 20 | 3 | 7 | 0.948905 | 0.869565 | 0.909235 | 0.881481 | 0.9375 | 0 |
| test | accepted | studio_M2.wav | 155.062 | 29.5667 | 120 | 0.23412 | 2.42019 | 3.44828 | 2.03419 | 0.362183 | 0.733317 | 118 | 18 | 2 | 10 | 0.921875 | 0.9 | 0.910937 | 0.850806 | 0.918919 | 0 |
| test | candidate | studio_M2.wav | 155.209 | 29.5222 | 120 | 0.32909 | 2.56701 | 3.44828 | 2.11479 | 0.509102 | 0.777803 | 118 | 18 | 2 | 10 | 0.921875 | 0.9 | 0.910937 | 0.850806 | 0.918919 | 0 |

Average MAPE là trung bình lỗi tương đối của thống kê mean/std/count cả file, không phải F0 từng khung. Không có per-frame pitch GT. Augmentation H47 không được chọn; hard170 đã biết từ H43. Không chỉnh GT, không sửa notebook đã nộp hoặc frozen_config gốc. Nếu test chưa đạt, giữ failure và không dò tham số trên chính test để gọi cải tiến độc lập.
