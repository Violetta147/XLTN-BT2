# Chẩn đoán các khung ngưỡng trễ thêm vào

Từ đúng bốn lượt leave-one-file-out của thí nghiệm 01, lấy các khung `hysteresis=True` và `core=False`; không dùng TEST, không đổi dự đoán. Chạy `.venv\Scripts\python.exe working_output\diagnose_experiment_01.py`. [Chi tiết 121 khung](experiment_01_added_frames.csv), [tóm tắt theo file và nhãn](experiment_01_added_summary.csv).

| Nhãn thật của khung mới | Số khung | Diễn giải trên V/UV |
|---|---:|---|
| V | 74 | Giảm FN 74 |
| UV | 15 | Tăng FP 15 |
| SIL | 32 | Không tính vào F1 V/UV, nhưng làm tăng false voiced trên silence và thay đổi F0mean/F0std |

Trong 32 khung SIL mới, `studio_F1` có 14 và `studio_M1` có 16. Có **16** khung SIL mới với F0 ứng viên cách F0mean LAB của file hơn 2 lần F0std LAB; ở `studio_F1`, F0 ứng viên SIL trải từ khoảng **73.9 đến 387.4 Hz**. Cũng có **9** khung V mới nằm ngoài dải thống kê đó, nên không thể quy toàn bộ biến động F0 cho SIL. Dải ±2 F0std chỉ là chuẩn tham chiếu thống kê của *file*, không phải nhãn F0 đúng cho từng frame; không gọi các khung ngoài dải là lỗi pitch đã được xác nhận.

Giải thích có bằng chứng: quy tắc ngưỡng trễ lấy nguyên block `weak` khi block chạm một khung `core`, nên một đoạn V có thể kéo theo cả biên SIL/UV. F1 V/UV tăng vì cứu 74 V đổi lấy 15 UV; F0mean/F0std xấu đi vì thêm 121 F0 ứng viên, gồm 32 SIL và nhiều giá trị xa vùng thống kê của file. Bước tiếp theo nên đặt điều kiện riêng cho độ tin cậy F0 của những khung *mới* và kiểm tra cả F0 lẫn SIL trong validation training. Chưa sử dụng biểu đồ/bảng TEST để chọn điều kiện đó.
