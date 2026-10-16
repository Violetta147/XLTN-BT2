# Tích hợp 13: median5 F0 trong notebook AMDF

- Điểm quay lại: `f2c32d7` (notebook median3) và baseline QA `integration_12_training_after.csv/json`; kế hoạch đăng ký trước ở `3908f16`.
- Thay đổi: helper hậu xử lý dùng median5 trong phần nội bộ của run predicted-voiced dài ≥5 frame, giữ hai frame đầu/cuối và run ngắn. Giữ nguyên contour raw, V/UV mask, ngưỡng, AMDF, frame 25 ms/hop 10 ms và các metric.
- Lệnh QA: `.venv\Scripts\python.exe working_output\integration_13_training_qa.py`.
- QA chỉ dùng bốn file training; giới hạn frame 25 ms và thay TEST_DIR bằng thư mục placeholder trước khi ghép cặp dữ liệu. Không chạy cell đánh giá TEST hay đọc WAV/LAB TEST.

| Chỉ số trên bốn file training (fit đầy đủ) | median3 trước | median5 sau |
|---|---:|---:|
| F0mean MAE trung bình file (Hz) | 2.234 | 1.850 |
| F0std MAE trung bình file (Hz) | 3.510 | 2.740 |
| Macro F1 trung bình | 0.8697 | 0.8697 |
| Balanced accuracy trung bình | 0.9232 | 0.9232 |
| Recall V / UV trung bình | 0.8814 / 0.9649 | 0.8814 / 0.9649 |
| NumF0 tổng | 548 | 548 |
| False voiced trên SIL | 0 | 0 |

Hash mask dự đoán và TP/TN/FP/FN khớp từng file với baseline median3; vì vậy phân loại không đổi. MAE cải thiện là QA in-sample để kiểm tra tích hợp; bằng chứng chọn median5 vẫn là LOFO training-only ở [thí nghiệm 13](EXPERIMENT_13_RESULT.md), không phải đánh giá độc lập. Kết quả máy và script: [CSV](integration_13_training_after.csv), [JSON](integration_13_training_after.json), [QA](integration_13_training_qa.py).
