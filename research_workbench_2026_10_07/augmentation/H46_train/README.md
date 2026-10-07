# Dữ liệu train được biến đổi trong H46

12 WAV sinh từ bốn file train gốc: mỗi file có nhiễu trắng 30 dB, nhiễu trắng 20 dB và nhiễu hồng 20 dB. Giữ tần số lấy mẫu, số mẫu và thời lượng; tránh clipping bằng gain chung cho tín hiệu và nhiễu nếu cần. Đây là dữ liệu tổng hợp của thí nghiệm, không phải bản phát hành mới từ giảng viên.

Không có thêm speaker hoặc transcript. Mỗi WAV phải đi cùng `origin_file` trong [manifest](../../results/H46_augmentation_manifest.json); mọi biến thể của cùng origin nằm trong cùng nhóm khi chia fit/held. Không chia ngẫu nhiên 12 WAV thành các nhóm độc lập.

Không tạo LAB mới. Nhãn đoạn và thống kê 3GT được tham chiếu tới file gốc qua manifest, với giả định chúng là mục tiêu của thành phần tiếng nói ban đầu dưới nhiễu. Những nhãn kế thừa này chưa được kiểm chứng trên bản trộn bằng F0 chuẩn từng khung.

Đọc [kết quả so sánh](../../AUGMENTATION_RESULT.md). Phép thử augmentation H46 chưa giảm lỗi trên bốn WAV gốc giữ riêng; không thay dữ liệu gốc bằng các WAV này trong bài nộp.
