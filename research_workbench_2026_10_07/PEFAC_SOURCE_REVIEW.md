# PEFAC — bản Python tìm được không đủ để benchmark thuật toán gốc

Source identity review08/10/2026 sauH63; không phải vòng đo BT2, không có H64 prereg hoặc train results. Đọc đủ hai source pinned, không thực thi chúng hoặc cài package. Search query `PEFAC Python pitch github fxpefac implementation` và `site.ee.ic.ac.uk hp staff dmb voicebox fxpefac`; HTML/code, khôngPDFextraction.

Nguồn chính thức: Sira Gonzalez/Mike Brookes, [ImperialCollegeLondon/sap-voicebox v_fxpefac.m](https://github.com/ImperialCollegeLondon/sap-voicebox/blob/f671f6de6afb0206813bc539fa41b9043f68c6bd/voicebox/v_fxpefac.m), pinf671f6de6afb0206813bc539fa41b9043f68c6bd. Nguồn có copyright2011/Id2018; không dùng ngàyđó làm version toànrepo. Reference được code nêu: Gonzalez/Brookes2014, PEFAC, DOI10.1109/TASLP.2013.2295918; đây là citation trong code, chưa đọc/đánh giá fullpaper hoặc xác minh DOI metadata ởlượt này.

Ứng viên Python: [MFA-X-AI/pyvoicebox v_fxpefac.py](https://github.com/MFA-X-AI/pyvoicebox/blob/700aa87f3ecfc31a46f18215b773a605278de0a2/pyvoicebox/v_fxpefac.py), pin700aa87f3ecfc31a46f18215b773a605278de0a2. README có claim completeport; inspection cho thấy hàm này chỉ dùng cửa sổHamming, FFTpower→IFFTautocorrelation, lagargmax, threshold .3 vàparaboliclag. `log_pw` được tính nhưng không được dùng để suy luận; range60–500 khác defaults gốc60–400. `pv` là giá trị đỉnhACF, không GMMposterior của PEFAC.

| Thành phần | MATLAB gốc (dòng trong snapshot) | Python ứng viên |
|---|---|---|
| Log-frequency spectrogram | v_spgrambw150, v_filtbankm155 | không có |
| Long-term average speech spectrum, amplitude normalization | v_stdspectrum162 vàalpha170–191 | không có |
| Filter họa âm trên log-frequency | tạo kernel195–212, filter214 trởđi | không có |
| V/UV GMM có hệ số đã học | params67–97, vuvfeatures244 vàgaussmix248–249 | ACFpeak>.3, pv=peak |
| Dynamic programming chọn contour | dpweights105/121 vàđườngđi phần sau | chọn độc lập lagargmax |

Vì thiếu các thành phần này, không dùng `v_fxpefac.py` như referencePEFAC trong BT2. Đây là kết luận về hàm tại pin đã đọc, không đánh giá toàn bộ thư viện Python hoặc mọi bản port. Không lấy lượt cài/star/README hoặc synthetictonePASS làm chứng nhận đúng thuật toán. Không chạy thêm một ACF dưới tên PEFAC để mở vòng mới.

Hai snapshot code được giữ dạng.txt trongresults; licenseLGPL/GPL từrepo tươngứng giữ kèm. URL/pin/hash và PATHprobe trong `results/PEFAC_source_identity_review.json`; chữ `candidate_rejected_as_reference_PEFAC` là verdict về identity, không measuredaccuracyFAIL. `matlab`, `octave`, `octave-cli` không thấy trongPATH củaphiên, không kết luận chúng không nằm ởbất kỳ vịtrí nào trênmáy. Mã MATLAB có helperdependencies; chỉ tải file chính không tạo runtime chạy được. Chưa port, cài MATLAB/Octave, hoặc kiểmparityvớiMATLAB.

Bước có giá trị nếu chọn hướng PEFAC: dựng adapter từ officialsource+helpers và runtime phù hợp hoặc port cóstageparity; xác minh grid/projection/probability/config trước đăng ký BT2. Hướng H64 đã được nêu trong chat là unanchoredHPS70–400 giữmask/count; chưa đăng ký/đo trong khi người dùng bổ sung câu hỏi vềskills. Không coi ý tưởng này là thí nghiệm hoàn tất. H63 vàbaseline giữ nguyên; không test mới, không đổiGT/notebook/frozen, noDrive/DL/PDF/Jev.
