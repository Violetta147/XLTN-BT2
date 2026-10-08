# Bắt đầu chat mới — XLTN / BT2

Cập nhật 08/10/2026, sau yêu cầu tiếp tục trong chat mới. **H63 đã đăng ký, push/xác minh remote, đo train và verifier PASS; không promote, không test mới. Không có thí nghiệm đang chạy; H64 mới được nêu hướng unanchoredHPS, chưa đăng ký/đo.** Người dùng đang bổ sung câu hỏi về skill ML/pipeline/kiến trúc/thí nghiệm. Trạng thái dừng sauH62 ởbản trước là lịch sử, không thay yêu cầu tiếp tục mới.

Đọc [H63_REPORT.md](research_workbench_2026_10_07/H63_REPORT.md) trước bước mới. H63 là boundedlogHPS3/5,25ms,mask/countgiữ: studio_F1 có gain1.473576→1.319059%, nhưngstudio_M1 1.909923→2.678125% ởHPS5; finalhard170, outerstudio_M1hps5, nested1.124932→1.316983%; baMAPEgatesFAIL. Preregc62ba22beeeeeead694783134cb5c307c18c4b1e vàresultsc60008241a015ab01c2893c363eae5d38a081a04 đãpush/remoteverified. KhôngrerunH63/H00–H62. Baselineall8FAIL vànotebookSHAgiữ.

Đã rà nguồn PEFAC mới tại [PEFAC_SOURCE_REVIEW.md](research_workbench_2026_10_07/PEFAC_SOURCE_REVIEW.md): `MFA-X-AI/pyvoicebox` pin700aa87 dùngACF tronghàmv_fxpefac, thiếulog-frequency/amplitudecompression/GMM/DP củamãImperial pinf671f6d. Khôngcài/chạy/chấm nó nhưPEFAC. Snapshots/license/hashes lưu; MATLAB/OctavekhôngthấyPATH. Đây là sourceidentityreview, không vòngaccuracy hoặc proofmọiPEFACFAIL. Chưa cài skill mới hoặc dùngpremiumplatform.

Mục tiêu còn thiếu: cùng một pipeline cho **từng file trong cả tám file có Average MAPE <2%**. Cải thiện BT2 tìm F0 trước; bài phân đoạn tiếng nói/khoảng lặng mới của thầy trong `../XLTN-BT1-BO-SUNG/` làm sau. Chưa chuyển bài hoặc tạo notebook thay bản đã nộp.

## Khôi phục nhanh

1. Đọc quy tắc workspace XLTN của người dùng và [AGENTS.md](AGENTS.md) trong repository.
2. Đọc file này, [H63_REPORT.md](research_workbench_2026_10_07/H63_REPORT.md); khi cần lịch sử đọc [H62_REPORT.md](research_workbench_2026_10_07/H62_REPORT.md) và [ma trận ba vòng](research_workbench_2026_10_07/figures/LOOP_H60_H62_train_matrix.png). Không quét lại toàn bộ STATE hoặc rerun để lấy lại context.
3. Kiểm tra Git branch/status/HEAD/remote hiện tại. Mốc kết quả đã push và xác minh remote trước bàn giao: `bc42283fcb2ec76147a22241faf4c937aef606ba`. HEAD có thể có commit hồ sơ bàn giao sau mốc này; xác minh live, không coi checkpoint là HEAD bắt buộc.
4. Khi cần chi tiết: [H60_REPORT](research_workbench_2026_10_07/H60_REPORT.md), [H61_REPORT](research_workbench_2026_10_07/H61_REPORT.md), [coverage](research_workbench_2026_10_07/EXPERIMENT_COVERAGE.md), [protocol](research_workbench_2026_10_07/PROTOCOL_F0.md). [STATE](research_workbench_2026_10_07/STATE.md) và [handoff cũ](docs/handoff/START_NEXT_CHAT_before_H60_H62_2026_10_08.md) là lịch sử; các dòng cũ “tiếp tục/chưa hoàn tất” không thay trạng thái dừng hiện tại.

Repository: `C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2`; branch `codex/train-mape-investigation`; remote `https://github.com/Violetta147/XLTN-BT2.git`. PowerShell; Python `C:/Users/violet/miniconda3/python.exe`. Không thấy MATLAB/Octave trong PATH ở phiên này. Dùng safe.directory cho Git:

```powershell
git -c 'safe.directory=C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2' status --short --branch
git -c 'safe.directory=C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2' rev-parse HEAD
git -c 'safe.directory=C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2' ls-remote origin refs/heads/codex/train-mape-investigation
```

## Cấu hình nghiên cứu vẫn được giữ

`hard170`: Praat7 filtered ACF voicing .30, range70–400; NAMDF ứng viên gần Praat trong200cents; pitch25ms chuyển40ms theo high-frequency ratio<=.05 và gatePraat>=170Hz. Canonical25ms/10ms, population std, nhãn LAB tại tâm. Đây là baseline nghiên cứu, **khác kết quả screenshot của notebook đã nộp**; không trộn MAPE hai pipeline.

| File | Train Average MAPE (%) | File | Test đã lưu Average MAPE (%) |
|---|---:|---|---:|
| phone_F1.wav | 0.340080 | phone_F2.wav | 4.197313 |
| phone_M1.wav | 0.776151 | phone_M2.wav | 6.833750 |
| studio_F1.wav | 1.473576 | studio_F2.wav | 5.063462 |
| studio_M1.wav | 1.909923 | studio_M2.wav | 2.114791 |

Baseline4/4train dưới2%,0/4test dưới2%: **all8 FAIL**. Số test lấy từ [H48 status](research_workbench_2026_10_07/ALL_FILES_STATUS.md), không đo lại trong H60–H62. Chưa promote/frozen rewrite và chưa có notebook mới được chấp nhận. Bản người dùng nộp là `../turn-in-assignment - Copy/BT2_ACF_best_no_energy_set.ipynb`; SHA256 giữ nguyên `b643a1cdf6ac67d3e1dcacf9ce45ea4c49625da114e8c07f402c3fca5d13f85c`.

## Ba vòng cuối đã hoàn tất

| Vòng | Giả thuyết và phạm vi đo | Kết luận |
|---|---|---|
| H60 | MAPS từ author Python; whole q=.2/.5/.8 và pitch-only;20 unique train groups | Final/outer hard170. Pitch-only studio_M1 37.506279%; không thắng. |
| H61 | Custom harmonic least-squares, order3/5, ±100cents;12 unique train groups; giữ mask/count | phone_F1 order5 .303953%,studio_F1 order3 1.254701% tốt riêng; studio_M1>2%. Final hard170; outer studio_M1 chọnorder3 rồi heldscore2.193784%. |
| H62 | Logistic PEZS4 so PEZS+coherence6; recovery và reject0/.1/.25;22 fits/140 groups/112 inner traces | Brier tốt hơn cả4heldtrain nhưng MAPE không tốt chung; final/outer hard170. studio_F1 có gain, phone/studio_M1 vẫn xấu. |

Tất cả tám gate chưa cùng đạt ở các vòng này; không đo test mới. Prereg đã commit/push/remoteSHAverify trước train: H60 `2488ef49087ab7fe026ee51075d05880091c763a`; H61 `079cbad1b9dcbf1e22e2b7ab927133fc72993c31`; H62 `b2af88eb635405a838d596d64b1b853a4ba1484c`. Reports đã commit riêng; không rerun.

Verifier H60v1 exact-path FAIL do tie; giữ `H60_path_tie_audit.json`. V2 kiểm log-objective độc lập khớp (0gap cả4file), projection/metric/selection PASS20groups; sửa verifier sau đo được ghi rõ, không đổi inference/config. MAPS vendor commitd51d0e870625b4b62152900cfe627b8127c522d7 byte-identical, GPLv3; ba runtime fixes,48kHz/2048nativewindow khác canonical, fixed spline clip. Initial25ms syntheticFAIL được giữ. Không claim exact upstream pipeline hoặc framepitchGT.

H61 QR/basis/Hann/grid/localbracket/metric PASS12groups; optimizer không refit độc lập. H62 QRfeature/scalarresponse/fitpool/designhash/gradient/mask/pitch/metric/selection PASS140groups/22models. H61/H62 là code custom, không fastF0Nls reference port. Algorithm deterministic; seed11/29/47 ở các syntheticfixtures là noise seed, không3MLtrainingseeds. H62 logistic học LABEL chỉ đúngfitpool; scaler cũng vậy.

Artifacts chính trong `research_workbench_2026_10_07/results/`: `H60/H61/H62_train_experiment.json`, `H60/H61/H62_verification.json`, CSV fullmetrics/innertraces/audits/changedcases, NPZproofs; `LOOP_H60_H62_SUMMARY.csv` tóm tắt số đã đo. Sources `maps_adapter.py/maps_experiment.py`, `harmonic_nls.py/nls_experiment.py`, `harmonic_voicing.py`, các registry/prereg/verifier tương ứng. Sources/config/data hash được kiểm trước đo; không chỉ có bảng cuối.

## Giới hạn và công việc còn mở

- Ground truth teacher3GT chỉ mean/std/count cả file; LAB V/UV/SIL theo đoạn. Không có F0 chuẩn từng timestamp. LABV không đồng nghĩa số khungF0 chuẩn; contourACF/MAPS/NLS và mean của file không thay framegroundtruth.
- Bốn trainingfiles tạo nested4outer/3inner, final4LOFO. Minimax worst-file MAPE→mean→ID và guard F1/recall/SIL; tám gate giữ nguyên. Repeated selection trên4train và lịch sử đã xem test khiến kết quả exploratory. Không tuyên bố độc lập mới vì vừa freeze hoặc dùngKfold. Không random split frames hoặc coi augmentation là thêm speaker mới.
- Nguồn dữ liệu: [provenance report](research_workbench_2026_10_07/DATASET_PROVENANCE_REPORT.md) đã thấy8WAV byte-identical với GitHubdthle; LAB nội dung khớp sau normalize newline. Hai bản stats khácmean/std, không chỉ thêmF0num; quy trình tạo reference/tác giả thu âm chưa rõ. Transcript “Anh vẫn có thể làm trọng tài”, giả thuyết4người/2nam2nữ và môi trườngphone/studio do người dùng cung cấp, speaker/session metadata chưa xác minh. Không kết luận thầy ghi nhầm hoặc testdata lỗi.
- Đã thử ML/MFCC/H51matrix, augmentation, KEELE10speaker, YAAPT/SRH/cepstrum/temporalpath/GMMmapping, H60–H63. Không chạy lại các vòng đã hoàn tất. BoundedHPS3/5 H63 đãđo; whole/unanchoredHPS, PEFAC thật và AR-noise harmonicmodel chưađo đầyđủ. H64chưađăngký, sourcereviewPEFAC khôngphải kếtquảđo.
- Bước tiếp theo có giá trị: xác minh cách tạo reference/timing, hoặc dữ liệu có frameF0GT và speaker mới; nếu chọn algorithm mới cần một giả thuyết hẹp và prereg riêng. Không kết luận “data ít là nguyên nhân duy nhất” từ các failure.
- Jev toolkit đã chép `C:/Users/LAPTOP T&T/Downloads/Jev_System_One_Reusable_Kit`; không cần đóng gói lại. Jev không được gọi ởH60–H62. Nhánh MCP lỗi lịch sử không tự retry; chỉ thử lại khi user yêu cầu. Đọc docs/jev/HUONG_DAN_JEV.md trước usecase mới, không giao tính MAPE/hash/LAB cho Jev.

Local only; tuyệt đối khôngGoogleDrive, khôngdeep learning/PDF/PDFextraction; khôngprose/reader-firstskill. Literature-review local dùng HTML/abstract/mã tác giả, cósource/provenance, khôngfullpaperclaim. Không sửa WAV/LAB/teacher3GT/notebookgốc/frozen. Mỗi thay đổi đã kiểm tra commit riêng rồi push/remoteSHAverify; khôngmerge main. Khôngschedule/automaticretry hoặc khởi động lại loop khi chỉ đọc bàn giao.

## Prompt để tiếp tục trong chat mới

> Đọc AGENTS.md và START_NEXT_CHAT.md trong XLTN-BT2, khôi phục trạng thái sau H62 rồi tiếp tục cải thiện BT2 trước bài phân đoạn mới. Không chạy lại các thí nghiệm đã hoàn tất. Giữ mục tiêu mỗi file trong cả8file Average MAPE<2%, chọn trên train theo file, đăng ký và push/xác minh remote trước đo; giữ mọi failure, original/frozen/GT và giới hạn test đã từng xem.
