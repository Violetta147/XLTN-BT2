# Kết quả thí nghiệm 13: median5 so với median3 cho F0

- Điểm quay lại: median3 đã tích hợp tại `f2c32d7`; kế hoạch đăng ký trước ở `a053206`.
- Lệnh tái lập: `.venv\Scripts\python.exe working_output\experiment_13_median_f0.py`.
- Dữ liệu và validation: bốn file `TinHieuHuanLuyen`, dùng ngưỡng theo từng fold LOFO đã lưu từ thí nghiệm 08. Không mở hoặc dùng `TinHieuKiemThu`.
- Thay đổi đo: median5 thay giá trị F0 tại frame nội bộ cách ít nhất hai frame từ đầu/cuối mỗi run predicted-voiced dài ≥5; mọi quyết định V/UV/SIL, ngưỡng, estimator và cách chia khung giữ nguyên.

| File | F0mean MAE median3 → median5 (Hz) | F0std MAE median3 → median5 (Hz) | NumF0 |
|---|---:|---:|---:|
| phone_F1.wav | 2.430 → 0.815 | 7.552 → 4.926 | 143 |
| phone_M1.wav | 1.827 → 1.815 | 4.753 → 4.456 | 209 |
| studio_F1.wav | 1.521 → 1.556 | 4.524 → 4.587 | 115 |
| studio_M1.wav | 2.686 → 2.654 | 1.609 → 1.601 | 78 |
| **Trung bình file** | **2.116 → 1.710** | **4.609 → 3.892** | **545** |

Tiêu chí đặt trước **đạt**: F0std MAE giảm **0.717 Hz** (ngưỡng tối thiểu 0.25), F0mean MAE giảm **0.406 Hz**, và mức xấu nhất theo file về F0mean chỉ **0.035 Hz** (giới hạn 1 Hz). Phân loại không đổi; tổng macro F1 trung bình 0.8646, balanced accuracy 0.9206, recall V/UV 0.8763/0.9649, NumF0 545 và FP trên SIL là 1.

Kết luận giới hạn ở bốn file training theo LOFO. median5 là ứng viên để tích hợp vào notebook; số liệu không phải đánh giá TEST độc lập. Tệp chi tiết, kết quả máy và mã: [CSV](experiment_13_lofo.csv), [JSON](experiment_13_summary.json), [script](experiment_13_median_f0.py).
