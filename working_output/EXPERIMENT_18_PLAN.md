# Kế hoạch audit 18: parity scorer ACF trên training

- Điểm quay lại: `c403147` (working tree sạch).
- Giả thuyết: scorer ACF tái lập trong `validate_saved_results.py` cho cùng score và lag với hàm ACF trong notebook gốc trên cùng frame 25 ms/10 ms của training; do đó kết quả LOFO của thí nghiệm 07 không bị lệch do bản cài scorer.
- Phạm vi: chỉ bốn WAV trong `TinHieuHuanLuyen`; đọc code notebook cell 7? (hàm `detect_pitch_acf`, cell 15) và cell 9 (framing), đối chiếu với `acf_score` và framing của script. Không đọc TEST, không đổi mô hình.
- Tiêu chí: frame count và center timestamps phải khớp chính xác; score và lag tuyệt đối tối đa sai khác `1e-9` trên mọi frame. Nếu vượt ngưỡng, ghi số khung lệch/độ lệch max và không coi parity đã đạt.
- Kết quả cần ghi: phiên bản Python/NumPy/SciPy, số frame, max abs delta score/lag, số vượt tolerance, lệnh có thể tái lập. Đây là audit triển khai, không phải đánh giá chất lượng mô hình.
