# H33 — reference pipeline pYIN

Đăng ký trước đo pYIN trên BT2. Rollback repository bc7e207; control H30 fixed Praat7 filtered voicing0.45, không dùng H31/H32 failure làm champion. Original009fd2c/frozen_config/notebooks giữ nguyên.

Giả thuyết: phân phối xác suất trên các ứng viên YIN và đường Viterbi chung F0/VUV có thể giảm lỗi octave/std và nhận khung V mà vẫn giữ SIL thấp. Đây là **whole pipeline comparison** với control, không phải tác động cô lập của một filter. Kết quả paper không thay metric BT2.

Nguồn đã đọc: [API pYIN librosa0.11.0](https://librosa.org/doc/0.11.0/generated/librosa.pyin.html), [source HTML](https://librosa.org/doc/0.11.0/_modules/librosa/core/pitch.html), official release source tag0.11.0 được hash so với source cài đặt. Đã biết cơ chế từ API/code, chưa claim đọc full paper ICASSP2014. Không extract PDF.

## Grid và tất cả tham số

Registry control + **pYIN frame40/60/80ms**, hop10ms. Làm tròn nearest sample theo Python round, sample rate gốc, audio float64 từ loader hiện có, không resample. Librosa0.11.0, fmin70/fmax400, n_thresholds100, beta_parameters(2,18), boltzmann_parameter2, resolution0.1 semitone, max_transition_rate35.92 octaves/s, switch_prob0.01, no_trough_prob0.01, fill_na=NaN, center=False. Không truyền win_length đã deprecated; pad_mode='constant' bị bỏ qua khi center=False. Không thêm noise, energy gate, lọc, median, StoneMask hoặc threshold voiced_prob.

Native time = (frame_index×hop_samples + frame_samples/2)/fs. Không padding, chỉ cửa sổ đủ tín hiệu. Trả voiced_flag từ Viterbi, F0 NaN khi UV, voiced_probability lưu riêng. CSV raw dùng0 cho NaN UV và giữ flag/probability; không dùng probability để tự chọn threshold. Output70–400Hz theo policy chung. Projection nearest center vềcanonical25/10 trong nửa hop+một mẫu, hòa chọn sớm hơn, unsupported=false/NaN. Frame dài mất support biên phải báo coverage, không bù padding hoặc count theo GT.

Control giữ nativePraat7.0.02 floor70/top800, attenuation0.03, silence0.09, voicing0.45, octave0.055, jump0.35,VUV0.14,max15,very_accurate=false,step10ms và output70–400. Adapter/script control H30 không sửa.

## Selection và tiêu chí

Cả control/pYIN không fit nhãn; actual_fit_files=[]/requires_fit=false. Nominal inner pool chỉ chọn pipeline/window. Final inner LOFO bốn file; outer held chấm sau inner LOFO ba file khác. Eligibility hữu hạn, mean F1/recallV≥control−0.01, tổngSIL≤control+1. Rank maxfileAverageMAPE, rồi mean/ID. Không chọn theo GT của outer held hoặc file name/giới/device.

Tám gates so H30fixed0.45: train giảm≥10%; selectedLOFO/nested giảm≥5%; nestedmeanF1/recall giảm≤0.01; tổngSIL tăng≤1; không fileMAPE xấu thêm>2pp; phone_F1std không xấu hơn. Mục tiêu mỗi nestedfile≤2% báo riêng, không thay bằng mean. Không thay gate/registry/GT sau đo; giữ failures và không auto-promote.

Trước đo: môi trường riêng `.venv-bt2-pyin`, official wheels/version/source/binary hashes; tám synthetic calls tone173Hz/silence×16k/44.1k×40/80ms, tone>80voiced/error<1.5Hz, silence0, time/length/no-padding checks. Check originalAMDFparity và nativecontrolbinary, không đo pYIN BT2. Sau đo: tái lậpcontrolH30fixed.45, verify64innertraces/68fits/24metrics; mọi rawfixedstats/MAPE/VUV/range/projection/coverage/callparams/framealignment, nominalpool exclusions, minmax/gates/hash/PNG/SVG vàpoisonheldinference.16extractcalls gồm4control+12pYIN; thư viện chỉ đọc array audio được agent nạp.

LAB chỉfile-stat/nhãnđoạn, không F0chuẩntừngkhung; lịch sử định hướng bốnfile làmnestedexploratory. Chỉlocaltrain, khôngtest/Drive/deeplearning/PDF. Jev branch đãlỗivalidation, khôngretry hoặc suy phán xét. Lệnh `.venv-bt2-pyin/Scripts/python.exe research_workbench_2026_10_07/pyin_reference.py register/check/H33`; verifier `verify_amdf_loop.py H33 praat7_filtered_v0.45`.
