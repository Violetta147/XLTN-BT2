# R01 — thử tái tạo cách tạo chuẩn

Kết luận: **chưa xác định được quy trình của thầy**. Preregistration `8a7af15cfc2df4c89d769327e21b41c7d773dfa4` đã push và remote-verified trước 16 phép đo train mới. Không chạy lại H00–H66, không đo F0 mới trên test và không thay teacher3GT.

Praat 6.1.38 qua Parselmouth0.4.7 đã chạy raw autocorrelation (AC) và cross-correlation (CC), floor75/ceiling600 mặc định, step tự động hoặc10ms. Dùng native voiced frames, thử std population và sample. Synthetic200Hz/silence cả4 cấu hình PASS. Không cấu hình/định nghĩa std nào khớp cả mean/std làm tròn1 chữ số và count chính xác trên cả4 train. Default raw AC có mean Average MAPE khoảng35.64%; phạm vi600Hz cho phép lỗi octave trên phone, không phải bằng chứng chuẩn sai.

Praat7 và pYIN được đọc lại từ **CSV native đã lưu**, không chạy inference. Gần nhất trong nhóm native đã rà là Praat7 filtered voicing.45 + sample std: mean Average MAPE2.124516%; population2.156992%. Đây là mean4file, không khẳng định từng file<2%. Không một file nào của cấu hình đó khớp cả3 số sau làm tròn. Harvest chỉ có cache canonical projected trong phạm vi kiểm tra này; bảng thống kê đó được lưu riêng, không gán là native hoặc dùng để kết luận phần mềm thầy.

Std population chia tổng bình phương độ lệch cho N; sample chia cho N−1. Thay cách chia chỉ thay std, không thay mean hoặc số khung; không thể tự giải thích các mismatch count. Nội dung chuẩn mới thay cả mean/std so LAB cũ; provenance đã lưu chưa có script, phần mềm, version hay cấu hình tạo chuẩn. Không chạy lại audit GitHub trước đây.

| File | Số tâm khung LAB V | F0num chuẩn | Count hard170 đã lưu |
|---|---:|---:|---:|
|phone_F1|153|148|147|
|phone_M1|244|232|233|
|studio_F1|123|127|123|
|studio_M1|94|82|85|
|phone_F2|235|219|220|
|phone_M2|134|123|130|
|studio_F2|137|139|133|
|studio_M2|128|116|120|

Bốn dòng test chỉ phân tích nhãn/count từ H48 cached contours; không new test inference/tuning. Nhãn V/UV/SIL theo đoạn và thống kê F0 cả file là hai loại bằng chứng khác nhau. Không có F0 chuẩn từng timestamp. Tái tạo gần số liệu chưa chứng minh thầy dùng phần mềm đó; cùng số làm tròn có thể do nhiều quy trình. Không kết luận thầy dùng Praat hay ghi sai.

Giữ giả thuyết none/unknown. Thông tin còn cần từ nguồn tạo chuẩn: algorithm/version, floor/ceiling, window/hop/time origin, tiêu chí voiced, sample/population std, định nghĩa count và liệu có chỉnh contour thủ công. Không tự gửi tin thầy. Các phép thử cải thiện tiếp tục dùng metric/gate/split hiện có.

Artifacts: `results/R01_reference_matches.csv`, `R01_new_native_frames.csv`, `R01_cached_pipeline_stats.csv`, `R01_label_count_audit.csv`, `R01_receipt.json`, `R01_precheck.json`. Scalar mean/std/count được đối chiếu độc lập với NumPy; source/output/protected hashes kiểm qua registry. Không tuning trên test.

Nguồn đã đọc: [Praat raw AC](https://www.fon.hum.uva.nl/praat/manual/Sound__To_Pitch__raw_autocorrelation____.html), [filtered AC](https://www.fon.hum.uva.nl/praat/manual/Sound__To_Pitch__filtered_autocorrelation____.html), HTML docs và mã runtime, không PDF. Workflow experimental-design/literature-review local; [Kassis et al., Scientific Agent Skills (2026)](https://arxiv.org/abs/2609.00065), DOI10.48550/arXiv.2609.00065, chỉ là nguồn thủ tục.
