# H78 — ngữ cảnh bản thu và điều phối mềm

Ngày 09/10/2026. Prereg b2b446344eb4a789d1b7b4fdf3eb2d83eafccb3e đã push và xác minh remote trước train; rollback 3b1b77365d3191faf517fbf872507b2107425787. Kết quả chọn theo held train vẫn là energy07. Giữ pipeline H71/H72, không chạy lại test. Thí nghiệm kiểm tra conditioning/routing, không chứng minh môi trường là nguyên nhân và không dùng deep learning.

Bốn train theo thứ tự phone_F1, phone_M1, studio_F1, studio_M1. Mỗi số sau là Average MAPE của pipeline trên file, không phải MAPE từng khung.

energy07: MAPE 1.955313/0.838965/1.883484/0.544270%, mean 1.305508%, worst 1.955313%, 4/4 file dưới2%. Macro F1 0.849625, recall V 0.903908/UV 0.845241, balanced 0.874575, MAE mean/std 1.239681/0.373099Hz, false_voiced_sil 1. Mean/std/count từng file và confusion counts lưu all_train_metrics.csv.

pooled_C1: MAPE 1.730014/1.437832/1.747907/1.340805%, mean 1.564140%, worst 1.747907%, 4/4 file dưới2%. Macro F1 0.892668, recall V 0.925384/UV 0.913643, balanced 0.919514, MAE mean/std 0.916397/0.247174Hz, false_voiced_sil 1. Mean/std/count từng file và confusion counts lưu all_train_metrics.csv.

contextual_C1: MAPE 1.730014/0.878571/2.546783/1.603642%, mean 1.689753%, worst 2.546783%, 3/4 file dưới2%. Macro F1 0.901933, recall V 0.926409/UV 0.940444, balanced 0.933427, MAE mean/std 0.828667/0.446424Hz, false_voiced_sil 2. Mean/std/count từng file và confusion counts lưu all_train_metrics.csv.

soft_gate_C1: MAPE 1.591450/1.817182/1.978336/1.603642%, mean 1.747652%, worst 1.978336%, 4/4 file dưới2%. Macro F1 0.900473, recall V 0.923750/UV 0.942124, balanced 0.932937, MAE mean/std 0.991236/0.379005Hz, false_voiced_sil 1. Mean/std/count từng file và confusion counts lưu all_train_metrics.csv.

Soft gate học nhãn môi trường từ hai đặc trưng tín hiệu: q20 log RMS tương đối và median tỷ lệ năng lượng tần số cao trong khung năng lượng thấp. Full train nhận đúng4/4 domain nhưng held ba-file chỉ đúng2/4: studio_F1 và studio_M1 bị route thiên phone. Trọng số nhánh studio fulltrain là 0.277907/0.213775/0.836894/0.671424. Trọng số held là 0.444448/0.309917/0.001737/0.366835. Đây là bốn file, không phải bốn môi trường độc lập hoặc kiểm chứng nhân quả. Điểm ngữ cảnh cao tần khác biệt rõ giữa hai file studio, nên không được gọi proxy này là SNR thật hay domain hoàn hảo.

Contextual17 chiều cải thiện phone_M1 nhưng studio_F1 fulltrain2,546783%; held studio_F1 lên15,337774%. Một inner pool contextual dự đoán zero F0 frames, dẫn tới NaN mean/std/MAPE; giữ nguyên failure và loại candidate không hữu hạn khi chọn. V1 verifier lỗi parser vì keep_default_na=False khiến cột số có ô trống trở thành text. Không sửa nguồn v1 hoặc số đo; verify_v2.py chỉ sửa đọc missing numeric, giữ textual fit_pool rỗng. V2 độc lập PASS24 model/context/scaler/gradient/mixture/decoder/88 nhóm mới và48cached,136total/64inner/12summary. Synthetic precheck có warning sqrt trong StandardScaler, raw warning đã lưu; certificates scaler/finite predictions/gradient PASS, không rerun.

24 fits mới gồm4 single-file experts,11 contextual,9 gates; reuse11 pooled C1 và2 domain-pair expert roles. Không pYIN inference hoặc feature extraction mới. Hai nhánh dùng cùng decoder H76 bridge10_edge25, native F0 ưu tiên, energy0,07/probability0,5/ACFstrength0,6. Ngữ cảnh toàn file và decoder dùng tương lai nên offline; acoustic window vẫn25ms/hop10ms. LAB V/UV/SIL và thống kê F0 file không cung cấp F0 ground truth từng khung.

Mục tiêu từng file cảtrain/test<2% vẫn chưa đạt. H72 giữ mean train1,305508%, mean test2,196094%,7/8file; phone_M2test4,422661%. Test đã được xem trong lịch sử nên nghiên cứu tiếp phải ghi exposure; không chọn từ test. Soft gate đạt4/4train nhưng chưa có số test cho gate, chỉ được đánh giá bằng đăng ký frozen evaluation riêng theo mục tiêu người dùng; không hồi tố selection H78.

Người dùng đề xuất kết hợp file rồi để mô hình decompose. H78 là nhánh chuyên biệt có nhãn môi trường; một phép thử kế tiếp có thể bỏ nhãn domain, gom context train và tự phân nhóm. Phân nhóm không đồng nghĩa tách tiếng nói/nhiễu hoặc phân rã phổ; phải gọi đúng cơ chế được triển khai. Không rerun H00–H78 hoặc thay notebook gốc.

Nguồn primary: [StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html) và source runtime1.8.0; [Mixture of Experts](https://arxiv.org/abs/1701.06538) đọc abstract cho khái niệm gate, không full-paper/benchmark claim. Kassis,T., Agarwal,V., He,Y., Patel,D., Brueckner,A.M.(2026), [Scientific Agent Skills](https://arxiv.org/abs/2609.00065), DOI10.48550/arXiv.2609.00065, HTML metadata09/10/2026. Jev không tham gia.
