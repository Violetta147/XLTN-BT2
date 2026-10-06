# Trạng thái nghiên cứu — đọc trước khi nối tiếp

- Mốc dừng cứng: 2026-10-07 04:00 Asia/Saigon (2026-10-06T21:00:00Z).
- Nhánh: codex/train-mape-investigation. Baseline accepted gốc: 009fd2c.
- Thư mục: research_workbench_2026_10_06; protocol PROTOCOL.md.
- Người dùng yêu cầu push sau từng thay đổi; không hỏi, dùng Gemini và Jev, figures/plots/reports.
- Automation heartbeat đã tạo: bt2-nghi-n-c-u-n-04-00, deadline RRULE UNTIL21:00UTC.
- Hiện đang làm: H00/H10–H14 hoàn thành. H15robustness đang chạy ởtoolsession21440, đọc results/robustness_progress.json và process trước khi resume; không chạy trùng. Chưa đọc WAVtest vòngmới. Nếu process dừng, chỉ resume nguyêncode/registry; deadline21:00UTC.
- Đã đọc: root/repo AGENTS, core/standalone_pipeline và frozen configs.
- Gemini Chrome: tab184651875, URL gemini.google.com/app/cd94cd87d07bc5c5; đã chọn Pro, đã gửi prompt reviewer đầu tiên. Cần đọc câu trả lời và lưu log.
- Google Translate tab184651878 đã đọc thông báo đầu (UI Dừng nghe). Chrome hiện có tab Drive, không đọc/thao tác tab đó.
- Python: C:/Users/violet/miniconda3/python.exe; numpy2.4.3 scipy1.17.1 pandas3.0.1 matplotlib3.10.8 sklearn1.8.0.
- Nguồn Claude Science official đã xác minh. Đã đọc MPM paper tác giả: cs.otago.ac.nz/graphics/Geoff/tartini/papers/A_Smarter_Way_to_Find_Pitch.pdf; librosa official YIN docs/source. YIN paper gốc URL ENS chưa truy cập được.

## Hàng đợi

- [x] H00: audit.py, H00_AUDIT_REPORT.md, results/audit_validation.json; 20 PNG/SVG, baseline khớp 1e-8, cache/labels khớp, 15 notebook giữ hash, poisoned scoring GT không đổi inference.
- [x] H00b: metric_audit.py, H00B_METRIC_REPORT.md, 2 PNG/SVG. Synthetic hoán vị: stats MAPE0%, frame MAPE61.5909%; không phải đo trên WAV.
- [ ] Đọc/lưu Gemini critique, đối chiếu và bổ sung quyết định trước chạy.
- [x] Jev chọn shortlist prospectiveH12;1call logged jev_h12_selection.json. Chọn score hysteresis(.70/fit.78), none-optionfit.54; không xem confidence như kiểm định.
- [x] H10 YIN adapter: 1600 synthetic cases, FFT/direct error4.3e-13, clean p95 .475cents; train9.3674%, LOFO12.2374% AvgMAPE. Gate FAIL, champion không đổi. Report YIN_EXPERIMENT_REPORT.md; 3 PNG/SVG.
- [x] H11 NSDF/MPM: numerical error<4.6e-14; 1600synthetic,12abstentions ở70Hz+noise, clean interior100%coverage/p95.0893cents. Train6.9604%, LOFO8.1883% AvgMAPE, gateFAIL. Report MPM_EXPERIMENT_REPORT.md,3PNG/SVG.
- [x] H12 hysteresis: registry0/.02/.04/.06/.08/.12, final margin.06; train2.697086%, selectedLOFO6.182753%, nested6.670683%. GatesPASS, provisional eligible, chưa promote/freeze/test. Nested recallV.884498/F1.854151/SIL3 vs accepted.865862/.841398/3. HYSTERESIS_EXPERIMENT_REPORT.md,2PNG/SVG.
- [x] H13 cùngACF candidates/path, chỉNSDFstrength: train5.0886%, LOFO7.2077%, cải thiệnLOFO<5% nên gateFAIL; không gộpH12. NSDF_STRENGTH_REPORT.md,2PNG/SVG.
- [x] H14 majority3mask: train4.2254%, LOFO5.8177%, Recall/F1tăng/SILkhôngtăng nhưng phone_F1std tăng, gateFAIL. Không bỏ gate chỉ vì AvgMAPE thấp hơn H12; MASK_VOTE_REPORT.md,1PNG/SVG.
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
- Voicing diagnostic: train FN84 gồm pitch-only76,both3,energy-only5;16interior+2boundary isolated mask gaps. Boundary FN chỉ5có previousV,13có followingV: hysteresis forward chỉ tác động offset, không cứu hết onset. Report VOICING_DIAGNOSTIC_REPORT.md,2PNG/SVG.
- Google Translate milestoneH12 đã phát tiếng Việt, UI Dừng nghe xác nhận playback được yêu cầu; không thể xác nhận người dùng nghe được. Gemini reviewer02 vẫn chưa có text phản hồi; tiếp tục độc lập.
- H12mechanism: train thêm18V+2UV+0SIL; nested thêm17V+2UV+0SIL. phone_F1train chỉ3sharedframes đổiF0, std26.5516→20.9325; append-only26.3657. Phần lớn std gain train này do path/median context, không chỉ thêmcount. LOFOphone_F1std29.2614→29.1584, gain nhỏ hơn; không suy diễn mọi frame đã đúng. HYSTERESIS_MECHANISM_REPORT.md,3PNG/SVG.
- CRITICAL metric-labelcoupling: phone_F1train2sharedUV ở1.6425/1.6625s đổiF0~71.608/82.785→247.050/240.541Hz, cùngFP, Voverlap0 ởcảhai. True-center-V stdaccepted20.7632/hysteresis20.6690 đã gầnGT20.6. UVcontributionvariance40.31%→6.55% explains mosttrainstatgain. GatesPASSgiữ nguyên nhưng không gọi đây là sửa F0 thật ởV; H12provisional. METRIC_LABEL_COUPLING_REPORT.md,1PNG/SVG.
- H15registry1744cases,3488modelrows: noise3types×7SNR×20seed×4file plusgain/DC/clip/impulses. Frozencleanheld-filefits và nestedH12margins; không tune từnoise. Rawextractor phải khớpcache trước. Đang chạy, chưaclaimcomplete.
- H16fixedlogistic C1/.5 trênACFscore+relativeRMS, perfile/classbalancedfit+scaleronlytrain; không thêmfeature. Train5.1192%, LOFO5.4707%, F1.863433/RecallV.884072/SIL1, fixedmethodgatesPASS, provisional. phone_F1LOFOFP8→3/SIL2→0 nhưngTP138→135/FN15→18; khôngtốtởmọifile/lớp. LOGISTIC_VOICING_REPORT.md,2PNG/SVG.
- Next H17: register joint family/margin shortlist và innerLOFOselection→outerheld evaluation, khôngchọnfamilybằngouter/test. Registry đượcđềxuấtsaucácphân tích trên4file, nênchỉexploratory, khôngxóaselectionhistory.
