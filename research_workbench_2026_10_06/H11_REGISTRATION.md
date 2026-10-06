# H11 — McLeod NSDF/MPM

Đăng ký trước chạy; champion009fd2c giữ nguyên, H10 đã commit53155f8 và gateFAIL.

Chỉ thay pitch estimator bằng NSDF/MPM (bao gồm bỏ ACF/path), cùng fixed ACF voiced mask, relative RMS gate fit từng fold, median3, frame25/hop10/range70–400. H10 fixed parameter.1 không được tune tiếp trong H11.

NSDF(tau)=2 sum x[j]x[j+tau] / (sum x[j]^2 + sum x[j+tau]^2), sums trên overlapN-tau. Mean-remove frame, bỏ lobe ban đầu chứa lag0; một peak cao nhất mỗi positive lobe; nếu lobe cuối chưa kết thúc chỉ giữ khi local peak đã xuất hiện. Trong range cho phép, chọn peak đầu đạt .93 của peak cao nhất; nội suy parabol; clamp period ở endpoints như H10. Không dùng score mới để đổi voiced mask.

Nguồn đã đọc: [McLeod/Wyvill, A Smarter Way to Find Pitch, paper tác giả](https://www.cs.otago.ac.nz/graphics/Geoff/tartini/papers/A_Smarter_Way_to_Find_Pitch.pdf), mục NSDF và peak picking. Với mục tiêu giữ frame/range giống baseline, adapter giới hạn key maxima vào range70–400; không coi score là calibrated probability.

Numerical check: FFT/NSDF khớp direct overlap sums trong1e-10, NSDF0≈1 trên signal không hằng, bounded[-1,1]. Silence/constant NaN, DC/gain invariant. Cùng1600synthetic cases và clean interior gate median<5cents/p95<15; missing-fundamental/noise/70Hz là stress tests. Train và LOFO giữ gatesPROTOCOL như H10; no tuning nghĩa không có inner selection độc lập.
