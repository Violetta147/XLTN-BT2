# Kết quả audit 17: chọn cấu hình ACF trong notebook khảo sát

- Điểm quay lại trước audit: `b490883`; kế hoạch audit commit riêng tại `0987d0e`.
- Phạm vi thực hiện đúng kế hoạch: đọc dataflow các cell 3, 17, 19–21, 24, 28 và 32–36 của `BT2_implement_finished_v3_executed_original - Copy.ipynb`. Không chạy notebook, không đọc/ghép WAV/LAB TEST, không sửa thuật toán.

## Phát hiện

1. Cell 17 trích score ACF và nhãn LAB từ `train_wavs` cho từng frame length. Cell 19 fit ba ngưỡng (Gaussian và hai phương pháp histogram) từ chính các score cùng nhãn này, rồi `vu_metrics_from_training(df, threshold)` tính metric trên cùng dataframe `df`.
2. `train_threshold` chọn phương pháp bằng balanced accuracy rồi accuracy đo trên những frame V/UV đã tham gia fit ngưỡng. Cell 24 tiếp tục chọn frame length tối đa hóa cùng cặp metric từ `training_rows`. Vì vậy cả lựa chọn phương pháp và 20/25/30 ms đều là **in-sample selection**, không phải validation hay LOFO. Các metric được in ở đây có nguy cơ lạc quan; chúng không ước lượng tổng quát hóa sang file chưa thấy.
3. Sau khi cấu hình đã được chọn như trên, cell 28 xử lý TEST và dùng LAB để tính metric; cells 32–36 báo cáo và vẽ TEST. Theo dataflow mã, TEST không tham gia chọn cấu hình trong notebook này. Tuy nhiên, project đã xem một số kết quả TEST để định hướng các lượt sau, vì vậy không gọi các số TEST hiện có là đánh giá độc lập.
4. Notebook này dùng supervised threshold từ LAB V/UV, không phải GMM không nhãn. Chọn nó làm cấu hình cuối cũng không phù hợp yêu cầu thầy vì cell 24 có thể chọn frame khác 25 ms; cần khóa 25 ms theo đề.

## Kết luận và bước tiếp

Không dùng các con số training hiện trên bảng để kết luận frame length hoặc phương pháp nào tổng quát hóa tốt hơn. Giữ notebook như khảo sát minh họa. Nếu cần so sánh lựa chọn threshold, đánh giá trên bốn file training bằng LOFO, mỗi fold fit threshold và chọn phương pháp chỉ trên ba file còn lại; giữ frame 25 ms cố định theo đề. Vì lựa chọn method trong LOFO cũng là một bước chọn mô hình, báo rõ đây là validation training-only với chỉ bốn file, và không lặp lại lựa chọn theo TEST.

Không phát sinh thay đổi thuật toán, nên không có metric trước/sau hoặc cấu hình nào được thay thế.
