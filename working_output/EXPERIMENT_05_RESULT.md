# Kết quả thí nghiệm 05: median 3 khung trên F0

Chạy `.venv\Scripts\python.exe experiment_05_median_f0.py` chỉ trên bốn fold training; [kế hoạch đặt trước](EXPERIMENT_05_PLAN.md), [CSV theo file](experiment_05_lofo.csv), [JSON](experiment_05_summary.json). Lọc median chỉ tác động F0 nội bộ của run V dự đoán; code xác nhận TP/TN/FP/FN, macro F1, BA, NumF0 và false voiced SIL **giống hệt** cấu hình 04.

| Chỉ số | GMM lõi | Có nhãn + năng lượng | Thêm median 3 |
|---|---:|---:|---:|
| Macro F1 V/UV | 0.8051 | 0.8747 | 0.8747 |
| Balanced accuracy | 0.8836 | 0.9166 | 0.9166 |
| F0mean MAE, Hz | **2.0851** | 3.7482 | 2.9663 |
| F0std MAE, Hz | 8.4196 | 8.3963 | **6.6175** |
| NumF0 / false voiced SIL, tổng | 520 / 25 | 568 / 3 | 568 / 3 |

`phone_F1` cải thiện F0mean MAE từ 6.92 xuống 3.13 Hz và F0std MAE từ 16.00 xuống 9.22 Hz; `studio_M1` vẫn khoảng 5.17 Hz F0mean MAE. Cổng áp dụng **không đạt** vì F0mean MAE trung bình còn cao hơn GMM lõi 0.8812 Hz. Không đưa chuỗi cấu hình 04+05 vào notebook, không xem TEST để chọn cửa sổ median khác.
