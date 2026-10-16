# Kết quả thí nghiệm 12: median F0 ba frame cho AMDF+energy

- Điểm quay lại: `5d7b9f3`; giả thuyết/tiêu chí được đăng ký trước ở `8a22077`.
- Lệnh tái lập: `.venv\Scripts\python.exe working_output\experiment_12_median_f0.py`.
- Dữ liệu và validation: bốn file `TinHieuHuanLuyen`, bốn fold LOFO; dùng đúng pitch/energy threshold lưu trong thí nghiệm 08. Không dùng TEST.
- Bộ lọc F0 giống hệt thí nghiệm 05: median 3 frame chỉ thay F0 ở frame nội bộ của các run voiced dài ít nhất ba frame. Hai đầu run và run ngắn giữ nguyên.

| File | F0mean MAE raw → median3 (Hz) | F0std MAE raw → median3 (Hz) | NumF0 |
|---|---:|---:|---:|
| phone_F1.wav | 6.373 → 2.430 | 14.905 → 7.552 | 143 |
| phone_M1.wav | 1.183 → 1.827 | 5.169 → 4.753 | 209 |
| studio_F1.wav | 1.595 → 1.521 | 4.394 → 4.524 | 115 |
| studio_M1.wav | 2.563 → 2.686 | 1.541 → 1.609 | 78 |
| **Trung bình file** | **2.929 → 2.116** | **6.502 → 4.609** | **545** |

Tiêu chí đã đặt trước **đạt**: F0mean MAE giảm 0.812 Hz, F0std MAE giảm 1.893 Hz; cả hai metric đều giảm theo trung bình file. Phân loại không đổi: macro F1 0.8646, BA 0.9206, recall V/UV 0.8763/0.9649, FP trên SIL 1; NumF0 545.

Đánh đổi theo file: phần lớn cải thiện đến từ `phone_F1`; F0mean MAE tăng ở `phone_M1` và `studio_M1`, F0std MAE tăng nhẹ ở hai file studio. Vì vậy kết luận chỉ là cải thiện trung bình training LOFO trên bốn file, không khẳng định tốt hơn cho từng file hay là đánh giá TEST độc lập. Chi tiết metric/script: [CSV](experiment_12_lofo.csv), [JSON](experiment_12_summary.json), [mã](experiment_12_median_f0.py).
