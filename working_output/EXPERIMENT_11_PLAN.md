# Thí nghiệm 11: median 3 frame cho RMS tương đối trước cổng

- Điểm quay lại: `d07c769`; notebook/cấu hình tích hợp không đổi.
- Bằng chứng: audit gate cho thấy 6 frame LAB V bị cổng loại đều thuộc hai file studio, cùng 50 frame SIL và 3 UV bị loại trên bốn fold training.
- Giả thuyết: median filter cửa sổ 3 frame trên relative RMS trước khi áp cổng sẽ khôi phục ít nhất 3/6 frame V bị loại ban đầu, vì một số frame V thấp năng lượng có thể là dip ngắn; số SIL false voiced tăng không quá 3.
- Thay đổi duy nhất: thay `relative_rms[t]` bằng median của ba frame liên tiếp (centered; biên dùng lặp giá trị đầu/cuối) khi đánh giá cổng. Không đổi frame, pitch score, ngưỡng pitch/energy đã fit, hay F0 estimator.
- Đánh giá: bốn fold LOFO trên `TinHieuHuanLuyen`, cùng ngưỡng riêng từng fold từ thí nghiệm 08. Báo macro F1, recall V/UV, balanced accuracy, F0mean/F0std MAE, NumF0, FP_SIL và số V/SIL được khôi phục. Đối chiếu trực tiếp cấu hình gate hiện tại.
- Tiêu chí giữ ứng viên: khôi phục ≥3 LAB V; macro F1 và BA không giảm quá 0.01; FP_SIL tăng không quá 3; F0mean/F0std MAE không tăng quá 0.5/2 Hz tương ứng. Nếu không đạt, ghi kết quả thất bại và giữ cấu hình hiện tại.
- Không dùng TEST; đây là validation exploratory trên bốn file training và không gọi độc lập.
