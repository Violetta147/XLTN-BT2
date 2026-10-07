# H23 — chuyển vòng thử nghiệm sang AMDF

Đăng ký trước đo ngày 07/10/2026. Repository rollback `d13c2f4`. Control của vòng này là AMDF_energy đã sửa tại `009fd2c`, không phải ACF. Notebook gốc, bản Colab và output cũ được giữ nguyên. Chỉ local train bốn file; không đọc test/Drive, không deep learning.

Người dùng chỉ ra các vòng gần đây bỏ qua notebook AMDF. Mục tiêu thứ nhất là đưa kết quả trước/sau AMDF vào một notebook local có source đúng cách chạy. Mục tiêu thí nghiệm H23 là kiểm tra riêng độ dài khung AMDF, không gom bộ lọc và classifier.

## Giả thuyết và registry

Chọn frame length20/25/40ms bằng inner LOFO có thể giảm lỗi thống kê F0 ngoài vòng chọn so với AMDF_energy25ms hiện tại. Giữ hop10ms, raw audio, normalized AMDF trong notebook baseline, range70–400Hz, pathjump0.35/octave0/median1, energy gate bật. Pitch/energy threshold refit từng training subset. Chỉ một biến được mở là frame length. Không dùng F/M để chọn dải F0 hoặc độ dài khung.

Chấm mọi output trên timestamp grid25/10 của control bằng nearest native center trong half-hop cộng tolerance1sample. Ngoài support dự đoán false/F0NaN. Giữ countnative/coverage riêng; không đổi GT hoặc cắt F0 để khớp count. Khi đổi frame, tâm khung và nhãn fit thay đổi; đây là ảnh hưởng geometry cần báo, không coi adapter là ground truth mới.

## Chọn và gate trước đo

Final chọn bằng LOFO4file. Mỗi outer file chọn bằng inner LOFO trên3file khác, refit3 rồi chấm outer. Inner gate: mọi AvgMAPE hữu hạn, macroF1/recallV không giảm quá0.01 và tổng SIL false voiced không tăng quá1 so AMDF25 refit cùng pool. Rank eligible theo AvgMAPE thấp nhất, hòa ID từ điển. AMDF25 luôn là fallback.

Gate cuối so AMDF25 đã sửa: trainAvgMAPE giảm10% tương đối; selectedLOFO và nested giảm5%; nestedF1/recallV giảm không quá0.01; SIL tăng không quá1; không file nestedAvgMAPE tăng quá2 điểm phần trăm; phone_F1 stdMAPE không tăng. Tất cả phải đạt, không promote tự động. Giữ toàn registry/trace/fit/results kể cả fail. Các file đã xem nhiều lần: nested vẫn là thăm dò, không phải corpus xác nhận độc lập.

## Notebook và kiểm tra

Tạo notebook mới `AMDF_LOCAL_TRAIN.ipynb`, không ghi đè bản gốc. Source dùng đường dẫn local và chính hàm AMDF của baseline, không giữ mã mount rồi thay ngầm trong bộ nhớ khi chạy. Notebook tính lại cả AMDF không energy và có energy, baseline và cải tiến, train và fixed LOFO; so saved values trong1e-8, báo riêng protocol. Giải thích dip thấp là tuần hoàn, energy gate và path chọn ứng viên. H23 selection ở runner riêng được gọi từ notebook; có output thực cho các cells. Chỉ train, không có cell đọc test.

Kiểm tra baseline AMDF25 train/LOFO tái lập cũ; counts/std/MAPE/nested contours/nhãn và source hashes bằng verifier độc lập. Registry có3options,48innertraces,24metricrows. Xuất nested PNG/SVG, fixed frame CSV và hình so AMDF trước/sau trong notebook. Không mở grid hoặc hạ gate sau đo. Kết thúc sau vòng này và notebook/audit report; không bắt đầu vô hạn các vòng ACF.

Notebook dùng những cải tiến AMDF đã có, không nhận chúng là kết quả mới của ngày07/10. H23 là thí nghiệm mới duy nhất ở lượt này. Tài liệu về [aligned AMDF](https://www.isca-archive.org/interspeech_2006/rahman06_interspeech.html) là hướng tìm hiểu sau, chưa được cài đặt; không đổi công thức NAMDF hiện tại theo abstract.
