# H75 — phục hồi khung V chưa đủ để phục hồi F0 đúng

Ngày 09/10/2026. H75 học logistic từ mọi khung có ứng viên pYIN hoặc ACF25, không chỉ các khung native V của H73. Giả thuyết là khôi phục coverage bị thiếu có thể giúp count và các thống kê F0. Năm đặc trưng giữ nguyên, StandardScaler trong Pipeline, C0,1/1/10, nhãn V so UV/SIL, tổng sample weight mỗi file bằng nhau. Quyết định >=0,5, log energy >=log(0,07), ưu tiên native pYIN, ACF25 fallback phải có strength >=0,6. Cửa sổ tín hiệu thật 25 ms/bước 10 ms, không trích lại train hoặc chạy lại native pYIN/H50/H73. Rollback c6b9023a7609c6ffe5745d8da811f42fdd388f4a.

recover5_C0.1: MAPE phone_F1/phone_M1/studio_F1/studio_M1 = 2.416904 / 10.833236 / 1.447456 / 2.569209%; mean 4.316702%, macro F1 0.891520, recall V 0.930704, 1/4 train dưới 2%.

recover5_C1: MAPE phone_F1/phone_M1/studio_F1/studio_M1 = 2.416904 / 11.032951 / 1.447456 / 2.777443%; mean 4.418689%, macro F1 0.889530, recall V 0.930704, 1/4 train dưới 2%.

recover5_C10: MAPE phone_F1/phone_M1/studio_F1/studio_M1 = 2.416904 / 11.032951 / 1.447456 / 2.777443%; mean 4.418689%, macro F1 0.889530, recall V 0.930704, 1/4 train dưới 2%.

H75 phục hồi 4/12/2/6 khung trên phone_F1/phone_M1/studio_F1/studio_M1, trong đó nhãn V là 3/12/1/5 và UV là 1/0/1/1; không thêm SIL. Các C cho cùng số khung phục hồi ở full train. Ở phone_M1, cả 12 khung phục hồi đều mang nhãn V, nhưng std ước lượng tăng từ 17,097475 Hz của energy07 lên 22,027265 Hz ở C1, so chuẩn16,8 Hz. MAPE tăng từ0,838965% lên11,032951%, dù count229 gần chuẩn232 và macro F1 tốt hơn. Đây là bằng chứng rõ cho sự khác nhau giữa phục hồi nhãn hữu thanh và chọn cao độ hợp lý; chưa xác định từng cao độ ACF nào sai vì thiếu F0 chuẩn từng khung. Không gọi 12 khung đó là12 F0 đã sửa đúng. Muốn nghiên cứu tiếp phải xử lý độ tin cậy của ứng viên F0, không chỉ tăng F1.

energy07: mean 1.305508%, worst 1.955313%, macro F1 0.849625, recall V 0.903908, SIL 1.

recover5_C0.1: mean 4.745442%, worst 12.436917%, macro F1 0.889042, recall V 0.925581, SIL 1.

recover5_C1: mean 4.797501%, worst 12.436917%, macro F1 0.885734, recall V 0.925581, SIL 1.

recover5_C10: mean 4.774844%, worst 12.457573%, macro F1 0.889385, recall V 0.926605, SIL 1.

Theo minimax/guard đã đăng ký, H75 giữ energy07. Mean train1,305508%, mean test2,196094%, đạt7/8 file; phone_M2 test4,422661% chưa đạt. Tái sử dụng H72 test, không đo các cấu hình recovery chưa được chọn. Không chọn tham số bằng test. Test đã tiếp xúc lịch sử/H72, đối chứng đã chọn bằng toàn bộ train, báo giới hạn. LOFO là chẩn đoán, không đòi mọi fold<2% để được đo test.

Precheck ba logistic synthetic và boundary native preference/energy/periodicity/missing candidate PASS. Prereg0c1b9efac04b17d4724c553055d8ae657bfceb0c đã commit/push/xác minh trước fit. H75 đo33 fits,136 nhóm,64 inner và12 summary; verifier PASS weighted scaler/gradient/mask/F0 branch/metric/pool/copies/selection và hashes, không refit optimizer hoặc pYIN. Nguồn/kế hoạch/registry ở H75_ml, artifacts ở run_train. Kế hoạch notes.txt bất biến; ghi sau đo trong run_train/notes.txt. Không promote hoặc sửa notebook/frozen/WAV/LAB/teacher GT. Không Drive/deep learning/PDF/Jev/GPU/Colab/schedule.

Dùng scikit-learn và experiment-code, cùng quy trình experimental-design. Tham chiếu Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M.(2026), [Scientific Agent Skills](https://arxiv.org/abs/2609.00065), DOI10.48550/arXiv.2609.00065; HTML metadata kiểm09/10/2026, không extract PDF. Runtime sklearn1.8.0/source được giữ, không nâng thư viện.
