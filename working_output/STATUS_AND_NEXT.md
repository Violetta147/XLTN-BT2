# Trạng thái BT2 và bước kế tiếp (29/09/2026)

## Hiện trạng có thể quay lại

- Toàn bộ WAV/LAB, bản export output và ba notebook chạy local nằm trong working folder. Output nhúng đã bỏ khỏi notebook để giảm từ khoảng 5.44 MB còn khoảng 289 KB hiện tại; bản gốc và 89 output có thể khôi phục/đối chiếu từ Git và `working_output/`.
- [AGENTS.md](../AGENTS.md) cấm tuyệt đối Google Drive/G Drive, yêu cầu mỗi thay đổi một commit, training-only validation và điểm quay lại. Colab trong Chrome chỉ là phương án dự phòng khi máy thiếu tài nguyên; các lượt đo hiện tại chạy local.
- Ba notebook đã có ma trận nhầm lẫn V/UV và biểu đồ F1/BA, sai số F0, NumF0 theo file. Hình waveform/F0 từng file mặc định tắt (`SHOW_DETAILED_TEST_PLOTS = False`) và có thể bật lại. [Ảnh xem trước](visualization_review/) được lưu ngoài notebook.
- Notebook AMDF đã cố định cấu hình cuối ở 25 ms, Gaussian từ training; **cổng năng lượng chưa được áp dụng vào notebook**. [Biên bản tích hợp 09](INTEGRATION_09_RESULT.md) và [số QA](integration_09_qa.json) lưu kiểm tra code. Điểm quay lại trước thay đổi cấu hình: `328a9ce`; các script thí nghiệm nằm riêng và đều đã commit.

## Sáu phép thử AMDF 25 ms trên training

Bốn lượt leave-one-file-out theo file, cùng frame 25 ms/hop 10 ms, cùng LAB tâm khung và F0 estimator. F1/BA/MAE là trung bình không trọng số qua bốn file; SIL FP là tổng. Chi tiết và quy tắc đặt trước ở [01](EXPERIMENT_01_RESULT.md), [02](EXPERIMENT_02_RESULT.md), [03](EXPERIMENT_03_RESULT.md), [04](EXPERIMENT_04_RESULT.md), [05](EXPERIMENT_05_RESULT.md), [06](EXPERIMENT_06_RESULT.md).

| Cấu hình | Macro F1 V/UV | BA | F0mean MAE Hz | F0std MAE Hz | FP trên SIL |
|---|---:|---:|---:|---:|---:|
| GMM lõi | 0.8051 | 0.8836 | **2.0851** | 8.4196 | 25 |
| 01: GMM ngưỡng trễ | 0.8862 | 0.9024 | 4.9212 | 16.1926 | 57 |
| 02: lấp một khung | 0.8147 | 0.8896 | 2.8330 | 9.1165 | 27 |
| 03: ngưỡng có nhãn | 0.8733 | 0.8939 | 5.2992 | 19.5540 | 88 |
| 04: có nhãn + năng lượng | 0.8747 | **0.9166** | 3.7482 | 8.3963 | **3** |
| 05: thêm median F0 ba khung | 0.8747 | **0.9166** | 2.9663 | **6.6175** | **3** |
| 06: giao điểm Gaussian có nhãn | 0.8695 | 0.9128 | 4.2787 | 14.5808 | 51 |

Không cấu hình mới nào đạt **đồng thời** cổng F1, BA, F0mean, F0std và SIL đặt trước, nên chưa đổi cấu hình cuối. Các kết quả 01/03 cho thấy GMM không nhãn bỏ lỡ nhiều V, nhưng nới ngưỡng đơn không đủ: nhận thêm UV/SIL và F0 bất thường. Cổng năng lượng xử lý SIL rất tốt; sai số F0mean còn lại ở `phone_F1` và `studio_M1`. [Chẩn đoán F0](EXPERIMENT_04_DIAGNOSIS.md) cho thấy đó không chỉ là vấn đề SIL.

## So sánh thuật toán ở đúng 25 ms

[Thí nghiệm 07](EXPERIMENT_07_RESULT.md) tái fit ba phương pháp ngưỡng của từng notebook trên ba file training rồi đánh giá file còn lại. AMDF cao hơn ACF về macro F1 **0.8695 so với 0.8363**, BA **0.9128 so với 0.8709**, F0mean MAE **4.28 so với 5.13 Hz** và F0std MAE **14.58 so với 16.41 Hz**. ACF ít false voiced trên SIL hơn: **44 so với 51**. Điều kiện vượt trội đặt trước không đạt cho cả hai; chưa chọn thuật toán cuối.

[Thí nghiệm 08](EXPERIMENT_08_RESULT.md) thêm đúng cổng năng lượng V/SIL cho AMDF Gaussian 25 ms, dùng cùng bốn fold training. Ứng viên **đạt cổng so với ACF 25 ms**: F1 **0.8646 so với 0.8363**, BA **0.9206 so với 0.8709**, F0mean MAE **2.93 so với 5.13 Hz**, F0std MAE **6.50 so với 16.41 Hz**, false voiced SIL **1 so với 44**. Ngưỡng fit từ đủ training đã đóng băng: `T_pitch=0.4124933063`, `T_energy=0.0615446159` với RMS chuẩn hóa bằng phân vị 95% từng file. Đây là ứng viên trên validation, chưa đưa vào notebook, chưa có TEST độc lập. NumF0 tổng giảm **600→545** so với ACF; điều kiện MinNumF0/MaxNumF0 của thầy chưa xác định.

## Bước tiếp theo duy nhất nên xét

Thêm **riêng** cổng năng lượng V/SIL từ thí nghiệm 08 vào notebook AMDF 25 ms trong một commit mới. Giữ nguyên score AMDF, ngưỡng Gaussian, frame/hop và cách tính metric; xác nhận các ngưỡng chỉ học từ training và số local khớp script LOFO trước khi xem TEST. Nếu chạy TEST để kiểm tra code sau khi đóng băng cấu hình, ghi rõ đó là kết quả mô tả vì bảng TEST trước đã được xem.

Với yêu cầu thầy, cấu hình nộp cuối phải chọn **một** trong ACF/AMDF ở 25 ms/10 ms. ACF gốc 25 ms hiện là baseline phù hợp khung đề; AMDF ban đầu 30 ms và GMM ACF 20 ms chỉ nên để ở phần khảo sát. [Ghi chú thầy và đối chiếu bạn học](PEER_COMPARISON.md) chưa cho công thức/giá trị MinNumF0 và MaxNumF0, nên chưa thể kết luận điều kiện số F0 ước lượng đã đạt. Cần làm rõ điều kiện này trước khi nộp.
