# Trạng thái BT2 và bước kế tiếp (14/10/2026)

## Hiện trạng có thể quay lại

- Toàn bộ WAV/LAB, bản export output và ba notebook chạy local nằm trong working folder. Output nhúng đã bỏ khỏi notebook để giảm từ khoảng 5.44 MB còn khoảng 289 KB hiện tại; bản gốc và 89 output có thể khôi phục/đối chiếu từ Git và `working_output/`.
- [AGENTS.md](../AGENTS.md) cấm tuyệt đối Google Drive/G Drive, yêu cầu mỗi thay đổi một commit, training-only validation và điểm quay lại. Colab trong Chrome chỉ là phương án dự phòng khi máy thiếu tài nguyên; các lượt đo hiện tại chạy local.
- Ba notebook đã có ma trận nhầm lẫn V/UV và biểu đồ F1/BA, sai số F0, NumF0 theo file. Hình waveform/F0 từng file mặc định tắt (`SHOW_DETAILED_TEST_PLOTS = False`) và có thể bật lại. [Ảnh xem trước](visualization_review/) được lưu ngoài notebook.
- Notebook AMDF đã cố định cấu hình cuối ở 25 ms/Gaussian và tích hợp cổng năng lượng đã đạt LOFO. [Biên bản tích hợp 09](INTEGRATION_09_RESULT.md), [biên bản tích hợp 10](INTEGRATION_10_RESULT.md) và [QA training](integration_10_training_qa.json) lưu kiểm tra. Điểm quay lại ngay trước cổng năng lượng: `26c7c7d`; các script thí nghiệm nằm riêng và đều đã commit.

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

Trong phạm vi **thí nghiệm 01–06** của bảng trên, không cấu hình mới nào đạt **đồng thời** cổng F1, BA, F0mean, F0std và SIL đặt trước. Câu này chỉ tổng kết sáu phép thử đó; thí nghiệm 08 được đánh giá riêng ở phần sau. Các kết quả 01/03 cho thấy GMM không nhãn bỏ lỡ nhiều V, nhưng nới ngưỡng đơn không đủ: nhận thêm UV/SIL và F0 bất thường. Cổng năng lượng xử lý SIL rất tốt; sai số F0mean còn lại ở `phone_F1` và `studio_M1`. [Chẩn đoán F0](EXPERIMENT_04_DIAGNOSIS.md) cho thấy đó không chỉ là vấn đề SIL.

## So sánh thuật toán ở đúng 25 ms

[Thí nghiệm 07](EXPERIMENT_07_RESULT.md) tái fit ba phương pháp ngưỡng của từng notebook trên ba file training rồi đánh giá file còn lại. AMDF cao hơn ACF về macro F1 **0.8695 so với 0.8363**, BA **0.9128 so với 0.8709**, F0mean MAE **4.28 so với 5.13 Hz** và F0std MAE **14.58 so với 16.41 Hz**. ACF ít false voiced trên SIL hơn: **44 so với 51**. Điều kiện vượt trội đặt trước không đạt cho cả hai; chưa chọn thuật toán cuối.

[Thí nghiệm 08](EXPERIMENT_08_RESULT.md) thêm đúng cổng năng lượng V/SIL cho AMDF Gaussian 25 ms, dùng cùng bốn fold training. Ứng viên **đạt cổng so với ACF 25 ms**: F1 **0.8646 so với 0.8363**, BA **0.9206 so với 0.8709**, F0mean MAE **2.93 so với 5.13 Hz**, F0std MAE **6.50 so với 16.41 Hz**, false voiced SIL **1 so với 44**. Ngưỡng fit từ đủ training đã đóng băng: `T_pitch=0.4124933063`, `T_energy=0.0615446159` với RMS chuẩn hóa bằng phân vị 95% từng file. [Tích hợp 10](INTEGRATION_10_RESULT.md) đưa gate vào notebook và xác nhận toàn bộ code cell chạy; TEST chỉ dùng mô tả sau khi khóa cấu hình. NumF0 tổng giảm **600→545** so với ACF; điều kiện MinNumF0/MaxNumF0 của thầy chưa xác định.

## Audit NumF0 hoàn tất

Audit training-only đã đối chiếu từng file/fold: LAB có 614 frame V, còn AMDF+energy dự đoán 545 frame voiced và tạo đúng 545 F0 hữu hạn/dương. Trong đó 535 F0 rơi trên LAB V, 9 trên UV, 1 trên SIL; không có frame chưa gán nhãn hay F0 dự đoán không hợp lệ. Số này khớp cột NumF0 đã lưu. Chi tiết, lệnh, mã và môi trường: [kết quả audit](NUMF0_AUDIT_RESULT.md), [CSV](numf0_training_audit.csv), [script](audit_numf0_training.py).

Audit xác nhận NumF0 theo mã, nhưng điều kiện `MinNumF0 < NumF0 < MaxNumF0` vẫn không kiểm tra được vì tài liệu thầy đưa chưa định nghĩa hai giới hạn hoặc phạm vi đếm. Không lấy cực trị bốn file làm giới hạn và không dùng TEST để chọn. Việc tiếp theo có ý nghĩa là lấy định nghĩa Min/Max từ đề/thầy khi có; cho đến lúc đó giữ nguyên cấu hình và báo rõ yêu cầu còn thiếu.

Chẩn đoán frame bị cổng năng lượng loại đã hoàn tất: 59 frame của bốn fold được loại, gồm 50 SIL, 3 UV và 6 V; sáu V bị loại đều nằm trong hai file studio. Cổng giảm NumF0 từ 604 xuống 545 so với AMDF Gaussian không gate, khớp chính xác số frame bị loại. Phân bố relative RMS và số đếm theo file ở [báo cáo chẩn đoán](ENERGY_GATE_DIAGNOSIS_RESULT.md) và [CSV](energy_gate_removed_frames.csv). Không thay đổi cấu hình.

[Thí nghiệm 11](EXPERIMENT_11_RESULT.md) thử median relative RMS 3 frame với cùng ngưỡng LOFO, nhưng quyết định voiced không đổi ở bất cứ frame nào; tiêu chí khôi phục V không đạt. Đã giữ kết quả thất bại, không thay đổi notebook.

[Thí nghiệm 15](EXPERIMENT_15_RESULT.md) thử rescue frame low-energy có AMDF dip mạnh theo ngưỡng fit trong mỗi LOFO fold. Không đạt cổng: recall V chỉ tăng 0.004, trong khi BA giảm 0.013, F0std MAE tăng 2.412 Hz và FP SIL tăng 1→27. Không tích hợp; giữ energy gate hiện tại.

[Thí nghiệm 16](EXPERIMENT_16_RESULT.md) thêm điều kiện ZCR vào nhánh rescue, nhưng cũng không đạt: recall V chỉ tăng 0.004, F0std MAE tăng 2.245 Hz và FP SIL tăng 1→21. Không tích hợp; giữ cấu hình AMDF+energy+median5.

Audit quy trình LOFO của thí nghiệm 08 xác nhận LAB holdout không đi vào bước fit threshold. Có một điều kiện triển khai cần nêu: RMS từng file được chuẩn hóa theo percentile 95 tính từ toàn recording, nên validation hiện mô phỏng suy luận offline trên file hoàn chỉnh, không phải streaming. [Báo cáo audit quy trình](VALIDATION_PROTOCOL_AUDIT_RESULT.md).

[Thí nghiệm 12](EXPERIMENT_12_RESULT.md) giữ nguyên quyết định V/UV/SIL và chỉ median F0 ba frame trong run voiced. Trung bình LOFO training, F0mean MAE cải thiện 2.929→2.116 Hz, F0std MAE 6.502→4.609 Hz; cả macro F1/BA, NumF0, SIL FP không đổi. Có file MAE tăng, nên đây là cải thiện trung bình trên bốn file chứ không phải từng file. Bước này đã được tích hợp sau khi rà cell notebook và xác nhận đầu ra; xem [biên bản tích hợp 12](INTEGRATION_12_RESULT.md).

Đã tích hợp median5 F0 vào notebook AMDF sau khi median5 đạt cổng LOFO training-only ở [thí nghiệm 13](EXPERIMENT_13_RESULT.md). QA chạy các cell training và xử lý 4 file training, không ghép cặp hay xử lý WAV/LAB TEST; hash mask dự đoán, TP/TN/FP/FN, macro F1, BA, recall, NumF0 và FP_SIL giữ nguyên so với median3. Trên cùng bốn file training với ngưỡng full-training, F0mean MAE giảm 2.234→1.850 Hz và F0std MAE 3.510→2.740 Hz. Đây là kiểm tra tích hợp in-sample; validation vẫn là LOFO của thí nghiệm 13. Xem [biên bản tích hợp 13](INTEGRATION_13_RESULT.md).

Vì median5 được chọn sau khi xem LOFO ở thí nghiệm 13, [thí nghiệm nested 14](EXPERIMENT_14_RESULT.md) chọn cửa sổ chỉ trong inner LOFO rồi đo ở outer held-out. Inner procedure chọn median5 ở cả 4 fold; outer F0mean/F0std MAE trung bình là 1.710/3.892 Hz, thấp hơn median3 cố định 2.116/4.609 Hz. Kết quả chỉ dùng training, chưa phải xác nhận độc lập ngoài bốn file.

Với yêu cầu thầy, cấu hình nộp cuối phải chọn **một** trong ACF/AMDF ở 25 ms/10 ms. ACF gốc 25 ms hiện là baseline phù hợp khung đề; AMDF ban đầu 30 ms và GMM ACF 20 ms chỉ nên để ở phần khảo sát. [Ghi chú thầy và đối chiếu bạn học](PEER_COMPARISON.md) chưa cho công thức/giá trị MinNumF0 và MaxNumF0, nên chưa thể kết luận điều kiện số F0 ước lượng đã đạt. Cần làm rõ điều kiện này trước khi nộp.



Audit 17 kiểm tra dataflow notebook ACF/GMM: ba threshold và metric V/UV được fit/tính trên cùng các frame LAB training; sau đó cùng các metric in-sample chọn threshold method và frame length. Đây là lựa chọn in-sample, không phải validation. Theo mã, TEST chỉ được mở sau khi đã chọn cấu hình và không quyết định lựa chọn trong notebook; tuy nhiên TEST của dự án đã từng được xem để định hướng nên không gọi đó là đánh giá độc lập. Chi tiết: [kế hoạch](EXPERIMENT_17_PLAN.md), [kết quả](EXPERIMENT_17_RESULT.md). Không thay đổi thuật toán. Nếu dùng notebook này làm khảo sát, giữ kết luận metric training là in-sample; mọi so sánh lựa chọn method tiếp theo phải dùng LOFO training-only và khóa frame 25 ms theo đề.

Đối chiếu sau audit 17: phần so sánh ACF/AMDF với chọn threshold theo method đã được kiểm định LOFO training-only ở [thí nghiệm 07](EXPERIMENT_07_RESULT.md), cố định 25 ms theo đề. Không cần chạy lặp. Notebook khảo sát vẫn hiển thị metric in-sample; không diễn giải chúng như validation. Việc chọn 20/25/30 ms bằng metric training trong notebook không dùng để quyết định cấu hình nộp, vì đề đã khóa 25 ms.

Audit 18 đối chiếu scorer ACF notebook với scorer tái lập dùng ở thí nghiệm 07 trên 1,291 frame training. Frame count và timestamp khớp; max delta score 7.78e-16, lag 9.10e-13 sample, không frame nào vượt tolerance 1e-9. Điều này xác nhận parity triển khai ACF cho LOFO ở mức số học; không phải bằng chứng tổng quát hóa. Xem [kế hoạch](EXPERIMENT_18_PLAN.md), [kết quả](EXPERIMENT_18_RESULT.md), [JSON](acf_scorer_parity.json), [script](audit_acf_scorer_parity.py).

Audit 19 đối chiếu scorer AMDF notebook với scorer dùng trong thí nghiệm 07 trên 1,291 frame training. Frame count/timestamp khớp; score và lag nội suy khớp tuyệt đối ở các frame. Kết quả và lệnh tái lập: [kế hoạch](EXPERIMENT_19_PLAN.md), [báo cáo](EXPERIMENT_19_RESULT.md), [JSON](amdf_scorer_parity.json), [script](audit_amdf_scorer_parity.py). Đây là xác nhận parity triển khai, không phải đánh giá tổng quát hóa.
