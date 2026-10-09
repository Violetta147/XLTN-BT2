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


## Cập nhật H60–H62, hoàn tất và dừng 08/10/2026

| Hướng bổ sung | Phạm vi đã đo | Kết luận và nguồn |
|---|---|---|
| MAPS biên độ +pha | H60 reference-derived whole/pitch-only,20train groups, khôngtest mới | [H60_REPORT](H60_REPORT.md); khác nativewindow/canonical; failure giữ, finalhard170 |
| Harmonic least-squares | H61 custom order3/5,12train groups, same mask/count | [H61_REPORT](H61_REPORT.md); gain riêng nhưng studio_M1>2; không reference fastF0Nls port |
| Harmonic coherence choV/UV | H62 logistic base4/6 ×rejection0/.1/.25,22fits/140groups/112traces | [H62_REPORT](H62_REPORT.md); Brier tốt cả4heldfile nhưng MAPE không tốt chung; finalhard170 |

[Ma trận ba vòng](figures/LOOP_H60_H62_train_matrix.png) và [summary CSV](results/LOOP_H60_H62_SUMMARY.csv) có số đã đo. Không suy từ mục “harmonics” cũ rằng mọi harmonicmethod đã thử; không suy từH61/H62 rằng fastNLS/ARnoise của tác giả đã được benchmark. Trạng thái dừng sauH62 đã được thay bằng yêu cầu tiếp tục trong chat mới08/10; xemH63 dưới đây. Không “thử hết” ngoài registry và không rerun để khôi phụcchat.

## H63 — bounded HPS, đã đo sau yêu cầu tiếp tục

Custom log-HPS order3/5,PCM25ms,anchor±100cents,mask/countgiữ;12train groups/48innertraces/24summaryrows,1176frameoptions được DFT/interpolation/argmax/scalarmetrics/selection verifier kiểm. Preregc62ba22 push/remoteverified trướctrain. Finalhard170; outerstudio_M1hps5 giữfile chấm2.678125%,nested1.316983% so1.124932%; baMAPEgatesFAIL. Gainriêngstudio_F1 1.473576→1.319059; khôngpromote/khôngtestmới. [H63_REPORT](H63_REPORT.md). GlobalHPS được bổ sung tạiH64/H65 bên dưới; PEFACthật chưađo, nguồnHTML/code và giớihạn tạiHPS_SOURCE_REVIEW.md/PEFAC_SOURCE_REVIEW.md.

## H64/H65 — HPS toàn dải, đã hoàn tất

H64globalHPS3/5 dừngsynthetic:30/36PASS,6order5/F090HzFAIL, khôngBT2measurement. [H64_REPORT](H64_REPORT.md). H65riêngorder3 táidùng18PASSfixturekhôngrerun;8train metricgroups/32innertraces/24summaryrows,588frameoptions directDFTverifierPASS,MAPEs63.276892/57.729610/6.303452/25.385793%. Final/mọiouterhard170,gateFAIL,khôngpromote/test. [H65_REPORT](H65_REPORT.md). Không suy tất cảharmonicmethod đềuFAIL hoặc đổiH64 thànhPASS bằng loạiorder5 khỏireport.

## H66 — nhiễu AR1 trong harmonic regression, đã hoàn tất

Customone-step residualAR1weightedNLS3:18syntheticfixturePASS,8train metricgroups,588frame nuisanceARfits/0supervisedfits,QR/objective/grid/bracket/scalarmetrics/selection verifierPASS588frameoptions. Preregc804f6d push/remoteverify trướctrain. Minimax chọnar1_nls_3 final/mọiouter,giảmworst1.909923→1.849260% nhưngmean1.124932→1.313829%,phone_F1stdxấu;4/8gatesFAIL,khôngpromote/testmới. [H66_REPORT](H66_REPORT.md), [source review](H66_SOURCE_REVIEW.md). Không referencejointML/fastsolver/ARorders hoặc proofresidual=externalnoise. [Countbudget](FIXED_COUNT_TARGET_BUDGET.md) chỉ đại sốcachedH48, khôngđo/testtuning. ChưađăngkýH67,khôngrerunH00–H66.


## Cập nhật 08/10/2026 — R01/H67/H68/R02/H69 đã hoàn tất

Trạng thái mới thay các dòng lịch sử “H67 chưa đăng ký / PEFAC chưa đo”. Không có thí nghiệm đang chạy; không rerun H00–H69 hoặc R01/R02. Người dùng cho phép khảo sát tham số, nhưng bản theo yêu cầu thầy phải dùng cửa sổ tín hiệu thực sự25ms và bước10ms. hard170 chỉ là đối chứng lịch sử, không đáp ứng cửa sổ25ms. Đọc [audit cửa sổ](FRAME_25MS_AUDIT.md) và START_NEXT_CHAT.md mới.

- R01: 16 suy luận Praat6 native train, đối chiếu cache; chưa tìm được cấu hình khớp cảmean/std/count. [Reference audit](REFERENCE_PROCEDURE_AUDIT.md).
- H67: residualAR4 custom harmonicNLS3, verifierPASS8groups/588frames; studio_M1 2,194889%, baMAPEgatesFAIL; khôngtest/promote. [H67_REPORT](H67_REPORT.md).
- H68: PEFAC thật Imperial pinf671f6d chạyOctave11.3; verifierPASS20groups. Nativewindow90,5ms; fixtureaccuracy4/6 giữ2FAIL. Mọiouter/finalhard170, gateFAIL; khôngtest/promote. [H68_REPORT](H68_REPORT.md).
- R02: 60groups phân tích phân phối từcache, khôngF0inference; phone_M1 rawPraat9/235giátrị>400Hz đóng góp90,981744% tổngbìnhphươngđộlệch. Khôngchứngminh thầytrim hoặcframeGT. [R02_REPORT](R02_DISTRIBUTION_REPORT.md), baPNG trongfigures. Initialhashfailure vàcorrectionbeforeanalysis giữ.
- H69: pYINthực25ms ba priors;12nativecalls,16groups,64innertraces,24summary,0supervisedfits. Default(2,18)MAPEs5,447286/6,056821/1,465577/.699716%,mean3,417350%,2/4train<2; final/outercontrol, gateFAIL,khôngtest/promote. Option(2,38)studio_M1zeroV/NaN; v1checkerFAIL, v2sửaNaN/CSVparsecuốiPASS16groups, mọi lỗi/checkernote giữ. Không đổiinference hoặcfinitegate. [H69_REPORT](H69_REPORT.md), [verification note](H69_VERIFICATION_NOTE.md).

Đãpush/remoteverifypreregtrướcđo. ResultsH69 `4f15a070dbb55b9b0761c0a37847ec5f8a95a9de`; rules25ms `c2cb69520a2d178357dc36d43c4879f4956efa19`. Toàn bộtestH48chỉđọc sốđãlưu, targetall8eachfile<2%vẫnFAIL; frozen/GT/notebookgốc giữ. H70chưađăngký: có thểauditcachepYINbeta(2,8) vànănglượng khungdư trướcpreregriêng, khôngđược gọi làresult. KhôngGPU/Colab/Drive/DL/PDF/Jev/schedule. Hồsơcũđượcarchive, xemSTART_NEXT_CHAT.md đểkhôiphục.


## Cập nhật 09/10/2026 — H70/H71 hoàn tất, trả lời theo prose

H70 lọc năng lượng từ cache pYIN25 H69 `(2,8)`: ngưỡng 0,08 cho mean train 1,617918%, 3/4 file dưới 2%, SIL bị dự đoán V giảm 60→0 nhưng mất 11 khung V. H71 dùng nguyên F0/RMS để đo bảy ngưỡng trung gian. Ngưỡng thống nhất 0,07 cho MAPE train 1,955313/0,838965/1,883484/0,544270%, mean 1,305508%, cả bốn file dưới 2%; SIL 60→1 và mất chín V, macro F1 0,849625/recall V 0,903908. Đây là kết quả chọn trên train, không chứng minh all8 hoặc held PASS. Chẩn đoán chọn bằng ba file rồi đo held file cho 2,780824/0,838965/2,497637/0,544270%, chỉ 2/4 dưới 2%. Guard lịch sử vẫn chọn hard170, `eligible=false`, không test/promote; hard170 không đáp ứng cửa sổ thực sự 25 ms.

Verifier H70 PASS 32 nhóm/128 inner traces/24 summary; H71 PASS 44 nhóm/176 inner traces/24 summary, cả hai ngay lần đầu. Không native inference hoặc supervised fit; H71 tái sử dụng waveform precheck H70 và chỉ kiểm thêm synthetic boundary. Prereg H70 `138d618688d37748aa0ec1a4fc80f9886156c2e0`, H71 `3e30d332ef43c71670cedcca441b26de6c857b44`; results H71 `f1096385ccae031b22bcca07d14751f5ab4b9d14` đã push/xác minh remote. Đọc H70_REPORT.md, H71_REPORT.md và START_NEXT_CHAT.md mới, không rerun H00–H71/R01/R02. H72 chưa đăng ký/chưa chạy; không có tiến trình đang chạy. Original/frozen/WAV/LAB/teacherGT/source hashes giữ nguyên. Người dùng yêu cầu prose style: ưu tiên đoạn văn tiếng Việt liền mạch trong chat và báo cáo. Không Drive/DL/PDF/Jev/GPU/Colab/schedule; mục tiêu cả tám file chưa được chứng minh.


## H72/H73 hoàn tất — 09/10/2026

H72 khóa pYIN 25 ms/bước 10 ms, prior (2,8), energy >=0,07 trên train rồi đo bốn test; verifier PASS. MAPE test 1,707043/4,422661/1,708944/0,945727%, pipeline đạt 7/8 file cả train/test; mục tiêu từng file <2% chưa đạt. LOFO là chẩn đoán theo lời làm rõ của người dùng, không phải gate bắt buộc mọi fold <2%; H71 lịch sử giữ nguyên. Prereg a0bacfca87763985e71912db9129bbf9a32f89d6, results ad0148273a43946458843ca9365b9e6801b29b32.

H73 thử logistic năm đặc trưng so với logistic chỉ năng lượng và energy07; 44 fits/180 groups/80 inner/12 summary, cache train tái sử dụng, verifier PASS. C1 tăng macro F1 full train 0,849625 ->0,876818, nhưng phone_M1 MAPE 2,541305%, chỉ 3/4 train <2%. Selection đã đăng ký giữ energy07; không đo logistic trên test, tái sử dụng H72. Prereg 90e70644fc16260f5793442e93895c56661dac48, results 0b051619b8f7ed33998dbcf7d4bed71db063d89c. Xem H72_REPORT.md/H73_REPORT.md và H73_ml/final_info.json. Không promote hoặc sửa notebook; không có thí nghiệm đang chạy. H74 chưa đăng ký. Không rerun H00–H73/R01/R02.


## H74–H77 hoàn tất — 09/10/2026

H74 thử Random Forest trên cùng năm đặc trưng: 33 fits/3168 cây, 136 nhóm metric, 64 inner và 12 summary, verifier PASS. Không vượt energy07, không test forest. Prereg f016fde60c7c779edd009cac4440c1eaea903ffa; results c6b9023a7609c6ffe5745d8da811f42fdd388f4a. H75 học logistic trên mọi khung có ứng viên và phục hồi ACF25: 33 fits/136 nhóm/64 inner/12 summary, verifier PASS. Phone_M1 phục hồi 12 khung LAB-V nhưng std tăng lên 22,027265 Hz và MAPE 11,032951%. Giữ control, không test H75. Prereg 0c1b9efac04b17d4724c553055d8ae657bfceb0c; results b4e064cbccb52960a2f5b90ee1fcc66b5b03cf32.

H76 giải mã F0 phục hồi, reuse model H75 C1, không fit: 132 nhóm mới và 48 cached, 80 inner/12 summary, scalar verifier PASS. Bridge10_edge25 đạt 4/4 train dưới 2%, mean 1,564140%; held selection vẫn energy07, nguồn và registry lịch sử giữ nguyên. Prereg 9db8bda67e43864d9509e57f8be0fa1a90c3834b; results 68c59966f4873bdab724db4059ca7a0570528568. H77 là frozen evaluation riêng đúng một full-train candidate, theo mục tiêu train/test đã làm rõ, không đổi selection H76. Freeze 3470fc96455c6d4643870115d5f220872d26a4ca; results 29b5cc4c549813271b27a6ff6adab8f71f752ff4. Reuse native H72, trích features/ACF25 mới trên bốn test, verifier PASS.

Test H77 MAPE 2,725091/4,219067/2,212639/0,486388%, mean 2,410796%, chỉ 1/4 test và 5/8 tổng dưới 2%. F1 test 0,866413 nhưng mục tiêu FAIL. Giữ energy07: mean train 1,305508%, mean test 2,196094%, đạt 7/8 file; phone_M2 test 4,422661% chưa đạt. Không promote hoặc sửa notebook. Test đã tiếp xúc trong lịch sử, không tìm thêm cấu hình từ test. H78 chưa đăng ký, không có thí nghiệm đang chạy; không rerun H00–H77/R01/R02.

Đọc H74_REPORT.md, H75_REPORT.md, H76_REPORT.md và H77_REPORT.md cùng registry/receipt theo family. Mọi failure được giữ, acoustic frame 25 ms và bước 10 ms tuân thủ. Nội suy/ACF/pYIN chỉ là ước lượng, không phải F0 chuẩn từng khung. Không Drive, deep learning, PDF, Jev, GPU, Colab, lịch tự động hoặc merge main.


## H78–H80 hoàn tất — 09/10/2026

H78 kiểm tra mô hình chung có ngữ cảnh và điều phối mềm phone/studio. Có24 fits mới,136 nhóm metric,64 inner,12 summary; nguồn cache H75/H76 tái sử dụng, không trích đặc trưng hoặc pYIN mới. Contextual full train MAPE1,730014/0,878571/2,546783/1,603642%; soft gate1,591450/1,817182/1,978336/1,603642%,4/4train. Gate nhận đúng4/4domain đã học nhưng chỉ2/4held, hai file studio bị route thiên phone. Historical held selection giữ energy07. V1 verifier lỗi parser numeric-NaN ở một inner fold contextual zeroF0; v2 chỉ sửa parser, không refit hoặc thay số đo. Verifier v2 PASS; precheck sqrt warning giữ raw log. Prereg b2b446344eb4a789d1b7b4fdf3eb2d83eafccb3e, results43d8e34a516533c03619bab89697a3efbabecea8. Không test mới hoặc promote.

Người dùng hỏi ghép file rồi decompose; sau khi hỏi lại đã chọn hướng2 và3: tách tiếng nói/nhiễu, ghép nối để nhận ra các đoạn phone/studio. Phác thảo phân nhóm context không nhãn đã viết nhưng chưa precheck/prereg/fit; giữ tại docs/hypotheses/UNRUN_context_clustering_sketch.py và note, commit7c50e4963390ffb2f3854b2da7746738519ca5e9. Không coi draft này là experiment H79.

H79 thực tế là jointNMF4: năm full/held dictionary fits, bốn held transforms, tám decomposition proofs; noise candidate chọn bằng lowest20%RMS contribution trong fit pool, không LAB/domain. Cửa sổ native25/10; phone16k/studio44,1k giữ fs, magnitude common0–8kHz/40Hz. Audio ứng viên speech+noise khôi phục original nhưng không có clean-source GT hoặc SI-SDR. Noise candidate góp12–24% phổLAB-V nên có speech contamination. Bốn pYIN inference mới chỉ trên audio đã lọc, nguyên beta(2,8)/25ms/energy0,07. MAPE train2,396199/2,800092/0,258293/8,185025%, chỉ1/4train<2%; guard FAIL, không test/promote. Verifier độc lập PASS5models/8decompositions/4newpitchmetrics/4cachedcontrols. Prereg600321417310d2bff1de5f0c2227e856a8ea2bfb, results5bef022eca128f2d6531b5c68c492353c82eb28b. Không rerun original pYIN; nooptimizer/convergence warnings, warning70Hz giữpitch_logs.

H80 ghép physical samples bản sao đã đưa về cùng16kHz, primaryphone_F1/studio_F1/phone_M1/studio_M1 vàreverse. ReuseH79dictionary, framewiseNNLS,25ms400samples/hop10ms160samples,52contextblocks mỗistream. 1KMeans2fitprimary, reverse dùngnguyênscaler/centers; noNMFfit/pitchcalls. Domain/sex/file/joinmetadata chỉchấm saupredict. Decoded domainARI0,100870/0,052514, bestpermutationdomainaccuracy67,31%/63,46%; mỗistream báo4boundaries,match1/3,precision25%,recall33,33%. HypothesisFAIL; rawmatch2/3nhưngfalsechangesnhiều. Verifier independentFIR/FFT/NNLSKKT/context/scaler/centroidSSE/pathoptimality/ARI/matching/hash PASS. Reverse làsamefourtrainreordered, khôngunseenvalidation hoặcF0MAPE. Prereg c21c823923983f3b60719815797331d96f8f3ade, results805dd96 (xemgitHEAD/remote đầyđủ). PNGstream_groups.png đãxem. Giữ mọifailures, khôngtune rank/mapping/smoothing bằngtest.

Best retained vẫnH71/H72 energy07: meantrain1,305508%, meantest2,196094%,7/8file. Testphone_M2 4,422661% chưađạt. Không có experiment đangchạy; H81 chưađăngký. Khôngrerun H00–H80/R01/R02, khôngnotebook/original/frozen/WAV/LAB/GTedit, khôngDrive/DL/PDF/Jev/GPU/Colab/schedule/merge. XemH78_REPORT.md/H79_REPORT.md/H80_REPORT.md vàH78_H80_SYNTHESIS.md; source/registry/receipts/completion giữtrong cácfamily. Commit/push/remoteverify sau mỗi thayđổi đãkiểm.
