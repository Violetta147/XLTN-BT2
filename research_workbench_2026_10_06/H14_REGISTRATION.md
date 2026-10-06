# H14 — majority vote cho voiced mask, width3 cố định

Đăng ký trước chạy. Champion009fd2c; H12eligible chưa promote; H13không đạt5%LOFO. Một yếu tố khác từ diagnostic16interior/2boundary isolated gaps.

Đổi raw voiced mask bằng majority3 (ít nhất2/3neighbors), paddingFalse ở hai đầu; áp RMSgate lần nữa để không lấp khung thiếu energy. Giữ thresholds foldfit, ACFcandidate/pathcosts và median3 pitch. Đây là lọc mask, khác median3 F0. No parameter tune, không chọn width từ kết quả.

Có thể lấp one-frame gaps nhưng cũng xóa short events; phải báo TP/FN/UVFP/SIL cả mới được thêm lẫn bị bỏ. Dùng framehop10ms, thêm nhìn trước1frame ở mask; toàn pipeline/path và per-filequantile vốn là batch, không tuyên bố real-time.

Train/LOFO cùng gatePROTOCOL, không tạo nested score lặp khi không có newselection. Giữ configchampion nếu fail. Assert toygap được lấp, isolatedtrue bị bỏ, RMSfail không được lấp; pred/F0 poisoningGT invariant. Test chưa đọc.
