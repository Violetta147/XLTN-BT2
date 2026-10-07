# H27 — pipeline tham chiếu Praat raw ACF

Đăng ký trước đo. Điểm quay lại: 556a9b9; control: H24 AMDF với cổng V/UV 25 ms và ứng viên F0 40 ms. Giữ baseline gốc 009fd2c và frozen_config. Nguồn thuật toán: https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_raw_autocorrelation.html. Máy có Parselmouth 0.4.7/Praat 6.1.38. Đây là so sánh toàn bộ pipeline, không phải thí nghiệm cô lập một filter.

## Giả thuyết và cấu hình

ACF hiệu chỉnh cửa sổ và chọn đường có trạng thái UV có thể xử lý cả F0 và voicing, khác AMDF dùng ngưỡng loại khung trước rồi chỉ tìm đường trong các đoạn dự đoán hữu thanh. Mục tiêu người dùng: **mỗi file Average MAPE ≤2%**.

Bốn lựa chọn: control và Praat raw với voicing threshold 0.35/0.45/0.55. Giữ tín hiệu raw, F0 70–400 Hz, bước 10 ms, 15 ứng viên, Hanning (very_accurate=false), silence threshold 0.03, octave cost 0.01, jump cost 0.35 và V/UV cost 0.14. Cửa sổ hiệu dụng là 3/pitch_floor = 42.857 ms; không fix 25 ms cho thuật toán. Không thêm cổng năng lượng AMDF hoặc median. API raw đang có khác filtered Praat năm 2023.

## Adapter và chọn cấu hình

Ghép tâm native gần nhất vào lưới chấm canonical 25/10 ms trong nửa hop cộng một mẫu; khi hòa chọn tâm sớm hơn. Ngoài vùng hỗ trợ: pred=false, F0=NaN. Không padding, fallback hoặc cắt/thêm khung theo GT. Báo native_frames, native_f0_count và projection_coverage. Praat không fit: actual_fit_files=[]/requires_fit=false; fit_files trong traces là tập danh nghĩa cho chọn cấu hình. Control vẫn fit đúng tập đã định.

Final chọn qua LOFO bốn file; mỗi outer fold chọn bằng inner LOFO ba file còn lại. Rank lỗi file lớn nhất, rồi mean và ID. Eligibility: mọi MAPE hữu hạn; F1/recall không thấp hơn control quá 0.01, SIL không tăng quá một khung. File outer không tham gia chọn cấu hình. Báo mọi fixed LOFO, selected LOFO, nested và contour; nested vẫn exploratory do lịch sử đã nghiên cứu bốn file.

## Tiêu chí trước đo

Giữ gates H25/H26: train MAPE giảm ít nhất 10%; selected LOFO/nested giảm ít nhất 5%; nested F1 và recall không giảm quá 0.01; SIL tăng không quá một khung; không file nào MAPE xấu thêm quá 2 điểm phần trăm; phone_F1 std không xấu hơn. Mục tiêu mỗi file ≤2% báo riêng. Không hạ gate sau đo hoặc tự promote. Giữ cả kết quả thất bại.

Check trước đo: tái lập AMDF gốc và synthetic 173 Hz/silence ở 16 kHz/44.1 kHz; chưa benchmark Praat trên WAV thật trong check. Sau đo: verify 64 traces/24 metric rows, provenance, contour/LAB/hash, minimax/gates/coverage và PNG/SVG. Runner hash bao gồm cả module amdf_dual_window dùng cho control.

Chỉ train local; không test/Drive/deep learning/PDF extraction. Harvest vẫn trong backlog: probe PyPI 0.3.6 chỉ liệt kê Windows wheels cp36/cp37/cp38, chưa có wheel cp313 phù hợp máy hiện tại. Không coi probe này là thuật toán không thể chạy; có thể dùng môi trường phù hợp hoặc build reference trong vòng riêng. Probe lưu results/pyworld_package_probe.json.

Lệnh: `python research_workbench_2026_10_07/praat_reference.py register/check/H27`.
