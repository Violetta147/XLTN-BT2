# H65 — chỉ global HPS3 sau H64 synthetic FAIL

Rollback `5668306620062a9fde8fc71648563aec371e3bb3`; accepted hard170. H64 thất bại synthetic, không đoBT2; giữ nguyên mọi failure. H65 là family riêng đăng ký trướcBT2, **không đổi H64 thànhPASS**. Options chỉ hard170 vàglobal_hps_3, khôngorder5 hay search thêm hậu nghiệm.

Giả thuyết: objective3 họa âm đã đạt18fixture có thể dùng toàn dải70–400Hz mà giữmask/count để cải thiện thống kê F0. SoH63 chỉ thay phạm vi tìmF0; soH64 loạioption5 theo phép kiểm synthetic trước dữ liệuBT2, không theo heldtest hoặcBT2metric. Cũng có khả năng sai octave và giảm độ chính xác.

Algorithm byte-identical `global_harmonic_product.py` đã commitH64: grid3301Hz70.0..400.0 step.1, DC/Hann/FFTnextpower2≥16×length, spectrum/max/floor1e-12, sum3log(interp amplitude(hf)), tiesHznhỏ nhất, zero→anchor. PCMcanonical25ms/hop10ms, voicing/labels/reference/frozen không đổi.

Không chạy lại fixtureH64. `register` kiểm hash và tái dùng chính18order3PASS ở `results/H64_precheck.json`, fs16k/44.1k, seeds11/29/47, F090/200/320, error<100cents, fullgrid directDFT/objective/argmax, gain/DC, zero fallback. Không loại một fixtureorder3 nào. H64original36fixtures/6fail và report vẫn được bảo vệ trongregistry. Seed chỉfixture noise.

Đo8unique train groups,32innertraces,24train/LOFO/nestedsummaryrows, khônglabel/modelfit. BaselineH47contour đã lưu/hash, khôngrerunaccepted inference. Nested4outer/3inner/final4LOFO chọn minimaxworst-file AverageMAPE→mean→ID; guardfinite,F1/recallVdrop≤.01,SIL+1. Támgate `voicing_recovery.gates` giữ. Khôngrandomframesplit; bốnfile không chứng minh bốn người mới. Test đãexposed vànestedexploratory.

AverageMAPE dựa thống kêF0mean/std/count cảfile, khôngframeF0GT. BáoMAEmean/std/count,macroF1,recallV/UV,balancedaccuracy,SIL vàcount. Mục tiêuall8từngfile AverageMAPE<2%. Hashsourceregistry/precheck/data/notebookkiểm trước đo; preregcommit/push/remoteSHAverify; verifier directDFT/scalarinterpolation/log/gridargmax vàscalarstatistics/selections/inner membership, untouchedgate.

FAIL: giữbằngchứng, khôngpromote/test. Eligible:lockconfig vàcommit/push/verify trước1test mới. KhôngDrive/DL/PDF/Jev/schedule/retry. Người dùng sẵn sàng chạyColab khiGPUthiếu; vòngclassicalCPU này không cầnGPU. `ml-pipeline-workflow` dùng quản lý config/hash/cache/ablation nhưH64, không tựđo hay cấpquyền.
