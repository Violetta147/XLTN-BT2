# BT2 science workbench — đêm 06/10/2026

## Hợp đồng nghiên cứu

- Phiên chạy đêm trước có thời hạn 04:00 ngày 07/10/2026 Asia/Saigon = 2026-10-06T21:00:00Z. Người dùng đã xóa schedule và chuyển sang làm trực tiếp trong chat ngày 07/10. Mốc cũ chỉ mô tả phiên lịch sử, không chặn phiên trực tiếp hiện tại.
- Điểm quay lại ban đầu: commit 009fd2c, nhánh codex/train-mape-investigation.
- Người dùng yêu cầu phân tích rất sâu, error analysis toàn diện, sáng tạo phương pháp mới, figures/plots/reports, dùng Gemini Chrome và Jev, không hỏi lại và commit/push sau mỗi thay đổi.
- Không Google Drive, không deep learning, không sửa notebook đã giao. Không tạo PDF.
- Hướng dẫn pipeline đính kèm là tài liệu tham khảo: áp dụng phần phù hợp, không tự thêm deployment, SMOTE, t-SNE hoặc imputation vào bài F0.
- Dữ liệu thực có 4 file train; 4 test đã được xem trong lịch sử. Test không được dùng để chọn/thay tham số ở vòng mới. Không gọi đây là test chưa từng thấy.
- GT thống kê là mean/std/count mỗi file, GT lớp là V/UV/SIL theo đoạn. Không có reference F0 từng timestamp trong nhóm LAB đã kiểm tra. Sai số cents từng khung chỉ được báo trên tín hiệu tổng hợp có F0 biết trước, không báo như kết quả WAV thật.

## Cách áp dụng nguyên tắc Claude Science

Áp dụng tính truy nguyên và tái lập như mô tả chính thức của Anthropic; không tuyên bố đang dùng ứng dụng Claude Science trên Windows hay có chứng nhận chuẩn.
Mỗi figure: PNG 200–300 dpi và SVG, CSV nguồn, script/command, hash nguồn/mã, môi trường phiên bản, caption tiếng Việt, giới hạn.
Mỗi thí nghiệm: giả thuyết, một biến thay đổi, baseline, tiêu chí trước chạy, số liệu train/LOFO/nested, kết luận giữ/bỏ, thời gian, commit và push.
Nguồn: https://www.anthropic.com/news/claude-science-ai-workbench

## Danh mục phân tích

1. Provenance: hashes WAV/LAB/notebook/mã/cấu hình, phiên bản môi trường, baseline reproduction.
2. Data quality: sample rate/channels/duration/NaN/clipping/DC/zero/duplicate; LAB coverage/overlap/gaps/tail, GT consistency.
3. Frame alignment: center labels/boundaries, 20/25/30 ms ảnh hưởng số V, số chu kỳ chứa trong frame, hỗ trợ lag.
4. Error taxonomy: V→UV FN, UV→V FP, SIL→V báo riêng, pred có F0 không hữu hạn, out-of-range; vị trí theo file/time/RMS/boundary.
5. F0 distribution: mean/std/count, std decomposition within/between label, oracle chẩn đoán không triển khai, quantiles, spikes/multiples như dấu hiệu chưa có frame GT.
6. Threshold and calibration: ROC/PR cho lớp V/UV, threshold sensitivity; scores không là xác suất calibrated.
7. Stratification: từng file, phone/studio và F/M theo tên; không suy diễn danh tính/người nói độc lập khi không có metadata.
8. Statistical stability: file là đơn vị độc lập, paired differences, file bootstrap mô tả, exact sign-flip chỉ thăm dò với 4 đơn vị; không chứng minh bằng p-values theo hàng nghìn frame chồng nhau.
9. Robustness: gain, DC, noise SNR, impulse/missing fundamental trên synthetic; tăng nhiễu WAV thật giữ nhãn nhưng báo perturbation mô phỏng.
10. Algorithm mechanisms: ACF vs AMDF vs YIN fixed-support CMND vs NSDF/MPM; minh họa curve/lag và lựa chọn.
11. Ablation/sensitivity: một yếu tố mỗi lượt; energy/path/median/periodicity/postprocess; không gộp nhiều hướng khi khẳng định nhân quả.
12. Generalization/leakage: fit train-only từng fold, nested selection, poisoned-GT inference invariance, test history; không adjust output để khớp thống kê thật.
13. Runtime/reproducibility: thời gian/CPU/environment hashes, rerun deterministic; không tuyên bố tiết kiệm do Jev từ latency nhỏ.
14. Synthesis: report có measured/diagnostic/hypothesis/unavailable, figures gallery và đủ lệnh tái lập.

## Registry thí nghiệm đầu tiên (trước khi đo)

H00 — audit và tái lập: Không đổi thuật toán. Đối chiếu original ACF và frozen accepted ACF bằng core.py với saved CSV. Chênh tolerance 1e-8 trên số thực; số đếm nguyên phải khớp. Nếu khác: điều tra nguồn/cache, không thử model mới khi baseline chưa rõ.

H10 — YIN fixed-support: Thay pitch estimator, giữ ACF voiced mask + RMS fit trong fold, cùng khung25/hop10/range70–400, median3. CMND dùng tổng bình phương khác biệt trên một support W cố định N-max_lag-1; chọn local minimum đầu dưới absolute threshold .1, nếu không có thì min CMND trong range; nội suy parabol. Đây là adapter frame25 hạn chế support ở F0 thấp, phải báo khác biệt với triển khai canonical dùng cửa sổ dài hơn. Chưa tune threshold.

H11 — NSDF/MPM: Thay pitch estimator sang NSDF = 2r(tau)/(m_left+m_right), chọn peak theo positive lobes và peak đầu đạt .93 của max peak, nội suy parabol; cùng voiced mask, RMS, median3 như H10. Không giả định NSDF score là probability hay thay voiced decision.

H12 — adaptive choice từ bằng chứng mới: Chỉ đăng ký sau khi phân tích H10/H11, Gemini và Jev. Một yếu tố: candidate quality, tracker hoặc voiced feature. Không quyết định bằng test.

## Gate giữ model mới

So với frozen accepted ACF refit train-only từng fold:
- Train Average MAPE giảm ít nhất 10% tương đối.
- LOFO và nested LOFO Average MAPE giảm ít nhất 5% tương đối; không dùng training score riêng để chọn.
- F0std MAPE phone_F1 không tăng.
- Macro F1 và recall V LOFO/nested không giảm quá .01; SIL false voiced không tăng quá 1 khung.
- Không per-file Average MAPE LOFO tăng quá 2 điểm phần trăm; nếu vi phạm, chỉ giữ như phương án thăm dò, không thay champion.
- Nếu mọi hướng thất bại: giữ champion, công bố failures và cơ chế học được.
- Selection nếu tune: inner LOFO chọn chỉ từ registry đã chốt; outer đánh giá rule selection không thấy held file; report final selected LOFO riêng với nested.
- Mỗi vòng có phạm vi và tiêu chí dừng trước chạy; không lặp vô hạn để tìm test tốt. Mốc chốt 03:40 chỉ thuộc phiên lịch sử đã kết thúc. Phiên trực tiếp theo STATE.md hiện tại.

## Pipeline 7 stage được chuyển vào bài này

| Stage tham khảo | Áp dụng |
|---|---|
| Understanding/light cleaning | Hash, format, LAB pairing, audit; không sửa raw WAV hoặc nhãn tùy ý |
| EDA | Waveforms, spectrograms, distributions, labels, errors, data quality |
| Statistics | Effect sizes/file-level uncertainty; n=4, không dùng test để “chứng minh” |
| Preparation | Train/LOFO/nested và xử lý âm thanh thử riêng; không SMOTE F0 frame |
| Modeling | Baseline + thuật toán tín hiệu cổ điển và ablation |
| MLOps | Environment, registry, versioning, tests, artifact manifests; không deploy ngoài yêu cầu |
| AI analysis | Gemini phản biện, Jev semantic checks; nguồn/code giữ quyền kết luận |

## Nối tiếp và thông báo

Đọc STATE.md trước khi tiếp tục. Tick việc đã hoàn thành, ghi lệnh và artifacts.
Heartbeat bt2-nghi-n-c-u-n-04-00 là lịch của phiên đêm cũ; người dùng đã xóa ngày 07/10 và yêu cầu làm trực tiếp. Không tạo lại lịch. Lịch không bảo đảm local compute tiếp tục khi máy/app ngủ.
Gemini: tab Chrome người dùng đã mở, Pro được chọn để phản biện; không gửi dữ liệu cá nhân, credentials hoặc waveform.
Phiên đêm đã dùng Google Translate cho mốc quan trọng; phiên trực tiếp cập nhật trong chat. Im lặng không cấp thêm quyền và không tự chuyển công việc thành schedule.
Jev: đọc docs/jev/HUONG_DAN_JEV.md, gửi bằng chứng tối thiểu, lưu raw input/output; không retry tự động.
