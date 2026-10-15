# Kết quả audit quy trình validation LOFO thí nghiệm 08

- Điểm quay lại: `8f056e9`; câu hỏi và tiêu chí được ghi trước ở commit `935c12f`.
- Phạm vi: rà luồng gọi hàm của ba script LOFO/energy gate; không truy cập TEST và không chạy lại mô hình.

## Rò rỉ nhãn

Không thấy rò rỉ nhãn từ file holdout vào việc chọn threshold:

- Trong `experiment_08_amdf_energy.py`, mỗi fold tạo `other` bằng cách bỏ object `held` khỏi danh sách bốn file, rồi chỉ truyền `other` vào `fit_selector` và `fit_energy_threshold`.
- `fit_selector` lấy các score V/UV và LAB từ đối số `training_files`; `fit_energy_threshold` lấy relative RMS theo nhãn V/SIL từ đối số `files`. Vì hai fitter chỉ nhận `other`, LAB của holdout không tham gia chọn threshold.
- Threshold và `relative_rms` của `held` chỉ được kết hợp để tạo dự đoán; sau đó LAB holdout mới được dùng để tính metric. Đây là trình tự validation phù hợp.

Mã tham chiếu: `experiment_08_amdf_energy.py` dòng 28–42; `experiment_07_acf_amdf_25ms.py` dòng 73–105; `experiment_04_energy_gate.py` dòng 13–44.

## Giả định triển khai

`load_with_energy` tính RMS của tất cả frame trong file hiện tại rồi chia cho phân vị 95% RMS của chính file đó. Trên holdout, đây là thích nghi **không giám sát** theo phân phối năng lượng của toàn recording: không đọc LAB, nhưng cần có sẵn toàn bộ recording để tính phân vị. Vì vậy kết quả LOFO đại diện cho cách xử lý offline từng file hoàn chỉnh; nó chưa chứng minh cùng hiệu năng cho xử lý streaming/online hoặc hệ thống không thể xem trước toàn file.

Mã tham chiếu: `experiment_04_energy_gate.py` dòng 13–20. Chưa có chỉ dấu đây là lỗi validation; đây là điều kiện sử dụng cần ghi trong mô tả cấu hình. Không đổi thuật toán hoặc kết luận metric.
