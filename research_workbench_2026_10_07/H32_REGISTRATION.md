# H32 — cô lập ngưỡng silence của Praat filtered

Đăng ký trước khi đo các ngưỡng silence mới trên BT2. Rollback repository f9e986e; control là H31 fixed voicing0.30/silence0.09. Original baseline009fd2c và frozen_config giữ nguyên. H30 fixed0.45 vẫn là reference đã qua gates, H31 là failure giữ lại. H32 không gọi H31 là champion.

Giả thuyết: nâng ngưỡng silence có thể thay đổi quyết định ở đoạn biên độ yếu và giảm lỗi thống kê, nhưng cũng có thể bỏ V thật. Không giả định các khung dư ở studio_M1 đều là false voiced. Nguồn cơ chế là [manual HTML của Praat](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_filtered_autocorrelation.html), mục Silence threshold: biên độ tương đối với cực đại toàn tín hiệu. Đây là tài liệu triển khai, không phải đã đọc toàn bộ paper. Không extract PDF.

## Một tham số được thay

Silence threshold **0.09/0.11/0.13/0.15**; 0.09 là control. Giữ Praat7.0.02, voicing0.30, floor70Hz, top800Hz, attenuation0.03, octave0.055, jump0.35, V/UV0.14, max15, very_accurate=false, step10ms, output70–400Hz. Script/adapter mới chỉ thêm đầu vào silence; script/adapter H30–H31 không sửa. Không thêm gate/median/noise, không đổi window/hop/filter/range/metric.

Lưu mọi native F0 trước range policy. Selected F0 ngoài70–400 nhận UV/NaN, không đổi thành ứng viên khác. Ghép tâm gần nhất với canonical25/10, cho sai lệch tối đa nửa hop cộng một mẫu; hòa chọn sớm hơn, không padding. Không cắt/thêm khung theo ground truth. LAB chỉ có thống kê cả file và nhãn đoạn V/UV/SIL, không có F0 chuẩn từng khung.

## Selection, gates và mục tiêu

Praat không fit; actual_fit_files=[]/requires_fit=false. Inner nominal pools chỉ dùng chọn ngưỡng. Final inner LOFO bốn file; outer held chỉ được chấm sau inner LOFO ba file còn lại. Eligibility: lỗi hữu hạn, mean F1/recall V≥control−0.01, tổng SIL≤control+1. Rank max file Average MAPE, rồi mean và ID. Không dùng metadata giới/file ID để chọn ngưỡng. Nested vẫn exploratory vì thiết kế chịu lịch sử đã nghiên cứu bốn file.

Giữ tám gates tương đối với control H31 fixed0.30: train giảm≥10%; selected LOFO/nested giảm≥5%; nested mean F1/recall giảm≤0.01; tổng SIL tăng≤1; không file MAPE xấu thêm>2 điểm phần trăm; phone_F1 std không xấu hơn. Mục tiêu **mỗi nested file Average MAPE≤2%** báo riêng, không thay bằng mean bốn file. Không tự promote hoặc thay gates sau đo; giữ kết quả thất bại.

Trước đo: tám synthetic calls tone/silence ở16k/44.1k và hai đầu ngưỡng .09/.15; kiểm binary/version/hash, original AMDF parity, compile và registry. Không đo ngưỡng BT2 mới trong check. Sau đo: control tái lập H31 fixed0.30; verify64 inner traces/24 metric rows, exclusions/minimax/eight gates, mọi native fixed stats/MAPE/VUV/range/projection từ raw dump, hashes và PNG/SVG; poison nhãn/stat held không đổi inference. 16 native BT2 calls dự kiến, không có actual fit của Praat.

Jev prospective evaluation bị input validation error, chưa có phán xét; nhánh MCP dừng, không retry. Chọn H32 là quyết định của agent. Support-duration controller chỉ là đề xuất chưa đăng ký/đo; không nằm trong H32.

Chỉ local train, không test/Drive/deep learning. Lệnh: `C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/praat_silence_threshold.py register/check/H32`; verify bằng `verify_amdf_loop.py H32 praat7_filtered_s0.09`.
