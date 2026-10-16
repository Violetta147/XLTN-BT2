# Kết quả thí nghiệm 15: rescue frame AMDF dưới ngưỡng năng lượng

- Điểm quay lại: AMDF+energy+median5 tại `3a883c2`; giả thuyết và tiêu chí đăng ký ở `274d3de`.
- Lệnh: `.venv\Scripts\python.exe working_output\experiment_15_low_energy_rescue.py`.
- Dữ liệu/validation: bốn file training, leave-one-file-out; mỗi fold chỉ dùng ba file training để fit Gaussian pitch threshold, energy threshold và rescue threshold. Rescue threshold tối đa hóa balanced accuracy V-vs-(UV/SIL) trên các frame thấp năng lượng, đủ điều kiện pitch. TEST không được đọc hoặc dùng.

| Chỉ số LOFO | Energy + median5 | Energy + rescue + median5 |
|---|---:|---:|
| Macro F1 trung bình | 0.8646 | 0.8604 |
| Balanced accuracy trung bình | 0.9206 | 0.9074 |
| Recall V trung bình | 0.8763 | 0.8804 |
| Recall UV trung bình | 0.9649 | 0.9345 |
| F0mean MAE trung bình (Hz) | 1.710 | 1.379 |
| F0std MAE trung bình (Hz) | 3.892 | 6.305 |
| NumF0 tổng | 545 | 576 |
| False voiced trên SIL | 1 | 27 |

Tiêu chí đặt trước **không đạt**: recall V chỉ tăng 0.0041, thấp hơn yêu cầu 0.02; macro F1 giảm 0.0042; BA giảm 0.0132; F0std MAE tăng 2.412 Hz; false voiced SIL tăng 1→27 (giới hạn 3). F0mean MAE giảm 0.331 Hz nhưng không bù được các suy giảm kia. Không tích hợp rescue; giữ energy gate và median5 hiện tại.

Theo file, rescue thêm 1 frame ở `phone_M1`, 22 ở `studio_F1` và 8 ở `studio_M1`; nhiều frame không phải V, làm tăng SIL false positives và giảm recall UV. Kết quả chi tiết và mã: [CSV](experiment_15_lofo.csv), [JSON](experiment_15_summary.json), [script](experiment_15_low_energy_rescue.py). Đây là LOFO training-only trên bốn file, không phải đánh giá độc lập ngoài tập đó.
