# Nhật ký chạy và lỗi — giữ cả lần thất bại

## H00 lần 1

- Lệnh: python research_workbench_2026_10_06/audit.py
- Tái lập baseline và tạo các CSV xong trước khi tới spectrogram; chưa coi toàn run thành công.
- SciPy cảnh báo WAV có chunk metadata không hiểu, bỏ qua chunk không phải audio data.
- Lỗi figure: nfft=1024 nhỏ hơn nperseg khi sample rate thực làm frame25ms dài hơn1024samples. ValueError: nfft must be greater than or equal to nperseg.
- Sửa mã tạo figure: nfft là power-of-two đủ dài cho nperseg thực; CSV phổ giữ đúng band0–2000Hz được vẽ. Không đổi frame/hop/threshold/thuật toán/metric.
- Chạy lại H00 sau sửa code, không lặp Jev hoặc Gemini để làm đẹp kết luận.

## H00 lần 2

- Hoàn tất số liệu, kiểm tra và 20 figure PNG/SVG; bước viết Markdown dùng pandas.to_markdown bị lỗi vì môi trường không có optional dependency tabulate.
- Sửa bước xuất report bằng hàm Markdown table nhỏ dùng thư viện có sẵn; không cài thêm dependency và không đổi số liệu hoặc biểu đồ.
- Chạy lại để manifest code hash, figures và report cùng một phiên bản.
# H11 synthetic validation stop

Lần đầu `python research_workbench_2026_10_06/estimator_experiment.py mpm` dừng ở assertion đòi mọi noisy/synthetic frame phải có pitch hữu hạn. NSDF numerical checks đã pass1e-10. MPM thiết kế trả NaN khi không có positive-lobe peak hợp lệ, nên không ép fallback pitch để làm đẹp coverage. Chẩn đoán abstention theo case trước sửa harness; clean interior gate vẫn giữ và phải có đủ coverage. Bổ sung coverage và lỗi có điều kiện trên frame được trả lời, không gọi missing estimates là pitch đúng.

