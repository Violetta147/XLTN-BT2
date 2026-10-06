# Trạng thái nghiên cứu BT2 — nối tiếp trực tiếp trong chat

Cập nhật ngày 07/10/2026. Người dùng xác nhận phần đang thấy mất là câu trả lời/tiến trình trong chat. Các artifacts tối 06/10 còn trên máy và đã được đối chiếu, lưu Git và push bổ sung.

## Chế độ làm việc hiện tại

- Làm trực tiếp trong chat. Người dùng đã xóa schedule bt2-nghi-n-c-u-n-04-00; không tạo lại lịch.
- Mốc 04:00 ngày 07/10 chỉ thuộc phiên chạy đêm cũ, không phải thời hạn của phiên trực tiếp hiện tại.
- Đọc AGENTS.md của workspace/repo; commit và push sau mỗi thay đổi đã kiểm tra, xác minh remote; không merge main.
- Chỉ local, không Google Drive, không deep learning. Người dùng cho phép Gemini Chrome và Jev để phản biện; ghi log, không retry lỗi System One.
- Giữ notebook đã giao, baseline và đăng ký/tiêu chí trước mỗi thí nghiệm mới. Không âm thầm bỏ gate để chấp nhận kết quả đẹp.
- Chọn cấu hình bằng train/LOFO/nested. Test từng được xem trong lịch sử: chỉ báo mô tả sau khi chốt, không dùng để tune.
- Bản kể lại tiến trình: [TIEN_TRINH_KHOI_PHUC_2026_10_07.md](TIEN_TRINH_KHOI_PHUC_2026_10_07.md).
- Trạng thái ghi tối qua được giữ nguyên tại [STATE_OVERNIGHT_SNAPSHOT_2026_10_06.md](STATE_OVERNIGHT_SNAPSHOT_2026_10_06.md). Không coi trạng thái process/tab trong snapshot là đang hoạt động.

## Điểm quay lại và bảo toàn artifacts

- Nhánh: codex/train-mape-investigation.
- Baseline repository trước vòng nghiên cứu: 009fd2c. Champion là frozen accepted ACF; không phương án mới nào đã được promote.
- Trước phục hồi: HEAD local/remote fa759d0; còn 24 tệp H15/H17 chưa được Git theo dõi.
- H15 đã kiểm tra và push riêng: 23bdb0c.
- H17 đã kiểm tra và push riêng: 79c3830.
- Kiểm tra phục hồi chỉ đọc artifacts: [H15 receipt](results/recovery_h15_checks_2026_10_07.json), [H17 receipt](results/recovery_h17_checks_2026_10_07.json). Không chạy lại inference hoặc đọc WAV test trong bước này.
- Thư mục figures hiện có 45 PNG và 45 SVG, gồm kết quả tốt, không đạt và phân tích cơ chế; không coi số figure là số thí nghiệm độc lập.
- Trạng thái runner H15 cũ không cần resume: progress JSON complete, đủ 1744 cases/3488 model rows, hoàn thành lúc 22:47 ngày 06/10 Asia/Saigon.

## Những gì đã hoàn thành

- [x] H00 audit/tái lập, 20 cặp figure, kiểm tra nguồn/cache/labels/notebooks và inference không dùng scoring GT.
- [x] H00b: minh họa thống kê mean/std/count không xác định F0 từng thời điểm; kiểm tra protocol count.
- [x] H10 YIN fixed-support: train AvgMAPE 9.367355%, LOFO 12.237352%, gate FAIL. Không kết luận mọi cách triển khai YIN đều kém.
- [x] H11 NSDF/MPM: train 6.960350%, LOFO 8.188307%, gate FAIL; báo coverage/abstention.
- [x] H12 hysteresis: train 2.697086%, selected LOFO 6.182753%, nested 6.670683%; gates PASS nhưng provisional, chưa promote.
- [x] H13 chỉ đổi NSDF strength với cùng ACF lags/path: train 5.088629%, LOFO 7.207657%, gate FAIL vì lợi ích LOFO chưa đủ 5%.
- [x] H14 majority3 voiced mask: train 4.225410%, LOFO 5.817675%, gate FAIL vì std phone_F1 tăng.
- [x] Chẩn đoán V/UV/SIL, mixed windows, hysteresis influence và metric-label coupling; không diễn giải cải thiện stats thành mọi pitch đã đúng.
- [x] H15 robustness: 1744/1744 cases, hai mô hình/case, noise/gain/DC/clipping/impulses; synthetic perturbations, không tune trên noise.
- [x] H16 logistic 2D cố định ACF_score + relative_rms: train 5.119156%, LOFO 5.470735%; fixed-method gates PASS, chưa promote.
- [x] H17 joint family/margin selection: selected LOFO 5.470735% nhưng nested procedure 7.374765% so với accepted 7.279236%; gate FAIL, champion giữ nguyên.
- [x] Bảo toàn 24 artifacts chưa commit thành hai commit riêng và xác minh remote.
- [x] Kể lại tiến trình trong tài liệu và cập nhật trạng thái cho phiên trực tiếp.

## Các phát hiện cần giữ khi giải thích

- Original ACF train AvgMAPE 29.834711%, accepted 6.177968%; accepted LOFO 7.279236%.
- Train false_voiced_sil 45→1 là số khung SIL bị dự đoán hữu thanh trên 4 file; TP 535→530, FN 79→84.
- Ground truth có mean/std/count từng file và nhãn loại đoạn, chưa có F0 reference mỗi timestamp trong LAB đang dùng.
- Manual V center counts 153/244/123/94 khác 3GT 148/232/127/82. Protocol tạo 3GT chưa được xác nhận; không sửa GT cho khớp.
- H12 phone_F1 train: một phần lớn std gain liên quan tới hai khung nhãn UV vẫn bị đoán V nhưng F0 đổi gần mean. Cần đọc METRIC_LABEL_COUPLING_REPORT.md, không gọi đây là sửa F0 thật của V.
- H17: chọn phương pháp tốt nhất trên LOFO rồi báo chính LOFO đó tạo ước lượng lạc quan cho quy trình chọn. Nested tách outer held file khỏi chọn phương án/fit, nhưng không xóa lịch sử đã quan sát bốn file để đề xuất registry.
- n=4 file train; các frame chồng nhau và seeds noise không tạo hàng nghìn người nói độc lập.

## Việc còn lại

- [ ] Đọc phản hồi Gemini reviewer02 nếu vẫn có thể truy cập và ghi đúng phần quan sát; không gửi lại prompt chỉ để có câu trả lời.
- [ ] Tạo tổng hợp uncertainty/stability theo file và gallery/captions giúp người dùng đọc toàn bộ findings.
- [ ] Đăng ký câu hỏi và gate cho vòng mới trước chạy, ưu tiên nguồn GT/count, phân loại lỗi voicing và thất bại dưới brown noise.
- [ ] Quyết định freeze/promote bằng đầy đủ điều kiện đã đăng ký; giữ kết quả không đạt.
- [ ] Chỉ đọc test sau khi cấu hình đã chốt cho một câu hỏi cụ thể; báo rõ test đã từng được xem.

## Môi trường và log

Python đã dùng: C:/Users/violet/miniconda3/python.exe. Môi trường và hashes của phiên gốc nằm trong manifests/results; kiểm tra runtime trước run mới.

AI_REVIEW_LOG.md giữ critique Gemini reviewer01 đã sửa các nhầm lẫn về metric/phoneme/interpolation; reviewer02 lúc lưu chưa có text để đọc. Jev H12 là 1 call lựa chọn semantic có log, không phải chạy F0. Tab IDs trong snapshot có thể lỗi thời; không suy ra tab còn tồn tại.

RUN_LOG.md giữ cả lần chạy lỗi và cách sửa. Không dựng lại câu trả lời chat cũ như thể nguyên văn đã được khôi phục; tài liệu hiện tại là tổng hợp mới từ bằng chứng.
