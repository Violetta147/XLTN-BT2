# Cửa sổ25ms và bước10ms — kiểm cấu hình thực

Người dùng làm rõ08/10: thầy yêu cầu fixed25ms frame length và10ms shift. Sau đó người dùng cho phép thử tham số tùy ý; hiểu là nghiên cứu có thể khảo sát rộng, còn bản cuối theo yêu cầu thầy phải25/10thực sự. Không chỉ project output của estimator dùng window dài về grid25/10 rồi gọi compliant.

| Source đã đọc | Cửa sổ tính thật | Bước | Kết luận |
|---|---|---|---|
|R01 Praat6 rawACfloor75|3/75=40ms|auto10ms hoặc10ms|chỉ nghiên cứu, không fixed25|
|R01 Praat6 rawCCfloor75|effective1/75=13.333ms theo docs|auto3.333ms hoặc10ms|khác25; chưa audit toàn acoustic support để claim25|
|H30 Praat7 filteredfloor70|effective3/70=42.857ms|10ms|khác25|
|H33 pYIN|40/60/80ms, center=False|10ms|khác25; chưa có pYIN25 trong H33|
|H68 officialPEFAC|v_spgrambw:winlen=fix(1.81fs/bw),bw=fres20Hz →xấp xỉ90.5ms|10ms|khác25; không sửa bandwidth sau đo|
|hard170|NAMDF25→40theospectralrule; Praatanchor/VUV42.857ms|canonical10ms|không thuần25; baseline nghiên cứu lịch sử|
|H66/H67 customAR|residual objective25ms, nhưng dùng mask/anchorhard170|10ms|objective25 không làm wholepipeline25|
|Notebook đã nộp|FRAME_CANDIDATES_MS=[20,25,30]; FINAL_FRAME_MS chọn best_row|HOP_MS=10|không hardcode25; không savedoutputs để xác nhận runtimefinal|

Notebook `../../turn-in-assignment - Copy/BT2_ACF_best_no_energy_set.ipynb` cell5 constants, cell9framing, cell24selection, cell28processing. SHA256 b643a1cdf6ac67d3e1dcacf9ce45ea4c49625da114e8c07f402c3fca5d13f85c kiểm live, toàn bộoutputs=0; không chạy hoặc sửa notebook. Defaultargframing30ms không tự chứng minh final30 vì process truyềnFINAL_FRAME_MS; cũng không được nóifinal25 khi chưa cóoutput. Giữfilegốc.

Nguồn window: `pyin_adapter.py` line33–34 vàH33_REPORT; `amdf_pitch_spectral.py` route line37/source windows; `H47_REGISTRY.json` frame_ms42.857/pitch_frame40; pinned `vendor/voicebox_pefac/v_spgrambw.m` line318–320 và `v_fxpefac.m` fres20/defaulttinc; R01outputs/primary [Praat AC](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_raw_autocorrelation.html), [CC](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_raw_cross-correlation.html). KhôngPDF.

Một khả năng chưa thử native là [MATLAB Audio Toolbox pitch](https://www.mathworks.com/help/audio/ref/pitch.html): API cóWindowLength/OverlapLength vàNCF/PEF/CEP/LHS/SRH, có thể chỉ địnhround(.025fs), overlap=window−round(.01fs). Docs R2026b còn chỉ rõ outputloc là mẫu cuối cửa sổ, không tâm; cần đổi timestamp đúng nếu đối chiếuLAB. RuntimeMATLAB/license chưa có nên đây là source-backed capability, **không số liệu MATLAB đã đo**, không suy thầy dùngMATLAB. Không dùngOctavefunctionkhác rồi gán làMathWorks.

Vòng mới phải lưu exactframe_samples/hop_samples/fs/rounding, center=False/noaudio-padding hoặc giải thích rõ adapter, range/vuvpolicy vàcomplianceflag. Với sample rate không biểu diễn chính xác25ms bằng số nguyên, ghi round policy/sai số thời gian. Chọn tham số theo filetrain; baseline compliant và baseline nghiên cứu phải báo riêng, không đổi gates/vòng lịch sử sau đo. Cần kiểm source actualwaveform support, không chỉ nhãnframe_ms trong bảng.
