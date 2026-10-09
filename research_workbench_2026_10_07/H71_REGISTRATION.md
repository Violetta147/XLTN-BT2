# H71 — khảo sát ngưỡng năng lượng mịn từ cache H70

Đăng ký ngày 09/10/2026, rollback `92956e9e26c012888f61cf05cde62f27e0e9bab6`. H70 đã hoàn tất và được lưu/push. Ngưỡng 0,04 giữ studio_F1 tốt nhưng phone_F1 còn trên 2%; ngưỡng 0,08 giúp ba file dưới 2% nhưng studio_F1 lên 2,497637%. Giả thuyết mới là một ngưỡng trung gian thống nhất có thể giữ thêm khung studio mà vẫn loại các khung dư ở phone. Không thử trước điểm trung gian rồi đăng ký sau.

Chỉ khảo sát tham số của bước lọc đã định nghĩa. Dùng nguyên cache F0 pYIN H69 `(2,8)` và RMS/p95 của H70, không chạy pYIN, không tính lại năng lượng để đo và không sửa source H70. Grid cố định gồm các đối chứng 0 / 0,04 / 0,08 đã lưu và bảy điểm mới: 0,045 / 0,05 / 0,055 / 0,06 / 0,065 / 0,07 / 0,075. Giữ ngưỡng >=, mask pYIN AND energy; khung còn lại giữ nguyên F0, khung loại nhận NaN. Không ghép theo filename, không ngưỡng thích nghi theo ground truth hoặc chọn trên test.

Cửa sổ tín hiệu vẫn thực sự 25 ms, bước 10 ms, không padding/resampling, số mẫu theo Python round. RMS sau trừ mean khung, chia p95 tuyến tính của chính file (floor1e-12), không dùng nhãn; đây là chuẩn hóa toàn file không streaming. Mọi cache H69/H70, source/runtime/dữ liệu/GT/notebook được kiểm hash và bảo vệ trong registry.

Có 44 nhóm metric: 16 nhóm đối chứng đã lưu (hard170, pYIN raw, q0,04 và q0,08 trên bốn file) và 28 nhóm mới ở bảy ngưỡng trung gian. Có 176 inner traces và 24 summary; 0 native inference, 0 energy extraction mới để đo, 0 supervised fit. Waveform precheck PASS của H70 được tái sử dụng và kiểm hash, không chạy lại. Chỉ kiểm thêm synthetic boundary của grid mới trước đăng ký. Nếu kiểm tra này FAIL thì lưu và dừng, không nới ngưỡng.

Giữ nguyên lựa chọn nghiên cứu theo file và tám gate lịch sử: bốn outer/ba inner/final bốn file, finite/F1/recall-V drop<=.01/SIL+1 so hard170, minimax worst MAPE rồi mean và ID. hard170 không tuân thủ cửa sổ25ms và không được chọn làm bản nộp. Báo thêm minimax hữu hạn chỉ trong pipeline25ms như chẩn đoán; không dùng nó để tự bỏ guard hoặc promote. Kiểm metric, đánh đổi V/UV/SIL, khung loại và F0mean/std/count; chuẩn của thầy chỉ có thống kê cảfile, không F0 từngkhung.

Không đo test khi chưa đủ điều kiện, lock/push/remoteverify và compliance25ms. Mục tiêu từngfile trongcả8file AverageMAPE<2%; train tốt chưa chứng minh all8, test đã xem lịch sử và nested vẫnexploratory. Không tự nới gate nếu grid mịn không đạt. Giữ mọi failure và original/frozen.

Verifier scalar RMS/p95 là kiểm tra bằng chứng cache, không chạy lại thuật toán pitch. Nó kiểm ngưỡng/mask/pitch giữ, metric, parity endpoints H70, các khung loại, labels/time, selection/gates và source/protected/output hashes. Dùng experimental-design; Kassis,T., Agarwal,V., He,Y., Patel,D., & Brueckner,A.M. (2026), [Scientific Agent Skills](https://arxiv.org/abs/2609.00065), DOI10.48550/arXiv.2609.00065; metadata HTML v2 kiểm09/10. Không Drive/DL/PDF/Jev/Colab/GPU/schedule hoặc sửa notebookgốc. Báo cáo và trả lời bằng prose tiếng Việt.
