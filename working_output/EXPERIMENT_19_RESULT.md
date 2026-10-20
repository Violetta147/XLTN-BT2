# Kết quả audit 19: parity scorer AMDF

- Điểm quay lại: `5731d7d`; kế hoạch commit trước phép đo: `1e02069`.
- Lệnh tái lập: `.venv\\Scripts\\python.exe working_output\\audit_amdf_scorer_parity.py`.
- Chỉ dùng bốn WAV training, frame 25 ms / hop 10 ms; không đọc TEST, không sửa notebook.
- Python 3.11.9, NumPy 2.3.5, SciPy 1.17.1.

| Kiểm tra | Kết quả |
|---|---:|
| Số frame so khớp | 1,291 |
| File lệch frame count / timestamp | 0 / 0 |
| Sai khác score AMDF tối đa | 0 |
| Sai khác lag nội suy tối đa (sample) | 0 |
| Frame vượt tolerance 1e-9: score / lag | 0 / 0 |

Giả thuyết đạt: `amdf_score` trong `validate_saved_results.py` và scorer AMDF trong notebook trả về cùng score và lag nội suy cho toàn bộ frame training. Điều này xác nhận parity triển khai cho AMDF ở thí nghiệm 07; không xác nhận hiệu năng ngoài bốn file. Dữ liệu máy đọc được ở [JSON](amdf_scorer_parity.json), mã audit ở [script](audit_amdf_scorer_parity.py).
