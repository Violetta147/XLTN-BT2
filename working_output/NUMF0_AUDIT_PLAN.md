# Audit NumF0: giới hạn nào suy ra được từ training

- Điểm quay lại: `73f5c7c`. Đây là audit chỉ đọc, không đổi thuật toán, notebook hay ngưỡng.
- Câu hỏi: đề yêu cầu `MinNumF0 < NumF0 < MaxNumF0` nhưng không cho công thức/giá trị hai giới hạn. Giả thuyết cần kiểm tra là NumF0 đếm số frame mà thuật toán xuất F0 hữu hạn; số frame LAB V là một mốc tham chiếu nhưng không bằng NumF0 vì bộ phân loại có thể bỏ sót V hoặc dự đoán V trên UV/SIL.
- Phép đo: trên bốn file `TinHieuHuanLuyen`, frame 25 ms/hop 10 ms, đếm tổng frame theo quy tắc notebook, frame theo LAB V/UV/SIL, và NumF0/TP/FP/FN của AMDF energy gate từ từng fold LOFO đã lưu. Báo cáo theo file và tổng; kiểm tra `NumF0 = TP + FP` chỉ khi toàn bộ frame được gán V/UV/SIL, nếu không chỉ rõ phần chênh.
- Đối chiếu đếm: nếu toàn bộ frame có nhãn V/UV/SIL, phải có `NumF0 = TP + FP + FP_SIL` (FP ở metric V/UV chỉ đếm frame UV bị dự đoán V); nếu có frame không nhãn, phần chênh phải bằng số frame không nhãn bị dự đoán V.
- Tiêu chí kết luận: chỉ khẳng định định nghĩa NumF0 và các quan hệ đếm được xác nhận bởi mã/nhãn. Không tự chọn giá trị Min/Max từ cực trị của bốn file; nếu đề không cho cách đặt giới hạn hoặc số tham chiếu, kết luận yêu cầu vẫn chưa xác định. Không dùng `TinHieuKiemThu`.
