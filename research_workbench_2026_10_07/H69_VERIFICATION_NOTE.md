# H69 — sửa verifier sau đo, giữ nguyên thất bại

Verifier đã đăng ký dừng ở `studio_M1.wav / F0mean`: cấu hình `pyin25_beta2_38` dự đoán **0 khung hữu thanh**. Mean, std và MAPE tương ứng đều là NaN trong cả phép tính độc lập và CSV đã lưu. `np.isclose` mặc định coi hai NaN là không bằng nhau. Audit độc lập xác nhận bảy trường khác biệt đều chỉ là trường hợp này; ba cấu hình còn lại của studio_M1 khớp.

Giữ nguyên verifier v1, registry, pipeline, mọi NPZ/CSV/receipt và kết luận không đủ điều kiện. V2 chỉ cho phép hai giá trị thiếu khớp nhau khi kiểm tra metric và bản sao trong inner trace; không thay tolerance, không điền số 0, không cho ứng viên NaN vượt điều kiện hữu hạn. Không chạy lại pYIN hoặc dữ liệu BT2.

`results/H69_verifier_v1_failure.json` giữ lỗi v1. Một lần ghi audit JSON bị từ chối vì chứa NaN; không tạo file ở lần đó, bản audit cuối biểu diễn giá trị thiếu bằng văn bản. `verify_pyin25_v2.py` là file mới; phải kiểm tra source/protected/output hash cũ trước khi đọc số đo và xuất `results/H69_verification_v2.json`. Đây là sửa kiểm tra sau đo, không phải verifier v1 đã PASS ngay lần đầu.

Lần kiểm tra v2 đầu khớp cả 16 nhóm metric nhưng dừng ở bản sao inner trace: CSV trống được đọc thành chuỗi rỗng vì `keep_default_na=False`. Sửa v2 nhận trường CSV trống chỉ khi metric độc lập là NaN; các số hữu hạn vẫn so chính xác. Giữ lỗi này trong `results/H69_verifier_v2_initial_failure.json`. Không chạy lại suy luận.

Rà dtype xác nhận trường trống làm cả bảy cột numeric thành chuỗi. Một lần kiểm tra trung gian vẫn dừng ở inner trace; đã ghi trong audit. Cách sửa cuối: đọc ô trống thành NaN riêng cho các cột numeric, giữ `actual_fit_files` là chuỗi rỗng và giữ parse float round-trip. Không đổi dữ liệu hoặc tolerance.
