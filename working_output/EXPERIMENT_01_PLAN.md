# Thí nghiệm 01: ngưỡng trễ trên AMDF 25 ms

- Điểm quay lại: commit `6b332a0` (notebook local gọn, chưa đổi thuật toán).
- Giả thuyết: một số khung V bị GMM bỏ sót có score AMDF lớn hơn ngưỡng lõi nhưng nằm liền vùng V có score thấp. Đây là giả thuyết cần kiểm chứng, chưa phải kết luận về nguyên nhân.
- Biến duy nhất: thêm ngưỡng duy trì vào quyết định V/UV; giữ AMDF 25 ms, hop 10 ms, score, cách fit GMM và nhãn tâm khung.
- Mỗi lượt leave-one-file-out: fit GMM hai thành phần trên score V/UV của 3 file training với cùng cấu hình notebook (`spherical`, `reg_covar=1e-6`, `n_init=10`, `random_state=42`). Ngưỡng lõi `T_core` là giao điểm hai thành phần như notebook. Từ 3 file đó tính `T_weak = max(T_core, mean(score_UV) - std(score_UV))`.
- Trên toàn chuỗi frame của file validation, `core = score < T_core`; `weak = score <= T_weak`. Một frame được dự đoán V nếu thuộc block `weak` liên tục có ít nhất một frame `core`. Không nối block qua ranh giới file. Tính metric trên V/UV; vẫn đưa SIL vào chuỗi quyết định.
- So sánh trực tiếp với dự đoán ngưỡng GMM đơn `score < T_core` ở cùng fold, cùng score/frame. Metric chính là macro F1 V/UV trung bình đều theo 4 file; metric phụ là balanced accuracy trung bình, TP/TN/FP/FN và sai số thống kê F0 theo file.
- Tiêu chí giữ, đặt trước khi chạy: macro F1 tăng ít nhất 0,01 tuyệt đối; balanced accuracy giảm không quá 0,01 tuyệt đối; tổng FP tăng không quá số FN giảm. Nếu không đạt, ghi số liệu rồi quay lại checkpoint để chọn giả thuyết khác. Không xem test để đổi quy tắc.
- Nếu đạt, fit lại quy tắc đã cố định trên đủ 4 file training. Bốn ngưỡng từ LOFO chỉ dùng để ước lượng độ ổn định, không lấy trung bình thay cho fit cuối nếu không có kiểm chứng riêng.
