# R01 — dò cách tạo thống kê chuẩn trên train

Đăng ký trước đo mới. Rollback e0b672970611abcdac4a802b22a5c121da9f48a6; giữ hard170 và teacher3GT. Người dùng không biết công cụ tạo chuẩn và yêu cầu thử phần mềm có khả năng được dùng. Đây là kiểm tra nguồn gốc số liệu, không một ứng viên thay baseline.

Dùng lại CSV đã lưu H28/H30/H33 để so Harvest, Praat 7, pYIN; không chạy lại các pipeline đó. Đo mới chỉ Praat 6.1.38 qua Parselmouth 0.4.7: raw AC và raw CC, default floor75/ceiling600, time_step=None (tự động) và .01 s; giữ toàn bộ voiced output native, không canonical projection, LAB masking, cắt theo count hoặc tuning. Hai cách std: population (ddof0) và sample (ddof1). Tính mean/std của F0>0; F0num là số native voiced frames. Đây là giả thuyết định nghĩa count, không khẳng định count thầy là native voiced frames.

Chỉ bốn train. Match nghiêm: mean và std làm tròn một chữ số thập phân bằng teacher3GT, count chính xác. Chỉ gọi tái tạo toàn bộ nếu cả ba số ở cả bốn file cùng khớp trong một cấu hình và một định nghĩa std. Không chọn từng file một cấu hình; none/unknown là kết quả hợp lệ. Không mở test để tìm cấu hình gần nhất; không thay bộ chuẩn, gate hay notebook. Cấu hình mặc định được đăng ký một lần; mismatch được giữ, không mở rộng grid sau thấy kết quả.

Đối chiếu thêm count LAB V trên canonical grid với F0num từ cached H47/H48, chỉ audit nhãn/count đã lưu, không new test inference. Không coi LAB V là F0 frame truth. Rà provenance receipts đã có; không chạy lại public repository audit. Kiểm SHA sources/input/output; scalar sum/std/count được tính độc lập để đối chiếu NumPy. Synthetic trước đo: AC/CC default trên 1s harmonic200Hz tại16k, ít nhất20voicedframes và median cents<100; constant silence output không voiced. Nếu fail giữ failure, không đo BT2.

Commit/push/remoteSHA trước đo. Không gửi tin thầy, Google Drive, deep learning, PDF, Jev hay schedule. Công cụ trùng output không chứng minh thầy dùng phần mềm đó: còn version, time origin, V/UV criterion, count definition và script chưa có.

Primary docs: [Praat raw autocorrelation](https://www.fon.hum.uva.nl/praat/manual/Sound__To_Pitch__raw_autocorrelation____.html). Kết quả cached Praat7 ở H30, khác runtime Praat6 trong R01. Workflow experimental-design và literature-review local; [Scientific Agent Skills](https://arxiv.org/abs/2609.00065) chỉ cung cấp thủ tục nghiên cứu, không bằng chứng về phần mềm của thầy.
