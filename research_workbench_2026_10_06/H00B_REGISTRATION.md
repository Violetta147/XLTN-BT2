# H00b — khả năng xác định F0 từ metric và count protocol

Đăng ký trước chạy. Rollback/champion vẫn 009fd2c, audit hiện d7fa32a. Không đổi thuật toán, dữ liệu, nhãn hoặc metric chính.

Giả thuyết chẩn đoán: mean/std/count không xác định thứ tự F0 theo thời gian; count theo nhãn V center có thể khác count3GT do protocol tham chiếu chưa rõ.

Phép kiểm tra: dùng dãy synthetic và đảo thứ tự, xác minh ba thống kê bằng nhau nhưng frame error có thể khác; tính count MAPE nếu mọi khung V center được phát hiện và đều có F0 hữu hạn. Đây là giá trị có điều kiện, không phải lower bound cho tất cả model hoặc ground-truth F0 thật của WAV.

Không điều chỉnh GT, không coi lệch count là nhãn sai, không tune offset/frame length để ép match3GT. Tìm provenance trước khi sửa protocol. Export CSV/PNG/SVG/Markdown, assertions chính xác và log lệnh.
