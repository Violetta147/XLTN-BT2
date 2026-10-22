# Kế hoạch thí nghiệm 21: scale năng lượng cố định fit từ training

- Điểm quay lại chấp nhận: commit `b490883` (mã thuật toán AMDF+energy+median5 không đổi sau snapshot này); baseline metric cùng protocol là outer LOFO ở `experiment_14_outer_lofo.csv`.
- Lý do: hiện relative RMS của file held-out chia cho p95 RMS tính từ toàn recording; điều này hợp lệ cho offline nhưng cần toàn file. Kiểm tra một thay đổi nhỏ xem có thể dùng gate với scale cố định chỉ fit trên training, thuận tiện hơn cho suy luận streaming.
- Giả thuyết: thay cách chuẩn hóa RMS từ p95 từng file sang một p95 gộp fit từ ba file training mỗi fold vẫn giữ được chất lượng gần baseline AMDF+energy+median5.
- Chỉ thay đổi: công thức scale RMS. Giữ frame 25 ms/hop 10 ms, AMDF score, Gaussian pitch threshold, cách fit energy threshold theo nhãn training, prediction gate và median5.
- Phép đo: 4-fold LOFO trên `TinHieuHuanLuyen`; mỗi fold lấy p95 RMS gộp của ba file train làm scale, fit energy threshold chỉ từ ba file đó, áp dụng cho file held-out. Không đọc TEST.
- Cổng giữ ứng viên: macro F1 và BA trung bình mỗi loại không thấp hơn baseline quá 0.01; recall V không thấp hơn quá 0.02; F0mean và F0std MAE trung bình không tăng quá 0.25 Hz so với median5; tổng FP voiced trên SIL không quá 3. Luôn báo NumF0; chưa đặt cổng Min/Max vì đề không định nghĩa.
- Nếu trượt một cổng, giữ baseline và chỉ lưu kết quả, không tích hợp. Đây chỉ là training-only LOFO trên bốn file, không xác nhận hiệu năng streaming thực tế.
