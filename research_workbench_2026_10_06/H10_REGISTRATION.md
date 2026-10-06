# H10 — YIN với support cố định trong frame25

Đăng ký trước chạy trên synthetic và WAV train. Champion009fd2c, audit585d6c4. Không sửa notebook hoặc champion.

Chỉ thay toàn bộ pitch estimator ACF/path bằng YIN CMND fixed-support, giữ voiced mask ACF + RMS fit từng fold, median3 trong voiced runs, frame25/hop10/range70–400. Bỏ path là phần thay estimator; thêm ACF best+median3 làm control để biết lợi ích từ path.

W=N-ceil(fs/70)-1; tổng difference dùng W mẫu đầu cho mọi lag. CMND d(k)/(mean d(1..k)); tìm local trough đầu dưới0.1, nếu không có dùng min trong range. Parabolic interpolation; clamp period về range70–400 để chặn sai số nội suy sát endpoint (không dùng GT). Silence/constant→NaN. Không threshold tune. Đây là adapter support ngắn, khác cấu hình cửa sổ dài của librosa YIN.

Validation: FFT curve khớp direct difference atol1e-10 trên synthetic chuẩn hóa; silence NaN; DC và gain không đổi F0; clean sine/harmonic interior80–380Hz median absolute cents<5 và p95<15. Low70 và missing-fundamental/noise là stress tests, không đặt gate hậu nghiệm.

Đánh giá train và outer held-file LOFO: mỗi fold fit chỉ other3. Không có hyperparameter selection mới, nên nested selection không có một bước chọn bên trong; không gọi hai bản tính lặp là hai bằng chứng độc lập. Giữ criterion PROTOCOL train/LOFO/tradeoff và phone_F1std; chỉ coi eligible nếu passes, không thay champion khi chưa hoàn thành toàn bộ quy trình. Cấu hình cũ đã từng chọn trên4file; mọi kết quả vẫn exploratory n=4.

Nguồn triển khai: [librosa official YIN docs](https://librosa.org/doc/main/api/generated/librosa.yin.html), [official source](https://librosa.org/doc/0.11.0/_modules/librosa/core/pitch.html). Công thức fixed-support được kiểm tra bằng direct sums; không tuyên bố adapter này giống từng chi tiết librosa hoặc đã đọc YIN PDF gốc.
