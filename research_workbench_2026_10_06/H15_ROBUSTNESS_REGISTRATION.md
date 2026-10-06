# H15 — robustness của hai cấu hình cố định, train-only

Đăng ký trước chạy, current8ee1f31. Không tune hoặc promote từ stress curves. So accepted009fd2c và H12 procedure: mỗi held-file dùng margin đã chọn bởi nested other3 và thresholds fit clean other3.

Registry: white/pink/brown noise, SNR=[30,25,20,15,10,5,0]dB,20seeds/cell,4files. Noise colored có PSD slope0/-1/-2 sinhFFT, zero-mean; SNR tính power của toàn WAV sạch (cóSIL), scale noise để achievedSNR khớp target. Đây là simulated noise, không phải Noisex/noise recordings thật. Gain[.1,.25,.5,2,4] giữ float, không quantize/clipping; DCoffset[.25,1,2]×fileRMS; clippingthreshold[.8,.5,.25]×filepeak; impulse±10fileRMS tại.1%randomsample,5seeds. Mỗi case chỉ một perturbation, không chồng noise+DC+clip.

Nhãn thời gian và3GT thống kê reference giữ nguyên; noise làm giảm thông tin quan sát. Không có pitchtruth mỗi frame; chỉ classification và file-stat deviations. Không lấy estimates sạch làm truth. Empty-F0 mean/std/AvgMAPE undefined phải báo coverage, không fill0.

Feature extractor onlyACF phải tái lập cache raw/candidates/RMS trước mọi stress. Fit không dùng audio noise để tuning. Seed/file/condition hashes, rawWAVhash, incrementalCSV+progressJSON; resume bỏ completedcase, code/registryhash phải khớp. Dừng trước2026-10-06T21:00Z nếu chưa xong; reportpartialchínhxác, không coi tất cảcases complete.

Figures: degradationRecall/F1/SIL/AvgMAPE acrossnoise/SNR, seed dispersion conditional+finitecoverage; gain/DC/clip/impulsechanges; per-fileworst cases. Repetitions đo sensitivity noise realization, không tăng4file thành1680independent speakers. Bootstrap nếu có: aggregate seed trước lấy file làm đơn vị; không pvalue theoframes.
