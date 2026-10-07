# Kiểm tra pipeline BT2 trên KEELE

Đã chạy cấu hình cố định trên tất cả 10 bản thu KEELE: 5 nam, 5 nữ, tổng 337.14 giây. Không học hoặc chọn tham số từ KEELE. Kết quả không đạt tiêu chí chẩn đoán đã đăng ký, và không file nào đạt Average MAPE <2%. Vì vậy phép thử này chưa hỗ trợ kết luận rằng kỹ thuật đã tốt và lỗi BT2 chỉ do thiếu dữ liệu.

Pipeline đang được kiểm tra là Praat 7.0.02 filtered autocorrelation với ngưỡng hữu thanh 0,30, sau đó NAMDF hard170 tinh chỉnh F0. Đây là cấu hình chọn từ các thí nghiệm BT2; không phải notebook ACF đã nộp. Control dùng cùng đầu ra Praat trước bước NAMDF. Giữ khoảng F0 70–400 Hz, cửa sổ NAMDF 25/40 ms, bước dịch 10 ms và tần số lấy mẫu KEELE 20 kHz.

## Kết quả tổng hợp

| model | gpe20_pct | vde_pct | ffe20_pct | rpa50_pct | file_mean_average_mape | worst_file_average_mape | files_average_mape_lt2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate | 0.800104 | 5.85594 | 6.23424 | 78.7382 | 5.91916 | 11.7339 | 0 |
| control | 0.780589 | 5.85594 | 6.22501 | 79.7288 | 5.97461 | 12.0086 | 0 |

GPE20 là tỷ lệ sai cao độ hơn 20% trong các khung mà cả tham chiếu và thuật toán đều nhận hữu thanh. Chỉ số này không tính khung hữu thanh bị bỏ sót. VDE đo sai quyết định hữu thanh trên toàn bộ khung chấm. FFE20 tính cả sai quyết định hữu thanh và sai cao độ lớn. RPA50 đo tỷ lệ khung tham chiếu hữu thanh được dự đoán đúng F0 trong 50 cents, khoảng 3% về tần số; bỏ sót được tính là sai. GPE/VDE/FFE thấp hơn tốt hơn; RPA cao hơn tốt hơn.

Trên 32,514 khung được chấm, pipeline có GPE20 0.8001%, VDE 5.8559%, FFE20 6.2342% và RPA50 78.7382%. MAE F0 trên các khung cùng hữu thanh là 2.9961 Hz; recall hữu thanh 90.6427%. Có 1587 khung hữu thanh bị bỏ sót và 317 khung không hữu thanh bị nhận nhầm.

Bước NAMDF làm RPA50 thay đổi -0.9906 điểm phần trăm so với Praat; Average MAPE trung bình từng file thay đổi -0.0554 điểm phần trăm. Một chỉ số thống kê cải thiện nhẹ trong khi độ chính xác từng khung giảm: chưa có bằng chứng bước tinh chỉnh này tốt hơn Praat trên corpus mới.

## Từng bản thu

| File | GPE20 (%) | VDE (%) | RPA50 (%) | MAPE mean (%) | MAPE std (%) | MAPE count (%) | Average MAPE (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| f1nw0000 | 0.923952 | 4.44727 | 83.8014 | 1.73876 | 19.725 | 7.05421 | 9.50601 |
| f2nw0000 | 1.51771 | 4.14619 | 85.9621 | 1.43406 | 10.7765 | 5.83596 | 6.01552 |
| f3nw0000 | 1.28023 | 3.76271 | 82.4503 | 0.727799 | 0.614473 | 6.42384 | 2.5887 |
| f4nw0000 | 1.16995 | 6.17886 | 80.4215 | 2.79744 | 13.7656 | 9.3178 | 8.62697 |
| f5nw0000 | 0.493963 | 2.10416 | 88.4822 | 1.14506 | 5.36128 | 0.430571 | 2.3123 |
| m1nw0000 | 0.729443 | 10.1101 | 58.6359 | 3.60654 | 2.79563 | 14.4114 | 6.93787 |
| m2nw0000 | 1.65593 | 11.3583 | 68.2344 | 2.99917 | 13.8958 | 18.3068 | 11.7339 |
| m3nw0000 | 0 | 5.66038 | 88.8433 | 0.999605 | 7.46235 | 4.51745 | 4.32647 |
| m4nw0000 | 0.204221 | 6.0256 | 72.1675 | 0.399478 | 2.23453 | 7.20443 | 3.27948 |
| m5nw0000 | 0.260688 | 5.35441 | 78.1265 | 1.82342 | 5.13415 | 4.63544 | 3.86433 |

Mean/std/count tham chiếu trong bảng được tính từ đường F0 KEELE trên cùng các thời điểm được chấm. Chúng không có cùng quy trình tạo chuẩn với ba thống kê thầy cung cấp cho BT2. Average MAPE dưới 2% vẫn được báo riêng, nhưng không thay cho việc chấm F0 từng khung.

## Điều phép thử cho thấy và chưa cho thấy

Pipeline ít mắc lỗi cao độ lớn trong các khung đã nhận hữu thanh, nhưng còn bỏ sót hoặc lệch F0 nhỏ ở khá nhiều khung. Vì thế chỉ nhìn GPE20 khoảng 0,8% sẽ quá lạc quan. Tiêu chí chẩn đoán đăng ký trước là RPA50 ≥90%, VDE ≤10% và FFE20 ≤10%; RPA50 không đạt. Các mốc này là tiêu chí của phép thử, không phải chuẩn chính thức của KEELE.

Có 199 khung tham chiếu hữu thanh nằm ngoài khoảng 70–400 Hz. Giới hạn khoảng F0 là một yếu tố kỹ thuật có thể ảnh hưởng kết quả; các khung này được giữ trong mẫu số để không che lỗi. Đồng thời có 1168 khung tham chiếu âm được loại vì không có tham chiếu đáng tin cậy. Coverage theo thời gian đạt trên 99,8% từng file. Không dịch đường tham chiếu để tìm kết quả tốt nhất.

KEELE có đường pitch kiểm tra bằng tay từ tín hiệu laryngograph, nhưng tài liệu gốc cảnh báo không coi nó là ground truth khớp chính xác khi cửa sổ phân tích khác. Tham chiếu dùng ACF khoảng 25,6 ms, trong khi gate Praat và NAMDF của ta có cửa sổ khác; độ trễ laryngograph–microphone cũng chỉ được hiệu chỉnh một phần. Do đó đây là kiểm tra chẩn đoán, không chứng nhận tuyệt đối độ chính xác F0. Không có nhãn SIL riêng trong KEELE này, nên không báo số khung false_voiced_sil như thể đã đo được; tham chiếu zero chỉ cung cấp lớp không hữu thanh.

Một benchmark tốt cũng chỉ chứng minh pipeline hoạt động trên corpus đó. Nó không loại trừ lỗi kỹ thuật riêng cho tiếng Việt, khác điều kiện thu, khác khoảng F0 hoặc khác cách tạo nhãn thống kê BT2. Kết quả hiện tại càng không đủ để quy nguyên nhân riêng cho thiếu data. Với cấu hình hard170 không học hệ số, dữ liệu ít chủ yếu hạn chế việc chọn và kiểm chứng tham số; tăng số bản sao không tự giải quyết vấn đề này.

## Kiểm tra và tái lập

Preregistration source/registry/manifest đã push và xác minh trước phép đo ở commit a2eec84. Verifier đã tính lại 31,910 đường NAMDF của 20 nhóm cửa sổ, kiểm full FFT, chọn ứng viên độc lập, căn thời gian, 20 nhóm metric và hash nguồn/dữ liệu. Không gọi lại Praat trong verifier. Mười call Praat trong phép đo và thời gian 218.64 giây không phải benchmark latency của thuật toán vì còn gồm lưu bằng chứng.

Lệnh: `python research_workbench_2026_10_07/benchmark_keele.py acquire`, `check`, `register`, `run`, rồi `python research_workbench_2026_10_07/verify_benchmark_keele.py`. Các output đã hoàn tất được bảo vệ khỏi ghi đè; không chạy lại register/run trên cùng thư mục nếu chưa tạo phiên riêng. Dữ liệu download ở benchmark_data được gitignore, chỉ manifest/checksum và bằng chứng đo được commit. WAV/LAB BT2, notebook đã nộp và frozen config gốc giữ nguyên.

Nguồn corpus: [Bechtold, Zenodo3921794](https://zenodo.org/records/3921794); README gốc trích trong sources/H49_KEELE_README.txt; [conversion code đã ghim commit](https://github.com/bastibe/Replication-Dataset-Scripts/blob/a29546dba8824c4bbba7573c7d795304830d0045/keele.py). Tham khảo cách đọc GPE và lỗi hữu thanh ở [trang tác giả](https://bastibe.github.io/Dissertation-Website/replication-dataset/index.html). Workflow tra cứu dùng literature-review local từ [Scientific Agent Skills](https://doi.org/10.48550/arXiv.2609.00065); không dùng skill prose. Chi tiết query và giới hạn nội dung đã đọc trong BENCHMARK_SOURCES.md.

Cách chia validation và áp dụng protocol: PROTOCOL_F0.md. Bốn protocol intra/cross-type của chống giả mạo khuôn mặt không phải bốn phép thử bắt buộc của bài F0.
