# Kết quả audit 20: parity nhãn LAB trong LOFO

- Điểm quay lại: `54779df`; kế hoạch commit trước khi đo: `d059d44`.
- Lệnh tái lập: `.venv\\Scripts\\python.exe working_output\\audit_lofo_label_parity.py`.
- Chỉ dùng bốn WAV/LAB training, 25 ms / hop 10 ms; không đọc TEST, không sửa thuật toán.
- Python 3.11.9, NumPy 2.3.5.

| So sánh | Số frame | Nhãn khác |
|---|---:|---:|
| Parser/lookup notebook ACF so với parser LOFO | 1,291 | 0 |
| Parser/lookup notebook AMDF so với parser LOFO | 1,291 | 0 |

Giả thuyết đạt: cả hai notebook và LOFO gán nhãn giống hệt nhau tại mọi tâm frame training. Kết quả xác nhận parity nhãn cho các phép đo LOFO, không phải hiệu năng mô hình. [JSON](lofo_label_parity.json) và [script](audit_lofo_label_parity.py) lưu dữ liệu tái lập.
