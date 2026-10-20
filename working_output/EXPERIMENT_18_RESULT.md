# Kết quả audit 18: parity scorer ACF

- Điểm quay lại: `c403147`; kế hoạch commit trước khi đo: `121d947`.
- Lệnh tái lập từ thư mục gốc: `.venv\\Scripts\\python.exe working_output\\audit_acf_scorer_parity.py`.
- Phạm vi: chỉ bốn WAV training, 25 ms / 10 ms; không đọc TEST và không đổi notebook.
- Python 3.11.9, NumPy 2.3.5, SciPy 1.17.1.

| Kiểm tra | Kết quả |
|---|---:|
| Số frame so khớp | 1,291 |
| File có frame count/timestamp lệch | 0 / 0 |
| Tối đa sai khác score ACF | 7.78e-16 |
| Tối đa sai khác lag (sample) | 9.10e-13 |
| Frame vượt tolerance 1e-9: score / lag | 0 / 0 |

Giả thuyết đạt: scorer trong `validate_saved_results.py` trùng với hàm ACF của notebook trong sai số số học rất nhỏ trên mọi frame training. Điều này hỗ trợ tính đúng của phần tính score/lag trong LOFO thí nghiệm 07; không xác nhận các giả định khoa học khác hoặc hiệu năng ngoài bốn file training. Số liệu máy đọc được lưu tại [JSON](acf_scorer_parity.json), script tại [audit](audit_acf_scorer_parity.py).
