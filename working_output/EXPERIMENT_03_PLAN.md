# Thí nghiệm 03: ngưỡng AMDF 25 ms học từ nhãn training

- Điểm quay lại: commit `f2d2d29`. Hai thử nghiệm làm mượt quyết định trước đó không được đưa vào notebook.
- Giả thuyết: hai thành phần GMM không nhãn không tương ứng đúng V/UV; ngưỡng học từ nhãn V/UV của training có thể giảm FN và tăng macro F1 trên file chưa dùng để chọn ngưỡng.
- **Một biến**: thay ngưỡng giao hai Gaussian GMM bằng một ngưỡng `score < T_label`. Giữ AMDF 25 ms, hop 10 ms, score, nhãn tâm khung, F0 estimator, không hậu xử lý chuỗi.
- Trong mỗi lượt leave-one-file-out của bốn file `TinHieuHuanLuyen`, tìm `T_label` chỉ trên ba file còn lại. Ứng viên là điểm giữa hai score V/UV kề nhau sau sắp xếp, thêm hai ngưỡng biên. Chọn ngưỡng tối đa hóa **trung bình theo ba file** của macro F1 V/UV; hòa điểm theo balanced accuracy trung bình cao hơn, FP tổng thấp hơn, rồi ngưỡng nhỏ hơn. Không dùng file holdout hoặc TEST để chọn.
- So sánh `T_label` với GMM `T_core` fit trên chính ba file đó; đánh giá trên file holdout gồm V/UV và SIL. Báo macro F1, BA, TP/TN/FP/FN, NumF0, F0mean/F0std MAE, false voiced SIL theo file.
- Tiêu chí cải thiện phân loại: trung bình macro F1 validation tăng ≥0.01; BA giảm không quá 0.01; FP tăng không quá FN giảm. **Chỉ áp dụng vào notebook như cấu hình cuối** nếu thêm hai điều kiện: F0mean và F0std MAE trung bình đều không cao hơn baseline, false voiced SIL tổng không tăng. Không dùng giới hạn MinNumF0/MaxNumF0 vì đề chưa cho giá trị/cách tính.
- Nếu chỉ đạt phân loại, báo rõ đánh đổi F0 và giữ nguyên notebook. Nếu đạt toàn bộ, fit lại trên cả bốn file training với cùng quy tắc và đóng băng trước khi xem TEST. Những số TEST đã xem trước đây không được dùng để chọn ngưỡng hay tuyên bố đánh giá độc lập.
