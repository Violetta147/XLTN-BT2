# Kết quả thí nghiệm 16: ZCR gate cho rescue low-energy

- Điểm quay lại: AMDF+energy+median5 tại `84eba83`; kế hoạch/tiêu chí ở `9d9ec8f`.
- Lệnh: `.venv\Scripts\python.exe working_output\experiment_16_zcr_rescue.py`.
- Phép đo: ZCR đếm tỷ lệ đổi dấu trong từng frame sau khi trừ mean; `T_zcr` fit riêng trên ba file training của mỗi LOFO fold. Chỉ rescue frame low-energy có AMDF score dưới `T_pitch` và ZCR không vượt `T_zcr`. F0 hậu xử lý median5.
- Chỉ dùng bốn file `TinHieuHuanLuyen`; không dùng TEST.

| Chỉ số LOFO | Energy + median5 | ZCR rescue + median5 |
|---|---:|---:|
| Macro F1 trung bình | 0.8646 | 0.8665 |
| Balanced accuracy trung bình | 0.9206 | 0.9174 |
| Recall V trung bình | 0.8763 | 0.8804 |
| Recall UV trung bình | 0.9649 | 0.9545 |
| F0mean MAE trung bình (Hz) | 1.710 | 1.535 |
| F0std MAE trung bình (Hz) | 3.892 | 6.137 |
| NumF0 tổng | 545 | 568 |
| False voiced trên SIL | 1 | 21 |

Tiêu chí đặt trước **không đạt**: recall V chỉ tăng 0.0041, thấp hơn mục tiêu 0.02; F0std MAE tăng 2.245 Hz; false voiced SIL tăng từ 1 lên 21. Macro F1 tăng nhẹ 0.0019, BA giảm nhẹ 0.0032 và F0mean MAE giảm 0.175 Hz, nhưng không bù được các tiêu chí trượt. Chỉ 23 frame được rescue, phần lớn ở hai file studio. Không tích hợp ZCR; notebook giữ nguyên.

Kết quả từng fold: [CSV](experiment_16_lofo.csv), [JSON](experiment_16_summary.json), [script](experiment_16_zcr_rescue.py). Đây là LOFO training-only với bốn file, không phải đánh giá độc lập ngoài tập đó.
