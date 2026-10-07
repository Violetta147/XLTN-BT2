# H30 — Praat 7 native filtered autocorrelation

Đăng ký trước đọc WAV BT2 bằng native7. Rollback 9a57006; control H24 AMDF gate25/pitch40, original 009fd2c/frozen_config giữ nguyên. Giả thuyết: pipeline filtered autocorrelation được tài liệu Praat khuyến nghị cho speech có thể giảm lỗi trên phone files so với raw/reference cũ. Đây là so sánh toàn bộ pipeline, không cô lập một lowpass filter.

## Nguồn và môi trường

Đã đọc [manual HTML filtered](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_filtered_autocorrelation.html), [API](https://www.fon.hum.uva.nl/praat/manual/Sound__To_Pitch__filtered_autocorrelation____.html), [CLI](https://www.fon.hum.uva.nl/praat/manual/Scripting_6_9__Calling_from_the_command_line.html) và định nghĩa tham số trong source tag v7.0.02, `fon/praat_Sound.cpp`. Version, URL, ZIP/native binary hashes và command source provenance đã commit9a57006. ZIP digest khớp asset tác giả. Portable x64(v1) trong workspace cha, không thay baseline Parselmouth/Praat6.

Script chỉ đọc WAV và xuất CSV qua stdout; Python parse UTF-16LE. Không mở GUI, không FULL-TRUST. Tám synthetic calls (173Hz hai harmonic và silence × raw/filtered ×16k/44.1k) đã qua trước đo. Native7 chưa benchmark trên WAV BT2 khi đăng ký. Giữ logs URL mismatch/file-write rejection và cách sửa bằng stdout.

## Registry năm lựa chọn

- AMDF H24 control.
- Praat7 raw: floor70, ceiling400, step10ms, max15, very_accurate=false, silence0.03, voicing0.45, octave0.01, jump0.35, V/UV0.14.
- Praat7 filtered: floor70, **top800**, step10ms, max15, very_accurate=false, attenuation_at_top0.03, silence0.09, octave0.055, jump0.35, V/UV0.14; voicing **0.45/0.50/0.55**.

Filtered top800 vừa điều khiển Gaussian attenuation vừa là giới hạn ứng viên native. Range đầu ra chấm giữ70–400Hz: selected native F0 ngoài range nhận UV/F0NaN, không sửa thành candidate khác. Chính sách này áp dụng mọi output native; raw ceiling400 đã giới hạn trước đó. Không claim hai nhánh chỉ khác filter vì costs, silence và native candidate top cũng khác. Ghi số range-rejected và **lưu tất cả native selected F0 trước range policy**. Không dùng GT để đặt range/top hay thay đổi sau đo.

Không energy gate AMDF, external median/StoneMask/noise/fallback. Support theo native floor70 (effective window khoảng42.86ms), không cố định25ms cho model. Ghép nearest center về canonical25/10ms trong nửa hop + một mẫu; hòa chọn sớm hơn. Unsupported=false/NaN. Canonical chỉ là lưới chấm; không chỉnh GT/count.

## Chọn cấu hình và gates

Praat không fit; actual_fit_files=[]/requires_fit=false. Inner trace pool chỉ dùng để chọn config; AMDF control fit đúng pool. Final inner LOFO bốn file; outer held chỉ chấm sau inner LOFO ba file. Minimax file Average MAPE rồi mean và ID. Eligibility hữu hạn, F1/recall≥control−0.01, SIL≤control+1. Nested vẫn exploratory do lịch sử đã nghiên cứu bốn file.

Train giảm≥10%; selected LOFO/nested giảm≥5%; nested F1/recall giảm≤0.01, SIL tăng≤1; không file MAPE xấu thêm>2 điểm phần trăm; phone_F1 std không xấu hơn. Mục tiêu **mỗi file Average MAPE≤2%** báo riêng. Không hạ gates, không tự promote; giữ cả failure.

Sau đo: verify80 inner traces/24 metric rows, baseline parity, no-fit/native hash/call provenance, replay minmax/gates; tái tính toàn bộ native fixed results từ raw F0 dump/range/projection; kiểm contour/LAB/WAV/source hashes và PNG/SVG. Poison nhãn/stat held không đổi inference. Chỉ local train; không test/Drive/deep learning/PDF extraction.

Lệnh: `C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/praat_filtered_reference.py register/check/H30`.
