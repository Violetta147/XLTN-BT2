# Kết quả thí nghiệm 02: lấp một khung yếu

Chạy `.venv\Scripts\python.exe experiment_02_single_gap.py`, chỉ dùng bốn file `TinHieuHuanLuyen`, leave-one-file-out; [kế hoạch đặt trước](EXPERIMENT_02_PLAN.md), [CSV từng file](experiment_02_lofo.csv), [JSON](experiment_02_summary.json). Điểm quay lại: commit `5767527`. Baseline GMM lõi được tính lại cùng frame và khớp chính xác thí nghiệm 01: TP/TN/FP/FN = 490/175/5/124, macro F1 = 0.8050679204.

| Chỉ số | GMM lõi | Lấp một khung | Chênh lệch |
|---|---:|---:|---:|
| Macro F1 V/UV, trung bình file | 0.8051 | 0.8147 | +0.0096 |
| Balanced accuracy, trung bình file | 0.8836 | 0.8896 | +0.0060 |
| TP / TN / FP / FN, tổng | 490 / 175 / 5 / 124 | 497 / 175 / 5 / 117 | +7 TP, FP không đổi |
| F0mean MAE, Hz | 2.0851 | 2.8330 | +0.7480 (xấu hơn) |
| F0std MAE, Hz | 8.4196 | 9.1165 | +0.6969 (xấu hơn) |
| NumF0, tổng | 520 | 529 | +9 |
| V sai trên SIL, tổng | 25 | 27 | +2 |

**Không giữ**: F1 tăng dưới 0.01 và cả hai F0 MAE cùng false voiced SIL đều vượt baseline. Không đưa quy tắc vào notebook, không chạy TEST để dò sửa. Kết quả phù hợp với rủi ro đã dự kiến: lỗ một khung chỉ cứu được một phần nhỏ FN; 2 khung SIL vẫn được thêm. Thử nghiệm khác cần kế hoạch và commit riêng.
