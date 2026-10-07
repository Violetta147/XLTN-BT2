# H24 — AMDF tách cửa sổ V/UV và cửa sổ F0

Đăng ký trước đo ngày07/10. Rollback repository `b256282`, acceptedAMDF_energy từ `009fd2c`. Người dùng yêu cầu tiếp tục đến MAPE1–2%; mặc định AverageMAPE file-stat trên validation giữriêngfile, đang chờ lựa chọn chỉ số nếu người dùng muốn ưu tiênStd/mỗifile. Không hạ gate của các vòng cũ để báo đạt. Chỉtrainlocal/noDrive/noDeepLearning, notebookgốc giữnguyên.

Giả thuyết: giữ AMDF_score/RMS quyết định V/UV ở25ms nhưng lấy ứng viênF0 từ40ms có thể giữ recall/count của25ms và giảm lỗi std. H23 full40ms giảm MAPE nhưng bỏsótV; H24 tách hai vai trò, không chỉ chạy lại H23.

Registry2options: accepted25ms và gate25/pitch40. Hop10ms; dài40ms đúng tâmkhung25ms, đọc raw khôngfilter/pad. Nếu khung40 không đủsamples ởbiên, giữ candidates25ms của khung đó; báo fallbackcounts. Giữ native timestamps và nhãn25ms. V/UVscore/RMS/relativeRMS và cách fitpitch/energythreshold không đổi. Chỉ thay AMDF_candidate_f0/strength bằng localdips40ms cùng parabolicrefine, tốiđa12ứngviên70–400Hz. Giữ pathjump.35/octave0/median1; không dùng nhãnheld trongextract/infer.

Final chọn2options bằngLOFO4file. OuterinnerLOFO trênother3, refit3 rồi chấmouter. InnergiốngH23: finiteallMAPE, F1/recall khônggiảmquá.01, SILtăngkhôngquá1 soacceptedcùngpool; rankAvgMAPE, tieID. Gatecuối train−10% tươngđối, selected/nested−5%, nestedF1/recall≥base−.01/SIL≤base+1, từngfileMAPE≤base+2pp, phone_F1stdkhôngxấu. Khôngpromoteauto. XuấtfixedLOFOcho cả2, nested/trace/fit/contour/sourcehashes vàfigurePNG/SVG. Khôngnoise/test/mởgrid sauđo.

Mục tiêu2% chưa thể giải quyết riêng bởi pitch nếucountgiữnguyên: acceptedLOFOmeanCountMAPE6.904760%, đónggóp2.301587điểmAverageMAPE ngaycảmean/stdhoànhảo. Đây là decomposition của control, khônglowerbound cho mọi thuật toán. H24 phải báo mean/std/count riêng; không sửaF0numGT hoặc giữ/cắt output theo sốGTheld. LAB khôngcóframepitchtruth.

Kiểmtra trước chạy: baselineAMDFtrain khớpold1e-8; synthetic40ms173Hz cócandidategần173vàgaininvariant. Sauchạy verifycontours/metrics/labelhashes, predcountso vớiaccepted, fallback/sourcecoverage; replayselection từtraces. Giữfailures vàứngviênđánhđổi. Lệnh `python research_workbench_2026_10_07/amdf_dual_window.py register/check/H24`.
