# H50 — khôi phục hữu thanh: chưa cải thiện MAPE

Prereg source/registry `2a4524f79c7b2a561a6ac4d8dd1a2403d9cdfb34` đã push/remoteverify trước đo. Chỉ bốn train, không test/KEELE. Verifier PASS 1.291 khung PCM/fullFFT/DCT/directACF, 40 refits, 100 metric groups, exclusion/selection/hash và GMM label poisoning. Không native calls mới, không sửa original/frozen/LAB.

| Fixed LOFO option | Mean Average MAPE % | Mean macro F1 | Mean recall V | V khôi phục/file | UV khôi phục/file | SIL khôi phục/file |
| --- | --- | --- | --- | --- | --- | --- |
| hard170 | 1.124932 | 0.893977 | 0.929270 | 0 | 0 | 0 |
| logistic base4 | 8.943603 | 0.904404 | 0.963592 | 4.75 | 3 | .25 |
| logistic +MFCC | 8.736663 | 0.909073 | 0.963194 | 4.75 | 2.25 | .25 |
| GMM base4 | 2.470608 | 0.896497 | 0.934987 | .75 | .25 | 0 |
| GMM +MFCC | 10.440779 | 0.908091 | 0.955651 | 3.5 | 1.25 | .5 |

Final chọn hard170; outer phone_M1 chọn GMM base4, ba outer khác hard170. Nested không vượt tám gate hoặc target từng file<2. Không promote. Fixed là kiểm cấu hình riêng giữ file ngoài fit; không thay thế nested selection. Bốn train đã dùng nhiều vòng nên mọi kết quả vẫn exploratory.

MFCC thêm thông tin phổ có thể giảm một số FP của logistic và tăng F1; không bảo đảm khớp std/count. GMM fit không đọc LAB, nghĩa cụm dùng mean periodicity; validation chọn pipeline vẫn dùng nhãn/3GT. Unsupervised không có nghĩa hoàn toàn không cần đánh giá có nhãn. Khung mixed tại biên được lưu overlap/majority, không thay nhãn tâm để giảm lỗi. Cần đọc các thành phần MAPE và recovered V/UV/SIL cùng nhau; LAB không phải per-frame F0 GT.

Lỗi strongest-peak trên tone200Hz được bắt trước đo, sửa earliest peak>=.93max và giữ lịch sử trong registration. Không gọi mọi khung recovered là cao độ đã sửa đúng.

Nguồn: [H50 registration](H50_REGISTRATION.md), [metrics](results/H50_metrics.csv), [fixed options](results/H50_fixed_lofo.csv), [contours](results/H50_contours.csv), [fit parameters](results/H50_fits.json), [nhãn theo độ phủ cửa sổ](results/H50_label_overlap.csv), [verification](results/H50_verification.json). API GMM/MFCC và giới hạn triển khai được ghi trong registration. Ma trận/đa seed/robustness mở rộng thuộc vòng mới; chưa được đo trong H50.
