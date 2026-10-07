# H48 — Test một cấu hình chốt từ train

Không phải thuật toán mới. H47 mọi selection dùng H43 hard170 và bốn train đều<2%. Chốt duy nhất hard170 trước test: Praat7.0.02 filtered.30 range70–400; NAMDF dip trong200cents quanh Praat; raw25ms, chuyển40ms chỉ khi phổ Hann40ms từ1000Hz có tỷ lệ≤.05 và gate≥170Hz. Hop10ms, canonical25ms/10ms, std population. Không classifier fit, không augmentation inference, không tham số theo tên file hoặc GT. Nhãn/3GT chỉ dùng scoring sau inference.

Điểm quay lại repository `77cae08e14fa6e29ff33c1d1f6ef40472b8816cb`. Không sửa original/frozen config. Config/source hash phải commit/push và remote verify trước measurement. Đo4test một lần, báo từngmean/std/count MAPE, Hz MAE, F0num và V/UV/SIL; controlPraat cùngcall/times. Kèm4train đã replayH47 để trả lời mục tiêu người dùng **mỗi trong8files Average MAPE<2%**. Không chọn best trên test, không grid test. Test đã được xem trong lịch sử bài/QA nên không gọi là pristine held-out.

Verifier kiểm tra config/code/data/LAB hashes, tái tính dự đoán từ curve evidence, full FFT, projection và thống kê cho8test rows; target strict<2 trên8candidate rows. Không gọi lại native để verification. Giữ failure nếu chưa đạt. Sau phép đo, test findings chỉ là mô tả; không tune trên test rồi gọi test độc lập. Không Jev/deep learning/Drive/PDF hoặc literature review mới.
