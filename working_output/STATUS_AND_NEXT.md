# Trạng thái BT2 và bước kế tiếp (29/09/2026)

## Hiện trạng có thể quay lại

- Toàn bộ WAV/LAB, bản export output và ba notebook chạy local nằm trong working folder. Output nhúng đã bỏ khỏi notebook để giảm từ khoảng 5.44 MB còn khoảng 289 KB hiện tại; bản gốc và 89 output có thể khôi phục/đối chiếu từ Git và `working_output/`.
- [AGENTS.md](../AGENTS.md) cấm tuyệt đối Google Drive/G Drive, yêu cầu mỗi thay đổi một commit, training-only validation và điểm quay lại. Colab trong Chrome chỉ là phương án dự phòng khi máy thiếu tài nguyên; các lượt đo hiện tại chạy local.
- Ba notebook đã có ma trận nhầm lẫn V/UV và biểu đồ F1/BA, sai số F0, NumF0 theo file. Hình waveform/F0 từng file mặc định tắt (`SHOW_DETAILED_TEST_PLOTS = False`) và có thể bật lại. [Ảnh xem trước](visualization_review/) được lưu ngoài notebook.
- **Chưa có thuật toán mới được áp dụng vào notebook**. Điểm quay lại thuật toán gọn ban đầu: `6b332a0`; các script thí nghiệm nằm riêng và đều đã commit.

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

## Bước tiếp theo duy nhất nên xét

So sánh **ACF gốc 25 ms** với AMDF 25 ms bằng cùng giao thức leave-one-file-out theo file training, tái fit ngưỡng ACF từ ba file từng fold theo đúng phương pháp có sẵn trong notebook ACF. Đặt trước cùng định nghĩa metric và cách xử lý SIL/F0, rồi báo số liệu từng file. Đây là bước chọn *thuật toán* phù hợp yêu cầu thầy; không thử thêm ngưỡng AMDF mới trước khi có phép so sánh này. Cấu hình Gaussian AMDF ở thí nghiệm 06 đã không đạt cổng F0/SIL. Vì bảng TEST của các biến thể đã được xem, số TEST cũ chỉ có giá trị mô tả, không được gọi là đánh giá độc lập của cấu hình mới.

Với yêu cầu thầy, cấu hình nộp cuối phải chọn **một** trong ACF/AMDF ở 25 ms/10 ms. ACF gốc 25 ms hiện là baseline phù hợp khung đề; AMDF gốc 30 ms và GMM ACF 20 ms chỉ nên để ở phần khảo sát. [Ghi chú thầy và đối chiếu bạn học](PEER_COMPARISON.md) chưa cho công thức/giá trị MinNumF0 và MaxNumF0, nên chưa thể kết luận điều kiện số F0 ước lượng đã đạt. Cần làm rõ điều kiện này trước khi nộp.
