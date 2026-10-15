# Kết quả chẩn đoán frame bị cổng năng lượng loại

- Điểm quay lại trước phép đo: `e8b181b`; câu hỏi và tiêu chí được đăng ký tại `12136a6`.
- Lệnh tái lập tại thư mục gốc: `.venv\Scripts\python.exe working_output\audit_energy_gate_removed.py`.
- Chỉ dùng 4 WAV/LAB trong `TinHieuHuanLuyen`; khung 25 ms/hop 10 ms; ngưỡng pitch và energy lấy nguyên từ từng fold trong `working_output/experiment_08_lofo.csv`. Không fit tham số và không dùng TEST.
- Mã thực thi lại scorer AMDF/LAB/energy hiện có trong `experiment_01_hysteresis.py`, `experiment_04_energy_gate.py` và `validate_saved_results.py`. CSV chi tiết và JSON tổng nằm cạnh báo cáo.

| File | Voiced trước gate | Voiced sau gate | Bị loại: V | Bị loại: UV | Bị loại: SIL |
|---|---:|---:|---:|---:|---:|
| phone_F1.wav | 143 | 143 | 0 | 0 | 0 |
| phone_M1.wav | 210 | 209 | 0 | 0 | 1 |
| studio_F1.wav | 142 | 115 | 2 | 1 | 24 |
| studio_M1.wav | 109 | 78 | 4 | 2 | 25 |
| **Tổng** | **604** | **545** | **6** | **3** | **50** |

Phép tái tạo khớp NumF0 đã lưu theo từng file và tổng 604→545. Tổng 59 frame bị loại được phân giải đầy đủ: 6 LAB V, 3 LAB UV, 50 LAB SIL. Vậy giả thuyết “phần lớn là SIL, một phần V bị đánh đổi” được xác nhận. Các frame V bị loại tập trung ở hai file studio; không có frame V nào bị loại trong hai file phone.

Các frame V bị loại có relative RMS trung vị 0.0533 ở `studio_F1` (min–max 0.0424–0.0643) và 0.0329 ở `studio_M1` (0.0270–0.0420). Các frame SIL bị loại có median thấp hơn, lần lượt 0.00755 và 0.00351. Đây là mô tả trên bốn file training, không đủ dữ liệu để suy ra Min/Max F0 hoặc chỉnh ngưỡng. Cấu hình không thay đổi; TEST không được dùng.
