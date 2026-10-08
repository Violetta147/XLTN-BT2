# H68 — PEFAC chính thức chưa vượt hard170

Đã chạy mã Imperial VOICEBOX PEFAC nguyên bản, pin f671f6de6afb0206813bc539fa41b9043f68c6bd, trong GNU Octave11.3.0 + image2.20.0. **Final và cả bốn outer folds đều chọn hard170; không promote hoặc test mới.** Đây là kết quả của cấu hình đã đăng ký trên BT2, không kết luận mọi PEFAC hoặc mọi cấu hình đều thất bại.

Đăng ký93e0e8f được push trước đo; commit dffb1d4 giữ lại quy tắc Git MAPS cũ bên cạnh quy tắc bảo toàn byte PEFAC và được remote-verified trước train. Receipt lưu measurement HEAD `dffb1d44a1cbbfdb37b1800618a13207d89a30cd`. Lúc thêm rule PEFAC đã ghi đè một rule MAPS; đã khôi phục trước inference, không đổi file MAPS. Upstream v_fxpefac bằng byte với snapshot đã rà và Git blob; toàn dependency closure có manifest/hash/license. Không dùng Python ACF giả PEFAC.

Một native inference cho mỗi trainfile, bốn projections: whole pv>.2/.5/.8 và pitch-only. Whole dùng V/UV PEFAC; pitch-only giữ mask/count baseline và fallback ở thiếu native coverage. Parameters tinc10ms/flim70–400; native bandwidth20Hz và window do upstream quyết định, khác canonical scoring25ms/10ms. Không padding hoặc count trimming theo GT, không chỉnh source hoặc fit GMM từ BT2. 4 native calls,0 supervised fits,20 metric groups,80 inner traces,24 summary rows. Train runtime 11.612s, không suy đây là benchmark tổng setup/verification.

| File | hard170 | PEFAC whole .2 | whole .5 | whole .8 | pitch-only |
|---|---:|---:|---:|---:|---:|
|phone_F1.wav|0.340080|41.284721|28.360641|27.929745|24.450745|
|phone_M1.wav|0.776151|21.102010|19.356367|28.787341|6.440169|
|studio_F1.wav|1.473576|12.301312|9.549223|8.572011|6.626914|
|studio_M1.wav|1.909923|39.980170|9.605462|2.901574|2.468976|

Các ô là Average MAPE (%) so mean/std/count teacher3GT, không F0 chuẩn từng khung. Không option PEFAC nào có một file train dưới2%; bảng giữ toàn bộ negative results. Pitch-only phone_F1 std34.999768Hz so chuẩn20.6Hz làm MAPE tăng; không gọi contour hay một octave sửa đổi là pitch đúng khi thiếu frameGT.

| Option | Mean MAPE % | MAE mean Hz | MAE std Hz | Macro F1 | Recall V | Recall UV | Balanced accuracy | SIL false voiced | Tổng count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|hard170|1.124932|1.070616|0.195550|0.893977|0.929270|0.899399|0.914335|0|588|
|pefac_whole_q0.2|28.667053|7.446726|15.147325|0.719771|0.934754|0.464248|0.699501|6|663|
|pefac_whole_q0.5|16.717923|5.708020|8.820404|0.788510|0.891593|0.699059|0.795326|4|591|
|pefac_whole_q0.8|17.047668|5.722624|6.781851|0.743155|0.756583|0.846016|0.801300|1|469|
|pefac_pitch_only|9.996701|3.806223|5.802065|0.893977|0.929270|0.899399|0.914335|0|588|

Final/nested đều baseline1.124932%, F1.893977, recallV.929270/UV.899399, balanced.914335, SIL0; ba gate cải thiện MAPE FAIL, năm guard PASS. each_nested_file_below_2=True chỉ vì giữ baseline trên train; không đồng nghĩa PEFAC đạt mục tiêu hoặc all8 PASS. All8 cached test vẫn0/4 dưới2%.

Verifier PASS20groups: hashes source/exe/image/protected/output, GMM log-density/posterior độc lập từ các constants và features đã lưu, DP recurrence/path/native selected candidate, nearest-time projection/range/mask/fallback, scalar statistics/VUV metrics, selection và inner/summary membership. Không dựng độc lập spectrogram/LTASS amplitude compression/peak extraction, không MATLAB binary parity hay calibration proof. Code nguyên bản chạy trong Octave không tự chứng minh mọi numerical stage tương đương MATLAB.

Precheck tích hợp6fixture PASS, accuracy diagnostic4/6 PASS: true300Hz chọn150.571Hz ở cả hai sample rates. Runtime probe trước đó200Hz chọn100.5864Hz cũng được giữ. Đây là octave/subharmonic failure của estimator trên synthetic, không runtime integration failure; gate tích hợp đã ghi riêng từ trước BT2. Gain test12nativecalls chỉ synthetic, không training seed replication. Initial40file closure thiếu legacy filtbankm đã lỗi exit1; bổ sung helpers cùng pinned archive, không sửa algorithm. PROVENANCE giữ lỗi đó; không che hoặc gọi accuracy toàn bộ PASS.

Original/frozen/WAV/LAB/teacherGT và notebook đã nộp giữ nguyên. Test đã có lịch sử được xem; nested exploratory, chỉ4train và không random frame split. Không Drive/DL/PDF/Jev/schedule. Octave đã cài local, chưa cần Colab.

Nguồn/code/content level, query failure Crossref, skill citation ở H68_REGISTRATION.md và PEFAC_SOURCE_REVIEW.md; nguồn chính [VOICEBOX v_fxpefac](https://github.com/ImperialCollegeLondon/sap-voicebox/blob/f671f6de6afb0206813bc539fa41b9043f68c6bd/voicebox/v_fxpefac.m). Không full-paper claim. Artifacts full ở results/H68_*; executable/dependency source hashes và exact command/bridge/PCM receipt đủ để tái lập cùng môi trường.
