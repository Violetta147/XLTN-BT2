# H76 — decoder giúp cao độ phục hồi, cấu hình chung đạt bốn train

Ngày 09/10/2026. H76 tái sử dụng đúng các model và prediction C1 H75 theo fit pool, chỉ đổi cao độ hoặc loại khung phục hồi bằng ngữ cảnh giới hạn. Native pYIN decision/F0 giữ nguyên. Anchor là native được C1 nhận V và energy07 giữ; bridge tối đa 10 hops, ratio anchor <=1,15, nội suy log F0. Nếu không bridge được, edge 0/10/25 hops chọn ACF nhân0,5/1/2 gần anchor nhất, ratio <=1,1, chỉ trong70–400Hz. Không fit, suy luận pYIN hoặc trích đặc trưng lại. Cửa sổ âm học vẫn thật 25 ms/bước 10 ms; decoder offline có dùng tương lai, không gọi streaming. Đây là thuật toán custom cho recovered pYIN25, không chạy lại H59 Markov hoặc H53 YAAPT.

bridge10_edge0: MAPE phone_F1 / phone_M1 / studio_F1 / studio_M1 = 1.488577 / 2.238153 / 2.285077 / 0.544270%; mean 1.639019%, worst 2.285077%, macro F1 0.875665, recall V 0.906982, 2/4 train dưới 2%.

bridge10_edge10: MAPE phone_F1 / phone_M1 / studio_F1 / studio_M1 = 1.730014 / 2.238153 / 1.747907 / 0.738871%; mean 1.613736%, worst 2.238153%, macro F1 0.882992, recall V 0.914942, 3/4 train dưới 2%.

bridge10_edge25: MAPE phone_F1 / phone_M1 / studio_F1 / studio_M1 = 1.730014 / 1.437832 / 1.747907 / 1.340805%; mean 1.564140%, worst 1.747907%, macro F1 0.892668, recall V 0.925384, 4/4 train dưới 2%.

raw_recovery_C1: MAPE phone_F1 / phone_M1 / studio_F1 / studio_M1 = 2.416904 / 11.032951 / 1.447456 / 2.777443%; mean 4.418689%, worst 11.032951%, macro F1 0.889530, recall V 0.930704, 1/4 train dưới 2%.

Cấu hình bridge10_edge25 là một cấu hình thống nhất đạt cả bốn train dưới 2%. Phone_M1 giảm từ 11,032951% của raw recovery xuống 1,437832%; std giảm 22,027265 xuống 17,185838 Hz. Điều này ủng hộ việc kiểm soát ứng viên F0 phục hồi, chưa chứng minh cao độ từng khung đúng vì không có GT từng khung. Trung bình MAPE của nó cao hơn energy07 nhưng worst fulltrain thấp hơn. Không gọi đây là pipeline đã đạt tám file hoặc đã được chọn theo LOFO.

bridge10_edge0: mean 1.948669%, worst 3.476753%, macro F1 0.873454.

bridge10_edge10: mean 1.923386%, worst 3.476753%, macro F1 0.880781.

bridge10_edge25: mean 1.870748%, worst 2.664264%, macro F1 0.890274.

energy07: mean 1.305508%, worst 1.955313%, macro F1 0.849625.

raw_recovery_C1: mean 4.797501%, worst 12.436917%, macro F1 0.885734.

Quy tắc chọn H76 theo minimax trên held train vẫn chọn energy07; lịch sử H76 giữ nguyên, không đổi receipt/selection thành chọn bridge25. H76 không đo test decoder và chỉ tái sử dụng H72 cho cấu hình được chọn: mean train 1,305508%, mean test 2,196094%,7/8file. Theo mục tiêu người dùng đã làm rõ, một phép đo mới riêng có thể khóa bridge10_edge25 từ kết quả bốn train để kiểm tra test, báo LOFO là chẩn đoán không ổn định. Đây phải là prereg/test receipt mới, không sửa lựa chọn hoặc điều kiện H76 sau số đo.

Precheck synthetic bridge/edge/ratio/octave/fast-shift/distance PASS. Prereg 9db8bda67e43864d9509e57f8be0fa1a90c3834b đã commit/push/xác minh remote trước đo. Có 132 decoder groups mới và48 cached groups,180 tổng/80 inner/12 summary. Verifier PASS scalar decoder/masks/F0/metrics/native unchanged/labels/time/pools/cache copies/selection/hashes, không refit optimizer. Rollback b4e064cbccb52960a2f5b90ee1fcc66b5b03cf32. Nguồn và registry tại H76_decode, đo tại run_train, kế hoạch notes.txt bất biến và ghi sau đo trong run_train/notes.txt. Không promote hoặc sửa notebook/frozen/WAV/LAB/teacher GT.

Không test search, filename routing hoặc coi interpolation/ACF/native là frame ground truth. Test đã xem trong lịch sử/H72, control có lịch sử chọn cấu hình bằng cả bốn train. Không Drive/deep learning/PDF/Jev/GPU/Colab/schedule. Dùng experiment-code, reuse scikit-learn và quy trình experimental-design; tham chiếu Kassis,T., Agarwal,V., He,Y., Patel,D., & Brueckner,A.M.(2026), [Scientific Agent Skills](https://arxiv.org/abs/2609.00065), DOI 10.48550/arXiv.2609.00065, HTML metadata kiểm 09/10/2026.
