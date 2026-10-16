# Kết quả thí nghiệm 14: nested LOFO chọn cửa sổ median F0

- Điểm quay lại: median3 tại `f2c32d7`; kế hoạch đăng ký trước ở `f47963b`.
- Lệnh: `.venv\Scripts\python.exe working_output\experiment_14_nested_median_f0.py`.
- Dữ liệu: chỉ bốn file `TinHieuHuanLuyen`. Outer LOFO giữ một file để đánh giá; trong ba file còn lại, inner LOFO fit lại ngưỡng Gaussian pitch và energy trên hai file rồi chọn median3/median5. Outer threshold được fit lại trên ba file training.
- Không truy cập WAV/LAB TEST. Cách chuẩn hóa RMS theo percentile của toàn recording vẫn mô phỏng suy luận offline, như đã nêu trong [audit protocol](VALIDATION_PROTOCOL_AUDIT_RESULT.md).

| Outer held-out | Cửa sổ được chọn bằng inner LOFO | F0mean MAE median3 → chiến lược nested (Hz) | F0std MAE median3 → chiến lược nested (Hz) | NumF0 |
|---|---:|---:|---:|---:|
| phone_F1.wav | 5 | 2.430 → 0.815 | 7.552 → 4.926 | 143 |
| phone_M1.wav | 5 | 1.827 → 1.815 | 4.753 → 4.456 | 209 |
| studio_F1.wav | 5 | 1.521 → 1.556 | 4.524 → 4.587 | 115 |
| studio_M1.wav | 5 | 2.686 → 2.654 | 1.609 → 1.601 | 78 |
| **Trung bình file** | **median5 ở 4/4 fold** | **2.116 → 1.710** | **4.609 → 3.892** | **545** |

Tiêu chí đặt trước **đạt**: inner procedure chọn median5 ở 4/4 outer folds; cả hai outer MAE trung bình đều thấp hơn median3 cố định. Mask phân loại không đổi: macro F1 0.8646, BA 0.9206, recall V/UV 0.8763/0.9649, FP_SIL 1, NumF0 545.

Kết quả hỗ trợ giữ median5 trong notebook; nó không phải đánh giá độc lập ngoài bốn file training và không giải quyết giới hạn MinNumF0/MaxNumF0 còn thiếu. Tệp chi tiết: [outer CSV](experiment_14_outer_lofo.csv), [inner CSV](experiment_14_inner_lofo.csv), [JSON](experiment_14_summary.json), [script](experiment_14_nested_median_f0.py).
