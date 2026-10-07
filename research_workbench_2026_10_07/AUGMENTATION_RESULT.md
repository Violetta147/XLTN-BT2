# Augmentation có giúp BT2 không?

So H45 clean-fit với H46 augmented-fit trên cùng bốn WAV train gốc được giữ riêng theo origin. Mỗi origin có ba noise variants; cả bản gốc và biến thể đều bị loại khỏi fit khi origin là held. K và memberbank giữ nguyên, chỉ thêm augmentation vào ranking fit pool.

| File | Clean-fit MAPE (%) | Augmented-fit MAPE (%) | Delta (pp) |
| --- | ---: | ---: | ---: |
| phone_F1.wav | 0.340080 | 0.340080 | 0.000000 |
| phone_M1.wav | 0.776151 | 0.776151 | 0.000000 |
| studio_F1.wav | 1.473576 | 1.473576 | 0.000000 |
| studio_M1.wav | 2.225623 | 2.225623 | 0.000000 |

Mean Average MAPE H45: 1.203857%; H46: 1.203857%. Worst H45: 2.225623%; H46: 2.225623%.

Mục tiêu mỗi nested file≤2% H46: False. Tám gate H46: True.

Đã sinh 12 WAV từ 4 file gốc, với 12 lần gọi Praat mới. Vẫn chỉ có bốn nhóm nguồn; chưa có thêm người đọc hoặc câu nói mới, cũng chưa xác minh tính độc lập giữa các bản thu gốc. Dùng nhiễu trắng 30/20 dB và nhiễu hồng 20 dB với seed cố định; giữ tần số lấy mẫu và thời lượng, không đổi cao độ, tốc độ hoặc cắt đỉnh.

Nhãn V/UV/SIL và F0mean/std/count kế thừa được xem là latent targets của speech ban đầu dưới noise. Chưa có ground truth pitch từng khung mới; không gọi bản augment là dữ liệu chuẩn được giảng viên xác nhận. SNR ở đây so toàn waveform gốc với noise thêm, không phải SNR speech sạch.

Chỉ augmentation train; không mở test, không chỉnh reference/frozen/original, không đổi threshold/grid/gate sauđo. Nested vẫnexploratory vì nhiều vòng trên4train. Augmentation có thể kiểmtra độbền với biến đổi đã biết, không bù được người nói/nội dung/phiên thu mới.

Đọc H46_REPORT.md/H46_REGISTRATION.md và results/H46_augmentation_manifest.json. Các componentMAPE/MAE/count/F1/BA/recall/SIL trước/sau giữ tại results/H46_clean_vs_augmented_fit.csv.
