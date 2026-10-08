# H67 — AR4 không thắng baseline

Prereg 79538f49e4b47ecc23a4ab529b446e69fba73bf0 đã push/remote-verified trước train. Synthetic36fixtures PASS, gồm trueAR1/AR4 noise; không rerun H66/H61. 8metricgroups/588waveformnoise fits,0supervisedfits; mask/count giữ147/233/123/85. Verifier QR độc lập chạy toàn588frames; kết quả xem results/H67_verification.json (không suy PASS trước verifier hoàn tất).

|File|hard170 Average MAPE %|AR4 Average MAPE %|
|---|---:|---:|
|phone_F1.wav|0.340080|0.441333|
|phone_M1.wav|0.776151|1.057928|
|studio_F1.wav|1.473576|1.254905|
|studio_M1.wav|1.909923|2.194889|

AR4 fixed mean 1.237264% so baseline 1.124932%. Final chọnhard170; outerstudio_M1 chọnAR4 rồiheld2.194889%, baouterkhácbaseline. Nestedmean 1.196174% thay1.124932%; threeMAPEgatesFAIL/5guardsPASS, khôngeligible/promote/test. Chỉstudio_F1 tốt hơn; higherorderkhôngmanggainchung.

Cảcandidate vàbaseline macroF1 0.893976795, recallV 0.929269896, recallUV 0.899399252, balancedaccuracy 0.914334574, SIL0. NestedmeanMAE 1.170193Hz/stdMAE 0.229485Hz so baseline1.070616/.195550Hz. H66cachedAR1mean1.313829/worst1.849260; AR4khônggiữđượcworstgaincủaAR1. Khôngreruncomparison.

574/588AR4vector bịco doL1norm>.95. Đây làđiềukiệnđủconservative, khôngchứngminhnoiseexternalhayARidentifiable. CSVrho/rho_raw làlegacyfirstcoefficient, đủ4raw/scaledcoefficients ghi a1..a4/raw_a1..raw_a4 vàđượckiểmđộclập. Conditionalobjectivebỏ4samplesđầu; khônggánexactjointML/authorfastsolver. Nuisancefitwaveformkhácsupervisedfitpooltrống.

Receipt/hash/NPZ/grid/bracket/scalarmetric/selection/traces đượckiểm. Optimizer khôngindependentlyrerun; 4file/nestedexploratory/testhistoricallyexposed; khôngframeF0truth. Baselineall8vẫnFAIL. Source/literature/skillcitation ởH67_REGISTRATION.md; giữfailurevàoriginals.
