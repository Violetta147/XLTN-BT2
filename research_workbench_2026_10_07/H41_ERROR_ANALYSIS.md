# H41 — Đạt Average MAPE từng file, còn std regression

Cảfinal/outerfolds chọn cùngamdf_anchor_w25_b200 bằngfile khác. Nestedmean1.332617%,worst1.940495%; cả4AverageMAPE≤2%. Đây là mốc số đo file-stat trêntrain, khôngF0frameaccuracy/generalization trêncorpusmới.

| file | option_id | F0mean | F0std | F0num | F0mean_mape | F0std_mape | F0num_mape | average_mape | macro_f1 | recall_v | recall_uv | balanced_accuracy | false_voiced_sil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phone_F1.wav | amdf_anchor_w25_b200 | 216.103 | 21.0805 | 147 | 0.23347 | 2.33251 | 0.675676 | 1.08055 | 0.938333 | 0.941176 | 0.956522 | 0.948849 | 0 |
| phone_M1.wav | amdf_anchor_w25_b200 | 122.477 | 16.9527 | 233 | 0.988737 | 0.908681 | 0.431034 | 0.776151 | 0.928721 | 0.946721 | 0.967742 | 0.957232 | 0 |
| studio_F1.wav | amdf_anchor_w25_b200 | 231.657 | 37.0039 | 123 | 0.896051 | 0.554161 | 3.14961 | 1.53327 | 0.900407 | 0.96748 | 0.833333 | 0.900407 | 0 |
| studio_M1.wav | amdf_anchor_w25_b200 | 116.905 | 25.8302 | 85 | 0.0045515 | 2.1584 | 3.65854 | 1.94049 | 0.808446 | 0.861702 | 0.84 | 0.850851 | 0 |

## Vì sao chưa promote?

Phone_F1stdMAPE2.332506% soPraatcontrol.851866%;AverageMAPEphone1.080551% so.595007%. GatephoneF1stdnotworseFAIL, bảygatekhácPASS. Không đổi gate sauđo, không gọiallgatesPASS hoặcpromotefrozen. StudioM1AverageMAPE3.175722→1.940495%/std5.456594→2.158397%; studioF1std1.291866→.554161%; phoneM1std1.605526→.908681%.

## Voicing/count giữ nguyên

Dựđoáncount147/233/123/85 soGT148/232/127/82. CountMAPE.675676/.431034/3.149606/3.658537%; macroF1.893977/recallV.929270/SIL0 aggregate. Khôngxóa/thêmframe hoặcfitheldstats đểđạt2%. Count khôngbằngGTnhưngtrungbìnhbaerrors≤2%; Avg≤2 khôngbảođảmmỗicomponent≤2.

## Tất cả cấu hình và nguồn

| option_id | file | F0mean_mape | F0std_mape | F0num_mape | average_mape |
| --- | --- | --- | --- | --- | --- |
| praat7_filtered_v0.3 | phone_F1.wav | 0.257478 | 0.851866 | 0.675676 | 0.595007 |
| praat7_filtered_v0.3 | phone_M1.wav | 1.00921 | 1.60553 | 0.431034 | 1.01526 |
| praat7_filtered_v0.3 | studio_F1.wav | 0.67006 | 1.29187 | 3.14961 | 1.70384 |
| praat7_filtered_v0.3 | studio_M1.wav | 0.412037 | 5.45659 | 3.65854 | 3.17572 |
| amdf_anchor_w25_b50 | phone_F1.wav | 0.158957 | 0.910314 | 0.675676 | 0.581649 |
| amdf_anchor_w25_b50 | phone_M1.wav | 1.01189 | 1.10472 | 0.431034 | 0.849214 |
| amdf_anchor_w25_b50 | studio_F1.wav | 0.739199 | 0.781379 | 3.14961 | 1.55673 |
| amdf_anchor_w25_b50 | studio_M1.wav | 0.291399 | 3.84148 | 3.65854 | 2.59714 |
| amdf_anchor_w25_b100 | phone_F1.wav | 0.165821 | 2.64696 | 0.675676 | 1.16282 |
| amdf_anchor_w25_b100 | phone_M1.wav | 1.0629 | 1.37239 | 0.431034 | 0.955443 |
| amdf_anchor_w25_b100 | studio_F1.wav | 0.683719 | 0.891108 | 3.14961 | 1.57481 |
| amdf_anchor_w25_b100 | studio_M1.wav | 0.060379 | 2.88731 | 3.65854 | 2.20208 |
| amdf_anchor_w25_b200 | phone_F1.wav | 0.23347 | 2.33251 | 0.675676 | 1.08055 |
| amdf_anchor_w25_b200 | phone_M1.wav | 0.988737 | 0.908681 | 0.431034 | 0.776151 |
| amdf_anchor_w25_b200 | studio_F1.wav | 0.896051 | 0.554161 | 3.14961 | 1.53327 |
| amdf_anchor_w25_b200 | studio_M1.wav | 0.0045515 | 2.1584 | 3.65854 | 1.94049 |
| amdf_anchor_w40_b50 | phone_F1.wav | 0.304662 | 0.585459 | 0.675676 | 0.521932 |
| amdf_anchor_w40_b50 | phone_M1.wav | 0.994341 | 1.41355 | 0.431034 | 0.946308 |
| amdf_anchor_w40_b50 | studio_F1.wav | 1.01178 | 0.747919 | 3.14961 | 1.63643 |
| amdf_anchor_w40_b50 | studio_M1.wav | 0.270333 | 4.81413 | 3.65854 | 2.91433 |
| amdf_anchor_w40_b100 | phone_F1.wav | 0.32755 | 0.45412 | 0.675676 | 0.485782 |
| amdf_anchor_w40_b100 | phone_M1.wav | 0.937248 | 1.29229 | 0.431034 | 0.886857 |
| amdf_anchor_w40_b100 | studio_F1.wav | 1.022 | 1.06634 | 3.14961 | 1.74598 |
| amdf_anchor_w40_b100 | studio_M1.wav | 0.276097 | 4.82826 | 3.65854 | 2.92096 |
| amdf_anchor_w40_b200 | phone_F1.wav | 0.239496 | 0.828316 | 0.675676 | 0.581162 |
| amdf_anchor_w40_b200 | phone_M1.wav | 1.02807 | 1.62114 | 0.431034 | 1.02675 |
| amdf_anchor_w40_b200 | studio_F1.wav | 0.958137 | 1.50536 | 3.14961 | 1.87103 |
| amdf_anchor_w40_b200 | studio_M1.wav | 0.411125 | 4.95254 | 3.65854 | 3.0074 |
| amdf_anchor_w55_b50 | phone_F1.wav | 0.306901 | 0.316599 | 0.675676 | 0.433059 |
| amdf_anchor_w55_b50 | phone_M1.wav | 0.937457 | 1.00891 | 0.431034 | 0.792467 |
| amdf_anchor_w55_b50 | studio_F1.wav | 0.981035 | 0.78512 | 3.14961 | 1.63859 |
| amdf_anchor_w55_b50 | studio_M1.wav | 0.235488 | 5.10684 | 3.65854 | 3.00029 |
| amdf_anchor_w55_b100 | phone_F1.wav | 0.377613 | 1.05029 | 0.675676 | 0.701193 |
| amdf_anchor_w55_b100 | phone_M1.wav | 0.910598 | 1.89738 | 0.431034 | 1.07967 |
| amdf_anchor_w55_b100 | studio_F1.wav | 1.35726 | 0.424311 | 3.14961 | 1.64373 |
| amdf_anchor_w55_b100 | studio_M1.wav | 0.0277916 | 3.91845 | 3.65854 | 2.53492 |
| amdf_anchor_w55_b200 | phone_F1.wav | 0.407586 | 0.768156 | 0.675676 | 0.617139 |
| amdf_anchor_w55_b200 | phone_M1.wav | 0.955417 | 2.24692 | 0.431034 | 1.21112 |
| amdf_anchor_w55_b200 | studio_F1.wav | 1.2094 | 2.66904 | 3.14961 | 2.34268 |
| amdf_anchor_w55_b200 | studio_M1.wav | 0.804553 | 7.6821 | 3.65854 | 4.0484 |

| option_id | file | amdf_dip | praat_disagreement | praat_no_candidate | praat_window_unsupported | praat_control | unvoiced |
| --- | --- | --- | --- | --- | --- | --- | --- |
| praat7_filtered_v0.3 | phone_F1.wav | 0 | 0 | 0 | 0 | 147 | 173 |
| amdf_anchor_w25_b50 | phone_F1.wav | 138 | 9 | 0 | 0 | 0 | 173 |
| amdf_anchor_w25_b100 | phone_F1.wav | 145 | 2 | 0 | 0 | 0 | 173 |
| amdf_anchor_w25_b200 | phone_F1.wav | 145 | 2 | 0 | 0 | 0 | 173 |
| amdf_anchor_w40_b50 | phone_F1.wav | 130 | 17 | 0 | 0 | 0 | 173 |
| amdf_anchor_w40_b100 | phone_F1.wav | 143 | 4 | 0 | 0 | 0 | 173 |
| amdf_anchor_w40_b200 | phone_F1.wav | 147 | 0 | 0 | 0 | 0 | 173 |
| amdf_anchor_w55_b50 | phone_F1.wav | 123 | 24 | 0 | 0 | 0 | 173 |
| amdf_anchor_w55_b100 | phone_F1.wav | 139 | 8 | 0 | 0 | 0 | 173 |
| amdf_anchor_w55_b200 | phone_F1.wav | 146 | 1 | 0 | 0 | 0 | 173 |
| praat7_filtered_v0.3 | phone_M1.wav | 0 | 0 | 0 | 0 | 235 | 177 |
| amdf_anchor_w25_b50 | phone_M1.wav | 229 | 4 | 0 | 0 | 2 | 177 |
| amdf_anchor_w25_b100 | phone_M1.wav | 233 | 0 | 0 | 0 | 2 | 177 |
| amdf_anchor_w25_b200 | phone_M1.wav | 233 | 0 | 0 | 0 | 2 | 177 |
| amdf_anchor_w40_b50 | phone_M1.wav | 224 | 9 | 0 | 0 | 2 | 177 |
| amdf_anchor_w40_b100 | phone_M1.wav | 232 | 1 | 0 | 0 | 2 | 177 |
| amdf_anchor_w40_b200 | phone_M1.wav | 233 | 0 | 0 | 0 | 2 | 177 |
| amdf_anchor_w55_b50 | phone_M1.wav | 218 | 15 | 0 | 0 | 2 | 177 |
| amdf_anchor_w55_b100 | phone_M1.wav | 231 | 2 | 0 | 0 | 2 | 177 |
| amdf_anchor_w55_b200 | phone_M1.wav | 233 | 0 | 0 | 0 | 2 | 177 |
| praat7_filtered_v0.3 | studio_F1.wav | 0 | 0 | 0 | 0 | 123 | 160 |
| amdf_anchor_w25_b50 | studio_F1.wav | 120 | 3 | 0 | 0 | 0 | 160 |
| amdf_anchor_w25_b100 | studio_F1.wav | 122 | 1 | 0 | 0 | 0 | 160 |
| amdf_anchor_w25_b200 | studio_F1.wav | 123 | 0 | 0 | 0 | 0 | 160 |
| amdf_anchor_w40_b50 | studio_F1.wav | 107 | 16 | 0 | 0 | 0 | 160 |
| amdf_anchor_w40_b100 | studio_F1.wav | 120 | 3 | 0 | 0 | 0 | 160 |
| amdf_anchor_w40_b200 | studio_F1.wav | 123 | 0 | 0 | 0 | 0 | 160 |
| amdf_anchor_w55_b50 | studio_F1.wav | 97 | 26 | 0 | 0 | 0 | 160 |
| amdf_anchor_w55_b100 | studio_F1.wav | 113 | 10 | 0 | 0 | 0 | 160 |
| amdf_anchor_w55_b200 | studio_F1.wav | 123 | 0 | 0 | 0 | 0 | 160 |
| praat7_filtered_v0.3 | studio_M1.wav | 0 | 0 | 0 | 0 | 85 | 184 |
| amdf_anchor_w25_b50 | studio_M1.wav | 83 | 2 | 0 | 0 | 0 | 184 |
| amdf_anchor_w25_b100 | studio_M1.wav | 85 | 0 | 0 | 0 | 0 | 184 |
| amdf_anchor_w25_b200 | studio_M1.wav | 85 | 0 | 0 | 0 | 0 | 184 |
| amdf_anchor_w40_b50 | studio_M1.wav | 76 | 9 | 0 | 0 | 0 | 184 |
| amdf_anchor_w40_b100 | studio_M1.wav | 85 | 0 | 0 | 0 | 0 | 184 |
| amdf_anchor_w40_b200 | studio_M1.wav | 85 | 0 | 0 | 0 | 0 | 184 |
| amdf_anchor_w55_b50 | studio_M1.wav | 75 | 10 | 0 | 0 | 0 | 184 |
| amdf_anchor_w55_b100 | studio_M1.wav | 83 | 2 | 0 | 0 | 0 | 184 |
| amdf_anchor_w55_b200 | studio_M1.wav | 85 | 0 | 0 | 0 | 0 | 184 |

Verifier độc lập:160innertraces/168fits/24metrics/40fixedgroups;4actualPraatcalls/12featuregroups/1764fullcurves đều tái tính bằng côngthứcNAMDF độc lập từnormalizedPCM, start/inputSHA/dipparabola/tie/band/fallback/tags/source/timeprojection/MAPE/VUV. KhôngWAV/backend/testcallmới trongdiagnostic.

AAMDFpaperexactmapping vẫnthiếucôngthức quaHTML/code; AMDF_ANCHOR_SOURCE_NOTE.md ghiabstract-only vàworkflowcitation. H41 engineeringrule khônggáncho tácgiảpaper. Hướngquality/dualwindowcontroller cóthểkhảo sát riêng, phảiprereg trướcmeasure; không chọnwindowtheofile/giới/device hoặcGTstd.
