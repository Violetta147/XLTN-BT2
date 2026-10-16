# Thí nghiệm 15: cứu khung F0 mạnh dưới ngưỡng năng lượng

- Điểm quay lại: AMDF+energy+median5 ở `3a883c2`.
- Bằng chứng/hypothesis: audit gate cho thấy energy gate loại 6 frame LAB V cùng 50 SIL và 3 UV; median smoothing RMS 3 frame không đổi quyết định. Kiểm tra liệu các frame thấp năng lượng nhưng có dip AMDF mạnh hơn (dip nhỏ hơn) có thể khôi phục V mà vẫn giới hạn false-voiced.
- Biến duy nhất: một ngưỡng rescue `T_rescue ≤ T_pitch`, fit riêng trong mỗi outer training fold bằng balanced accuracy V-vs-nonV trên frame có relative RMS dưới `T_energy` và score dưới `T_pitch`. NonV gồm UV và SIL; hòa chọn ngưỡng thấp hơn. Dự đoán rescue chỉ áp dụng cho những frame thấp năng lượng có score dưới ngưỡng này. Giữ nguyên pitch selector Gaussian, energy gate, frame 25 ms/hop 10 ms và median5 hậu xử lý.
- Đánh giá: 4-fold LOFO trên training; `T_pitch`, `T_energy` và `T_rescue` đều fit chỉ từ ba file training. So cùng fold với AMDF+energy+median5 hiện tại: macro F1, BA, recall V/UV, F0mean/F0std MAE, NumF0 và FP_SIL. Không xem/dùng TEST.
- Cổng đạt: recall V tăng ít nhất 0.02; macro F1 và BA mỗi metric không giảm quá 0.01; F0mean và F0std MAE không tăng quá 0.25 Hz; FP_SIL tổng không vượt 3 (baseline 1). Nếu trượt bất cứ điều kiện nào, giữ gate hiện hành và không tích hợp rescue.
