# Phiên thí nghiệm trực tiếp ngày 07/10

Không schedule, không deadline04:00 của phiên cũ. Tiếp tục từ eceb094. Giữ champion009fd2c acceptedACF và notebook gốc, local/noDrive/no deep learning. Người dùng cho phép thay frame/hop và tuning, yêu cầu Gemini đề xuất, phân tích F/M và clipping.

- [x] Đăng ký H18(81 options), H19(244 options), H20(120 stress cases) trước đo; runner/rawbaseline checks ở636c039, stress runner aa63bd3.
- [x] Gemini đã trả lời ở https://gemini.google.com/app/7d333d9203907dd2. Prompt thực, rawAX phản hồi, screenshot và đối chiếu sai sót được lưu. Center clipping/ZCR/zero-phase là ý tưởng chưa đo trong phiên này.
- [x] H18 hoàn thành, verify1296 inner traces và nested contour counts/stats/hash. Train5.282995%, selectedLOFO3.409875%, nested8.295856%; acceptednested7.279236%. GateFAIL, không promote. Commit1ccb47c.
- [x] Slice25/10 filters: LP800LOFO4.046405%, BP30–8004.587153%; các điểm đã dùng cho selection không thay nested. Bảng81 configs và heatmaps ở61d5b3c.
- [x] Hình response/group delay và frame cycles + CSV ở602af3a. Hai PNG/SVG pairs là curve/tính toán, không metric pitch accuracy.
- [x] Jev1call prospective chọn explicit option none để hoàn tất H19/H20 trước chọn hướng tiếp. Request72fbafc5-e38e-4fdf-abc0-a2ff4294c033,1939input/130output,375ms. IDs hợp lệ; relativechoice.59/fitnone.81 không calibrated. Raw JEV_NEXT_HYPOTHESIS.json.
- [x] H19 hoàn thành: train3.822016%, selectedLOFO3.815757%, nested8.513215%; gateFAIL, chưapromote. H19outputs6b8ba23 đãpush; verify3904innertraces/contourstats/labels/sourcehashes. Runtime535.92s.
- [x] H19grid/controls đãxuất vàpush6b90124; raw25/10/C1 tái hiện H16LOFO5.470735%.
- [x] H20 hoànthành120case/360rows, control khớpH15, coverage100%, đúngSNR; F/M/device/boundary/clippingfraction/noise figures vàCSVs. Commita6514b9 đãpush; runtime146.43s. Brownnoise0dB SIL72.33accepted→31.67H18/35H19 (4file,3seedmean); clipping.25 AvgMAPE8.02accepted→9.37H18/10.13H19.
- [x] Tổng hợp tại [SUMMARY.md](SUMMARY.md),12cặpPNG/SVG +1ảnhGeminiUI; STATE cũ đãlink vào thưmục này. Liên kết đãkiểmtra; doc tổnghợpđược commit/push tronglượt hoàn tất.
- [x] H21 center clipping0/.3/.5: đăngký45f405b, kết quảdc87b79. FixedLOFO .3=8.534217%, .5=11.540008% so raw7.279236%; cả final và4outer chọn raw, nested7.279236%. GateFAIL, không promote. Verify48innertraces/24metrics/contours/LABhashes,3cặpPNG/SVG. Đọc H21_REPORT.md.
- [x] H22 logistic thêmZCR crossings/s, giữC1: đăngkýad11efe, kết quả0e20eb9. Fixed2D5.470735% tái lậpH16; fixed3D5.757400%, F1/recall bình quân tăng nhẹ nhưng phone_M1recall giảm. Finalchọn2D; nested7.732759% so accepted7.279236%, gateFAIL. Outer phone_M1chọn3D,3file khácraw. Verify48innertraces/24metrics/contours/hash.
- [x] Replay lựa chọn độc lập và toàn bộgate H21/H22 bằng verify_selection.py, receiptsởfbded31. H22diagnostics4cf4653:1291frame rows, fixedscores tái lập, transitions/hashes/PNG/SVG verified. Phone_M1V mất12/nhận3, ròng−9; không suy thành quy luật giọng nam. Đọc H22_ERROR_ANALYSIS.md.
- [x] Theo phê bình của người dùng, chuyển sang AMDF: H23 đăngkýc1c3072; notebooklocal vàsource0054572; output89c7aeb đãpush vàverifyremote. Sáucodecells nguyênsource được execute bằng Python+displayadapter, không phảiJupyterkernel. Hai nhánh AMDF trước/sau train vàfixedLOFO tái lập1e-8;32perfile rows. Original/Colab notebooks không sửa.
- [x] H23 thửframe20/25/40 vớihop10, accepted AMDF_energy làmcontrol. Fixed40 giảmAvgMAPE6.767627→5.632639% vàstdMAPE12.855443→5.814854%, nhưngF1.864626→.840410/recallV.876303→.847026, phone_M1AvgMAPE5.003046→10.686380%. Final/outer chọn25, nested6.767627%, khôngpromote. Giữ40 nhưứng viên cóđánhđổi. Verify48innertraces/24metrics/contours/hash, source notebook/outputhash, PNG/SVG.
- [ ] Ưu tiên vòng AMDF tiếp: đọc lỗi theo khung40ms ởphone_M1/studio_M1, cân nhắc đăngký tách cửa sổV/UV vàtìmF0. Chưa chạy. Không quay lại mởgridACF mặc định. Báo cảmetric cải thiện lẫnđánhđổi, không dùng nhãnFAIL thaytoàn bộkết quả. Không mởtest hoặc hạgate sauđo.
- Không còn runner đang chạy từ phiên này; H18–H23 đãhoàn tất. Không tạo lại schedule. Hiện có20cặpPNG/SVG khoa học và1ảnhGeminiUI. Đọc AMDF_SCOPE_AUDIT.md vàAMDF_LOCAL_TRAIN.ipynb.

GT chỉ file-stat + loại đoạn, không F0 từng khung. Projection về grid chấm25/10 là adapter; thuật toán thực dùng native frame20/25/40 và hop5/10/20. Median3 span2hop. Weights budget logistic theo nativeV/UV làm regularization effect đổi khi hop đổi; H19 là joint search.

Giữ failures, không mở grid theo test hoặc claim filter luôn tốt/xấu. F/M theo tên, mỗi nhóm2file/mỗi ô device×F/M1file; chưa đủ metadata để coi file là speaker độc lập. Gemini/Jev là review, không số đo hoặc permission.

Lượt nối tiếp H21/H22 dùng hai ý tưởng Gemini đã lưu, không gửi lại Gemini và không gọi Jev mới: các quyết định gate/count/fit ở lượt này đều được kiểm tra bằng code, không có câu hỏi ngữ nghĩa hẹp còn cần gửi. Không discovery hoặc retry System One. Hai lỗi import ở đoạn hậu xử lý bảng Markdown đã sửa bằng đường dẫn module đúng; không đổi runner, grid/gate hay rerun thí nghiệm để sửa chúng. Notebook và test không rerun.
