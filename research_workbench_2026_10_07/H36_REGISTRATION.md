# H36 — REAPER reference pipeline

Đăng ký trước đo REAPER trên BT2. Rollback repository **fc34e81**; control H30 fixed Praat7 filtered voicing0.45. Original009fd2c, frozen_config và notebook gốc giữ nguyên. Không thay cấu hình đã chấp nhận khi pipeline mới chưa qua tiêu chí.

Giả thuyết: lấy ứng viên từ residual dự đoán tuyến tính và nối bằng dynamic programming có thể bổ sung một cơ chế khác ACF/AMDF/SWIPE′, giảm lỗi mean/std/count mà không nhận nhiều UV/SIL. Đây là so sánh toàn pipeline, không thí nghiệm cô lập high-pass filter. Residual là phần tín hiệu còn lại sau dự đoán tuyến tính; dynamic programming chọn chuỗi ứng viên có tổng cost thấp. Không coi ứng viên là F0 ground truth.

## Nguồn và adapter

SPTK4.4 commit **0ebff5a9b1fb5851709130efa1d3efb186ef702a**, binary đã build và hash ở sptk_native_provenance.json. REAPER tác giả David Talkin, [README/source chính thức](https://github.com/google/REAPER), author pin1d6e9b95e6b08b500fccbc9a043989dbda747276 ghi riêng. Benchmark dùng bản bundled trong SPTK, không giả toàn bộ source giống upstream. Full vendor hashes từ reaper_synthetic_probe.json được kiểm lại trước/sau đo. Đã đọc README thuật toán, SPTK manual và wrapper/epoch_tracker source; không claim đã đọc paper full text, không extract PDF.

Registry: control và **unvoiced cost 0.6/0.9/1.2/1.5**, default0.9. Lệnh `-a2 -p round(fs×0.01) -s fs/1000 -L70 -H400 -t2 cost -o1`. Cost tăng khuyến khích nhận V, không đồng nghĩa strength threshold SWIPE′ và không phải probability. Giữ mọi internal parameters mặc định; highpass=True/Hilbert=False theo SPTK wrapper. Không tùy tham số theo giới tính, device, file hoặc held-stat.

Input float64 little-endian PCM scale = audio normalized×32768; wrapper castint16. Không clipping/peak-normalize/resample hoặc thêm noise. Native output Hz, UV0, time origin0 với bước hop/fs. REAPER internal endpoint padding/resampling và SPTK truncation/repeatlast giữ theo nguồn; không giả cửa sổ25ms. Projection nearest-time về canonical25/10, nửa hop+một mẫu, ties earlier; range70–400, lưu raw trước policy.

Native từ chối input toàn0 vì không có residual peaks. Adapter **chỉ khi toàn bộ input bằng0** trả UV0, không gọi native; không dùng cổng silence theo đoạn và không chuyển RuntimeError thành kết quả0. Mọi input khác đi nguyên vào native, lỗi khác dừng vòng và giữ bằng chứng. Verifier phải xác nhận bốn train WAV đều thực sự gọi native, không đi nhánh zero.

## Kiểm trước đo và giới hạn

Raw12 synthetic calls giữ đủ: tám thành công ở transport, bốn whole-zero failures; tonehaiharmonic 44.1k/cost1.2 có half-frequency và cost.3 abstain. Không gọi đó là PASS pitch accuracy. Harmonic-rich173Hz/cost1.2 có error<1Hz tại16k/44.1k. Adapter probe8 thêm harmonic-rich/zero×16k/44.1k×cost.9/1.5: wholezero UV0; cost1.5 ≥80% centerV và maxerror<3Hz; mọi command/hash/coverage ghi riêng. Các probe không chứng minh accuracy BT2; giữ cả subharmonic case và raw error.

Trước BT2: AMDF original parity, native Praat/source/binary/hash, REAPER vendor source, adapter probes, compile/registry checks, rồi commit và push prereg. Không đo REAPER BT2 trước bước này.

## Chọn cấu hình và kiểm sau đo

Praat/REAPER không fit nhãn, actual_fit_files=[]; inner pools chỉ chọn cost. Final innerLOFO bốn file, outerheld bị loại khỏi innerLOFO ba file khác rồi mới chấm. Eligibility finite Average MAPE, mean F1/recallV≥control−0.01 và tổng SIL≤control+1; rank maxfileMAPE, rồi mean/ID. Nếu không có voiced frame, mean/std/MAPE không xác định phải giữ NaN và option không eligible, không thay thành0%.

Giữ tám gates relative control: train gain≥10%; selectedLOFO/nested gain≥5%; F1/recallV mean drop≤0.01; SIL tăng≤1; không file xấu>2pp; phone_F1 std không xấu hơn. Target **mỗi nestedfile Average MAPE≤2%** riêng. Không auto-promote hoặc sửa gates sau đo.

Kiểm80 inner traces,24 metrics,20 native calls,84 unique fit/scoring logs nếu finalcontrol hoặc88 nếu finalREAPER (do cache); all-fixed mean/std/count/MAPE/VUV/range/projection, command/PCM input hash/source/binary/timing, nofit/held exclusions/minimax/gates/poisoned-GT invariance và PNG/SVG. Control phải khớp H30fixed.45 ở1e-8. Báo F1, recallV/UV, balanced accuracy, mean/std MAE, count, coverage và SIL cùng MAPE. Lịch sử đã xem bốn file làm nested exploratory; không coi là independent unseen dataset.

Chỉ local train, không test/Drive/deep learning/PDF hoặc MCP retry. Lệnh `python research_workbench_2026_10_07/reaper_reference.py register/check/H36`; verify `verify_amdf_loop.py H36 praat7_filtered_v0.45`.
