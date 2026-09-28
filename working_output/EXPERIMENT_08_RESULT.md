# Kết quả thí nghiệm 08: AMDF Gaussian 25 ms + cổng năng lượng

Chạy `.venv\Scripts\python.exe experiment_08_amdf_energy.py` trên **bốn fold leave-one-file-out của training**, theo [kế hoạch đặt trước](EXPERIMENT_08_PLAN.md). Script tính lại AMDF Gaussian không cổng và xác nhận từng fold khớp [thí nghiệm 07](EXPERIMENT_07_RESULT.md), sau đó thêm duy nhất cổng relative RMS học từ V/SIL của ba file training. [CSV theo file](experiment_08_lofo.csv) và [JSON tổng hợp](experiment_08_summary.json) lưu cấu hình và metric.

| Chỉ số, trung bình theo file trừ số đếm | ACF 25 ms | AMDF Gaussian 25 ms | AMDF + năng lượng |
|---|---:|---:|---:|
| Macro F1 V/UV | 0.8363 | **0.8695** | 0.8646 |
| Balanced accuracy | 0.8709 | 0.9128 | **0.9206** |
| Recall V | 0.8799 | **0.8910** | 0.8763 |
| Recall UV | 0.8619 | 0.9345 | **0.9649** |
| TP / TN / FP / FN, tổng | 533 / 157 / 23 / 81 | 541 / 168 / 12 / 73 | 535 / 171 / 9 / 79 |
| F0mean MAE, Hz | 5.1277 | 4.2787 | **2.9286** |
| F0std MAE, Hz | 16.4110 | 14.5808 | **6.5022** |
| NumF0, tổng | 600 | 604 | 545 |
| V sai trên SIL, tổng | 44 | 51 | **1** |

**Đạt cổng đã đặt:** so với ACF, F1 tăng **0.0283**, BA tăng **0.0497**, cả hai F0 MAE thấp hơn và false voiced SIL giảm 44→1. So với AMDF không cổng, SIL giảm 51→1 trong khi F1 chỉ giảm **0.0049** (<0.01 cho phép). Cổng AMDF tốt hơn ACF về F1 và BA ở cả bốn file validation; F0 MAE không tốt hơn ở *mọi* file riêng lẻ, nên chỉ kết luận theo trung bình file đã đặt trước.

Ngưỡng fit lại trên **đủ bốn file training** đã đóng băng để tái lập: `T_pitch = 0.4124933063` (Gaussian), `T_energy = 0.0615446159` trên RMS chia phân vị 95% RMS của từng file. Các ngưỡng này không được dùng trong LOFO. Cấu hình là **ứng viên để triển khai/kiểm tra tiếp**, chưa phải kết quả TEST độc lập hoặc cấu hình nộp cuối: `NumF0` giảm 600→545 so với ACF và thầy chưa cho cách tính MinNumF0/MaxNumF0. Notebook hiện vẫn chưa đổi. TEST của các biến thể trước đã được xem; nếu báo TEST cho ứng viên này, phải ghi rõ giới hạn do lựa chọn nghiên cứu đã chịu ảnh hưởng từ TEST cũ.
