# Kế hoạch audit rò rỉ nhãn trong LOFO thí nghiệm 08

- Điểm quay lại: `8f056e9`.
- Giả thuyết: ngưỡng pitch và energy của mỗi fold chỉ dùng ba file training còn lại; file holdout chỉ dùng để tính metric. Cách chuẩn hóa RMS có thể đọc toàn bộ waveform holdout nhưng không dùng nhãn, nên là thích nghi không giám sát theo file và chỉ đại diện cho chế độ xử lý offline cả file.
- Phép kiểm tra: rà luồng dữ liệu của `experiment_08_amdf_energy.py`, `experiment_07_acf_amdf_25ms.py`, `experiment_04_energy_gate.py`; xác định rõ đối số fitter, nguồn nhãn và phép tính relative RMS ở holdout.
- Tiêu chí: ghi riêng kết luận về rò rỉ nhãn và giả định triển khai do chuẩn hóa theo toàn file. Không chạy lại thuật toán, không sửa threshold/notebook, không dùng TEST.
