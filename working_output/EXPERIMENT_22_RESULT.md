# Kết quả thí nghiệm 22: ngưỡng energy ưu tiên Recall V dưới giới hạn FP SIL

- Kế hoạch đăng ký trước: [EXPERIMENT_22_PLAN.md](EXPERIMENT_22_PLAN.md). Điểm baseline/rollback: `942499810070c27c71ed338592ff2015b56faa2d`.
- Chỉ dữ liệu `TinHieuHuanLuyen`, bốn fold outer LOFO, frame 25 ms / hop 10 ms. Không đọc hay dùng TEST.
- Lệnh: `.venv\Scripts\python.exe working_output\experiment_22_energy_threshold_recall.py`.
- Môi trường: Python 3.11.9, NumPy 2.3.5, pandas 3.0.3, scikit-learn 1.9.1.
- Candidate chỉ đổi objective fit `T_energy`: tối đa hóa Recall V trung bình theo file trên 3 file training, với tối đa 1 FP voiced SIL tổng trên tập training; tie-break theo ít FP SIL hơn rồi ngưỡng cao hơn. Pitch threshold Gaussian, gate AND, smoothing median5 và mọi bước khác giữ nguyên.

## Kết quả trung bình trên bốn file holdout

| Metric | Baseline AMDF + energy + median5 | Candidate | Thay đổi |
|---|---:|---:|---:|
| Macro F1 V/UV | 0.8646 | 0.8588 | -0.0059 |
| Balanced accuracy | 0.9206 | 0.9165 | -0.0041 |
| Recall V | 0.8763 | 0.8681 | -0.0082 |
| Recall UV | 0.9649 | 0.9649 | 0.0000 |
| F0mean MAE | 1.7099 Hz | 2.1382 Hz | +0.4283 Hz |
| F0std MAE | 3.8924 Hz | 3.4193 Hz | -0.4731 Hz |
| NumF0 | 545 | 539 | -6 |
| FP voiced trên SIL | 1 | 0 | -1 |

## Theo fold

| File holdout | T_energy baseline → candidate | Recall V baseline → candidate | Macro F1 baseline → candidate | FP SIL baseline → candidate |
|---|---:|---:|---:|---:|
| phone_F1.wav | 0.054661 → 0.089755 | 0.9085 → 0.8758 | 0.9141 → 0.8906 | 1 → 0 |
| phone_M1.wav | 0.057730 → 0.074999 | 0.8320 → 0.8320 | 0.8003 → 0.8003 | 0 → 0 |
| studio_F1.wav | 0.066837 → 0.066837 | 0.9350 → 0.9350 | 0.9118 → 0.9118 | 0 → 0 |
| studio_M1.wav | 0.061545 → 0.086123 | 0.8298 → 0.8298 | 0.8323 → 0.8323 | 0 → 0 |

Baseline parity check passed on all four folds before candidate scores were compared.

## Kết luận

Candidate giảm được một lỗi voiced trên SIL, nhưng không phục hồi Recall V: trung bình giảm 0.0082, macro F1 giảm 0.0059 và F0mean MAE tăng 0.4283 Hz. Candidate trượt các cổng đặt trước về macro F1, Recall V và F0mean MAE. Không giữ ứng viên, không đổi notebook; baseline EXP14/median5 vẫn là cấu hình hiện tại. Đây là kết quả validation nội bộ trên bốn file training, không phải đánh giá độc lập hoặc bảo đảm tổng quát hóa.

Tệp tái lập: [script](experiment_22_energy_threshold_recall.py), [CSV từng fold](experiment_22_lofo.csv), [JSON tổng hợp](experiment_22_summary.json).
