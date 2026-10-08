# H63 — tích phổ họa âm, chỉ thay F0 của khung hữu thanh

Rollback `e06e382cc9e8e4b0294a1d92917ac20a6387db03`; accepted `hard170` giữ nguyên. User đã yêu cầu tiếp tục sau H62 trong chat ngày 08/10/2026. Không chạy lại H00–H62.

Giả thuyết: thay objective khớp waveform bằng tích biên độ phổ tại các họa âm quanh anchor baseline có thể giảm sai lệch F0mean/F0std mà giữ nguyên quyết định hữu thanh và F0num. Họa âm là thành phần có tần số h lần F0; HPS tìm F0 có tích biên độ tại hF0 lớn nhất. Đây là custom bounded HPS, không port nguyên pipeline tác giả. Nguồn HTML/code và giới hạn trong HPS_SOURCE_REVIEW.md.

Chỉ ba option: hard170, hps_3, hps_5 (số họa âm 3/5). Khung PCM 25ms, hop10ms canonical, trừ DC trước Hann; không resample, filter, thay nhãn/voicing, smooth hoặc ép thống kê theo teacher3GT. FFT zero-padding tới power-of-two nhỏ nhất >=16×frame samples. Phổ biên độ chia maximum; floor1e-12 để log hữu hạn; objective sum_h log(max(interp_linear(|X(hf)|),1e-12)). Grid Hz bước0.1 trong [anchor×2^(-100/1200),anchor×2^(100/1200)] clip70–400; thêm hai endpoints và anchor, unique/sorted, tie→F0 nhỏ nhất. Zero spectrum giữ anchor. Không optimizer hoặc ngưỡng hậu nghiệm. Giới hạn ±100cents (100cents = một bán âm) tránh đổi octave; không có khả năng sửa lỗi octave hoặc khung bị baseline loại.

Precheck chỉ synthetic: fs16k/44.1k, F0 90/200/320Hz, noise seeds11/29/47, order3/5, 25ms, anchor +50cents; yêu cầu error<100cents, gain/DC invariance và DFT trực tiếp đối chiếu mọi harmonic interpolation/objective/grid argmax. Seed chỉ tạo nhiễu fixture, không MLtraining. Nếu lỗi giữ bằng chứng, không nới tolerance sau đo. Zero-input fallback phải đúng.

12 unique train metric groups,48 inner traces,24 train/LOFO/nested summary rows. Không học hệ số/nhãn; nested4outer/3inner/final4LOFO chọn option theo minimax worst-file Average MAPE→mean→ID, finite/F1/recallV drop<=.01/SIL+1 guards như H61. Giữ tám gate trong voicing_recovery.gates; all8 yêu cầu từng file Average MAPE<2%. Test có lịch sử exposure, nested exploratory. Không random frameCV hoặc claim speaker independence.

Prereg/source/precheck/registry commit rồi push và remoteSHA verify trước train. Baseline đọc contour đã lưu H47 có hash, kiểm grid/PCM/LAB/teacher3GT; không đo lại baseline inference. Verifier độc lập: DFT trực tiếp tại FFT bins cần dùng, scalar linear interpolation/log product; kiểm toàn grid argmax, mask/count, scalar metrics, inner membership/selection và tám gates. Baseline artifacts/hashes và notebook đã nộp được bảo vệ. Không frameF0GT: pitch thay đổi hoặc metric tốt không chứng minh từng timestamp đúng.

Nếu không eligible, giữ failure, không đo test mới, baseline không promote. Nếu eligible, commit/push/verify train+locked config trước test cùng option; chưa tuyên bố đạt8file trước kết quả test. Không tự chuyển bài phân đoạn, không Drive/DL/PDF/Jev/schedule/automaticretry.
