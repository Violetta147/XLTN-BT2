# Chẩn đoán F0 sau cổng năng lượng

Chạy `.venv\Scripts\python.exe working_output\diagnose_experiment_04.py` chỉ trên các fold training. [Thống kê theo file](experiment_04_f0_diagnosis.csv), [theo nhãn thật](experiment_04_f0_by_label.csv). Nhãn chỉ được xem ở bước chẩn đoán sau suy luận.

- `phone_F1`: cổng năng lượng cho F0mean **210.08 Hz** so với LAB **217 Hz**, sai số có dấu −6.92 Hz; median F0 ứng viên **218.66 Hz**. Có 9/148 ứng viên ngoài dải mean ±2 std LAB, gồm 6 V, 1 UV, 2 SIL. Mean thấp trong khi median gần LAB cho thấy vài giá trị thấp có ảnh hưởng lớn; chưa chứng minh từng frame là lỗi octave.
- `studio_M1`: F0mean **118.07 Hz** so với LAB **113 Hz**, sai số +5.07 Hz; median ứng viên **104.78 Hz**. Hai khung UV bị nhận V có F0 trung bình **206.45 Hz**; đây là một nguồn kéo mean lên. Ngoài ra 7 khung V ngoài dải ±2 std LAB. Lọc SIL đơn thuần không xử lý hết UV và lag bất thường.
- `studio_F1`: cổng năng lượng hạ F0std từ 49.92 xuống 36.24 Hz, gần LAB 40 Hz hơn; F0mean chuyển từ 233.85 sang 229.33 Hz so với LAB 232 Hz. `phone_M1` có F0mean gần LAB ở cả hai cấu hình.

Thay đổi tiếp theo cần xử lý độ ổn định F0 ứng viên, không nên chỉ mở rộng/ngắt ngưỡng V/UV. Có thể kiểm tra lọc trung vị ba khung trên F0 *sau khi* quyết định V, nhưng phải ghi tiêu chí trước và không nối qua khoảng UV/SIL. Vì F0mean và F0std đang đánh đổi theo file, không suy từ vài ví dụ để công bố cải thiện chung.
