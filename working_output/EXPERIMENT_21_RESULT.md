# Kết quả thí nghiệm 21: scale RMS cố định từ training

- Điểm quay lại: `b490883`; kế hoạch đặt trước: `d0692b4`.
- Lệnh tái lập: `.venv\\Scripts\\python.exe experiment_21_fixed_rms_scale.py`.
- Chỉ dùng 4 WAV trong `TinHieuHuanLuyen`, 25 ms / 10 ms, 4-fold LOFO. Scale p95 RMS gộp và T_energy đều fit trên đúng ba file train của fold. Không đọc TEST.
- Python 3.11.9, NumPy 2.3.5, pandas 3.0.3, SciPy 1.17.1.

| Chỉ số LOFO, trung bình đều theo file (trừ NumF0/FP_SIL là tổng) | p95 từng file (median5) | p95 gộp training (median5) | Thay đổi |
|---|---:|---:|---:|
| Macro F1 V/UV | 0.8646 | 0.8572 | -0.0074 |
| Balanced accuracy | 0.9206 | 0.9242 | +0.0036 |
| Recall V | 0.8763 | 0.8593 | -0.0170 |
| Recall UV | 0.9649 | 0.9891 | +0.0242 |
| F0mean MAE (Hz) | 1.7099 | 1.6989 | -0.0110 |
| F0std MAE (Hz) | 3.8924 | 3.9464 | +0.0539 |
| NumF0 | 545 | 525 | -20 |
| False voiced SIL | 1 | 1 | 0 |

**Đạt cổng giữ ứng viên đã đặt trước**: F1/BA nằm trong biên 0.01; recall V giảm 0.017, trong giới hạn 0.02; F0std tăng 0.054 Hz, trong giới hạn 0.25; F0mean giảm nhẹ và FP SIL không tăng. Tuy vậy đây là đánh đổi, không phải cải thiện toàn diện: macro F1, recall V và NumF0 thấp hơn, còn BA/recall UV cao hơn. Cấu hình fixed scale là lựa chọn offline/streaming-friendly để cân nhắc, nhưng chưa tích hợp vì streaming không phải yêu cầu đã xác nhận và không có ưu thế chất lượng rõ ràng. Baseline notebook giữ nguyên.

Kết quả chỉ là LOFO trên bốn file training; không xác nhận hiệu năng streaming thực tế. Điều kiện MinNumF0/MaxNumF0 vẫn không thể kết luận do thiếu định nghĩa. CSV và JSON theo từng fold tại [CSV](experiment_21_lofo.csv), [JSON](experiment_21_summary.json); mã tại [script](../experiment_21_fixed_rms_scale.py).
