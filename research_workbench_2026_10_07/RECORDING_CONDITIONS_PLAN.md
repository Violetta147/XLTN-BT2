# Phân tích điều kiện thu — phạm vi chốt trước phép đo

Ngày 07/10/2026, người dùng yêu cầu tiếp tục phân tích giả thuyết hai điều kiện thu phone/studio. Điểm quay lại: commit `08f94aa3192229d08a9277dc5c9f8ea47153a15e`.

Đây là phân tích mô tả tín hiệu và kết quả đã lưu, không thay thuật toán F0, không chọn tham số và không chạy H44. Không kiểm chứng quan hệ nhân quả bằng bốn file không có cặp người đọc đã xác minh.

- Chỉ đọc bốn WAV/LAB **train**. Không đọc WAV/LAB test, không fit hoặc inference F0.
- Đo trên tín hiệu native và phiên bản cùng 16 kHz. Studio được resample_poly với tỉ lệ 160/441, window=('kaiser', 5.0), padtype='constant'; phone giữ nguyên. Không ghi bản WAV mới. Bước này có lọc chống alias, không được gọi là cô lập chỉ một biến sample rate.
- Khung 25 ms, bước 10 ms, chỉ giữ khung hoàn toàn nằm trong một đoạn V/UV/SIL và cách biên đoạn ít nhất 20 ms. Đo RMS raw, tỷ lệ mẫu bằng 0; phổ từ khung trừ mean × Hann đối xứng, rFFT nfft=4096, bốn dải [0,70), [70,1000), [1000,4000), [4000,8000] Hz. Khi native fs=44.1 kHz chỉ chuẩn hóa phổ trong 0–8 kHz; bỏ phần trên 8 kHz để so chung băng thông. Đo centroid trong cùng băng. Không gọi tỷ lệ V/SIL là SNR có tín hiệu sạch chuẩn.
- Gộp năng lượng theo số khung, giữ số khung và trường không xác định nếu thiếu đoạn/năng lượng. Đây không phải grid F0num của đề: việc loại biên chỉ phục vụ mô tả âm thanh.
- Tổng hợp Average MAPE train đã nộp từ ảnh người dùng, H20 clean accepted/H18/H19, H31 fixed0.30, H41/H43 candidate nested đã lưu. Không tìm cấu hình tốt nhất theo phone/studio. Các protocol khác nhau được ghi riêng; không lấy bảng này làm kiểm định thắng/thua giữa thuật toán.
- Lưu script, CSV theo file/nhãn và khung, receipt hash đầu vào/đầu ra, phiên bản runtime, báo cáo tiếng Việt. Kiểm tra công thức năng lượng, bảo toàn WAV/LAB và phạm vi file trước commit/push.

Câu hỏi: khác biệt năng lượng nền và phổ còn thấy sau phép chuẩn hóa rate/băng thông này không? Mức khó phone/studio có cố định giữa các pipeline đã lưu không? Không suy từ tên nhóm thành thông tin microphone, phòng thu, compression hoặc speaker ID đã xác minh. Transcript studio và nhận xét bốn giọng do người dùng cung cấp, chưa có xác nhận tương ứng cho phone.
