# H18/H19 — tuning bộ lọc, độ dài khung, bước nhảy và logistic

Đăng ký ngày 07/10/2026 trước khi đo các cấu hình mới. Điểm quay lại repository: eceb094; champion frozen accepted ACF từ 009fd2c. Notebook gốc không sửa. Train local bốn file, không đọc test/Drive, không deep learning.

Người dùng yêu cầu mở frame/hop, thử high-pass/low-pass/band-pass, logistic regression và tuning; cho phép Gemini đề xuất. Đây là hai câu hỏi về quy trình chọn cấu hình joint, không phải chứng minh riêng từng biến gây cải thiện.

## H18: geometry/filter với detector ACF

Giả thuyết: chọn từ grid bộ lọc và độ phân giải thời gian trên inner train có thể giảm lỗi file-stat và giữ chất lượng V/UV/SIL trên outer held file.

- Filters: raw; Butterworth SOS N=2 causal high-pass30/60Hz, low-pass800/1500Hz, band-pass low30/60 × high800/1500Hz. BP có order thực4. Initial rest, filter liên tục cả file, không reset mỗi khung; không bù delay dùng GT.
- Frame20/25/40ms × hop5/10/20ms. Tổng81 cấu hình. Cutoffs/frame/hop thực trong registry JSON, không mở rộng sau xem điểm.
- Giữ range70–400, pathjump.35/octave.03/median3 và rule threshold hiện có. RMS lấy raw cùng native frame; filtering chỉ pitch features. Pitch/RMS threshold refit trên native training fold.
- Có raw25/10 làm fallback/control; phải tái lập features và baseline metrics trong tolerance1e-8.

## H19: logistic trên cùng grid, tuning C

Giả thuyết riêng: thay rule voiced bằng logistic ACFscore+relativeRMS và chọn regularization C có thể cải thiện quy trình H18/fixedACF.

Grid H18 × C=.1/1/10, threshold score=.5, giữ energy gate. Có accepted raw25/10 fallback, tổng244 options. StandardScaler và class weights cân bằng file/V-UV, coefficients chỉ fit training subset. Không thêm ZCR hoặc spectral flatness ở vòng này. H16 C1 fixed là đối chiếu thứ cấp; không dùng điểm H18 để thu hẹp grid H19.

## Chấm khi hop thay đổi

Count native thay theo hop và không thể so trực tiếp với F0num 3GT có protocol chưa rõ. Cả hai vòng chấm output trên cùng timestamp grid của baseline25/10. Ghép nearest native center, tie chọn center sớm; chỉ nhận trong half-hop cộng tolerance1sample. Ngoài support: pred false, F0 NaN. Không nội suy qua UV, không thêm/cắt F0 để khớp count GT. Native frames/count/projection coverage lưu riêng.

Đây là adapter chấm thống kê để so fair hơn, không tạo ground truth từng khung. Frame/hop thuật toán thay đổi thật; grid chấm là thước đo chung. Phase delay/transient và median3 có span2hop phải báo. Không gọi grid/nativecount là F0 reference.

## Quy trình chọn trước đo

Final chọn bằng LOFO4file. Mỗi outer held file chọn bằng inner LOFO trên other3 (fit2/chấm1), refit other3 và chấm outer. F/M hoặc phone/studio không được dùng để chọn F0 range cho held file.

Inner ranking: chỉ cấu hình có tất cả AvgMAPE hữu hạn; macroF1/recallV không giảm quá.01 và tổng SILfalsevoiced không tăng quá1 so control cùng inner pool. Trong số đạt, chọn AvgMAPE trung bình file thấp nhất; hòa chọn ID từ điển. Baseline luôn có trong registry. Outer held không tham gia lựa chọn/fit/scaler.

Gate cuối so accepted: trainAvgMAPE giảm10% tương đối; selectedLOFO và nested giảm5%; nestedmacroF1/recallV giảm không quá.01; nestedSIL tăng không quá1; không file nestedMAPE tăng trên2pp; phone_F1nestedstdMAPE không tăng. Tất cả gate phải đạt, không promote tự động; finite-stat coverage phải đầy đủ. Lưu toàn grid/inner fits kể cả fail. Nested không xóa explorationhistory trên bốn file nhỏ.

## H20: mô tả nhóm và stress sau freeze

Chỉ dùng outer choices đã chốt từ clean train của từng family. Stress white/pink/brown SNR20/10/0dB, seeds0/1/2 của H15 perturbation; clipping symmetric tại .8/.5/.25 × peak raw. Tổng120 cases, không tune lại. Báo seed-mean trong file rồi nhóm file; noise là mô phỏng, không thêm speaker.

F/M và phone/studio là tên file: mỗi ô chỉ1file, mỗi nhóm2file. So mean/std/countGT, recallV/UV, F1, SIL, boundary. Báo clippingfraction samples vàframes từ audio trước filtering, spectral effect và trade-off; raw native min/max chưa chắc đại diện analog clipping. Không dùng giới làm classifier hoặc phán đoán người nói.

Nguồn API: [SciPy butter](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.butter.html), [sosfilt](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.sosfilt.html). Phiên bản runtime thực lưu riêng.

Giới hạn dừng: hoàn thành registry hai vòng và120case stress; không mở grid theo test hoặc loop vô hạn. Nếu lỗi code/validation: giữ log lỗi, sửa harness và kiểm tra lại, không thay gate dựa trên điểm đã thấy. MCP lỗi không retry tự động.
