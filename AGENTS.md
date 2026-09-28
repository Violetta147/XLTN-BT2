# Quy tắc làm việc cho BT2

- Chạy trên máy local, dùng `TinHieuHuanLuyen/` và `TinHieuKiemThu/` trong working folder. Tuyệt đối không truy cập, mount, đọc, ghi, đồng bộ hoặc thao tác với Google Drive/G Drive dưới bất kỳ hình thức nào.
- Không dùng deep learning. Chỉ dùng dữ liệu và thuật toán tín hiệu/học máy cổ điển cần thiết cho bài.
- Mỗi thay đổi có một giả thuyết rõ ràng và một commit riêng. Không gộp thay đổi đường dẫn, thư viện, frame length, đặc trưng, ngưỡng và metric vào cùng một thí nghiệm.
- Trước mỗi thí nghiệm, ghi commit đang được chấp nhận làm điểm quay lại. Nếu kết quả không đạt tiêu chí đã định, giữ số liệu thất bại, quay về điểm đó và thử một giả thuyết khác trong commit mới; có thể hỏi Gemini kèm bằng chứng để tìm hướng mới. Không gộp nhiều hướng thử vào một commit.
- Không dừng công việc để chờ câu trả lời cho thông tin bổ sung. Nếu người dùng vắng mặt, ghi rõ giả định hợp lý, tiếp tục mọi phần độc lập và chỉ hỏi khi thiếu dữ liệu khiến bước cần thiết thực sự không thể thực hiện.
- Trước khi đổi thuật toán, lưu baseline local. Sau mỗi thay đổi, chạy cùng dữ liệu, cùng cách chia khung, cùng metric; ghi số liệu trước/sau và kết luận cải thiện hay suy giảm.
- Chọn tham số bằng training hoặc validation tách theo file training. Không chọn ngưỡng bằng test rồi dùng cùng test như đánh giá độc lập.
- Chỉ xem test sau khi chốt cấu hình của một thí nghiệm; nếu test đã được xem để định hướng thí nghiệm tiếp, ghi rõ giới hạn này trong báo cáo.
- Giữ notebook gốc và output đã lưu để đối chiếu. Các kết quả chạy local phải có đường dẫn, lệnh chạy, phiên bản môi trường, cấu hình và dữ liệu đầu vào đủ để tái lập.
- Báo cáo cả metric chính và đánh đổi: macro F1 V/UV, recall V, recall UV, balanced accuracy, F0mean/F0std MAE và số khung F0 hợp lệ.
