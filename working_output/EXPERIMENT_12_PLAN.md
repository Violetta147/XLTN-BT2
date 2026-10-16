# Thí nghiệm 12: median F0 ba frame trong run voiced của AMDF+energy

- Điểm quay lại: `5d7b9f3`; giữ nguyên cấu hình dự đoán và notebook.
- Giả thuyết: median cửa sổ 3 frame trong các run voiced dài ít nhất 3 frame, đúng cách đã đăng ký ở thí nghiệm 05, sẽ giảm ít nhất một trong hai F0 MAE trên cấu hình AMDF+energy mà không làm metric còn lại xấu đi đáng kể.
- Biến duy nhất: làm mượt giá trị F0 ở các frame nội bộ của run dự đoán voiced; không thay quyết định V/UV, threshold, frame/hop hoặc estimator. Run <3 frame và hai đầu mỗi run giữ nguyên.
- Đánh giá: bốn fold LOFO training, cùng threshold và dự đoán của thí nghiệm 08; so theo từng file và trung bình F0mean/F0std MAE, xác nhận macro F1, BA, recall, NumF0 và FP_SIL không đổi. Không dùng TEST.
- Tiêu chí đo có ý nghĩa: giữ ứng viên nếu cả hai F0 MAE không tăng và ít nhất một giảm ≥0.25 Hz. Nếu không đạt, ghi kết quả rồi giữ F0 estimator hiện tại.
