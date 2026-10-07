# H34 — SWIPE′ reference pipeline

Đăng ký trước đo SWIPE′ trên BT2. Rollback repository b000433; control H30 fixed Praat7 filtered voicing0.45 đã qua gates củaH30. Original009fd2c/frozen_config/notebooks giữ nguyên.

Giả thuyết: spectral harmonic template của SWIPE′ cung cấp ứng viên khác AMDF/ACF/pYIN, có thể giảm octave/std error và cho quyết định V/UV phù hợp hơn khi chọn strength threshold trên training. Đây là whole pipeline comparison, không cô lập một filter. Không coi strength/contour là F0 ground truth.

Nguồn: [SPTK manual pitch](https://sp-nitech.github.io/sptk/latest/main/pitch.html), repository sp-nitech/SPTK commit **0ebff5a9b1fb5851709130efa1d3efb186ef702a**, bundled SWIPE implementation của Kyle Gorman, thuật toán SWIPE′/prime. Code wrapper/third-party và help/version được đối chiếu, hash riêng. Review paper dùng abstract PubMed/Camacho-Harris2008 và code/manual, chưa claim đọc full paper. Không extract PDF.

## Grid, định dạng và thời gian

Registry gồm control và SWIPE′ threshold **0.2/0.3/0.4/0.5**, default0.3 theo source. Native SPTK4.4 executable build từ nguồn giữ nguyên, algorithm `-a1`, hop `-p round(fs×0.01)`, sample rate `-s fs/1000` kHz, range `-L70 -H400`, threshold `-t1`, F0 output `-o1`. Các FFT windows thay đổi theo tần số trong implementation; không ghi frame25/40ms giả cho SWIPE. Không đổi tham số kernel, FFT, interpolation hay step theo file.

Input stdin float64 little-endian, biên độ PCM = normalized audio×32768. Training được kiểm profile16bit/mono; đây là đảo normalization của loader, không peak normalization/clipping. Native output double little-endian Hz, UV=0, time index×hop/fs từ0. Wrapper giữ ceil(samples/hop) output cùng truncation/repeat-last sẵn trong nguồn. Internal window padding của implementation giữ nguyên; agent không thêm padding/resample/filter/gate/median/noise.

Lưu tất cả raw native F0 trước rangepolicy70–400, command, input/outputSHA, samplecount/hop, binary/source/adapterSHA. Projection nearestcenter vềcanonical25/10 với nửa hop+một mẫu, hòa chọn sớm hơn; unsupported=false/NaN. Không cắt/thêm theo GTcount. Control giữ toàn bộnativePraatH30params, script không sửa.

## Selection, gates và kiểm chứng

SWIPE/Praat không fit bằng nhãn; actual_fit_files=[]/requires_fit=false. Nominal inner pools chỉ chọnthreshold. Final innerLOFO4file; outer held chỉ chấm sau innerLOFO3file khác. Eligibility finiteMAPE, meanF1/recallV≥control−0.01, tổngSIL≤control+1. Rank maxfileAverageMAPE, rồi mean/ID. Không chọn bằng GT củaouterheld hoặcmetadatafile/giới/device.

Tám gates tương đốiH30fixed.45: train giảm≥10%; selectedLOFO/nested giảm≥5%; nestedmeanF1/recall giảm≤0.01; tổngSIL tăng≤1; khôngfileMAPE xấu thêm>2pp; phone_F1std khôngxấu hơn. Mục tiêu **mỗi nestedfile≤2%** riêng. Không đổi grid/GT/gates sau đo, giữ failures, không promote.

Prerequisites: portable build/source/binary checks vàtám synthetic tone173Hz/silence×16k/44.1k×threshold.2/.5. Threshold.2 tone>80V/maxerror<2Hz; strict.5 có thểabstain vàcoverage phảighi. Silence0V. Trước đo check originalAMDFparity/nativePraat/binary/probe; khôngSWIPEBT2. Sau đo tái lậpcontrolH30, verify80innertraces/88fits/24metrics vànative20calls; replayrawfixedstats/MAPE/VUV/timealignment/PCMunmodifiedinputSHA/range/projection, inner/outer exclusions/minimax/gates, nofit/poisonheld, data/LAB/source/PNG/SVG.

MSVC configure thất bại vìthiếuWindowsSDK/kernel32.lib; log giữ nguyên. PortableLLVM-MinGW build dùng forceinclude standard algorithm header vìvendoredREAPER thiếu explicitinclude, khôngsửa referencealgorithm/source. Toolchain/buildflags/provenance ghi riêng trước benchmark. Không cài SDK hoặc thay đổiVisualStudio.

LAB chỉfile-stat/nhãnđoạn, khôngF0chuẩntừngkhung. Lịch sửn4 làmnestedexploratory. Chỉlocaltrain, khôngtest/Drive/deeplearning/PDF. Jev lỗi đãdừngMCP, khôngretry. REAPER chưađo trongH34 dùbinarycóalgorithm2. Lệnh `C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/swipe_reference.py register/check/H34`; verify `verify_amdf_loop.py H34 praat7_filtered_v0.45`.
