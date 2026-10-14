# Tích hợp 10: AMDF 25 ms với cổng năng lượng

- Điểm quay lại trước thay đổi thuật toán: `26c7c7d` (kế hoạch tích hợp sau khi đồng bộ commit remote). Notebook giờ học `T_energy` chỉ từ các file `TinHieuHuanLuyen`: RMS mỗi frame chia cho phân vị 95% RMS của cùng file; chọn ngưỡng để tối đa balanced accuracy V/SIL trung bình theo file, hòa chọn ngưỡng thấp. Frame 25 ms, hop 10 ms, AMDF score, ngưỡng Gaussian pitch, estimator F0 và metric được giữ nguyên.
- Ngưỡng từ notebook khớp đúng ngưỡng khóa từ đủ training: `T_pitch=0.41249330632749887`; `T_energy=0.061544615883604575`. Bảng chọn phương pháp/ngưỡng 20/25/30 ms khớp bản trước; không đổi phần fit pitch.
- Kiểm tra đầy đủ: chạy **14/14 code cell** theo thứ tự trong tiến trình Python mới, từ working folder. Tất cả đồ thị được tạo ở backend không giao diện, đóng sau mỗi cell để không nhúng output lớn trở lại notebook. Phiên bản môi trường và dữ liệu theo file ở [integration_10_training_qa.json](integration_10_training_qa.json).

## Đối chiếu implementation trên training

Đây là kiểm tra khớp mã với ngưỡng fit trên đủ bốn file training, nên **không phải ước lượng validation**. Notebook và script thí nghiệm khớp nhãn, score, relative RMS, quyết định từng frame, TP/TN/FP/FN, NumF0, false voiced SIL và sai số F0 trên cả bốn file.

| Chỉ số trên cùng bốn file training | Chỉ ngưỡng AMDF | AMDF + energy gate |
|---|---:|---:|
| Macro F1 V/UV, trung bình theo file | 0.8721 | 0.8697 |
| Recall V, gộp khung | 0.8860 | 0.8779 |
| Recall UV, gộp khung | 0.9333 | 0.9500 |
| Balanced accuracy, trung bình theo file | 0.9143 | 0.9232 |
| F0mean MAE, trung bình theo file (Hz) | 4.4580 | 3.0801 |
| F0std MAE, trung bình theo file (Hz) | 14.3290 | 5.6210 |
| NumF0 tổng | 606 | 548 |
| False voiced trên SIL tổng | 50 | 0 |

## Bằng chứng lựa chọn: LOFO training-only đã đặt trước

Quyết định giữ ứng viên dựa trên bốn fold leave-one-file-out trong [thí nghiệm 08](EXPERIMENT_08_RESULT.md), mỗi fold chỉ học ngưỡng bằng ba file training. Kết quả so với ACF và AMDF không gate:

| Chỉ số LOFO | ACF 25 ms | AMDF Gaussian | AMDF + energy gate |
|---|---:|---:|---:|
| Macro F1 V/UV | 0.8363 | **0.8695** | 0.8646 |
| Recall V | 0.8799 | **0.8910** | 0.8763 |
| Recall UV | 0.8619 | 0.9345 | **0.9649** |
| Balanced accuracy | 0.8709 | 0.9128 | **0.9206** |
| F0mean MAE (Hz) | 5.1277 | 4.2787 | **2.9286** |
| F0std MAE (Hz) | 16.4110 | 14.5808 | **6.5022** |
| NumF0 tổng | 600 | 604 | 545 |
| False voiced trên SIL tổng | 44 | 51 | **1** |

Ứng viên vẫn đạt quy tắc đặt trước: F1 tăng ít nhất 0.01 và BA không giảm quá 0.01 so với ACF; hai F0 MAE không cao hơn; SIL false positive không tăng. So với AMDF không gate, SIL giảm còn 1 và F1 chỉ giảm 0.0049. Recall V giảm so với ACF và NumF0 ít hơn ACF 55 khung; cần giữ hai đánh đổi này trong báo cáo. Chưa thể xác nhận ràng buộc MinNumF0/MaxNumF0 vì đề chưa định nghĩa giá trị/cách tính.

## TEST: chỉ mô tả sau khi cấu hình đã khóa

Notebook đã chạy phần báo cáo TEST để kiểm tra các cell downstream; macro F1 V/UV trung bình theo file là **0.8260**, F0mean MAE **2.0815 Hz**, F0std MAE **1.6741 Hz**, NumF0 **560**, false voiced SIL **2**. TEST từng được xem trong các bước trước, nên các con số này **chỉ mô tả**, không tham gia chọn gate/ngưỡng, không được gọi là đánh giá độc lập và không dùng để sửa cấu hình.
