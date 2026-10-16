# Thí nghiệm 13: so sánh median F0 cửa sổ 5 với median3

- Điểm quay lại cấu hình hiện tại: `f2c32d7`; median3 trong notebook giữ nguyên.
- Giả thuyết: median5 bên trong các run predicted-voiced dài ít nhất 5 frame có thể giảm thêm F0std MAE so với median3, nhưng giới hạn thay đổi cửa sổ sẽ tránh làm F0mean MAE xấu đi đáng kể.
- Biến duy nhất: cửa sổ median hậu xử lý đổi từ 3 sang 5 frame; chỉ sửa ba frame nội bộ trở lên cách hai đầu run, dùng giá trị F0 gốc trong cùng run. Mọi threshold, mask V/UV, frame 25 ms, hop 10 ms, F0 estimator và metric giữ nguyên.
- Đánh giá: bốn fold LOFO trên `TinHieuHuanLuyen`, dùng ngưỡng pitch/energy đã lưu từ thí nghiệm 08 cho đúng file held-out. So median5 với median3 theo F0mean/F0std MAE từng file và trung bình file; kiểm tra macro F1, balanced accuracy, recall V/UV, NumF0 và FP_SIL không đổi. Không đọc hoặc dùng TEST.
- Tiêu chí giữ median5: F0std MAE trung bình giảm ít nhất 0.25 Hz, F0mean MAE trung bình tăng không quá 0.10 Hz, không file nào tăng F0mean MAE quá 1 Hz; mọi metric phân loại và NumF0 phải bất biến. Nếu trượt bất kỳ điều kiện nào, ghi kết quả và giữ median3.
- Giới hạn: bốn file training ít; kết quả chỉ dùng để quyết định ứng viên hậu xử lý trên training LOFO, không phải xác nhận độc lập.
