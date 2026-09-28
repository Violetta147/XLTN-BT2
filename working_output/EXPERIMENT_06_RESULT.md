# Kết quả thí nghiệm 06: ngưỡng Gaussian có nhãn, AMDF 25 ms

Chạy `.venv\Scripts\python.exe experiment_06_gaussian_threshold.py` trên **bốn fold training**, theo [kế hoạch đặt trước](EXPERIMENT_06_PLAN.md). [CSV từng file](experiment_06_lofo.csv) và [JSON tổng hợp](experiment_06_summary.json) lưu đủ ngưỡng, TP/TN/FP/FN, recall, F0, NumF0 và SIL. Ngưỡng Gaussian trong từng fold là **0.4083–0.4162**, fit riêng trên ba file training. Kiểm tra công thức với score của toàn training cho **0.4124933**, khớp số 0.4125 trong notebook AMDF; số toàn training này chỉ dùng để kiểm tra cách tính, không áp dụng cố định trong các fold.

| Chỉ số, trung bình theo file trừ số đếm | GMM lõi | Gaussian có nhãn | Chênh lệch |
|---|---:|---:|---:|
| Macro F1 V/UV | 0.8051 | 0.8695 | +0.0644 |
| Balanced accuracy | 0.8836 | 0.9128 | +0.0292 |
| Recall V | 0.8056 | 0.8910 | +0.0854 |
| Recall UV | 0.9615 | 0.9345 | −0.0270 |
| TP / TN / FP / FN, tổng | 490 / 175 / 5 / 124 | 541 / 168 / 12 / 73 | +51 TP, +7 FP |
| F0mean MAE, Hz | 2.0851 | 4.2787 | +2.1936 (xấu hơn) |
| F0std MAE, Hz | 8.4196 | 14.5808 | +6.1612 (xấu hơn) |
| NumF0, tổng | 520 | 604 | +84 |
| V sai trên SIL, tổng | 25 | 51 | +26 |

Ngưỡng có nhãn đạt phần phân loại của cổng đã đặt nhưng **không đạt cổng áp dụng tổng thể** vì cả hai sai số F0 và false voiced trên SIL cùng tăng. Không đổi notebook, không xem TEST để chọn biến thể mới. Điều này củng cố kết luận từ thí nghiệm 01/03: một ngưỡng AMDF rộng hơn cứu V nhưng cũng nhận thêm F0 ứng viên không đáng tin; chỉ đổi công thức ngưỡng chưa giải quyết đồng thời V/UV và F0. Hướng tiếp theo cần kiểm tra độ tin cậy F0 hoặc chọn baseline 25 ms phù hợp yêu cầu thầy, không lặp lại dò một ngưỡng trên TEST.
