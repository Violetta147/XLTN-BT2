# Kế hoạch chẩn đoán frame bị cổng năng lượng loại

- Điểm quay lại: `e8b181b`.
- Giả thuyết: trong bốn fold LOFO training, phần lớn các frame AMDF Gaussian bị cổng năng lượng loại là frame SIL; nhóm frame V bị loại là phần đánh đổi tạo ra giảm F1 và NumF0.
- Phép đo: tái tạo dự đoán pitch-only và pitch+energy theo đúng ngưỡng từng fold trong `experiment_08_lofo.csv`; đếm frame bị loại theo LAB V/UV/SIL, file, và phân bố relative RMS. Không fit ngưỡng, không dùng TEST.
- Tiêu chí: tổng frame bị loại phân loại theo LAB khớp số chênh dự đoán voiced/NumF0 giữa hai cấu hình; báo riêng số LAB V bị loại và SIL bị loại. Đây là chẩn đoán, không thay đổi cấu hình.
- Kết quả lưu CSV/JSON/script và cập nhật STATUS bằng một commit riêng; nếu phép tái tạo không khớp số liệu đã lưu thì dừng và báo lỗi.
