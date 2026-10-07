# Praat 7.0.02 cho pipeline tham chiếu

Bản Windows x64(v1) được lấy theo [trang tải chính thức](https://www.fon.hum.uva.nl/praat/download_win.html), phiên bản v7.0.02. Chạy portable từ `.bt2-tools/praat-7.0.02` trong workspace cha, không thay Parselmouth 0.4.7/Praat 6.1.38 của baseline.

ZIP SHA256 khớp digest của asset GitHub; binary và URL được lưu `results/praat_native_7002_provenance.json`. Trang chính thức liên kết repository `praat/praat`, API release trả asset trong repository `praat/praat.github.io`; lần kiểm tra URL literal mismatch trước download được giữ tại `praat_native_install_attempt1.json`. Sau đó xác minh filename/version cùng asset của tổ chức Praat và checksum trước khi chạy.

Chạy `Praat.exe --run` theo [manual CLI](https://www.fon.hum.uva.nl/praat/manual/Scripting_6_9__Calling_from_the_command_line.html), không tạo GUI. Tham số của raw và filtered được đối chiếu source tag v7.0.02, `fon/praat_Sound.cpp`, metadata hash tại `results/praat_native_command_source.json`. Nguồn HTML đã đọc, không extract PDF.

Script do agent viết `praat_extract_native.praat` chỉ đọc WAV, chạy pitch và in CSV ra stdout; Python parse và lưu kết quả. Praat 7 chặn lần thử ghi CSV trực tiếp từ script; stderr nguyên bản được giữ trong `results/praat_native_probe_file_write_rejected.json`. Không bật `--FULL-TRUST`. Adapter xử lý stdout UTF-16LE và giữ command/returncode/hash/phiên bản. Các tiến trình chạy ẩn và có timeout.

`praat_native_probe.py` kiểm tín hiệu hai harmonic 173Hz và silence, ở16k/44.1k, bằng raw/filtered (8 calls). Sai số tone dưới1Hz, silence không voiced. Probe chỉ xác minh adapter và tín hiệu đơn giản, chưa chứng minh chất lượng speech. Không đọc WAV BT2 trong probe. Kết quả lưu `results/praat_native_synthetic_probe.json`.

Chưa đo native 7.0.02 trên WAV BT2 tại thời điểm tạo tài liệu này. Vòng H30 phải đăng ký riêng các tham số và chính sách range/adapter trước đo. Không coi pipeline mặc định filtered là cô lập một lowpass filter: nó còn có các cost/threshold khác raw. `Pitch top` của API filtered đồng thời điều khiển attenuation và giới hạn ứng viên; phải ghi riêng với range kết quả được chấm.

Tái lập probe: `C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/praat_native_probe.py`. Tải lại đúng asset URL/ZIP hash trong provenance nếu binary portable bị thiếu; không cần cài hệ thống hoặc mở GUI.
