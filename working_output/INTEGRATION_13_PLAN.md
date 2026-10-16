# Tích hợp 13: median5 F0 vào notebook AMDF

- Điểm quay lại notebook median3: `f2c32d7`; đã lưu QA baseline ở `integration_12_training_after.csv/json`.
- Bằng chứng quyết định: thí nghiệm 13 LOFO training-only đạt cổng đăng ký trước; xem `EXPERIMENT_13_RESULT.md`. Chỉ tích hợp sau kết quả này.
- Giả thuyết: thay median3 bằng median5 trong helper nội bộ run voiced sẽ tái hiện cải thiện F0 khi chạy notebook trên training và giữ nguyên mọi dự đoán V/UV/SIL.
- Thay đổi duy nhất: helper chỉ cập nhật F0 tại vị trí nội bộ cách hai đầu mỗi run predicted-voiced ≥5 frame; giữ nguyên contour raw, mask voiced, threshold, frame/hop, estimator và phần đánh giá.
- QA: chạy cell cấu hình và hàm xử lý trên bốn file training, giới hạn frame 25 ms, không enumerate hoặc chạy cell TEST. So với baseline median3 đã lưu: hash mask, TP/TN/FP/FN, macro F1, BA, recall, NumF0 và FP_SIL phải khớp; F0mean/F0std MAE trung bình training phải giảm. Nếu QA phân loại thay đổi hoặc F0 không đạt, khôi phục notebook từ điểm quay lại và ghi rõ kết quả.
- Kết quả in-sample chỉ kiểm tra tích hợp, không thay thế LOFO và không được gọi là kết quả độc lập.
