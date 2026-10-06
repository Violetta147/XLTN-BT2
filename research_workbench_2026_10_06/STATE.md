# Trạng thái nghiên cứu — đọc trước khi nối tiếp

- Mốc dừng cứng: 2026-10-07 04:00 Asia/Saigon (2026-10-06T21:00:00Z).
- Nhánh: codex/train-mape-investigation. Baseline accepted gốc: 009fd2c.
- Thư mục: research_workbench_2026_10_06; protocol PROTOCOL.md.
- Người dùng yêu cầu push sau từng thay đổi; không hỏi, dùng Gemini và Jev, figures/plots/reports.
- Automation heartbeat đã tạo: bt2-nghi-n-c-u-n-04-00, deadline RRULE UNTIL21:00UTC.
- Hiện đang làm: H00 audit/baseline; chưa thay estimator, chưa đọc lại WAV test trong vòng mới.
- Đã đọc: root/repo AGENTS, core/standalone_pipeline và frozen configs.
- Gemini Chrome: tab184651875, URL gemini.google.com/app/cd94cd87d07bc5c5; đã chọn Pro, đã gửi prompt reviewer đầu tiên. Cần đọc câu trả lời và lưu log.
- Google Translate tab184651878 đã đọc thông báo đầu (UI Dừng nghe). Chrome hiện có tab Drive, không đọc/thao tác tab đó.
- Python: C:/Users/violet/miniconda3/python.exe; numpy2.4.3 scipy1.17.1 pandas3.0.1 matplotlib3.10.8 sklearn1.8.0.
- Nguồn Claude Science official đã xác minh. Paper YIN/MPM URL tác giả có lỗi web; cần nguồn primary khác hoặc paper mirror có tác giả, không tuyên bố đã đọc full PDF chưa lấy được.

## Hàng đợi

- [ ] H00 script audit, tái lập baseline, error analysis, CSV và figures nền.
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
