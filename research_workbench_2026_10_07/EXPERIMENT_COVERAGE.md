# Phạm vi thí nghiệm BT2

“Thử hết” được thực hiện trong phạm vi ma trận H51 đã đăng ký: mọi tổ hợp đặc trưng khác rỗng và mọi learner/seed trong registry. Không có danh sách hữu hạn chứa toàn bộ thuật toán, tham số, phép biến đổi dữ liệu hoặc corpus có thể có. Bảng này phân biệt các hướng đã đo với các hướng chưa nằm trong ma trận.

| Nhóm | Đã thực hiện | Bằng chứng |
| --- | --- | --- |
| V/UV, năng lượng, nhãn khung | Cổng RMS/STE, threshold, hysteresis, majority mask; nhãn tâm và phân tích độ phủ cửa sổ | [Voicing diagnosis](../research_workbench_2026_10_06/VOICING_DIAGNOSTIC_REPORT.md), [H14](../research_workbench_2026_10_06/MASK_VOTE_REPORT.md), [H00b count](../research_workbench_2026_10_06/H00B_METRIC_REPORT.md), H50_label_overlap.csv |
| Học có giám sát và ZCR | Logistic với đặc trưng tín hiệu; ZCR riêng H22; clean/augmented rejection H47; recovery H50 | [H22](H22_REPORT.md), [H47](H47_REPORT.md), [H50](H50_REPORT.md) |
| Học không giám sát | H50 GMM trên mọi khung, không dùng LAB fit/mapping; H51 GMM ba seed | [H50](H50_REPORT.md), [H51 registration](H51_REGISTRATION.md) |
| Geometry/filter/classical ACF/AMDF | Các vòng filter, frame/hop, clipping và sửa AMDF; tách gate25/pitch40 | H18–H27 trong STATE.md, [H20](H20_REPORT.md), [H24](H24_REPORT.md) |
| Whole/reference pipelines | Harvest, Praat filtered ACF, pYIN, SWIPE′, REAPER, RAPT, YAAPT | [H28](H28_REPORT.md), [H30](H30_REPORT.md), [H33](H33_REPORT.md), [H34](H34_REPORT.md), [H36](H36_REPORT.md), [H39](H39_REPORT.md), [YAAPT H40](H40_REPORT.md) |
| Miền tần số và phối hợp pitch | SWIPE′, tỷ lệ năng lượng phổ, spectral route NAMDF25/40, bounded fusion; cepstrum/NCCF pitch path H53 | [H34](H34_REPORT.md), [H35](H35_REPORT.md), [H38](H38_REPORT.md), [H43](H43_REPORT.md), [H53](H53_REPORT.md) |
| Mở rộng YAAPT và temporal path | H52 NLFER/pitch-only/final-DP ablation; H53 alpha/lambda grid, mask giữ nguyên | [H52](H52_REPORT.md), [H53](H53_REPORT.md) |
| LPC residual/harmonics | H54 SRH port COVAREP,60/80/100ms ×whole/pitch-only; H55 bounded100/200/400cents; train/testkhôngthắngcấuhìnhchung | [H54](H54_REPORT.md), [H55](H55_REPORT.md), [source](SRH_SOURCE_NOTE.md) |
| Estimator của khung recovery | H56 gmm_PEZS×3seed, same-mask pitchACF/bound100/200/400,33fits; đã cô lập tác động std, chưa thắngcấuhìnhchung | [H56](H56_REPORT.md), [preregistration](H56_REGISTRATION.md) |
| Two-sided mask và semantic GMM | H57 cùngmodelsH56,thêmrejectposterior.1/.25/.5;loạinhiềuLABV/mapeFAIL, auditonecluster≠calibratedP(V);timingdeviationgiữ | [H57](H57_REPORT.md), [timing note](results/H57_prereg_remote_verification_note.md) |
| Ensemble/augmentation | Ranking pitch members, noise augmentation grouped theo file gốc, augmented logistic rejection | [H45](H45_REPORT.md), [H46](H46_REPORT.md), [H47](H47_REPORT.md) |
| Ma trận ML/MFCC | 31 subsets × logistic/SVM/kNN/RF/GMM, seeds11/29/47; đơn nhóm và leave-one-block-out | H51_REGISTRY.json, H51_fixed_lofo.csv, H51_seed_summary.csv |
| Grouped CV, synergy, permutation | Nested file4fold/inner3fold; 150 pair contrasts và75 remove-block contrasts (gồm seed);900 permutations | H51_inner_traces.csv, H51_pair_interactions.csv, H51_leave_one_block_out.csv, H51_permutation.csv |
| Robustness/cross-condition | White30/20, pink20; phone→studio và studio→phone; không fit held origin/condition | H51_robustness.csv, H51_cross_condition.csv |
| Generalization | Frozen BT2test; KEELE10speakers, giữ reference/timing caveat; không tune corpus | [H48 status](ALL_FILES_STATUS.md), [H49 benchmark](BENCHMARK_KEELE_REPORT.md), H51_test_metrics.csv, H51_keele_metrics.csv |
| Qualitative/error/mechanism | Waveform/spectrogram/F0 ước lượng, V/UV/SIL/boundary, variance contribution của recovery | H51_REPORT.md, H51_INTERPRETATION.md, H51_error_by_boundary.csv |

Đính chính08/10: YAAPT đã được thử ởH40 trướcH51; thông tin cũ liệt kê nó là hướng chưa thử là sai. H52 mở rộng YAAPT, H53 đã thử cepstrum/correlation và đường đi trên các khung hữu thanh baseline. H54 đã thử LPC-residual SRH, H55 giới hạn chọn đỉnh gần baseline; chưa đo mọi LPC method. H56 cô lập estimatorACF cóanchor của khung recovery, không thaylearner/feature/count. H57 two-sidedreject/recover đã thử một GMMmapping/ngưỡng, không mọitwo-sidedmodel/calibration. H53 không phải cepstral recovery các khung non-V; vẫn còn hướng khôi phục hữu thanh dùng pitch estimator khác, HPS/PEFAC, HMM riêng cho recovery, mapping/calibrationđaGMMcluster hoặcclassifierhai-sidedkhác, protocol center/majority như thí nghiệm riêng, pitch/time augmentation, nhiều noise seed và corpus chưa từng xem như PTDB-TUG. Chúng cần hypothesis/registry riêng, không suy ra PASS/FAIL từH51–H57. pYIN có path model nhưng không đồng nghĩa thử mọi HMM.

H51 chỉ ablate đầu vào của learner. Điều kiện maxACF/năng lượng và cách lấy pitch khôi phục giữ chung. Các giới hạn này phải được giữ khi diễn giải kết quả về ML/MFCC. Test và KEELE đã có lịch sử exposure; đánh giá hiện tại là mô tả/thăm dò, không chứng nhận một tập kiểm tra hoàn toàn mới. Không có F0 chuẩn từng khung trên BT2.

Lệnh kiểm tra hiện hành dùng `verify_voicing_matrix_v2.py train` và `verify_voicing_matrix_v3.py external`, xem [hồ sơ sửa bộ kiểm tra](H51_VERIFICATION_REPAIR.md). Notebook đã nộp, WAV/LAB và frozen baseline gốc không đổi. Bài mới nằm ở `../../XLTN-BT1-BO-SUNG/` và vẫn sau ưu tiên cải thiện BT2.

## H58 — mapping cụm có giám sát, đã đo

H58 học trọng số LAB V của cả ba cụm GMM chỉ từ fit pool trong mỗi fold, giữ F0/recovery H56 để cô lập rejection mapping. 5 options ×3 seed, grouped nested, permutation và held-label poisoning fixtures; 300 train/36 test metric groups được verifier kiểm độc lập. Mapping giảm loại nhầm V và Brier nhưng chưa cải thiện cấu hình chung; giữ hard170, all8 target FAIL. [Báo cáo H58](H58_REPORT.md). Không gọi mapping có LAB là unsupervised, không gọi test đã xem là independent mới.

## H59 — temporal context riêng cho rejection, đã đo

Chuỗi hai trạng thái với transition học từ LAB fit pool, unary H58 giữ nguyên, marginal forward-backward dùng để loại original baseline V. 6 options ×3seed, grouped nested,360 train/48 test groups; enumeration/scalar/parity và fold isolation được kiểm. Markov giảm một số lỗi phone nhưng làm studio train xấu hơn; test .25 chỉ studio_M2<2 với recall V giảm, không train-selected. Giữ hard170, all8 target FAIL. [Báo cáo H59](H59_REPORT.md). Đây là offline posterior-potential chain, không claim generative HMM/streaming hoặc calibrated valid-F0 probability.
