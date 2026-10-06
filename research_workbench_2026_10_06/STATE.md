# Trạng thái nghiên cứu — đọc trước khi nối tiếp

- Mốc dừng cứng: 2026-10-07 04:00 Asia/Saigon (2026-10-06T21:00:00Z).
- Nhánh: codex/train-mape-investigation. Baseline accepted gốc: 009fd2c.
- Thư mục: research_workbench_2026_10_06; protocol PROTOCOL.md.
- Người dùng yêu cầu push sau từng thay đổi; không hỏi, dùng Gemini và Jev, figures/plots/reports.
- Automation heartbeat đã tạo: bt2-nghi-n-c-u-n-04-00, deadline RRULE UNTIL21:00UTC.
- Hiện đang làm: H00 hoàn thành, chuẩn bị H10; chưa đọc lại WAV test trong vòng mới. Không có audit process đang chạy.
- Đã đọc: root/repo AGENTS, core/standalone_pipeline và frozen configs.
- Gemini Chrome: tab184651875, URL gemini.google.com/app/cd94cd87d07bc5c5; đã chọn Pro, đã gửi prompt reviewer đầu tiên. Cần đọc câu trả lời và lưu log.
- Google Translate tab184651878 đã đọc thông báo đầu (UI Dừng nghe). Chrome hiện có tab Drive, không đọc/thao tác tab đó.
- Python: C:/Users/violet/miniconda3/python.exe; numpy2.4.3 scipy1.17.1 pandas3.0.1 matplotlib3.10.8 sklearn1.8.0.
- Nguồn Claude Science official đã xác minh. Đã đọc MPM paper tác giả: cs.otago.ac.nz/graphics/Geoff/tartini/papers/A_Smarter_Way_to_Find_Pitch.pdf; librosa official YIN docs/source. YIN paper gốc URL ENS chưa truy cập được.

## Hàng đợi

- [x] H00: audit.py, H00_AUDIT_REPORT.md, results/audit_validation.json; 20 PNG/SVG, baseline khớp 1e-8, cache/labels khớp, 15 notebook giữ hash, poisoned scoring GT không đổi inference.
- [x] H00b: metric_audit.py, H00B_METRIC_REPORT.md, 2 PNG/SVG. Synthetic hoán vị: stats MAPE0%, frame MAPE61.5909%; không phải đo trên WAV.
- [ ] Đọc/lưu Gemini critique, đối chiếu và bổ sung quyết định trước chạy.
- [ ] Jev rà phạm vi một hoặc vài claim/chọn phương án khi còn ngữ nghĩa chưa rõ.
- [ ] H10 YIN adapter: implementation + synthetic known-F0 checks + real training evaluation/LOFO, commit/push riêng.
- [ ] H11 NSDF/MPM: implementation + synthetic checks + same protocol evaluation, commit/push riêng.
- [ ] H12+ từ kết quả mới: ghi hypothesis/registry/gates trước mỗi experiment.
- [ ] Robustness/stability/stratification/threshold plots.
- [ ] Freeze trước test; test mô tả một lượt, không tune.
- [ ] Figure manifests, final reports/gallery/repro commands, validation.
- [ ] 03:40 chốt để 04:00 dừng, lưu trạng thái và push.

Các artifacts từ analysis phải là số đo thật. Không tạo placeholder metric hoặc ảnh giả.

## Phát hiện đã đo H00

- Accepted ACF: train Avg MAPE 6.177967772%, LOFO 7.279236147%; original tương ứng 29.834710577%, 29.110827818%.
- Train SIL false voiced 45→1, TP535→530, FN79→84. Recall V/UV và confusion được báo riêng.
- Accepted train V boundary33FN/66, interior51FN/548. Không có nhãn phoneme để kết luận loại phụ âm gây lỗi.
- Manual V center counts153/244/123/94 khác 3GT148/232/127/82 (phone_F1,phone_M1,studio_F1,studio_M1). Chưa biết protocol tạo 3GT; không sửa GT để khớp nhãn.
- RUN_LOG.md giữ lỗi nfft và tabulate của hai lần audit đầu; lần sau chạy thành công, không thay môi trường.
