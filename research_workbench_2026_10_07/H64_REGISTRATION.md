# H64 — HPS toàn dải, giữ mask/count baseline

Rollback `ad32ebf2b0a7b05e31595b55648d736dcad7dd6d`; accepted pipeline `hard170`. H00–H63 hoàn tất, không chạy lại. Nguồn thuật toán và giới hạn custom HPS theo `HPS_SOURCE_REVIEW.md` của H63; H64 chỉ thay miền tìm kiếm, không port pipeline upstream. Không cần vòng tìm paper mới để thay miền tìm của objective đã rà nguồn.

Giả thuyết: ràng buộc quanh anchor ±100 cents ở H63 có thể ngăn HPS tìm được cực đại phù hợp; tìm toàn dải 70–400 Hz có thể giảm sai số thống kê F0mean/F0std. Cents là đơn vị log của tỉ số tần số, 1200 cents bằng một octave. Bỏ anchor cho phép đổi octave và có thể làm lỗi tăng; không coi contour đổi nhiều là sửa đúng từng khung.

Options duy nhất: hard170, global_hps_3, global_hps_5. So với H63 giữ PCM25ms/hop10ms, trừ DC, Hann, FFT next power2≥16×length, amplitude/max, linear interpolation, floor1e-12, tổng log biên độ tại hF0 với h=1..3 hoặc 1..5; đổi grid thành 70.0..400.0 Hz bước0.1, 3301 điểm, không thêm anchor. Ties chọn Hz nhỏ nhất. Spectrum zero giữ anchor như trước. Không resample/filter/smooth hoặc đổi voicing/label/reference.

Precheck trước đo BT2: synthetic fs16k/44.1k, noise seeds11/29/47, F0 90/200/320, orders3/5, 36 fixtures; error<100cents, gain/DC invariance, toàn grid score/argmax so DFT trực tiếp; zero fallback phải đúng. Seed là fixture noise, không model training. Nếu FAIL giữ bằng chứng và dừng H64, không nới tolerance. DFT matrix được cache theo fs/length/order, không cache kết quả đo BT2; scipyFFT chỉ lấy global normalizer.

Đo train một lần: 12 unique metric groups; 48 inner traces; 24 summary rows. Đọc baseline contour H47 đã lưu/hash, không chạy lại baseline. Không fit nhãn/hệ số. Nested4outer/3inner và final4LOFO chọn config theo minimax worst-file Average MAPE→mean→ID, finite/F1/recallV drop≤.01/SIL+1. Cả tám gate `voicing_recovery.gates` giữ nguyên; mục tiêu all8 là từng file Average MAPE<2%. Không thêm search option hậu nghiệm sau đo.

Metric chính là Average MAPE của F0mean/F0std/F0num so teacher3GT thống kê cả file, không là framewise pitch accuracy. Báo macroF1 V/UV, recallV/UV, balanced accuracy, MAEmean/std/count và số khungF0. Mask/count không đổi nên các metric voicing phải khớp baseline. Test đã từng được xem, nested vẫn exploratory trên bốn train files, không giả thêm frame là speaker độc lập.

Đăng ký source/precheck/registry rồi commit/push/xác minh remote trước đo train. Verifier độc lập dùng directDFT/scalar interpolation/log/argmax, scalar metrics, selections, inner membership, unchanged gate và protected hashes. H64 thất bại thì lưu report, không promote/đo test. Chỉ nếu eligible, lock config và commit/push/verify kết quả train trước một lần test mới. Không sửa notebook/WAV/LAB/GT/frozen; không Drive, deep learning, PDF, Jev, lịch tự chạy hoặc retry tự động.

Skill tham gia: `ml-pipeline-workflow` (bản local trong manifest `docs/skills/ML_RESEARCH_SKILLS_2026-10-08.json`), dùng contract hashes/config/cache, đơn vị file và isolated ablation. Skill không tự đo, cấp quyền hoặc là bằng chứng thuật toán hiệu quả.
