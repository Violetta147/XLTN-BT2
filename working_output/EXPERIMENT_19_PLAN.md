# Kế hoạch audit 19: parity scorer AMDF trên training

- Điểm quay lại: `5731d7d` (working tree sạch).
- Giả thuyết: `amdf_score` tái lập trong `validate_saved_results.py` cho cùng AMDF score và lag nội suy với hàm trong notebook AMDF trên cùng frame 25 ms/10 ms training.
- Phạm vi: bốn WAV trong `TinHieuHuanLuyen`, so sánh `normalized_amdf`/`deepest_local_dip` của notebook với `amdf_score`; không đọc TEST, không đổi notebook hay mô hình.
- Tiêu chí: frame count/timestamp phải trùng; trên mọi frame, sai khác score và refined lag không quá `1e-9` (lag tính theo sample). Nếu vượt ngưỡng, ghi số frame lệch và cực đại sai khác.
- Lưu lệnh, Python/NumPy/SciPy, kết quả JSON và script tái lập. Đây là audit triển khai, không phải đánh giá hiệu năng.
