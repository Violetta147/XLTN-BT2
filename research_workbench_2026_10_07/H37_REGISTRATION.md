# H37 — F0 REAPER dưới cổng V/UV Praat

Đăng ký trước đo hybrid. Rollback repository63c9b9c, original009fd2c/frozen/notebooks giữ. Control **H31 fixed Praatfiltered.30**. H36 whole REAPER nhiều std/count/SIL errors; H37 kiểm giả thuyết rằng giữ một maskV tốt rồi dùng residual pitch có thể giảm lỗi thống kê mà tránh SIL dư.

Ba options: control và REAPER **cost0.6/0.9** cùng cổng Praatfiltered voicing.30. Chỉ thay nguồn F0; gate/filters/range/hop/candidate/internalparams giữ như H31/H36. Không làm octave correction, distribution calibration, smoothing hoặc trim count trong vòng này. Không gọi đây là tác động riêng của high-pass filter.

Ghép REAPER lên nativePraatgrid bằng nearest time trong5ms+mộtmẫu, tie sớm. Tại PraatV70–400Hz, dùng REAPER khi có support và F0 trong70–400, nếu thiếu giữPraatF0 (fallback). PraatUV không nhận thêmV dù REAPER có pitch. Sau đó projection nativePraat→canonical25/10 tương tựcontrol. Lưu raw hai nguồn, rawhybrid/source tags, fallback và command/hash. Không chọn theo giới, device, filename hoặc held-stat.

Nativecalls cachemỗi file mộtPraat.30 vàhaiREAPER.6/.9=12calls. REAPER sourcepin/fullvendorhash/probes/binary giữ H36; exactwholezero policy giữ, verifier xácnhận mọi trainREAPERcallactualnative. Nofitactual_fit_files=[]/classifierNone; innerLOFO4file/outerinner3file, heldvắngkhỏipool. EligibilityfiniteMAPE/F1 vàrecallVmean≥control−.01/SIL≤control+1. RankmaxfileMAPE, mean, ID. Giữ8gatesrelativecontrol: train gain≥10%, selectedLOFO/nested≥5%, F1/recalldrop≤.01, SIL+1, nofileworse>2pp, phoneF1stdnotworse. Targetmỗi nestedfile≤2% riêng, khôngautopromote.

Prereq AMDFparity, REAPER/Praat identity, eightadapterprobes/rawfailuresretained vàpurefusiontests UV/missing/outofrange/unsupported/tie. Commit/push trước BT2hybrid. Sau đo verify48innertraces/24metrics,52uniquefitsnếufinalcontrolhoặc56nếuhybrid,12sourcecalls/12sourcegroups/12hybridgroups, allfixedMAPE/VUV/PCMunchangedinputSHA/fullsource/binary/timing vàindependenttwo-stagefusion/fallback. Mọi hybridV/count/F1/recallUV/balancedaccuracy/SIL từngfile bằngcontrol; baselineH31fixed.30 exact1e-8, poisonedlabels/stat inferenceinvariant, heldexclusions/minimax/gates vàPNG/SVG.

Source/code review level ghi REAPER_SOURCE_NOTE.md; không fullpaper/PDF claim. LAB chỉfile-stat/nhãnđoạn, khôngF0chuẩntừngkhung. Nestedexploratory từlịch sửn4. Chỉlocaltrain, khôngtest/Drive/deeplearning/MCP retry. Lệnh `reaper_praat_hybrid.py register/check/H37`; verify `verify_reaper_hybrid.py`. Anchored octave correction hoặc support-duration controller là giả thuyết khác, chưa đo ởH37.
