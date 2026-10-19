# Kế hoạch audit 17: rò rỉ nhãn vào chọn cấu hình ACF/GMM

- Điểm quay lại: `b490883` (working tree sạch trước audit).
- Giả thuyết: notebook `BT2_implement_finished_v3_executed_original - Copy.ipynb` chọn frame length/threshold bằng metric tính trên chính các frame LAB đã dùng để fit threshold, làm metric training được hiển thị lạc quan; TEST chỉ được dùng sau khi chốt cấu hình.
- Phạm vi: audit tĩnh dataflow của cell đọc đường dẫn, tạo score LAB training, fit threshold, tính metric chọn cấu hình, và áp dụng cấu hình lên TEST. Không chạy TEST, không sửa notebook hay thuật toán.
- Tiêu chí đo: xác định từng bước và tập dữ liệu đầu vào; kết luận “in-sample selection” chỉ nếu cùng frame training tham gia fit threshold lẫn điểm chọn frame/method. Xác định riêng liệu test labels có đi vào chọn cấu hình hay không.
- Kết quả cần ghi: cell/biến liên quan, vai trò chính xác của metric, giới hạn diễn giải, và một đề xuất thay đổi có thể kiểm chứng nếu cần.
