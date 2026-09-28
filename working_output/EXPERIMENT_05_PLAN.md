# Thí nghiệm 05: median ba khung trên F0 đã được chấp nhận

- Điểm quay lại: commit `0783e70`. Thí nghiệm 04 có F1/BA và false voiced SIL tốt nhưng F0mean MAE chưa đạt baseline GMM lõi, nên chưa vào notebook.
- Giả thuyết: F0 ứng viên đơn lẻ bất thường kéo mean/std theo file; median cục bộ ba khung có thể giảm ảnh hưởng mà không đổi quyết định V/UV.
- Một biến thêm so với **cấu hình 04**: sau ngưỡng pitch có nhãn + cổng năng lượng, với mỗi run V dự đoán liên tục dài ≥3, thay F0 của **khung nội bộ** bằng median của F0 trước/nó/sau trong run. Giữ hai đầu run và mọi run ngắn hơn 3; không nối qua khung UV/SIL dự đoán. `NumF0`, nhãn, AMDF score, ngưỡng fit trên ba file training, frame 25 ms và hop 10 ms không đổi. Không dùng LAB trong bộ lọc.
- Đánh giá leave-one-file-out trên bốn file `TinHieuHuanLuyen`, so với GMM lõi và cấu hình 04 ở cùng fold. Báo F0mean/F0std MAE và sai số từng file; xác nhận F1/BA/TP/TN/FP/FN, NumF0, false voiced SIL **giữ nguyên** so với cấu hình 04.
- Chỉ áp dụng chuỗi cấu hình 04+05 vào notebook nếu đồng thời đáp ứng cổng đã đặt ở thí nghiệm 04 so với GMM lõi: macro F1 +≥0.01, BA giảm ≤0.01, FP tăng không quá FN giảm, cả hai F0 MAE không tăng, false voiced SIL không tăng. Nếu không đạt, lưu kết quả thất bại và không đổi notebook/không dùng TEST để dò sửa.
