# Kết quả thí nghiệm 03: ngưỡng có nhãn AMDF 25 ms

Chạy `.venv\Scripts\python.exe experiment_03_labeled_threshold.py`, chỉ dùng `TinHieuHuanLuyen` với leave-one-file-out; [kế hoạch đặt trước](EXPERIMENT_03_PLAN.md), [kết quả từng fold](experiment_03_lofo.csv), [JSON](experiment_03_summary.json). Mỗi fold chọn ngưỡng trên ba file training và kiểm tra trên file thứ tư. Baseline GMM cùng fold khớp thí nghiệm 01/02.

| Chỉ số | GMM không nhãn | Ngưỡng từ nhãn training | Chênh lệch |
|---|---:|---:|---:|
| Macro F1 V/UV, trung bình file | 0.8051 | 0.8733 | +0.0683 |
| Balanced accuracy, trung bình file | 0.8836 | 0.8939 | +0.0103 |
| TP / TN / FP / FN, tổng | 490 / 175 / 5 / 124 | 559 / 159 / 21 / 55 | +69 TP, +16 FP |
| F0mean MAE, Hz | 2.0851 | 5.2992 | +3.2141 (xấu hơn) |
| F0std MAE, Hz | 8.4196 | 19.5540 | +11.1344 (xấu hơn) |
| NumF0, tổng | 520 | 668 | +148 |
| V sai trên SIL, tổng | 25 | 88 | +63 |

Ngưỡng có nhãn qua bốn fold = 0.4393, 0.4393, 0.4467, 0.4649; GMM lõi = 0.3508, 0.3413, 0.3478, 0.3495. Ngưỡng cao hơn thu hồi nhiều V nhưng cũng nhận thêm UV/SIL và nhiều F0 ứng viên. Cổng **phân loại** đặt trước đạt; cổng **áp dụng đầy đủ** không đạt do cả F0mean/F0std MAE và false voiced SIL cùng tăng. Không fit ngưỡng cuối trên bốn file, không đổi notebook và không dùng TEST để tinh chỉnh.

Kết luận giới hạn: với đúng AMDF 25 ms và cùng F0 estimator, dùng nhãn để học một ngưỡng duy nhất cải thiện phân loại V/UV trong validation theo file; nó chưa là giải pháp tổng thể cho thống kê F0. Cần tách bài toán nhận diện V/UV khỏi việc chấp nhận F0 ứng viên, hoặc kiểm soát SIL/độ tin cậy pitch, bằng một giả thuyết mới có tiêu chí đặt trước. Không thể kết luận ngưỡng có nhãn luôn tốt hơn mọi chỉ số.
