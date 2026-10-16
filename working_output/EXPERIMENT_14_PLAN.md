# Thí nghiệm 14: nested LOFO cho lựa chọn median F0

- Điểm quay lại: notebook median3 tại `f2c32d7`; hiện notebook median5 là ứng viên ở `4aca85d`.
- Lý do: cửa sổ median5 được chọn sau khi xem kết quả LOFO của thí nghiệm 13. Để ước lượng ít thiên lệch hơn, cửa sổ cần được chọn bên trong ba file training còn lại rồi đánh giá trên file outer held-out.
- Giả thuyết: lựa chọn cửa sổ theo inner LOFO sẽ vẫn chọn median5 ở đa số outer fold và cải thiện cả hai F0 MAE so với median3 cố định.
- Quy trình: outer leave-one-file-out trên 4 file training. Trong từng outer fold, dùng 3 file còn lại chạy inner leave-one-file-out; với mỗi inner held-out, fit lại pitch Gaussian selector và energy threshold chỉ trên 2 file inner-training. Chọn median5 nếu trung bình inner F0mean MAE và F0std MAE đều không cao hơn median3, và ít nhất một giảm; nếu không chọn median3. Fit lại threshold trên 3 file outer-training, đánh giá cửa sổ đã chọn trên outer held-out. Cùng frame 25 ms/hop 10 ms và F0 estimator.
- Tiêu chí giữ tích hợp median5: inner selection chọn median5 ở ít nhất 3/4 outer folds; so outer scores, cả F0mean MAE và F0std MAE trung bình của chiến lược nested phải thấp hơn median3 cố định; mask phân loại và NumF0 phải giữ nguyên. Nếu không đạt, ghi kết quả rồi đưa notebook về median3 bằng commit riêng.
- Chỉ dùng `TinHieuHuanLuyen`; không đọc hoặc dùng TEST. Kết quả vẫn là cross-validation trên bốn file, không phải kiểm định độc lập.
