# H47 — Học loại khung hữu thanh sai từ clean và augmentation

Điểm quay lại repository: `ea21067f6589e19a5252eec6596e20acdbf400ce`; baseline toán học vẫn H31 Praat filtered .30. Original và frozen config không đổi.

H46 chỉ tăng cường dữ liệu để xếp hạng pitch members nên không thay mask/count. H47 kiểm tra giả thuyết khác: học phân biệt hữu thanh V với UV/SIL từ nhãn đoạn train có thể loại khung hữu thanh sai và cải thiện thống kê F0. Không cắt số khung theo F0num chuẩn.

Logistic regression C=1, StandardScaler học bằng fit pool. Đặc trưng 25ms tại thời gian native Praat: tương quan chuẩn hóa tại chu kỳ Praat, log RMS tương đối percentile95 của chính waveform, tỷ lệ đổi dấu, tỷ lệ năng lượng phổ từ 1000Hz. RMS và ZCR tính sau trừ mean; FFT Hann, DC bỏ, trọng số phổ một phía đúng. Không thêm người nói/giới tính/thiết bị hay F0mean/std/count chuẩn vào đặc trưng.

Chỉ học trên các khung đã được Praat .30 nhận hữu thanh và nhãn V/UV/SIL rõ. Lớp theo tỷ lệ tự nhiên; tổng trọng số mỗi origin và mỗi variant bằng nhau. Hai fit modes: clean, clean+H46 white30/white20/pink20. Augmentation kế thừa nhãn đoạn; không tạo người nói độc lập. Không biến đổi pitch/thời gian. Mỗi held origin và mọi variants của nó loại khỏi fit. Khung inference không đọc nhãn/GT. Pitch giữ H43 hard170, chỉ mask được phép giảm. Không khôi phục khung Praat đã loại.

Sáu options: Praat control, hard170 control, clean/aug logistic threshold .25/.50. Việc bỏ ensemble H45/H46 dựa trên kết quả đã thất bại; nếu fallback hard170 đạt target phải nêu rõ đây là cấu hình đã biết trên train, không bằng chứng augmentation cải thiện.

Selection cố định trước đo: inner leave-one-file-out, tối thiểu worst-file Average MAPE, rồi mean, rồi ID; invalid nếu macroF1 hoặc recallV giảm hơn .01, false_voiced_sil tăng hơn1 so với Praat control. Giữ tám eligibility gates của H46, phone_F1 std không xấu đi. Target mới người dùng: **mỗi nested clean train file Average MAPE <2%** (strict), không sửa predicate lịch sử. Inner fit trên2 origins; outer fit trên3. Các thống kê train-fit và selected LOFO phải báo riêng. Test chưa dùng trong H47; không suy từ4train sang8files.

Kiểm tra trước đo chỉ synthetic tính periodicity, scale invariance, silence và xác suất logistic. Commit/push registry+source và xác minh remote trước measurement. Sau đo kiểm tra hash, exclusion origin/variant, replay classifier, selection, thống kê và strict predicate. Giữ failure; không sửa frozen/original, không promote tự động. Nested là exploratory sau lịch sử nhiều vòng dùng bốn file, không đánh giá độc lập mới.

Không dùng Jev: nhánh MCP đang lỗi từ H32 và không tự retry. Không deep learning, không Drive, không literature review mới.
