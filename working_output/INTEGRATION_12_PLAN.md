# Tích hợp 12: median F0 ba frame vào notebook AMDF

- Điểm quay lại: `093436c`; LOFO training-only của thí nghiệm 12 đạt tiêu chí F0 nhưng một số file riêng lẻ xấu đi.
- Giả thuyết: thêm đúng bộ lọc median3 đã kiểm tra vào `process_file_amdf` sẽ giảm MAE F0 trung bình trên bốn file training mà giữ nguyên dự đoán V/UV/SIL và NumF0.
- Thay đổi duy nhất: hậu xử lý F0 tại frame nội bộ của mỗi run predicted-voiced dài ≥3; không lọc qua biên run, không đổi threshold, score, frame, hop hoặc decision mask.
- Điểm so sánh trước: `BT2_AMDF_implement_executed_original - Copy.ipynb` tại commit `093436c`. Lưu metrics baseline training trước khi sửa.
- QA sau sửa: thực thi các cell định nghĩa/training (không chạy cell đánh giá TEST), chỉ dùng `TinHieuHuanLuyen`. Xác nhận per-frame predicted mask, TP/TN/FP/FN, macro F1, BA, recall, NumF0 và FP_SIL không đổi; xác nhận MAE sau sửa bằng bản raw estimator trên đúng bốn file và MAE trung bình giảm. Lưu lệnh/môi trường/số liệu trước–sau.
- Không dùng TEST để quyết định tích hợp; các metric TEST từng xem trước đây không được gọi độc lập.
