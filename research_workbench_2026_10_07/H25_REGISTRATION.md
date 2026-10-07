# H25 — học quyết định V/UV cho AMDF

Đăng ký trước đo; rollback/control9456632. Giữ original accepted009fd2c để đối chiếu. Control của H25 là cấu hình cố định H24 gate25/pitch40 có LOFO5.721646%, khác selection nested H24(5.671863%). Không thay frozen_config gốc. Người dùng làm rõ: **mỗi file Average MAPE≤2%**; đây là mục tiêu, không cam kết thuật toán chắc đạt.

Giả thuyết: đường quyết định tuyến tính học từ AMDF_score và relativeRMS có thể giảm FN và countMAPE so với cắt từng ngưỡng, trong khi energy gate giữ SIL thấp. Đây là thử nghiệm AMDF riêng, không mượn số đo ACF Logistic Regression.

4options: control và LR C0.1/1/10. Chỉ thay classifier. Scaler và LR fit trên V/UV của pool fit; trọng số mỗi file×class cân bằng, tổng weight bằng số khung V/UV pool. Không dùng SIL làm negative trong LR; giữ energy gate fit V/SIL như control. Probability threshold0.5, maxiter500 và assert converged. Fit scaler weighted đúng cùng pool, không dùng held. Feature raw AMDF_score và relativeRMS, không log/ZCR/newfilter. Giữ decision25ms/hop10ms, pitch40ms cùngtâm/fallback25, pathjump.35/octave0/median1/range70–400. C được chọn bằng inner folds, không chỉnh bằng test.

Final LOFO4file và outer nested4fold (mỗi inner fit2/eval1); tất cả evidence/fitIDs/rawmetrics lưu. Inner eligible finiteallMAPE, macroF1/recallV≥control−.01, SIL≤control+1. Vì mục tiêu từngfile, rank **max file Average MAPE**, rồi mean, rồi lexicalID; không dùng mean làm rank đầu. Fallbackcontrol. Báo fixedLOFOcho cả4, selectedLOFO riêng, nested riêng.

Gate cải thiện giữ nguyên: train−10% tươngđối; selectedLOFO vànested−5%; nestedF1/recallV≥control−.01, SIL≤control+1, khôngfileMAPExấu>2pp, phoneF1stdkhôngxấu. Mục tiêu từngfile≤2% báo thêmriêng, không thay gate sauđo. Không auto-promote. Giữ thất bại. HashWAV/LAB/source, poisoningheldGTinvariant, kiểmtra exactcontrol1e-8 trước chạy; sau chạy tính lại contour/stat/classification, replay worst-file selection vàgates. FiguresPNG/SVG. Chỉ trainlocal, noDrive/noDL, không sửaGT/count theo held, không mở test.

Lệnh: `python research_workbench_2026_10_07/amdf_logistic.py register/check/H25`. Cố định grid4 trước đo, không thêm C/threshold sau khi xem H25.
