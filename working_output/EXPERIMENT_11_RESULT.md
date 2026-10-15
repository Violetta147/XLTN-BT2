# Kết quả thí nghiệm 11: median 3 frame cho RMS

- Điểm quay lại: `d07c769`; kế hoạch và tiêu chí được commit trước khi chạy tại `84fb3b2`.
- Lệnh: `.venv\Scripts\python.exe working_output\experiment_11_rms_smoothing.py`.
- Dữ liệu: bốn file `TinHieuHuanLuyen`, leave-one-file-out; giữ nguyên các ngưỡng pitch và energy của từng fold trong thí nghiệm 08. Không dùng TEST.
- Biến thử duy nhất: median cửa sổ 3 frame trên relative RMS trước khi áp energy gate; biên lặp giá trị đầu/cuối.

## Kết quả

Median smoothing làm **0 thay đổi** trong quyết định voiced trên tổng 1,291 frame ở cả bốn fold. Vì vậy tất cả metric giữ nguyên:

| Metric | Gate gốc | Median 3 frame |
|---|---:|---:|
| Macro F1 | 0.864626 | 0.864626 |
| Balanced accuracy | 0.920620 | 0.920620 |
| Recall V / UV | 0.876303 / 0.964937 | 0.876303 / 0.964937 |
| F0mean MAE (Hz) | 2.9286 | 2.9286 |
| F0std MAE (Hz) | 6.5022 | 6.5022 |
| NumF0 | 545 | 545 |
| False voiced trên SIL | 1 | 1 |
| LAB V được khôi phục từ gate | — | 0 |

Giả thuyết không đạt: không có frame LAB V nào được khôi phục (tiêu chí yêu cầu ít nhất 3/6). Kết quả cho thấy các frame bị loại không phải những dip RMS ngắn mà median 3 frame có thể đảo lại. Đây là phép thử không cải thiện; giữ nguyên cấu hình notebook và gate hiện tại. Chi tiết theo file ở [CSV](experiment_11_lofo.csv), tóm tắt có thể tái lập ở [JSON](experiment_11_summary.json), mã ở [script](experiment_11_rms_smoothing.py).
