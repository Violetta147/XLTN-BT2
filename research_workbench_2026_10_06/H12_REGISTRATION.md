# H12 — một yếu tố: hysteresis cho ACF voiced mask

Đăng ký trước chạy. Champion009fd2c; current audit fc5bfe9; H10/H11FAIL nên không dùng estimator mới cho H12.

Hypothesis: một ngưỡng thấp hơn để tiếp tục voiced run có thể cứu score dip/ngắt offset; onset vẫn dùng ngưỡng gốc. Logic causal trước→sau, không nhìn nhãn hoặc tương lai khi infer. Giữ RMS gate và mọi pitch candidate/path/median3 nguyên. RMSfail luôn reset state. Thay mask có thể nối run nên path/median output bị ảnh hưởng; đó là hệ quả của một yếu tố voicing chứ không phải patch pitch bằng GT.

Jev gợi ý hysteresis; diagnostic cho thấy train FN84 gồm76pitch-only,3both,5energy-only. Chỉ5/33boundaryFN có previousV,13có followingV; không kỳ vọng forward hysteresis cứu mọi onset. Không dùng số đo test.

Registry margin=[0,.02,.04,.06,.08,.12]. onset=t_ACF đã fit; offset=t_ACF-margin. Chọn margin bằng inner LOFO trên training của fold, lower MAPE trong options thỏa guard: macroF1/recallV giảm≤.01, SIL tăng≤1, per-fileMAPE tăng≤2pp, phone_F1std không tệ hơn khi có file đó trong inner validation. Tie chọn margin nhỏ. Margin0 là rollback/default nếu không có variant cải thiện.

Final selected bằng LOFO của4train, report train/selected-LOFO riêng; nested outer4fold chọn margin lại chỉ từ other3, innerheld trong3 phải fitother2. Báo rõ finalLOFO đã dùng selection; nested là score selection procedure mới. Cả hai cần gatesPROTOCOL để eligible; test chưa đọc. Không đổi accepted config khi fail. Không kiểm định theo hàng nghìn frame.

Assertions: margin0 pred/F0 khớp accepted; mask margin>0 chứa baseline mask; toy state transitions đúng; mọi held ID loại khỏi fit và outerheld loại khỏi inner selection files; scoringGT poison không đổi inference. Xuất registry/innerchoices/fits/CSV/figures/report.
