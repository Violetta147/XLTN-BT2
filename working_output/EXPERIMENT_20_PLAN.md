# Kế hoạch audit 20: parity nhãn LAB trong LOFO

- Điểm quay lại: `54779df` (working tree sạch).
- Giả thuyết: nhãn frame lấy bởi hai notebook (ACF/GMM và AMDF) khớp với nhãn do `validate_saved_results.read_lab` dùng trong thí nghiệm LOFO trên cùng bốn WAV training và tâm frame 25 ms/10 ms.
- Phạm vi: chỉ đọc LAB trong `TinHieuHuanLuyen`; so sánh parser/label lookup của notebook với parser dùng bởi LOFO tại mọi tâm frame. Không đọc TEST, không thay đổi phân loại.
- Tiêu chí: số frame và nhãn từng frame phải khớp tuyệt đối; báo tổng frame, số nhãn khác nhau, file/frame đầu tiên nếu có bất kỳ lệch nào.
- Lưu mã tái lập, JSON, phiên bản môi trường và kết luận. Đây là audit nhãn validation, không phải đánh giá hiệu năng.
