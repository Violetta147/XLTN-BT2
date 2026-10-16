# Thí nghiệm 16: zero-crossing gate cho rescue F0 low-energy

- Điểm quay lại: AMDF+energy+median5 tại `84eba83`.
- Bằng chứng/hypothesis: rescue theo AMDF dip ở thí nghiệm 15 phục hồi nhiều frame không phải V, đặc biệt ở studio, nên tăng false voiced SIL/UV. Zero-crossing rate (ZCR) là đặc trưng tín hiệu cổ điển có thể loại bớt các frame low-energy không tuần hoàn trước khi rescue.
- Biến duy nhất: thêm điều kiện ZCR ≤ `T_zcr` cho nhánh rescue; ngưỡng fit trong mỗi fold từ ba file training bằng balanced accuracy V-vs-(UV/SIL) trên frame low-energy và score dưới `T_pitch`; hòa chọn ngưỡng thấp hơn. Không thay Gaussian pitch threshold, energy threshold, frame 25 ms/hop 10 ms, estimator hay median5.
- Đánh giá: 4-fold LOFO training, fit `T_zcr` chỉ từ ba file còn lại. So với AMDF+energy+median5 trên cùng fold: macro F1, BA, recall V/UV, F0mean/F0std MAE, NumF0 và FP_SIL. Không dùng TEST.
- Cổng đạt: recall V tăng ít nhất 0.02; macro F1 và BA mỗi metric không giảm quá 0.01; F0mean và F0std MAE không tăng quá 0.25 Hz; FP_SIL tổng ≤3. Nếu trượt cổng, lưu kết quả và không tích hợp.
