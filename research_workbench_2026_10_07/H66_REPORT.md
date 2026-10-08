# H66: mô hình nhiễu AR(1) giảm lỗi lớn nhất, nhưng chưa đủ để chấp nhận

**H66 hoàn tất, kiểm chứng PASS; quyết định thực nghiệm FAIL.** Giữ pipeline được chấp nhận `hard170`, không đo test mới và không sửa notebook đã nộp. Giả thuyết/source/precheck/registry được commit tại `c804f6d87cd2a86cc6e2157933e9d8f6a24a08ea`, push và xác minh remote trước đo train. Rollback `211bb03ba13c1672518932768b1b864d9390ce6c`.

## Thay đổi đã thử

Hồi quy họa âm khớp tín hiệu bằng tổng các sóng sin có tần số bằng bội của F0. H61 tính sai số khớp với trọng số cửa sổ Hann. H66 thêm mô hình nhiễu AR(1): phần dư ở một mẫu có thể phụ thuộc phần dư ngay trước nó. Từ waveform trong mỗi khung, H66 ước lượng hệ số rho rồi biến đổi **cả dữ liệu và các sóng sin của mô hình** để tính lại sai số. Không đổi nhãn V/UV/SIL, quyết định hữu thanh, số khung hoặc thống kê chuẩn.

Đây là custom one-step residual weighting theo [đăng ký H66](H66_REGISTRATION.md), không joint maximum-likelihood hoặc solver tham chiếu của tác giả. Ba họa âm, canonical25ms/hop10ms, miền tìm anchor±100cents, thuật toán tối ưu và các tiêu chí giữ nguyên. Không tự điều chỉnh rho clip hoặc bounds sau khi xem kết quả.

## Kết quả train

Average MAPE là trung bình lỗi tương đối của **F0mean/F0std/F0num cả file** so teacher3GT. Bảng không thể hiện accuracy F0 từng khung vì BT2 không có chuẩn F0 từng timestamp.

| File train | Baseline hard170 (%) | H61 NLS3 đã lưu (%) | H66 AR1 NLS3 mới (%) |
|---|---:|---:|---:|
| phone_F1.wav | 0.340080 | 0.443094 | 1.122741 |
| phone_M1.wav | 0.776151 | 1.034688 | 0.920194 |
| studio_F1.wav | 1.473576 | 1.254701 | 1.363120 |
| studio_M1.wav | 1.909923 | 2.193784 | 1.849260 |
| Mean bốn file | 1.124932 | 1.231567 | 1.313829 |

H61 ở bảng là cache `results/H61_fixed.csv` được bảo vệ bằng hash, không chạy lại H61. H66 so H61 cải thiện phone_M1/studio_M1 nhưng làm phone_F1/studio_F1 xấu hơn. So baseline, H66 giảm lỗi hai file studio nhưng tăng lỗi hai file phone.

Selector minimax ưu tiên file có Average MAPE lớn nhất. Vì worst-file giảm 1.909923→1.849260%, final và cả bốn outer folds chọn `ar1_nls_3`. Mọi held train file của H66 dưới2%, nhưng **chưa đạt gate chấp nhận**: mean tăng 1.124932→1.313829%, khoảng16.79%; F0std MAPE phone_F1 tăng .089632→2.566557%. Không gọi việc selector chọn H66 hoặc 4/4train<2 là đạt mục tiêu8file.

| Gate đã định trước | Kết quả |
|---|---|
| Train mean MAPE giảm ít nhất10% | FAIL |
| Nested mean MAPE giảm ít nhất5% | FAIL |
| MacroF1 giảm không quá.01 | PASS |
| RecallV giảm không quá.01 | PASS |
| false_voiced_sil tăng không quá1 | PASS |
| Không file nested tăng MAPE hơn2 điểm phần trăm | PASS |
| F0std MAPE phone_F1 không xấu hơn | FAIL |
| Selected LOFO mean MAPE giảm ít nhất5% | FAIL |

MAE F0mean trung bình file giảm1.070616→.829611Hz; MAE F0std tăng.195550→.318574Hz. F0num giữ147/233/123/85, tổng588; sai số tuyệt đối count1/1/4/3, mean2.25khung, cùng baseline. MacroF1 .893977, recallV .929270, recallUV .899399, balancedaccuracy .914335, false_voiced_sil0 giữ nguyên. Chi tiết per-file/split trong `results/H66_fixed.csv` và `H66_metrics.csv`.

297/588khung chạm clip |rho|=.95. Mean rho của studio_F1/.M1 là.946799/.948612; đây là dấu hiệu cần xem lại mức phù hợp của nuisance model, không chứng minh phần dư là externalnoise hoặc tăng clip sẽ cải thiện. 31/588pitch chạm biên tìm kiếm (11/9/7/4 theo thứ tự file trên); không mở bounds hậu nghiệm.

## Kiểm chứng

- Precheck PASS18/18fixture mới: harmonic waveform +AR1noise rho.8, fs16k/44.1k, F090/200/320, seeds11/29/47. Kiểm error<100cents, độc lậpQR/rho/whitening/objective/grid/bracket, gain/DC, rho0 khớp objectiveH61 và zero/constantfallback. Chỉ seed tạo nhiễu fixture, không ba trainingreplications.
- Train:8unique metricgroups,32innertraces,24summaryrows; baseline đọc cacheH47, bốn group mới đo một lần. 0supervisedfits,588frame nuisanceARfits cùng nhiều harmonicLSfits trongsearch; không nói thuật toán không fit gì. Inner `actual_fit_files` là trường supervisedfitpool, không waveformnuisancefit.
- `results/H66_verification.json`: PASS8groups/588frameoptions. Độc lập QR tại anchor tính residual/rho; scalar row whitening, QRobjective mọi coarsegrid và returnedpitch/localbracket/cost; scalarstatistics, selection, innermembership, mask/count và protectedhashes. Không rerun optimizer độc lập; gateimplementation dùng bản cũ, không claim độc lập toàn bộ gatecode.
- Môi trường Python3.13.11,NumPy2.4.3,pandas3.0.1,SciPy1.17.1; train receipt ghi12.596931s (phần đo sau import, không end-to-end benchmark). Chạy localCPU: `C:/Users/violet/miniconda3/python.exe -X utf8 research_workbench_2026_10_07/ar_nls_experiment.py train`, sau đó `.../verify_ar_nls.py`. GPU/Colab không cần cho vòng này.

## Giới hạn và nguồn

Nested4outer/3inner/final4LOFO theo file, không random frames; repeatedselection trên bốn file và test history vẫn exploratory. Tiêu chí all8 strict<2% chưa đạt; test chỉ giữ số H48 lịch sử. Không rerun H00–H65, không sửa WAV/LAB/teacher3GT/frozen/original notebook. Không GoogleDrive, deep learning, PDF, Jev, schedule hoặc automaticretry.

[H66_SOURCE_REVIEW](H66_SOURCE_REVIEW.md) ghi query/ngày/contentlevel và khác biệt với source. Primary HTML/abstract: [Quinn, Nielsen & Christensen(2021), F0 in autoregressive noise](https://researchers.mq.edu.au/en/publications/fast-algorithms-for-fundamental-frequency-estimation-in-autoregre/), DOI10.1016/j.sigpro.2020.107860; [Esquivel Jaramillo(2021), Pre-processing of Speech Signals](https://vbn.aau.dk/en/publications/pre-processing-of-speech-signals-for-robust-parameter-estimation/), DOI10.54337/aau456472165. Không đọc/extract fullpaperPDF hoặc nhập benchmark của tác giả vào metricBT2.

Workflow skills: experimental-design và literature-review local. Citation metadata xác minh08/10/2026: Kassis,T.;Agarwal,V.;He,Y.;Patel,D.;Brueckner,A.M.(2026), [Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents](https://arxiv.org/abs/2609.00065), DOI10.48550/arXiv.2609.00065. Skill giúp tổ chức design/đơn vị/citation, không bảo đảm accuracy hoặc thay kiểm chứng code.
