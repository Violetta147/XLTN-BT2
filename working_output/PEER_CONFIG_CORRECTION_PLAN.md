# Kế hoạch sửa mô tả frame length trong đối chiếu

- Điểm quay lại: `9c7a744`.
- Phát hiện: `PEER_COMPARISON.md` nói AMDF local cuối dùng 30 ms, nhưng notebook AMDF hiện hành cố định `FINAL_FRAME_MS = 25` và ghi 20/30 ms chỉ để khảo sát.
- Giả thuyết: sửa mô tả theo notebook hiện tại sẽ loại bỏ thông tin cấu hình lỗi thời mà không đổi kết quả thí nghiệm.
- Tiêu chí: phần yêu cầu thầy mô tả AMDF notebook cuối là 25 ms/10 ms và chỉ gọi AMDF 30 ms là cấu hình ban đầu/khảo sát; số liệu khác giữ nguyên.
- Phép xác minh: đối chiếu câu đã sửa với cell 14 của `BT2_AMDF_implement_executed_original - Copy.ipynb`; chỉ commit tài liệu.
