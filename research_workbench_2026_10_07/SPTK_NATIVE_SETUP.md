# SPTK native local cho SWIPE′

SPTK4.4 được build thành công từ repository chính thức, commit `0ebff5a9b1fb5851709130efa1d3efb186ef702a`. Nguồn thuật toán không sửa. Binary và compiler portable nằm ngoài Git repository trong `../.bt2-tools/`; các receipt và adapter nằm trong workbench. Không thay môi trường Python gốc hoặc Visual Studio.

Nguồn đã đọc: [repository tác giả](https://github.com/sp-nitech/SPTK) và [manual pitch](https://sp-nitech.github.io/sptk/latest/main/pitch.html). Đây là đối chiếu code/manual, không phải đọc toàn văn paper. SWIPE′ dùng kernel theo các harmonic nguyên tố để chọn chu kỳ từ phổ; FFT windows thay đổi theo tần số. Bản bundled có tên tác giả Kyle Gorman và license MIT trong source. REAPER có trong binary nhưng chưa đo trong H34.

## Build và lỗi giữ lại

1. CMake3.31.6 và Ninja1.11.1.4 cài bằng official PyPI wheels với `--target ../.bt2-tools/cmake-runtime` và `--target ../.bt2-tools/ninja-runtime`. Install reports giữ trong `results/`.
2. Cấu hình Visual Studio2022 ban đầu thất bại: MSVC có nhưng thiếu Windows SDK, linker không tìm `kernel32.lib`. Log trong `sptk_msvc_configure_failure.json`; build directory cũ giữ lại.
3. LLVM-MinGW portable release20260922 UCRT x86_64 từ repository `mstorsjo/llvm-mingw`, archive SHA256 `e3ad77d117a4bea19a7a3b333341824d79a5a371004a10e25b8504e7b3047666`, trùng digest của GitHub asset. Chi tiết đường dẫn/compiler hash trong `llvm_mingw_provenance.json`.
4. Lần build MinGW đầu thất bại do vendored REAPER gọi `std::fill` mà không include `<algorithm>`. Log trong `sptk_mingw_include_failure.json`. Sửa build flags bằng force include standard header; không sửa source/reference algorithm.
5. Build cuối chạy đủ188 actions và exit0. CMakeCache, versions, compiler/binary/source SHA nằm trong `sptk_native_provenance.json`. Ninja executable thực nằm ở `ninja-runtime/bin/ninja.exe`.

Lệnh tái lập từ repo, sau khi tải đúng compiler/source và cài hai wheels đã ghi:

```powershell
$taskTools = (Resolve-Path '../.bt2-tools').Path
$taskCmake = Join-Path $taskTools 'cmake-runtime/cmake/data/bin/cmake.exe'
$taskNinja = Join-Path $taskTools 'ninja-runtime/bin/ninja.exe'
$taskCompiler = Join-Path $taskTools 'llvm-mingw-portable/llvm-mingw-20260922-ucrt-x86_64/bin'
$taskSource = Join-Path $taskTools 'sptk-reference'
$taskBuild = Join-Path $taskSource 'build-mingw'
& $taskCmake -S $taskSource -B $taskBuild -G Ninja "-DCMAKE_MAKE_PROGRAM=$taskNinja" "-DCMAKE_C_COMPILER=$taskCompiler/x86_64-w64-mingw32-clang.exe" "-DCMAKE_CXX_COMPILER=$taskCompiler/x86_64-w64-mingw32-clang++.exe" -DCMAKE_BUILD_TYPE=Release '-DCMAKE_CXX_FLAGS_RELEASE=-O3 -DNDEBUG -include algorithm' -DCMAKE_EXE_LINKER_FLAGS=-static -DSPTK_INSTALL_DRAW_COMMANDS=OFF
& $taskCmake --build $taskBuild --target pitch --parallel 2
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/sptk_setup_probe.py
```

## Đơn vị và probe

Input CLI là float64 little-endian với scale PCM16; adapter nhân audio đã normalize với32768 để khôi phục biên độ PCM, không peak normalize/clipping. `-a1 -p round(fs*.01) -s fs/1000 -L70 -H400 -t1 threshold -o1`. Output Hz, UV0; thời gian bắt đầu0 với bước hop/fs. SPTK giữ ceil(samples/hop), có internal padding/truncation/repeatlast theo source; agent không thêm padding/resample. H34 lưu raw trước range policy và hash toàn bộ input/output.

Tám probe tone173Hz hai harmonic/silence, fs16k/44.1k, threshold.2/.5 đã PASS trước đọc BT2 bằng SWIPE. Tone.2 có >80 khung hữu thanh và maxerror<2Hz; threshold.5 được phép abstain, coverage ghi riêng. Silence không có khung hữu thanh. Probe receipt lưu mọi command và binary/source hashes; chỉ tín hiệu tổng hợp, không suy thành độ chính xác trên BT2.

H34_REGISTRATION.md và H34_REGISTRY.json chốt grid/gates trước đo. SPTK/Praat không fit nhãn; inner folds chỉ chọn threshold, outer file tách khỏi selection. Target mỗi file≤2% độc lập với pass gates. Control/frozen original/notebooks không sửa. Không dùng test, Drive, deep learning, PDF hoặc retry Jev.
