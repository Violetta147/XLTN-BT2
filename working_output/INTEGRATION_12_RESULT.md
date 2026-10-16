# Tích hợp 12: median F0 ba frame trong notebook AMDF

- Điểm quay lại trước khi sửa notebook: `2f48d20`; bảng baseline training được lưu trong commit này.
- Thay đổi: `process_file_amdf` lưu contour F0 raw để đối chiếu và trả contour dùng sau khi median 3 frame ở phần nội bộ run voiced dài ≥3 frame. Hai đầu run giữ nguyên; quyết định voiced, threshold 25 ms/10 ms và cổng energy không đổi. Biểu đồ contour ghi rõ F0 đã qua median3.
- QA: `.venv\Scripts\python.exe working_output\integration_12_training_qa.py --tag after`. Script thực thi các cell cấu hình/training và cell xử lý file, giới hạn frame 25 ms, thay TEST_DIR bằng thư mục không tồn tại trước khi ghép cặp dữ liệu. Chỉ chạy bốn WAV/LAB training; không chạy cell đánh giá TEST.
- Trước sửa: [CSV](integration_12_training_before.csv), [JSON](integration_12_training_before.json). Sau sửa: [CSV](integration_12_training_after.csv), [JSON](integration_12_training_after.json). Môi trường và lệnh nằm trong script QA.

## Kết quả kiểm tra tích hợp trên training

| Chỉ số | Raw F0 | Sau median3 | Chênh lệch |
|---|---:|---:|---:|
| Macro F1 trung bình file | 0.869716 | 0.869716 | 0 |
| Balanced accuracy trung bình file | 0.923173 | 0.923173 | 0 |
| Recall V / UV trung bình file | 0.881409 / 0.964937 | 0.881409 / 0.964937 | 0 |
| F0mean MAE trung bình file (Hz) | 3.0801 | 2.2337 | −0.8465 |
| F0std MAE trung bình file (Hz) | 5.6210 | 3.5096 | −2.1114 |
| NumF0 tổng | 548 | 548 | 0 |
| False voiced trên SIL | 0 | 0 | 0 |

Hash quyết định voiced của từng file giống hệt baseline; các ngưỡng khóa cũng khớp: `T_pitch=0.4124933063`, `T_energy=0.0615446159`. Vì vậy code tích hợp giữ nguyên phân loại và số lượng F0, đồng thời giảm cả hai F0 MAE trên bốn file training khi chạy bằng ngưỡng full-training.

Đây là **kiểm tra tính đúng của tích hợp trên training đã dùng fit ngưỡng**, không phải ước lượng hiệu năng độc lập. Căn cứ validation là thí nghiệm 12 LOFO: hai MAE trung bình giảm nhưng một vài file riêng lẻ xấu đi. TEST không được chạy lại.
