# H31 — chỉ mở ngưỡng hữu thanh của Praat filtered

Đăng ký trước đo grid mới. Rollback/control commit7432dd6; control cấu hình native filtered H30 voicing0.45, đã qua8gate nhưng worst file2.769856%. Original AMDF009fd2c/frozen_config giữ nguyên. Giả thuyết: ngưỡng hữu thanh thấp hơn có thể lấy lại khung V bị bỏ, giảm count error mà vẫn giữ std/SIL và V/UV.

## Thay một tham số

Registry voicing threshold **0.25/0.30/0.35/0.40/0.45**; 0.45 là control. Giữ Praat7.0.02/binary/script, floor70, top800, attenuation0.03, silence0.09, octave0.055, jump0.35, V/UV0.14, max15, very_accurate=false, step10ms. Không đổi candidate top, output range, filter, window, hop, gate năng lượng hoặc median; không thêm noise/StoneMask.

Chính sách H30 giữ nguyên: selectedF0 native ngoài70–400Hz nhận UV/NaN, không đổi thành candidate khác. Lưu raw native F0 trước range và đếm range rejected. Ghép nearest center về canonical25/10 trong nửa hop + một mẫu; hòa chọn sớm hơn; unsupported=false/NaN. Không cắt hoặc thêm khung theo GT.

## Chọn cấu hình và tiêu chí

Praat không fit; actual_fit_files=[]/requires_fit=false. Inner nominal pool dùng chọn threshold, không phải training của Praat. Final inner LOFO bốn file; outer held chỉ chấm sau inner LOFO ba file còn lại. Rank max file Average MAPE, rồi mean và ID. Eligibility lỗi hữu hạn, mean F1/recall≥control−0.01, tổng SIL≤control+1. Nested vẫn exploratory vì lịch sử đã nghiên cứu bốn file.

Giữ dạng gates, tính tương đối với **control H30 fixed0.45**: train giảm≥10%; selected LOFO/nested giảm≥5%; nested mean F1/recall giảm≤0.01; tổng SIL tăng≤1; không file Average MAPE xấu thêm>2 điểm phần trăm; phone_F1 std không xấu hơn. Mục tiêu **mỗi file Average MAPE≤2%** là tiêu chí riêng, không thay bằng mean bốn file. Không hạ gates hoặc tự promote sau đo.

Check trước đo: native binary/hash/probe8calls của H30 và AMDF original parity; không đo threshold mới trên BT2 trong check. Sau đo phải tái lập control H30, verify80inner traces/24metric rows, no-fit/selection exclusions, replay minmax/gates, mọi native fixed stats/VUV/range/projection từ raw dump và binary/call provenance, contour/LAB/source/WAV hashes/PNG/SVG; poisonheld nhãn/stat không đổi inference. Lưu cả failures.

Chỉ train local, không test/Drive/deep learning/PDF extraction. Lệnh: `C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/praat_voicing_threshold.py register/check/H31`.
