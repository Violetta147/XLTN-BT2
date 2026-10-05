# Thí nghiệm BT2 ngày 05-10-2026

Điểm quay lại: `c9a8cd1`. Sáu notebook đã giao được giữ nguyên. Notebook mới có tên riêng.

## Dữ liệu và giới hạn

- Chọn cấu hình bằng bốn file train, LAB đoạn v/uv/sil và LAB ba thống kê F0 của train.
- Không đọc WAV/LAB test trong chương trình tìm cấu hình. Hàm loader chỉ cho phép train trước khi có `frozen_config.json`.
- Khi đã chốt cấu hình, chạy test đúng một lượt so sánh và không sửa thuật toán theo kết quả test.
- Baseline test đã được xem trước đây; kết quả cuối độc lập với lựa chọn cải tiến mới nhưng không thể gọi là tập chưa từng thấy.
- Không có nhãn F0 từng khung. Phân tích octave dùng bằng chứng ứng viên và tính liên tục; không báo frame pitch accuracy hoặc RMSE/cents so với GT không tồn tại.
- Không sử dụng F0mean/F0std/F0num GT của file đang suy luận để sửa F0, giới hạn dải, chọn giọng nam/nữ hoặc lọc ngoại lệ.
- F0num là số F0 hữu hạn do mô hình sinh ra. Không loại khung theo nhãn thật khi tính bảng điểm chính.

## Giả thuyết và các bước

H0: sai đường dẫn, ghép LAB, đơn vị, chia khung hoặc cách tính MAPE. Tái lập baseline và kiểm tra manifest/hash.

H1: nhầm UV/SIL hoặc khung giáp ranh làm phương sai tăng. Đo phân rã phương sai theo nhãn, năng lượng và giáp ranh. Các phép lọc theo nhãn là oracle chẩn đoán, không dùng triển khai.

H2: chọn cực trị cao nhất/thấp nhất độc lập từng khung chọn bội chu kỳ, làm F0 giảm một octave. Đo peak/dip gần nhau trên phone_F1, minh họa waveform và ứng viên. Thử ưu tiên chu kỳ ngắn trong các cực trị gần tốt nhất, và đường đi liên tục giữa ứng viên.

H3: median theo chuỗi có tiếng giảm spike; lọc tần số trước ACF/AMDF giảm nhiễu/ảnh hưởng formant. Thử riêng median 3/5; Gaussian low-pass top 800 Hz với attenuation 0.03 (tham khảo Praat) như một thí nghiệm độc lập.

H4: chọn ngưỡng theo balanced accuracy V/UV không tối ưu ba MAPE. So sánh ba ngưỡng Gaussian/histogram đã có bằng LOFO ba thống kê; đối chiếu trọng số file và F0num. Không chỉnh thống kê đầu ra để khớp nhãn.

## Chọn cấu hình

Khung chính 25 ms, hop 10 ms, dải F0 70–400 Hz. Giữ baseline GMM ACF 20 ms để so sánh nguyên bản. Những thử nghiệm frame được ghi riêng.

Ngưỡng periodicity được fit lại trong từng fold. Ngưỡng RMS tương đối được fit trên V/SIL của các file training trong fold. Tham số xử lý F0 được chọn qua leave-one-file-out (LOFO). Báo thêm nested LOFO: ngoài giữ một file, bên trong chọn cấu hình chỉ bằng ba file còn lại.

Tiêu chí giữ: giảm MAPE train tối thiểu 20% tương đối, giảm MAPE F0std phone_F1, LOFO và nested LOFO không xấu hơn baseline quá 1 điểm phần trăm, macro F1 V/UV không giảm quá 0.03. Báo tất cả thử nghiệm thất bại và đánh đổi, không chỉ best row.

Kết thúc khi nguyên nhân có kiểm chứng và có cấu hình đáp ứng tiêu chí; không lặp vô hạn tìm điểm test tốt hơn.

## Nguồn tham khảo chính

- https://www.fon.hum.uva.nl/praat/manual/how_to_choose_a_pitch_analysis_method.html
- https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_filtered_autocorrelation.html
- https://www.fon.hum.uva.nl/paul/papers/Proceedings_1993.pdf

