# H29 — kiểm tra riêng cổng V/UV khi dùng F0 Harvest

Đăng ký trước đo các nhánh gated. Rollback 4b29af2; control H24 AMDF gate25/pitch40, baseline gốc 009fd2c/frozen_config giữ nguyên. H28 đã cho bằng chứng: Harvest 10 ms recall V 0.991226 nhưng SIL false voiced 268 và mean Average MAPE 50.605862%. Giả thuyết là thêm cổng V/UV đang có có thể loại phần false voiced trước tính thống kê F0; chưa biết lỗi cao độ còn lại vì không có F0 chuẩn từng khung.

## Chỉ một thay đổi: gate

Giữ Harvest raw signal, F0 70–400 Hz, frame_period 10 ms, PyWORLD 0.3.5 và binary đã ghi hash. Không đổi F0 extractor/filter/StoneMask/median/noise/range. Registry bốn lựa chọn:

- `amdf_control`: H24, ngưỡng fit và pitch AMDF như cũ.
- `harvest_raw`: Harvest không thêm gate, tái lập H28 10 ms.
- `harvest_energy`: Harvest + relativeRMS ≥ ngưỡng. Fit energy từ V/SIL của các file training bằng balanced accuracy, đúng hàm baseline.
- `harvest_amdf`: Harvest + cả cổng energy và AMDF_score25ms của control. Fit hai ngưỡng như baseline, không thay classifier hay threshold method. Chỉ dùng AMDF cho V/UV; F0 còn lại lấy Harvest.

Đọc nhãn chỉ khi fit các file trong pool hoặc khi chấm. Inference held chỉ dùng signal/features. Không dùng số GT để cắt/thêm khung, không fallback F0 khi Harvest gọi UV. Đặc trưng relativeRMS lấy từ khung canonical25ms, chuẩn hóa bằng quantile95 trong chính signal; không dùng nhãn held.

## Lưới chấm và provenance

Ghép Harvest native vào canonical25/10 ms trước gate, tâm gần nhất trong nửa hop + một mẫu, hòa chọn tâm sớm hơn; unsupported=false/NaN. native_frames/native_f0_count ghi output Harvest trước gate; F0num ghi output cuối trên lưới chấm. Không gọi bước 10 ms là độ dài cửa sổ Harvest.

Control và các nhánh có gate ghi requires_fit=true/actual_fit_files đúng pool; raw ghi false/[] dù trace vẫn ghi pool danh nghĩa của lựa chọn. Final dùng inner LOFO bốn file; outer held chọn từ inner LOFO ba file còn lại. Minimax file Average MAPE rồi mean/ID; eligibility mọi lỗi hữu hạn, F1/recall ≥control−0.01, SIL ≤control+1. Outer file bị loại khỏi cả fit và selection. Nested vẫn exploratory vì đã nghiên cứu lịch sử bốn file.

## Gates trước đo

Train giảm ≥10%; selected LOFO/nested giảm ≥5%; nested F1/recall giảm ≤0.01; SIL tăng ≤1; không file MAPE xấu thêm >2 điểm phần trăm; phone_F1 std không xấu hơn. Mục tiêu mỗi file Average MAPE≤2% báo riêng. Không thay gates sau đo, không tự promote. Giữ failures.

Kiểm tra trước đo: tái lập AMDF gốc; kiểm native binary hash và synthetic12-harmonic173Hz/silence như H28, giữ synthetic failure. Sau đo: tái lập cả control H24 và raw Harvest H28; verify64 traces/24 metric rows, pool/gate provenance, replay minimax/gates, contour/LAB/source/WAV hashes, PNG/SVG; poison nhãn/GT held không đổi inference. Chỉ local train, không test/Drive/deep learning/PDF extraction.

Lệnh: `../.venv-bt2-world/Scripts/python.exe research_workbench_2026_10_07/harvest_voicing.py register/check/H29`.
