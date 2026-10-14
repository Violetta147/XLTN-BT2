# Kết quả audit NumF0 trên training

- Điểm quay lại trước phép đo: `73f5c7c`; kế hoạch được ghi và commit trước khi chạy ở `25d3e8f`.
- Phép đo: 4 file `TinHieuHuanLuyen`, 25 ms / hop 10 ms, LAB gán theo tâm khung. Dùng nguyên ngưỡng pitch và energy theo từng fold LOFO trong `experiment_08_lofo.csv`; không fit lại, không dùng `TinHieuKiemThu`.
- Lệnh tái lập: `.venv\Scripts\python.exe working_output\audit_numf0_training.py` từ thư mục gốc. Script dùng lại scorer, đọc LAB và cách tạo frame của `experiment_01_hysteresis.py` cùng `load_with_energy` của `experiment_04_energy_gate.py`; đối chiếu NumF0 với kết quả đã lưu.
- Đầu vào/mã: `TinHieuHuanLuyen/*.wav`, `.lab`, `working_output/experiment_08_lofo.csv`, `working_output/audit_numf0_training.py`. Python/pandas/NumPy versions được lưu trong `numf0_training_audit_environment.json`.

## Kết quả theo file

| File | Tổng frame | LAB V | LAB UV | LAB SIL | Dự đoán voiced | TP V | FP UV | FP SIL | NumF0 hợp lệ | F0 hợp lệ trên V / UV / SIL |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| phone_F1.wav | 322 | 153 | 69 | 100 | 143 | 139 | 3 | 1 | 143 | 139 / 3 / 1 |
| phone_M1.wav | 414 | 244 | 62 | 108 | 209 | 203 | 6 | 0 | 209 | 203 / 6 / 0 |
| studio_F1.wav | 284 | 123 | 24 | 137 | 115 | 115 | 0 | 0 | 115 | 115 / 0 / 0 |
| studio_M1.wav | 271 | 94 | 25 | 152 | 78 | 78 | 0 | 0 | 78 | 78 / 0 / 0 |
| **Tổng** | **1291** | **614** | **180** | **497** | **545** | **535** | **9** | **1** | **545** | **535 / 9 / 1** |

Không có frame chưa gán nhãn. Mọi dự đoán voiced trong bốn fold đều tạo F0 hữu hạn, dương; do đó NumF0 khớp chính xác số dự đoán voiced (545) và tổng TP + FP(UV) + FP(SIL) (535 + 9 + 1). Mỗi NumF0 theo file cũng khớp cột NumF0 đã lưu trong LOFO. Đây là kết quả của cấu hình fold-specific trên training; không phải đánh giá độc lập.

## Kết luận

Audit xác nhận cách mã hiện tại đếm NumF0 và cho biết nó trùng số frame dự đoán voiced trong các fold này. LAB có 614 frame V, còn cấu hình tạo 545 F0 hợp lệ; hai đại lượng khác nhau vì có 79 frame LAB V không được dự đoán voiced, đồng thời có 10 dự đoán voiced thuộc UV/SIL.

Điều kiện `MinNumF0 < NumF0 < MaxNumF0` vẫn chưa thể xác nhận đạt: đề và ghi chú hiện có không nêu Min/Max, cách xác định chúng, hoặc phạm vi đếm. Không suy ra giới hạn từ cực trị của bốn file, và không chỉnh ngưỡng theo yêu cầu chưa định nghĩa. Kết quả không dùng TEST.
