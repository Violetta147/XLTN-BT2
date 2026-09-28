# Kết quả thí nghiệm 07: ACF so với AMDF, cùng 25 ms

Chạy `.venv\Scripts\python.exe experiment_07_acf_amdf_25ms.py` trên **bốn file training leave-one-file-out** theo [kế hoạch đã chốt](EXPERIMENT_07_PLAN.md). Hàm tạo ba ngưỡng được nạp trực tiếp từ hai notebook gốc; mỗi fold chỉ chọn phương pháp/ngưỡng trên ba file training. [CSV từng file](experiment_07_lofo.csv) và [JSON tổng hợp](experiment_07_summary.json) ghi đủ TP/TN/FP/FN, recall, F0 và NumF0. Fit cả bốn file chỉ để đối chiếu implementation: ACF chọn `Histogram V/UV intersection`, ngưỡng **0.6840818** (notebook 0.6841); AMDF chọn `Gaussian`, ngưỡng **0.4124933** (notebook 0.4125). Không dùng hai ngưỡng toàn training đó cho các fold.

| Chỉ số, trung bình theo file trừ số đếm | ACF 25 ms | AMDF 25 ms | AMDF − ACF |
|---|---:|---:|---:|
| Macro F1 V/UV | 0.8363 | **0.8695** | +0.0331 |
| Balanced accuracy | 0.8709 | **0.9128** | +0.0418 |
| Recall V | 0.8799 | **0.8910** | +0.0111 |
| Recall UV | 0.8619 | **0.9345** | +0.0726 |
| TP / TN / FP / FN, tổng | 533 / 157 / 23 / 81 | **541 / 168 / 12 / 73** | +8 TP, +11 TN |
| F0mean MAE, Hz | 5.1277 | **4.2787** | −0.8491 |
| F0std MAE, Hz | 16.4110 | **14.5808** | −1.8302 |
| NumF0, tổng | 600 | 604 | +4 |
| V sai trên SIL, tổng | **44** | 51 | +7 |

AMDF cao hơn F1/BA trên **cả bốn file** validation; phương pháp chọn ngưỡng AMDF là Gaussian ở cả bốn fold. ACF chọn `Histogram M1/M2` ở một fold và `Histogram V/UV intersection` ở ba fold. AMDF có F0 MAE trung bình thấp hơn, nhưng không tốt hơn trên mọi file riêng lẻ. Điều kiện vượt trội đã đặt trước **không đạt** vì AMDF tăng false voiced trên SIL từ 44 lên 51; ACF cũng không vượt trội do F1 thấp hơn. Giữ cả hai notebook, chưa chọn cấu hình nộp chỉ bằng bảng này.

Giới hạn: dữ liệu validation chỉ bốn file; NumF0 không phải recall V. MinNumF0/MaxNumF0 trong ghi chú thầy chưa có định nghĩa, nên không thể chấm điều kiện số F0. Bảng TEST của các cấu hình trước đây đã được xem; không dùng nó để phá hòa hay báo cáo như đánh giá độc lập cho lựa chọn mới.
