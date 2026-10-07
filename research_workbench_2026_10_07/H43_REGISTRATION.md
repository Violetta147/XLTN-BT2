# H43 — Thêm điều kiện cao độ vào bộ chọn cửa sổ phổ

Prereg trước phép đo BT2 mới, rollback repository **40916e3**. Mathematicalcontrol **H31 fixedPraatfiltered.30**, original/frozen009fd2c giữ. H42 là tiến bộ có số đo thất bại đã kiểm tra/push, không chờ process. H41 đã đạt cả4nestedAverage≤2% nhưngstdgatephone_F1FAIL; H42HF05fixedstdphone_F1 tốt hơn, studio_M1 xấu vànestedtargetFAIL. Không chạy lại benchmark đã hoàn tất.

Giả thuyết: dùng40ms cho vùng phổ ít năng lượng trên1kHz có thể hữu ích khi cao độ đủ cao; tránh40ms ở cao độ thấp có thể giữ ưu điểm25ms. Chu kỳT=1/F0; gateF0 là ứng viênPraat chứkhôngnhãn chuẩn. Đây là điều kiện từngkhung từtín hiệu, không nhận diện nam/nữ, thiết bị hoặc tênfile. Giả thuyết được định hướng sau nhiều lần xem4train nên nested vẫnexploratory. Không dùng dữ liệu QA test để chọn hướng/grid; không test inference/tuning.

Một yếu tố mới soH42: thêm minimum_gate_hz vào route; spectralHFthreshold cố định.05, cutoff1000Hz/feature40ms/rawDC/Hann/FFTpowerweights vàNAMDF25/40/band200/gatePraat.30 giữ. **7options**: Praat.30control; fixed25/b200; fixed40/b200; HF05 với minimum_gate_hz **0/140/170/200Hz**. Minimum0 làH42HF05ablation. 40ms iff ratio finite≤.05 ANDgateF0≥minimum, else25ms. NativeUV/rangeoutside giữ; chỉ70–400Hz đượcroute. NaNratio dùng25ms; unsupported/flat/noallowedcandidate giữPraat.

Gate/times/NAMDFrawcurves từH41 cóhash,8curvegroups reused; H43 đo lạifeature phổ từ4trainPCM vàlưu4NPZ riêng. **0newnativecall**,4historicalPraatgroups; no newfilter/noise/clip/resample/mean-statcalibration/smoothing/path. Không dùngLAB/GTvàoextract/route, tênfile chỉghépevidence. Count147/233/123/85 saucanonical25/10 nhưH31 dự kiến giữ; reportbothnativepositive/rangereject/inrange/canonicalcounts.

Selection/gates giữH42: minimaxworst-fileAverageMAPE, rồi mean,ID; finite/F1/recallVdrop≤.01/SIL+1 before ranking. Train/selectedLOFO/nested; outerexcluded khỏiinnerselection/fit, actual_fit_files=[] classifierNone. Támgate soH31: trainrelativegain≥10%,selectedLOFO/nested≥5%,F1/recallVdrop≤.01,SIL+1,nofileworse>2pp,phone_F1stdnotworse. Mỗi nestedfileAverage≤2% là targetriêng bắt buộc; khôngthaymetric/gate sauđo. Reportstd/countMAE/MAPE,VUV/BA/SIL. Std/mean/countstatisticsddof0, giữundefined/failures.

Syntheticcheckzero/low/hightone/gain/DC/frequency &ratio equality boundaries tại16/44.1k, khôngBT2. Source/registry/precheck/verifier commit/pushremoteverified trướcđo. Aftermeasure independentlyverify112traces/116–120fits/24metrics/28fixedgroups, scalarNAMDFfullPCM/hash/parabola/dips/band/tie/fallback/frameindices/timealign/fullcomplexFFT/Hannratio/routepitch+spectralcondition/sourcebinary/hash/LAB/MAPEstd/count/VUV/gates/pools/PNGSVG/layout. Fixed25/40/control tái lậpH41, minimum0 phải tái lậpH42HF05. Giữsource/receipts/traces và thất bại. Khôngpromote automatically; notebook riêng replay saukết quả, không sửanotebookgốc hoặc frozen.

Nguồn: H43_SOURCE_NOTE.md, codeH41/H42 đã kiểm tra. Khôngclaimpaperreplication, không literaturesearch mới; khôngPDF/deeplearning/Drive/MCP retry. NhánhJev sauH32 vẫn dừng, đây là phép tínhcode khôngcầnJev.

Lệnh: `amdf_pitch_spectral_controller.py register/check/H43`, `verify_amdf_pitch_spectral.py`. Không mở rộnggrid sau đo; hướngmới cầnprereg vòngkhác.
