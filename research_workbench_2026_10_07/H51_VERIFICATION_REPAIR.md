# Sửa bộ kiểm tra H51, giữ nguyên phép đo

Lượt chạy `verify_voicing_matrix.py train` đã dừng với TypeError ở cột permutation `repeat`: `row.repeat` trả về method của pandas.Series, không phải giá trị cột. Lỗi này xảy ra sau các bước refit/đối chiếu fixed, inner, nested và noise; lượt đó **chưa PASS** và không có receipt thành công.

Bản source đã đăng ký, registry và mọi output đo giữ nguyên. `verify_voicing_matrix_v2.py` chỉ đổi `int(row.repeat)` thành `int(row['repeat'])` và thêm SHA256 của chính verifier vào receipt. Không đổi mô hình, recipe, seed, nhãn, metric hoặc lựa chọn; không đo lại H51. Biên dịch source v2 đạt trước khi chạy. V2 phải thực hiện lại đầy đủ mọi kiểm tra, không bỏ các refits để tiết kiệm thời gian.

Lệnh thay thế: `verify_voicing_matrix_v2.py train`, sau đó `external`. Các hash đăng ký vẫn kiểm bản source v1 được giữ nguyên; receipt thêm hash v2 để định danh bộ kiểm tra thực tế.
