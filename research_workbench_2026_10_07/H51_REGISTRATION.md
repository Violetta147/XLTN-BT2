# H51 — ma trận hữu thanh có kiểm soát

Người dùng yêu cầu ablation, multiple seeds, grouped K-fold, synergy/complementary, mechanism, combinatorial matrix, permutation, qualitative/error analysis, robustness và generalization. Đăng ký trước mọi measurement H51, sau H50 thất bại. Điểm quay lại là commit H50 đã push `521a849ffbc559e55fc897b2a028e8ff694352c1`. Original/frozen/WAV/LAB giữ nguyên. Đây là ma trận hữu hạn của nhánh recovery cổ điển; không tuyên bố thử toàn bộ thuật toán/siêu tham số có thể có.

## Ma trận và thay đổi được kiểm soát

Năm blocks: P=max normalized ACF, E=log relative RMS, Z=ZCR crossings/s, S=high-frequency spectral ratio, M=13 MFCC. Năm learners: logistic C1; SVM RBF C1/gamma scale (sigmoid decision chỉ để threshold0 tương đương .5, không xác suất đã calibration); kNN5 uniform Euclidean; RF64trees/maxdepth6/minleaf4; GMM3 diagonal/reg1e-3/ninit3/tol1e-4/maxiter500. Mọi 31 tập con khác rỗng x5 learners =155 recipes. Control là hard170, tương đương không thêm recovery. Mỗi recipe đánh giá seeds11/29/47: 465 replicated recipes +3control. LR/SVM/kNN deterministic được cache và ghi rõ ba seed chỉ lặp kết quả, không ba fitted models độc lập. RF/GMM học riêng ba seed. Không chọn seed tốt nhất, không mở grid sau score. Threadpool1, không dùng DL.

Đặc trưng, geometry25/10ms, scaler, file-balanced deterministic sample indices, recovery pitch/guards giống H50. Chỉ thay tập đặc trưng và learner trong ma trận. Các ablation là inputs của learner; guard maxACF>=.6/RMS>=.01 vẫn giữ. GMM mapping dùng responsibility-weighted mean raw periodicity trong fit pool; đây là quy tắc vật lý không dùng LAB, vẫn dùng P cho mapping ngay khi P bị bỏ khỏi clustering inputs. Vì vậy không gọi cell GMM thiếu P là bỏ hoàn toàn periodicity khỏi pipeline. No online/streaming claim vì q95 mỗi waveform.

## CV, mục tiêu và seed

Nested Group K-fold với group=file: outer4fold, inner3fold; với4train, leave-one-file-out tương đương GroupKFold4. Các subsets2/3files được fit độc lập; held file không tham gia scaler/model/selection. Final innerLOFO4file. Minimax worst-file MAPE trên cả3seed, rồi mean/ID; guardF1/recall giảm<=.01/SIL+1 phải đạt ở từng seed. Không chọn recipe hoặc seed theo test/KEELE/noise/permutation. Tám gates H50, strict từng file<2, báo riêng từng seed. Count sum chỉ tính trong một seed, không nhân3 thành cỡ mẫu. N=4files, std seed là độ biến động thuật toán, không confidence interval về quần thể người nói. H50/H51 và các vòng cũ đã xem4train nhiều lần; nested vẫn exploratory.

## Ablation, synergy và permutation

Lưu tất cả465 fixedLOFO cells x4files và toàn bộ innertraces. Báo đơn đặc trưng, leave-one-block-out và toàn factorial (không chọn chỉ cell đẹp). Contrast tương tác A+B: f(A+B)-f(A)-f(B)+f(control), với f là F1 hoặc MAPE; đây là contrast phi tuyến trên nhánh thêm khung, không chứng minh quan hệ nhân quả hoặc global complementarity. Empty learner được đại diện bởi control vì không có recovery. MFCC block13dim so các block1dim là ablation nhóm, không so số chiều bằng nhau.

Permutation cho5full-feature reference recipes: mỗi heldfile x3seeds x5blocks x3repeats =900 perturbations. Shuffle cả13MFCC cùng thứ tự để giữ quan hệ nội bộ; seedpermutation SHA256(file,seed,block,repeat). Chỉ đảo inputs classifier, guard/pitch và baseline giữ raw, do đó đo dependency của classifier. Không retrain hoặc chọn recipe từ permutation. Temporal correlations bị phá; importance không có diễn giải nhân quả. Difference deltaMAPE/deltaF1 được lưu cả khi trái dấu.

## Robustness và điều kiện thu

Chỉ fit clean train pool không gồm heldorigin. Chấm12 H46 white30/white20/pink20 waveforms trên cùng grid và kế thừa nhãn/3GT của clean. Baseline noisy lấy hard170 đã đo trong bank H46, không giữ baseline clean trên noisy; hash waveform/member cache đối chiếu. Targets là latent inherited, không đo pitchGT mới. Ba perturbations không phải người nói/corpus mới hoặc ba noise seed mới. Check gain/DC là numerical invariance H50, không claim robustness với mọi channel. So control, train-selected recipe và5full-feature controls, từngseed.

Cross-condition: phone2trainfiles→studio2trainfiles và ngược lại; cùng các frozen/reference recipes, không tune vào targetcondition. Đây là2files/source và không metadata người nói độc lập; confound speaker/channel/giới tính nên không kết luận tác động nhân quả của môi trường thu.

## Generalization stage khóa riêng trước khi đọc test

Sau train/robustness/permutation, lưu H51_FROZEN_SELECTION.json; verifierPASS rồi commit/push/remoteverify trước external stage. Chấm4BT2test một lần cho selected recipe+control+5reference recipes đã định trước, mỗi3seeds. Không grid/selection trên test. Test đã có lịch sử exposure, không pristine independent. Chấm cả10KEELE microphone bằng cùng models fit4BT2train, không học/fit trên KEELE. Baseline nativeH49 giữ pitch/mask; classifier features canonical25/10 được nearest vềnative tronghalfhop+1sample, khôngsupported thì khôngrecover. KEELE reference/prediction timestamps/scoring giữ H49, không tìm offset/loại pitch ngoài70–400 của reference. GPE/VDE/FFE/RPA và file3stats báo riêng; KEELE reference window/delay caveat vẫn áp dụng, không cóSIL labels. KEELE đã được nhìn trong H49 nên đây là transfer diagnostic; nếu dùng nó định hướng tiếp, muốn kết luận độc lập phải có corpus/heldspeakers chưa dùng. Không gọi train→test là cross-dataset.

## Kiểm tra và artifacts

Sources/input hashes khóa trongregistry trướctrain. H50design verified được reuse, không chạy lại H50/H48/H49 experiments. Lưu predictors NPZ allfixedcells thay CSV lặp dài; fit pool/indices/scaler/response hashes không pickle. Verifier refit toàn bộ mô hình với thread1, độc lập kiểm stats/VUV/recovery/preservation, selectionseed/group, noise/permutation/crosscondition và external alignment/features/metrics/hashes. Verifier đọcPCM để đối chiếu features bằng fullFFT/directDCT/directACF. Report do code tạo từverifiedCSV, include fulltables, seedstats, signedablation/interaction/permutation, heatmaps và4qualitative waveform/spectrogram/estimatedF0 plots chọn định trước: filetrain sorted, minh họa fullLR seed11. Không gọi estimatedF0 là GT; chọn fixed file tránh chỉ minh họa case đẹp. Chỉlocal, noDrive/DL/Jevretry/PDF/proseskill.

Lệnh: `voicing_matrix.py register/train/external`; `verify_voicing_matrix.py train/external`; `report_voicing_matrix.py` với Python local. Không cài thư viện mới. API source: sklearn official docs của LR/GMM/SVC/kNN/RF; model parameters và runtime local được ghi, không giả bảnstable trùng bảncài. MFCC source level và failedlibrosaHTML ởH50 registration.
