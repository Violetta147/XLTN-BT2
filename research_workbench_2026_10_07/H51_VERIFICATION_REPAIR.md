# Sửa bộ kiểm tra H51, giữ nguyên phép đo

Lượt chạy `verify_voicing_matrix.py train` đã dừng với TypeError ở cột permutation `repeat`: `row.repeat` trả về method của pandas.Series, không phải giá trị cột. Lỗi này xảy ra sau các bước refit/đối chiếu fixed, inner, nested và noise; lượt đó **chưa PASS** và không có receipt thành công.

Bản source đã đăng ký, registry và mọi output đo giữ nguyên. `verify_voicing_matrix_v2.py` chỉ đổi `int(row.repeat)` thành `int(row['repeat'])` và thêm SHA256 của chính verifier vào receipt. Không đổi mô hình, recipe, seed, nhãn, metric hoặc lựa chọn; không đo lại H51. Biên dịch source v2 đạt trước khi chạy. V2 phải thực hiện lại đầy đủ mọi kiểm tra, không bỏ các refits để tiết kiệm thời gian.

Lệnh thay thế: `verify_voicing_matrix_v2.py train`, sau đó `external`. Các hash đăng ký vẫn kiểm bản source v1 được giữ nguyên; receipt thêm hash v2 để định danh bộ kiểm tra thực tế.

V2 train đã PASS đủ 2.793 refits/10.668 metric groups/3.873 noisy PCM feature frames. V2 external đã kiểm tra các test rows nhưng dừng khi tính features KEELE: `StopIteration` tại earliest peak >=.93max khi mọi local peak âm. Pipeline gốc đã coi trường hợp max<=0 là không có pitch; helper độc lập thiếu điều kiện này. Không có external receipt PASS từ v2.

V3 external dùng `verify_voicing_features_v2.py`: cùng fullFFT/directDCT/directACF và independent metrics, chỉ thêm điều kiện max peak>0 trước chọn chu kỳ. Source H50/H51 đã đăng ký và measurements tiếp tục giữ nguyên. V3 receipt ghi SHA256 của verifier lẫn helper. V2 train receipt vẫn hợp lệ cho các khung đã kiểm; external được kiểm lại đầy đủ bằng v3, không bỏ corpus hay âm thầm thay NaN bằng F0. Lệnh cuối: `verify_voicing_matrix_v2.py train`, `verify_voicing_matrix_v3.py external`.
