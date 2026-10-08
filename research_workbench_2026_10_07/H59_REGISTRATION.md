# H59 — ngữ cảnh thời gian cho rejection, giữ estimator/recovery

Rollback repository 7662b99abecfef2c90a4db9f00fde1b83839bca8; accepted hard170 và notebook đã nộp giữ nguyên. H58 giảm lỗi điểm theo nhãn LAB nhưng vẫn loại nhiều V trên phone_M1. Giả thuyết mới: quyết định từng khung thiếu thông tin về đoạn hữu thanh liên tục; một chuỗi Markov hai trạng thái có thể giữ các khung V yếu nằm cạnh V mạnh và phân biệt đoạn non-V rõ ràng. Đây là thiết kế custom từ bằng chứng H58, không phải port/reference implementation hay benchmark một paper mới.

## Thay đổi duy nhất

Giữ nguyên 33 GMM H56, 33 mapping có giám sát H58, đặc trưng, framing25ms/10ms, recovery mask và pitch bound200 H56. Thay duy nhất **điểm rejection theo khung** bằng marginal của chuỗi hai trạng thái N/V, N gộp UV và SIL. Không thay recovery, không sửa LAB/3GT và không ép F0count bằng nhãn.

Mỗi đúng fit pool học counts chuyển trạng thái từ chuỗi nhãn tâm LAB train. Initial counts +1 cho hai trạng thái, transition counts +1 cho bốn cặp; cộng counts ở từng file riêng, không tạo transition từ cuối file này sang đầu file khác. Dùng tất cả khung train trong pool; file dài đóng góp nhiều transition hơn. Row-normalize để có ma trận transition; normalize initial counts. Mapping của H58 vẫn dùng balanced sampling riêng như đã đăng ký. Transition không phụ thuộc seed nhưng serialize 33 records theo model ID (11 pools ×3 seeds); không nói đây là 33 stochastic fits khác nhau.

Unary potentials là `[1-p_t,p_t]` từ điểm mapped H58, clip epsilon cố định1e-6. Phân phối chuỗi tỷ lệ với `initial(z_0)*product(unary_t(z_t))*product(transition(z_{t-1},z_t))`. Forward-backward trong log domain trả marginal V. Điểm H58 là posterior-derived potential, không được chứng minh là emission likelihood hay calibrated P(V); không gọi đây là HMM generative đã fit tối đa likelihood. Kết quả marginal cũng không chứng nhận valid-F0 reference của thầy. Chạy offline trên toàn file, có dùng khung tương lai; không claim streaming hoặc latency realtime.

## Ma trận và tiêu chí

6 options: hard170; recovery_only; static mapped_rejection_025 (H58 parity control); markov_rejection_010/025/050. Markov có một transition rule cố định, không grid strength/duration. Chỉ original baseline V bị loại khi điểm <q, q=.1/.25/.5, giữ ties; khung recovery và pitch giữ lại y hệt H56. Đổi subset vẫn ảnh hưởng đồng thời count/mean/std và V/UV.

Train360 metric groups;288 inner traces;72 summary rows. Grouped nested4outer/3inner và final4LOFO, seed11/29/47. Mapping và transition fit chỉ đúng training pool2/3/4, không nhãn inner/outer held. Minimax worst file MAPE qua3seeds ->mean ->ID; guards từngseed finiteMAPE, mean macroF1/recallV drop<=.01, SILtotal<=control+1. Giữ tám gates hiện hành và mục tiêu riêng tất cả8file Average MAPE **<2%**. Không chọn seed hoặc route theo tên file. Nested vẫn exploratory sau nhiều vòng trên bốn file; không random split frames hay khẳng định speaker IDs độc lập đã được xác minh.

## Kiểm tra trước đo

Synthetic sequences length1/2/5/6: so với enumeration toàn bộ2^N paths và forward-backward scalar scaled probability-space; uniform transitions cho kết quả bằng unary; chuỗi2000 khung cực đoan phải finite. Fixture transition counts không nối các file; poison held labels không đổi transition; đổi fit labels có đổi. Strict thresholds, retained pitch/recovery được đối chiếu scalar. Đây là kiểm công thức, không kiểm accuracy của BT2.

Prereg source/config/registry/precheck phải commit/push và xác minh remote SHA trước train. Verifier train PASS mới freeze selection +mapping/transition SHA, commit/push/remoteverify trước test. Không đo train/test khi push/readback còn lỗi.

## Test đã khóa và báo cáo

Test chỉ control+selected+predeclared recovery_only/static025/markov025 (dedup), mọiseed; default48 groups nếu finalhard170. Không xem q010/050test nếu không selected. Reuse mappings/transitions fulltrain đã lưu; test zero fits. Test có lịch sử exposure và H59 được định hướng sau H58; không gọi là independent test mới hoặc kết luận duy nhất do thiếu data.

Báo đủ perfile MAPEmean/std/count, mean/std MAE, macroF1, recallV/UV, balancedaccuracy/SIL, seed variation và all8. So cùngngưỡng static025/markov025, removedV/UV/SIL, Brier trên fixedLOFO train, qualitative score quanh khung đổi và khoảng cách biên. Audit ngữ cảnh bảo toàn V yếu hoặc kéo dài non-V; không chỉ báo trường hợp tốt. Lưu transition counts/proofs/marginals/source/cấu hình/runtime/hash và thất bại. Baseline giữ nếu không đạt gates.

Verifier độc lập recompute scalar Gaussian/mapping H58, transition poolcounts, scalar marginal, static parity H58, inference/pitch, metrics/folds/selection/gates/hash. Không optimizer/native rerun, không claim source GMM optimizer độc lập mới. No Drive/DL/PDF/Jev/prose skill hoặc rerun các vòng cũ; bài segmentation vẫn sau BT2. Lệnh markov_rejection.py precheck/register/train/test; verify_markov_rejection.py train/test; report_markov_rejection.py.
