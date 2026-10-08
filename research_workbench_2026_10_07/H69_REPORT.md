# H69 — pYIN thực sự 25 ms: tốt riêng hai file studio, chưa đạt chung

Đã hoàn tất 12 lần suy luận mới trên **bốn file train**, không đo test và không chạy lại H00–H68/R01/R02. Cấu hình `(2,18)` mặc định là cấu hình pYIN 25 ms thống nhất tốt nhất trong ba cấu hình theo MAPE file tệ nhất, nhưng vẫn thất bại ở hai file phone. hard170 chỉ được giữ làm đối chứng lịch sử; nó không đáp ứng cửa sổ thực sự 25 ms của bài.

Average MAPE là trung bình ba sai số phần trăm của F0mean, F0std và F0num. F0num được pipeline tính là số khung có F0 hữu hạn; chưa biết quy trình đếm chuẩn của thầy. Hữu thanh (V) có rung dây thanh, vô thanh (UV) không có; SIL là đoạn im lặng theo LAB. Không có F0 chuẩn từng khung.

## Cấu hình và bằng chứng cửa sổ

Librosa 0.11.0, không đổi tần số lấy mẫu, không thêm mẫu biên, `center=False`, F0 70–400 Hz, độ phân giải 0,1 bán âm. Ba `beta_parameters=(2,8)/(2,18)/(2,38)` có kỳ vọng ngưỡng 0,2/0,1/0,05. Các tham số còn lại lấy từ H33 đã khóa. Cửa sổ/bước khung phone: 400/160 mẫu ở 16 kHz; studio: 1102/441 mẫu ở 44,1 kHz, tương ứng 24,988662/10 ms theo Python round (làm tròn gần nhất, hòa chọn số chẵn). Không dùng cửa sổ Praat dài hơn hoặc chỉ chiếu kết quả lên lưới 25 ms.

Có 12 cảnh báo về 70 Hz chứa dưới hai chu kỳ trong 25 ms; giữ nguyên trong log. Không kéo dài cửa sổ để né cảnh báo. Sai khác quy ước làm tròn 1102/1103 mẫu chưa được khảo sát, không coi là nguyên nhân đã xác nhận.

18 tín hiệu tổng hợp và 6 tín hiệu bằng không PASS trước khi đo BT2. Native timestamps, số khung, dải F0, xác suất và mặt nạ đã được kiểm độc lập. Đây là kiểm tra tích hợp và các fixture đơn giản, không bảo đảm đúng trên tiếng nói thật.

## MAPE theo file train

| Cấu hình | phone_F1 | phone_M1 | studio_F1 | studio_M1 | Mean bốn file | Worst |
|---|---:|---:|---:|---:|---:|---:|
| hard170 | 0.340080 | 0.776151 | 1.473576 | 1.909923 | 1.124932 | 1.909923 |
| pyin25_beta2_8 | 3.901941 | 1.047267 | 11.994667 | 24.428648 | 10.343131 | 24.428648 |
| pyin25_beta2_18 | 5.447286 | 6.056821 | 1.465577 | 0.699716 | 3.417350 | 6.056821 |
| pyin25_beta2_38 | 7.065133 | 32.709611 | 1.553355 | NaN | Không hợp lệ | Không hợp lệ |

Cấu hình mặc định có 2/4 file train dưới 2%, mean **3,417350%**, worst **6,056821%**. Không ghép cấu hình theo file. `(2,38)` dự đoán studio_M1 có 0 khung hữu thanh nên mean/std/MAPE là NaN; không lấy mean bỏ qua NaN để xếp hạng cấu hình đó.

## Phân phối và số khung

| File | Mean pYIN mặc định / chuẩn (Hz) | Std pYIN mặc định / chuẩn (Hz) | Count pYIN mặc định / chuẩn |
|---|---:|---:|---:|
| phone_F1.wav | 218.445931 / 215.6 | 20.632340 / 20.6 | 126 / 148 |
| phone_M1.wav | 125.351196 / 123.7 | 16.578512 / 16.8 | 196 / 232 |
| studio_F1.wav | 231.264226 / 229.6 | 36.992202 / 36.8 | 131 / 127 |
| studio_M1.wav | 117.145461 / 116.9 | 26.576790 / 26.4 | 83 / 82 |

Ở phone, prior mặc định loại quá nhiều khung so với count chuẩn: 126/148 và 196/232, trong khi std gần chuẩn. Khi chuyển prior `(2,8)`, count lên 157/235; phone_M1 đạt 1,047267%, nhưng studio_F1 có 15 và studio_M1 có 45 khung SIL dự đoán hữu thanh. Prior thống nhất không giải quyết đồng thời hai môi trường trong phép thử này. Không suy từ đây rằng phần mềm của thầy là pYIN hoặc Viterbi đã đúng từng khung.

## Đánh đổi V/UV và cao độ

Các tỷ lệ dưới đây là mean theo bốn file; SIL là tổng số khung. MAE mean/std có đơn vị Hz.

| Cấu hình | Macro F1 | Recall V | Recall UV | Balanced accuracy | MAE mean | MAE std | SIL dự đoán V |
|---|---:|---:|---:|---:|---:|---:|---:|
| hard170 | 0.893977 | 0.929270 | 0.899399 | 0.914335 | 1.070616 | 0.195550 | 0 |
| pyin25_beta2_8 | 0.828165 | 0.923912 | 0.732536 | 0.828224 | 2.966907 | 2.641465 | 60 |
| pyin25_beta2_18 | 0.816298 | 0.853346 | 0.855219 | 0.854282 | 1.601704 | 0.155705 | 3 |

Baseline ACF 25 ms đã lưu (full-train, ngưỡng học từ cả train) có MAPE 29,834711%, macro F1 0,848791 và 45 SIL dự đoán V. pYIN mặc định có MAPE mô tả thấp hơn nhiều và SIL 3, nhưng macro F1 giảm còn 0,816298. Đây là đối chiếu pipeline và protocol full-train đã lưu, không phải chứng minh mức cải thiện nested tương đương. Baseline AMDF_energy 25 ms đã lưu có MAPE 12,270267%, F1 0,869716, SIL 0; cũng không bị thay thế. Không tuyên bố đây là tốt nhất toàn bộ lịch sử 25 ms chưa được kiểm toán đầy đủ.

## Chọn cấu hình và kiểm tra

Giữ nguyên tám gate nghiên cứu lịch sử. Final và cả bốn vòng ngoài chọn hard170, ba gate cải thiện MAPE FAIL, năm điều kiện còn lại PASS; candidate đồng nhất với control trong summary không có nghĩa pYIN đã đạt. `eligible=false`, `champion_promoted=false`. Không đo test. Mục tiêu mỗi file trong cả tám file dưới 2% vẫn chưa đạt; hard170 không phải bản nộp tuân thủ 25 ms.

Verifier v1 dừng vì hai NaN không được coi là bằng nhau. V2 sửa riêng việc đọc và so trường numeric bị thiếu, có các lần dừng trung gian được giữ tại [ghi chú kiểm tra](H69_VERIFICATION_NOTE.md). V2 cuối **PASS 16 nhóm**, metric scalar, timestamps/mask/probability, 64 inner traces, 24 summary, membership thay đổi, source/runtime/protected/output hashes. Không sửa suy luận, số đo, tolerance, lựa chọn hoặc điều kiện hữu hạn; ứng viên 0 khung vẫn thất bại. Thuật toán ứng viên/xác suất/Viterbi là mã librosa đã khóa, không được triển khai độc lập lại.

## Tái lập và giới hạn

Prereg đã commit/push và xác minh SHA remote trước đo: `ee4b08b682f69d29e37f7ed0725bb2823a514fe4`. Runtime Python 3.13.11, NumPy 2.4.3, SciPy 1.17.1; pYIN runtime theo H33. Phần đo train khoảng 21.324 giây, không gồm cài đặt/precheck/kiểm tra và không phải benchmark phần mềm.

Nguồn mới: `pyin25_adapter.py`, `pyin25_experiment.py`, `verify_pyin25.py`, `verify_pyin25_v2.py`; registry/prereg và artifacts H69 trong `results/`. Lệnh đã chạy: `pyin25_experiment.py precheck`, `pyin25_experiment.py train`, `verify_pyin25_v2.py` bằng venv pYIN. **Không chạy lại những lệnh đo này để khôi phục chat**; đọc receipt/CSV/NPZ đã lưu.

Bốn file train và lịch sử nhiều phép chọn làm kết quả mang tính khám phá; test đã từng tiếp xúc. Không dùng test để chọn thêm prior. Hướng hẹp còn đáng cân nhắc: kiểm tra từ cache liệu các khung dư của prior `(2,8)` tập trung ở năng lượng thấp, rồi mới đăng ký phép loại khung bằng năng lượng trên cùng cửa sổ 25 ms. Hiện chưa đăng ký hoặc đo H70, không gọi hướng đó là kết quả.

Dùng experimental-design / literature-review; nguồn [librosa pYIN 0.11](https://librosa.org/doc/0.11.0/generated/librosa.pyin.html) và [Scientific Agent Skills](https://arxiv.org/abs/2609.00065), DOI 10.48550/arXiv.2609.00065. Không Jev, Drive, deep learning, PDF, Colab hoặc sửa notebook gốc.
