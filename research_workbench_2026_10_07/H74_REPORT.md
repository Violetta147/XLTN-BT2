# H74 — Random Forest chưa vượt cấu hình năng lượng

Ngày 09/10/2026. Giả thuyết là quan hệ phi tuyến giữa năm đặc trưng có thể giúp hơn logistic H73. H74 giữ nguyên đặc trưng, nhãn, F0 pYIN, cửa sổ thật 25 ms/bước 10 ms và threshold xác suất 0,5; chỉ thay bộ phân loại bằng Random Forest. Ba độ sâu 2/4/6, cùng 96 cây, leaf tối thiểu 8 mẫu, sample weight cân bằng tổng mỗi file, seed 74 và n_jobs=1. Không trích lại train, chạy lại pYIN hoặc H73. Rollback eaa8ccf9f0b3091396df9e79d2672028acb3a566.

rf5_depth2: MAPE phone_F1/phone_M1/studio_F1/studio_M1 = 1.389742 / 2.704013 / 2.671108 / 0.544270%; mean 1.827283%, macro F1 0.869619, 2/4 train dưới 2%.

rf5_depth4: MAPE phone_F1/phone_M1/studio_F1/studio_M1 = 1.325242 / 2.847280 / 0.840999 / 1.886347%; mean 1.724967%, macro F1 0.876359, 3/4 train dưới 2%.

rf5_depth6: MAPE phone_F1/phone_M1/studio_F1/studio_M1 = 1.325242 / 2.847280 / 0.840999 / 2.752385%; mean 1.941476%, macro F1 0.878737, 2/4 train dưới 2%.

Cả ba cấu hình đều không đạt MAPE dưới 2% trên toàn bộ bốn train. Kết quả xác nhận mô hình phi tuyến có thay đổi quyết định nhưng chưa giải quyết được mục tiêu thống kê F0. Không suy rằng không có pattern chung hoặc học máy vô dụng từ phép thử này.

energy07: mean 1.305508%, worst 1.955313%, macro F1 0.849625, recall V 0.903908, SIL 1.

rf5_depth2: mean 1.962076%, worst 2.497637%, macro F1 0.851225, recall V 0.896957, SIL 5.

rf5_depth4: mean 1.654170%, worst 2.480928%, macro F1 0.852253, recall V 0.899998, SIL 6.

rf5_depth6: mean 1.654170%, worst 2.480928%, macro F1 0.852253, recall V 0.899998, SIL 6.

Theo minimax worst rồi mean/ID và guard F1/recall V/SIL đã đăng ký, H74 chọn energy07. Giữ nguyên pipeline H71/H72: mean train 1,305508%, mean test 2,196094%, đạt 7/8 file; phone_M2 test 4,422661% chưa đạt. Test H72 được tái sử dụng, không đo những mô hình forest không được chọn trên test. LOFO là chẩn đoán, không yêu cầu mọi fold <2% để chặn test. Đối chứng đã được chọn bằng cả bốn train trong lịch sử, nên không gọi các fold của nó là xác nhận độc lập.

Rà cache train cho thấy pYIN không cấp F0 cho 9/28/3/10 khung có nhãn V của phone_F1/phone_M1/studio_F1/studio_M1; cả các khung đó có ứng viên ACF 25 ms trong cache H50. Điều này chỉ chứng minh ứng viên tồn tại, không chứng minh cao độ ACF đúng. H73/H74 chỉ loại ứng viên pYIN, không thể khôi phục các khung ấy. Ở phone_M1, logistic C1 H73 giữ 218 khung so chuẩn 232, dù macro F1 cải thiện; nhánh chỉ loại khung có thể làm count thiếu thêm. Đây là động cơ cho phép thử phục hồi mới, chưa phải kết quả phục hồi hoặc nhãn F0 chuẩn từng khung.

Precheck ba forest synthetic PASS; prereg f016fde60c7c779edd009cac4440c1eaea903ffa đã commit/push/xác minh remote trước fit BT2. H74 đo 33 forest/3168 cây, 136 metric groups gồm bốn control cached, 64 inner rows và 12 summary rows. Verifier PASS routing scalar, seed/bootstrap và weighted class totals tại mọi node, xác suất/mask/F0, metric, pool, copies/selection và hashes; không refit split optimizer. sklearn 1.8.0/source/binaries được khóa. Nguồn tại H74_ml/experiment.py, verify.py, REGISTRY.json và REGISTRATION.md; đo tại run_train/ với receipt, model/proof JSON, CSV và verification. Kế hoạch notes.txt giữ nguyên; ghi kết quả sau chạy trong run_train/notes.txt.

Không promote, sửa notebook/frozen/WAV/LAB/teacher GT, chọn tham số từ test hoặc route theo tên file. Test đã từng xem trong lịch sử/H72. Không Drive/deep learning/PDF/Jev/GPU/Colab/schedule. Dùng skills scikit-learn và experiment-code. Tài liệu primary [RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html); tham chiếu Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026), [Scientific Agent Skills](https://arxiv.org/abs/2609.00065), DOI 10.48550/arXiv.2609.00065, HTML metadata kiểm ngày 09/10/2026, không extract PDF.
