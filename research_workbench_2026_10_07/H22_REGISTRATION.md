# H22 — thêm ZCR vào logistic, giữ C1

Đăng ký trước đo ngày07/10/2026. Repository rollback `dc87b79`; champion accepted ACF `009fd2c`. Chỉ local train4file; không test/Drive/deep learning. Giữ toàn bộ notebook và H18–H21.

Giả thuyết: thêm tần suất đổi dấu của tín hiệu (ZCR, zero crossing rate) vào logistic2D có thể giúp phân biệt V/UV, giảm lỗi thống kê F0 mà không đổi C hoặc cách lấy cao độ.

## Câu hỏi và can thiệp

Registry3options: accepted raw ACF; logistic2D gồm ACFscore + relativeRMS; logistic3D thêm ZCR. Hai logistic cùng C=1, threshold probability0.5, StandardScaler, trọng số cân bằng file và V/UV như H16/H19. Không tune C, threshold, filter hoặc geometry trong vòng này. Đây là kiểm tra đóng góp đặc trưng, không search quanh giá trị thắng.

ZCR lấy từ raw khung sau trừ mean: `mean(signbit(x[1:]) != signbit(x[:-1])) × fs`, đơn vị crossings/s. Zero có signbit=false, được tính theo công thức này; khung hằng số sau trừ mean cho0. Không gọi ZCR là F0 hoặc mặc định ZCR của mọi noise đều cao. Chuẩn hóa theo fs để phone16k/studio44.1k cùng đơn vị; không tái dùng fraction ZCR phụ thuộc fs của hình audit cũ.

Giữ frame25/hop10, raw ACF, range70–400, pathjump0.35/octave0.03/median3 và energy rule. Native grid trùng grid chấm. StandardScaler/coefficients chỉ fit training subset. SIL không thuộc hai lớp dùng để fit logistic; energy gate vẫn áp dụng cho SIL. Không dùng nhãn/file-stat của held file trong inference. Mean/RMS/ZCR mỗi khung và q95 mỗi file là preprocessing như control; không khẳng định đây là streaming detector.

## Lựa chọn và chấm

Primary: final chọn bằng LOFO4file; mỗi outer file innerLOFO trên other3, refit3 và chấm outer. Inner eligibility: toàn AvgMAPE hữu hạn, macroF1/recallV không giảm quá0.01, tổng SIL tăng không quá1 so accepted refit cùng pool. Rank eligible theo mean file AvgMAPE; hòa theo ID. Raw fallback luôn có.

Gate cuối so accepted: train AvgMAPE giảm10% tương đối; selectedLOFO và nested giảm5%; nestedF1/recallV giảm không quá0.01; SIL tăng không quá1; không file AvgMAPE xấu thêm quá2 điểm phần trăm; phone_F1 stdMAPE không tăng. Không promote tự động. Finite coverage và mọi gate phải đạt.

Secondary, đã định trước: fixed LOFO logistic3D so logistic2D để cô lập thêm ZCR; báo từng file, AvgMAPE/F1/recallV/SIL. Đây không phải kết quả nested của việc chọn3options. Logistic2D phải khớp H16 trong1e-8. Không chọn giữa primary/secondary để chỉ báo điểm đẹp.

GT chỉ thống kê mean/std/count mỗi file và nhãn đoạn V/UV/SIL; không F0reference theo timestamp. AvgMAPE không là pitch error từng khung. Registry dựa trên lịch sử bốn file đã xem và ý tưởng Gemini nên nested vẫn là exploration, không held-out corpus độc lập.

## Kiểm tra và giới hạn dừng

Kiểm tra ZCR bằng số đổi dấu biết trước, DC/gain invariance, raw ACF feature identity; baseline và logistic2D tái lập metric cũ. Đối chiếu contour stats/count/labels/hashes, held-file exclusions, scaler/coefficients dimension và lựa chọn từ inner traces. Xuất nested và fixed-control figures PNG/SVG kèm CSV/sourcehash. Hoàn thành registry3options rồi kiểm tra/báo cáo; không mở grid theo kết quả hoặc chạy noise trong vòng này.

Lệnh: `python research_workbench_2026_10_07/zcr_logistic.py register`, `check`, `H22`. API [scikit-learn LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html); runtime dùng môi trường local đã có, phiên bản ghi JSON, không cài thêm để đuổi theo docs stable.
