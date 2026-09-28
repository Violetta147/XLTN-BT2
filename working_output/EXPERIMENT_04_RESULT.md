# Kết quả thí nghiệm 04: cổng năng lượng V/SIL

Chạy `.venv\Scripts\python.exe experiment_04_energy_gate.py`, chỉ dùng `TinHieuHuanLuyen` trong bốn fold leave-one-file-out. [Kế hoạch đặt trước](EXPERIMENT_04_PLAN.md), [CSV từng file](experiment_04_lofo.csv), [JSON](experiment_04_summary.json). Ngưỡng năng lượng relative RMS qua bốn fold là 0.0547, 0.0577, 0.0668, 0.0615, học từ ba file training của từng fold.

| Chỉ số | GMM lõi | Ngưỡng có nhãn | Có nhãn + năng lượng |
|---|---:|---:|---:|
| Macro F1 V/UV, trung bình file | 0.8051 | 0.8733 | **0.8747** |
| Balanced accuracy, trung bình file | 0.8836 | 0.8939 | **0.9166** |
| TP / TN / FP / FN, tổng | 490 / 175 / 5 / 124 | 559 / 159 / 21 / 55 | 551 / 166 / 14 / 63 |
| F0mean MAE, Hz | **2.0851** | 5.2992 | 3.7482 |
| F0std MAE, Hz | 8.4196 | 19.5540 | **8.3963** |
| NumF0, tổng | 520 | 668 | 568 |
| V sai trên SIL, tổng | 25 | 88 | **3** |

Cổng năng lượng giữ gần như toàn bộ lợi ích phân loại của ngưỡng có nhãn, giảm false voiced SIL từ 88 xuống 3 và giảm mạnh sai số F0std. So với GMM lõi, macro F1 tăng 0.0696, BA tăng 0.0331, FN giảm 61 trong khi FP tăng 9; F0std MAE thấp hơn khoảng 0.0233 Hz. Nhưng F0mean MAE **cao hơn 1.6631 Hz**, nên **không đạt cổng áp dụng** đã đặt trước. Không fit cấu hình cuối, không đưa vào notebook, không xem TEST để tinh chỉnh.

Theo file, F0mean MAE sau cổng còn cao ở `phone_F1` (6.92 Hz) và `studio_M1` (5.07 Hz). Chẩn đoán tiếp cần xem dấu sai số và phân bố F0 ứng viên ở hai file này trước khi đề xuất một biến mới; không thể quy lỗi còn lại cho SIL vì false voiced SIL chỉ còn 3. Không tự coi cổng năng lượng là lời giải hoàn chỉnh.
