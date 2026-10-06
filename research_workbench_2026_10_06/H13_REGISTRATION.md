# H13 — thay chuẩn hóa candidate strength, giữ cùng lag/path

Đăng ký trước chạy. Champion009fd2c; H12eligible ởf27d3ae nhưng chưa promote. H13 so với champion cũ, không gộp hysteresis.

Chỉ thay strength của đúng các candidate lag ACF đã lưu bằng NSDF tại cùng integer peak. Không thay lag/F0 candidates, voiced mask, RMS, fit thresholds, pathjump.35/octave.03 hoặc median3.

ACF normalized=r/sqrt(Eleft Eright), NSDF=2r/(Eleft+Eright). Với r>0, factor2sqrt(Eleft Eright)/(Eleft+Eright)≤1. NSDF giảm strength khi energy hai vùng overlap khác nhau. Hypothesis: local candidate ranking sau penalty này có thể giảm chọn lag không phù hợp trong cửa sổ có envelope thay đổi. Không khẳng định đó là pitch error đã có ground truth.

Numerical assertion: cached candidate strength khớp ACF curve tại integer peak (atol1e-8), NSDF=-1..1, candidateF0 set không đổi; pred mask không đổi; inference poisonGT invariant. Fallback khi không có candidate giữ core cũ, không ép F0 theo3GT.

Không tune parameter, train/LOFO cùng gatesPROTOCOL; không tạo fake nested iteration. Chưa đọc WAVtest. Bất kể pass/fail giữ CSV/figures/report và champion configuration. Nếu thất bại, không gộp với H12 rồi tuyên bố candidate strength tốt hơn.
