# Kết quả thí nghiệm 01: ngưỡng trễ AMDF 25 ms

Chạy bằng `.venv\Scripts\python.exe experiment_01_hysteresis.py` (scikit-learn 1.9.1), dữ liệu **chỉ** `TinHieuHuanLuyen`, leave-one-file-out bốn lượt, frame 25 ms/hop 10 ms. Quy tắc và tiêu chí đã ghi trước ở [EXPERIMENT_01_PLAN.md](EXPERIMENT_01_PLAN.md); kết quả từng file tại [CSV](experiment_01_lofo.csv), tóm tắt máy đọc được tại [JSON](experiment_01_summary.json). Điểm quay lại thuật toán: `6b332a0`.

| Chỉ số trung bình theo file, trừ số đếm cộng bốn file | GMM một ngưỡng | GMM ngưỡng trễ | Chênh lệch |
|---|---:|---:|---:|
| Macro F1 V/UV | 0.8051 | 0.8862 | +0.0811 |
| Balanced accuracy | 0.8836 | 0.9024 | +0.0188 |
| TP / TN / FP / FN | 490 / 175 / 5 / 124 | 564 / 160 / 20 / 50 | +74 TP, +15 FP |
| F0mean MAE, Hz | 2.0851 | 4.9212 | +2.8361 (xấu hơn) |
| F0std MAE, Hz | 8.4196 | 16.1926 | +7.7730 (xấu hơn) |
| NumF0, tổng | 520 | 641 | +121 |
| V sai trên SIL, tổng | 25 | 57 | +32 |

Ngưỡng lõi qua bốn fold: 0.3413–0.3508; ngưỡng duy trì: 0.4557–0.4739. Cả ba điều kiện giữ đặt trước đều đạt: F1 +0.0811 ≥ 0.01; balanced accuracy +0.0188 ≥ −0.01; FP tăng 15 ≤ FN giảm 74. Điều này **chỉ** xác nhận tiêu chí V/UV đã đăng ký, không xác nhận cải thiện toàn bài. Sai số F0 và false voiced trên SIL tăng đáng kể; giữ script và số liệu để đối chiếu nhưng chưa đưa ngưỡng trễ vào notebook/cấu hình nộp.

Không thay đổi tiêu chí sau khi xem kết quả. Thí nghiệm kế tiếp, nếu làm, phải đặt trước ràng buộc riêng cho F0 và SIL, rồi kiểm tra bằng validation training. Những số TEST đã xem trước đây được coi là dữ liệu tham khảo, không dùng để chỉnh quy tắc.
