# Vì sao H40 chọn control dù YAAPT cải thiện phone?

Minimax là giảm lỗi lớn nhất trong những file được phép chọn. Option phải qua điều kiện V/UV/SIL trước khi xếp hạng, theo đúng prereg. Đây là đọc lại trace đã lưu, không thay gate sau khi xem kết quả.

## Selection trên cả bốn file train

| outer_held | option_id | selection_files | mean_mape | worst_mape | macro_f1 | recall_v | SIL | control_SIL | finite_ok | F1_ok | recall_ok | SIL_ok | eligible | chosen |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final | praat7_filtered_v0.45 | phone_F1.wav\|phone_M1.wav\|studio_F1.wav\|studio_M1.wav | 2.15699 | 2.76986 | 0.879377 | 0.908626 | 0 | 0 | True | True | True | True | True | True |
| final | yaapt_f25 | phone_F1.wav\|phone_M1.wav\|studio_F1.wav\|studio_M1.wav | 2.9221 | 6.33433 | 0.912118 | 0.940104 | 1 | 0 | True | True | True | True | True | False |
| final | yaapt_f35 | phone_F1.wav\|phone_M1.wav\|studio_F1.wav\|studio_M1.wav | 3.57777 | 8.66448 | 0.8915 | 0.942569 | 2 | 0 | True | True | True | False | False | False |
| final | yaapt_f45 | phone_F1.wav\|phone_M1.wav\|studio_F1.wav\|studio_M1.wav | 4.41368 | 10.7436 | 0.894007 | 0.956854 | 4 | 0 | True | True | True | False | False | False |

YAAPT25 giảm lỗi hai phonefiles nhưng worst6.334329% ởstudioM1 lớn hơn control2.769856%, nên không chọn. Không dùng best từng file rồi ghép thành một bảng như thể một pipeline chung.

## Khi giữ riêng studio_M1

| option_id | outer_held | selection_files | mean_mape | worst_mape | macro_f1 | recall_v | SIL | control_SIL | finite_ok | F1_ok | recall_ok | SIL_ok | eligible | chosen |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| praat7_filtered_v0.45 | studio_M1.wav | phone_F1.wav\|phone_M1.wav\|studio_F1.wav | 2.21458 | 2.76986 | 0.906023 | 0.927814 | 0 | 0 | True | True | True | True | True | True |
| yaapt_f25 | studio_M1.wav | phone_F1.wav\|phone_M1.wav\|studio_F1.wav | 1.78469 | 3.15082 | 0.918294 | 0.944962 | 1 | 0 | True | True | True | True | True | False |
| yaapt_f35 | studio_M1.wav | phone_F1.wav\|phone_M1.wav\|studio_F1.wav | 1.8822 | 2.04954 | 0.909403 | 0.948248 | 2 | 0 | True | True | True | False | False | False |
| yaapt_f45 | studio_M1.wav | phone_F1.wav\|phone_M1.wav\|studio_F1.wav | 2.30371 | 2.66794 | 0.914358 | 0.963748 | 3 | 0 | True | True | True | False | False | False |

Trong ba file còn lại, YAAPT35 cóworst2.049538% thấp hơn control2.769856%. Nhưng tổngfalse_voiced_sil=2 vượt control0+1; option bị loại trước xếp hạng. YAAPT45 cũng vượtSIL, YAAPT25worst3.150820% lớn hơncontrol. Vì vậy fold này vẫnchọncontrol, không dùng heldstudioM1 để quyết định.

Đây là đánh đổi thật của gate đăng ký, không dấu hiệu code bỏ qua YAAPT. Điều chỉnh điều kiện hoặc thêm cổng silence từ signal cần giả thuyết/grid/gate mới trước đo; không sửaH40 để choPASS. Unknown groundtruth từngkhung vẫngiữ.
