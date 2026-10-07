# Diễn giải cơ chế và lỗi H51

Cấu hình final là gmm_PE. Kết quả fixed LOFO của nó có bằng control hard170 ở mọi file và seed không: **True**. Nếu bằng nhau, lựa chọn này là hòa điểm theo ID, không phải mô hình đã cải thiện pipeline. Các outer folds vẫn phải đánh giá recipe riêng do bước chọn bên trong quyết định.

Bảng dưới phân rã những khung mới của cấu hình được chọn ở từng outer fold. Chỉ trình bày seed 11 cho gọn; CSV lưu đủ ba seed. V/UV/SIL là nhãn tại tâm khung, không xác nhận F0 của khung đó.

| file | recipe_id | added_frames | added_v | added_non_v | old_count | new_count | old_std | new_std | added_mean | between_variance_hz2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phone_F1.wav | gmm_PE | 0 | 0 | 0 | 147 | 147 | 20.5815 | 20.5815 | nan | 0 |
| phone_M1.wav | gmm_PEZS | 1 | 1 | 0 | 233 | 234 | 16.9527 | 18.5771 | 240.172 | 58.9445 |
| studio_F1.wav | gmm_PES | 0 | 0 | 0 | 123 | 123 | 36.8685 | 36.8685 | nan | 0 |
| studio_M1.wav | gmm_PES | 1 | 1 | 0 | 85 | 86 | 25.8575 | 25.8492 | 91.6324 | 7.34853 |

Chi tiết khung mới và F0 ước lượng gần nhất của baseline:

| file | recipe_id | time_s | center_label | boundary | added_estimated_f0_hz | periodicity | relative_rms | zcr_per_second | high_frequency_ratio | nearest_baseline_time_s | nearest_baseline_estimated_f0_hz | distance_ms | per_frame_pitch_truth_available |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phone_M1.wav | gmm_PEZS | 1.9925 | v | False | 240.172 | 0.75991 | 0.29661 | 1122.81 | 0.00518763 | 1.9625 | 98.1114 | 30 | False |
| studio_M1.wav | gmm_PES | 1.70249 | v | False | 91.6324 | 0.753645 | 0.585896 | 881.199 | 0.0749678 | 1.69249 | 91.4556 | 10 | False |

Khi thêm một nhóm F0 có mean xa mean cũ, phương sai tăng qua thành phần giữa hai nhóm: w0×w1×(mean0−mean1)². Đã kiểm độc lập rằng phương sai trong nhóm cộng thành phần này khớp phương sai toàn bộ output. Vì vậy một khung có nhãn V đúng vẫn có thể làm F0std MAPE tăng mạnh nếu cao độ ước lượng của nó lệch xa phần còn lại. Cần tách hai câu hỏi: khung có hữu thanh không, và cao độ được ước lượng có đúng không.

Ma trận H51 cô lập các đầu vào/mô hình phân loại nhưng dùng chung ACF để lấy pitch của khung khôi phục. Nó chưa cô lập được chất lượng pitch này với quyết định khôi phục. Kết quả thất bại không chứng minh ML, MFCC hoặc miền tần số nói chung không hữu ích. Các estimated pitch gần nhau cũng chưa thay thế ground truth.

LAB và F0num đo những thứ khác nhau:

| file | center_v_frames | reference_F0num | count_mape_if_exact_v_and_all_finite | average_mape_contribution_if_other_components_zero |
| --- | --- | --- | --- | --- |
| phone_F1.wav | 153 | 148 | 3.37838 | 1.12613 |
| phone_M1.wav | 244 | 232 | 5.17241 | 1.72414 |
| studio_F1.wav | 123 | 127 | 3.14961 | 1.04987 |
| studio_M1.wav | 94 | 82 | 14.6341 | 4.87805 |

Ví dụ studio_M1 có 94 khung tâm V, F0num chuẩn là 82. Nếu phát F0 hữu hạn đúng ở mọi tâm V và không phát ngoài V, count MAPE sẽ là 14,63%; riêng phần count đã đóng góp 4,88 điểm phần trăm vào Average MAPE. Đây là kết quả có điều kiện của giả thuyết trên, không phải cận dưới cho mọi mô hình. Mô hình có thể không phát F0 ở một số khung V. V theo đoạn ngữ âm cũng không nhất thiết đồng nghĩa mọi cửa sổ đều có F0 ước lượng hợp lệ.

Chưa biết cách thầy tạo mean/std/count: độ dài, độ dịch và tâm khung, điều kiện giữ F0, xử lý biên, engine và ngưỡng. Không đủ bằng chứng kết luận thầy ghi nhầm hoặc sửa sai. Không đổi LAB để đạt điểm. Cần cùng lúc giữ các lỗi MAPE, F1/recall và SIL để thấy sự đánh đổi.

Phạm vi đã chạy và những hướng chưa thuộc ma trận này được ghi trong EXPERIMENT_COVERAGE.md. Lỗi parser của verifier v1 và bản kiểm tra v2 nằm ở H51_VERIFICATION_REPAIR.md; mọi source đăng ký và output đo được giữ nguyên.
