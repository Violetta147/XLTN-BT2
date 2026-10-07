# Phone và studio: khác biệt bản thu có giải thích sai số không?

Ngày 07/10/2026. Kết luận: **bốn file train có khác biệt rõ về độ tách biệt năng lượng tiếng nói/khoảng lặng; khác biệt này vẫn tồn tại sau khi đưa về cùng 16 kHz. Tuy nhiên, nhóm phone không luôn có sai số F0 cao hơn studio.** Điều kiện thu là một giả thuyết có bằng chứng tín hiệu liên quan, chưa được xác nhận là nguyên nhân gây lỗi.

Tên `phone`/`studio` là cách chia nhóm theo file. Chưa có metadata chứng nhận microphone, phòng, khoảng cách, phần mềm xử lý hoặc người đọc. Không khẳng định đây chính xác là hai môi trường thu vật lý đã biết.

## 1. Phép đo mới

Chỉ đọc bốn WAV/LAB train. [Phạm vi chốt trước đo](RECORDING_CONDITIONS_PLAN.md) và source được commit/push tại `100951c5106458185d3a7f772b1abe706f6de440`, trước phép đo. Không chạy F0 mới, không fit/chọn tham số, không mở WAV/LAB test và không chạy H44. Các bảng sai số bên dưới được tổng hợp từ kết quả đã lưu.

Giữ WAV/LAB gốc. Với studio, chỉ trong bộ nhớ, đổi 44.1 kHz thành 16 kHz bằng lọc đa pha; phone 16 kHz giữ nguyên. Bước này đồng thời lọc chống alias, không được diễn giải là cô lập hoàn toàn ảnh hưởng tần số lấy mẫu. Nó cũng không biến microphone hay âm học phòng studio thành phone.

Tính khung 25 ms, bước 10 ms, chỉ dùng khung hoàn toàn trong một nhãn và cách biên đoạn 20 ms. RMS là căn trung bình bình phương biên độ tín hiệu. Tỷ lệ dưới đây là `20 log10(RMS_V / RMS_SIL)`, trong đó V là đoạn hữu thanh, SIL là khoảng lặng theo LAB gốc. Giá trị cao nghĩa là tiếng hữu thanh tách biệt năng lượng với khoảng lặng hơn. Đây là chỉ số mô tả, không phải SNR đo từ tiếng sạch và nhiễu đã tách riêng.

| File train | Native (dB) | Cùng 16 kHz (dB) | Thay đổi (dB) |
| --- | ---: | ---: | ---: |
| phone_F1 | 26.13 | 26.13 | 0.00 |
| phone_M1 | 24.21 | 24.21 | 0.00 |
| studio_F1 | 40.38 | 40.43 | +0.04 |
| studio_M1 | 38.72 | 38.74 | +0.01 |

Cả hai studio vẫn có mức tách biệt cao hơn cả hai phone sau phép chuẩn hóa này. Vì vậy, khác biệt không biến mất chỉ bằng việc đưa về cùng rate/băng thông; không nên quy toàn bộ khoảng cách cho 16 kHz so với 44.1 kHz. Chưa biết mức nền khác nhau đến từ tiếng ồn phòng, gain, microphone, xử lý file, cách phát âm hay tổ hợp những yếu tố này. Gain nhân đồng đều toàn bộ file tự nó không đổi tỷ lệ V/SIL này.

Số đo ở đây khác nhẹ bảng profile cũ vì cách chọn đoạn/khung khác: profile cũ dùng tâm khung hoặc mẫu nội đoạn; lượt này dùng toàn khung và guard 20 ms. Không trộn hai cách đo thành một chuỗi trước/sau.

## 2. Phổ cho thấy phone_F1 khác biệt, chưa thể gán cho cả nhóm phone

Phân tích phổ các khung V bằng Hann, trừ mean mỗi khung, rFFT 4096 điểm; tỷ lệ là tổng bình phương biên độ FFT trong dải chia tổng trong 0–8 kHz. Các số sau đều trên tín hiệu cùng 16 kHz.

| File train | Khung V đủ điều kiện | Phần phổ V trong 1–8 kHz (%) |
| --- | ---: | ---: |
| phone_F1 | 111 | 3.75 |
| phone_M1 | 208 | 13.21 |
| studio_F1 | 87 | 14.48 |
| studio_M1 | 70 | 10.77 |

Phone_F1 có phần phổ cao tần ít hơn ba file còn lại trong phép đo này. Nhưng phone_M1 không cùng mức thấp đó. Vì thế, không đủ cơ sở nói mọi file phone đều bị lọc cao tần giống nhau. Người đọc, âm tiết, cách phát âm, microphone và xử lý tín hiệu vẫn có thể cùng tác động. Các tỷ lệ này không phải tỷ lệ F0 đúng và không xác nhận sai bội chu kỳ ở từng khung.

Guard loại bỏ toàn bộ khung UV của studio_F1 và chỉ giữ 3 khung UV studio_M1; dữ liệu không đủ cho so sánh phổ UV giữa hai nhóm theo cùng phép đo. CSV giữ những số lượng này, không điền kết quả thiếu bằng 0.

## 3. Phone không luôn khó hơn: đối chiếu kết quả đã lưu

Average MAPE mỗi file là trung bình lỗi phần trăm của F0mean/F0std/F0num. Bảng dưới gộp hai file trong mỗi nhóm, chỉ train. Các hàng có protocol khác nhau: kết quả trên train trực tiếp, outer held file hoặc nested selection; không dùng bảng này để kiểm định pipeline nào thắng trên một benchmark độc lập. Nested ở đây vẫn exploratory do lịch sử nhiều vòng nghiên cứu trên bốn file.

| Nguồn kết quả train | Phone (%) | Studio (%) |
| --- | ---: | ---: |
| ACF đã nộp, chép từ ảnh người dùng | 31.33 | 28.34 |
| H20 accepted, outer train | 11.61 | 2.95 |
| H20 H18, nested outer train | 13.90 | 2.69 |
| H20 H19, nested outer train | 13.48 | 3.55 |
| H31 Praat fixed0.30, train | 0.81 | 2.44 |
| H41 candidate, nested train | 0.93 | 1.74 |
| H43 candidate, nested train | 0.56 | 2.00 |

Ở H20, phone có sai số cao hơn. Nhưng H31/H41/H43 cho thứ tự ngược lại trên cùng bốn WAV. Đây là phản chứng với khẳng định mạnh “nhóm phone luôn khó hơn” hoặc “mọi khoảng cách MAPE chủ yếu do môi trường phone”. Thuật toán và cách chọn cấu hình tương tác với đặc điểm từng file.

Ngay trong kết quả đã nộp, studio_M1 có Average MAPE33.85%, cao hơn phone_M1 14.01%; nhóm studio không bảo đảm từng file đều dễ hơn. F0std MAPE137.56% của phone_F1 là một điểm khó riêng, không được lấy một file để kết luận cho mọi bản thu phone.

F0std chuẩn khác nhau cũng làm mẫu số MAPE khác nhau. Các CSV giữ MAE Hz, macro F1, recall V/UV, balanced accuracy, count và SIL false voiced khi source có các trường đó; ảnh đã nộp chỉ có MAPE nên không tự bổ sung các metric còn thiếu. Không suy từ MAPE nhỏ thành contour từng khung đúng, vì dữ liệu không có F0 chuẩn từng khung.

## 4. Điều có thể kết luận và phần cần kiểm chứng

Đã có bằng chứng khác biệt tín hiệu và tương tác với pipeline; chưa có thí nghiệm tách riêng tác động môi trường thu. Chỉ hai file train mỗi nhóm, một file mỗi ô F/M × phone/studio. Chưa xác minh phone và studio có cùng người đọc, cùng câu hoặc cùng phiên thu. Người dùng cung cấp câu “Anh vẫn có thể làm trọng tài” cho bốn studio train/test và nghe sơ qua bốn giọng khác nhau; thông tin đó chưa chứng minh cặp người đọc giữa phone và studio.

Muốn kiểm chứng nhân quả bằng thu mới, cần cùng người đọc cùng câu trong các điều kiện đã ghi rõ, nhiều lần lặp, ưu tiên thu đồng thời để giảm thay đổi ngữ điệu. Nếu tiếp tục với dữ liệu hiện có, có thể đăng ký một phép can thiệp trong cùng file: giữ pipeline F0 cố định và so native/common16k hoặc một bộ lọc chốt trước trên train. Đó sẽ kiểm tra tác động của phép biến đổi tín hiệu đã biết, vẫn không xác nhận môi trường thu ban đầu. Lượt này chưa chạy phép can thiệp F0 đó và chưa tạo registry mới.

Vấn đề LAB gốc/3GT là câu hỏi riêng. Khác người hoặc điều kiện thu giải thích khác biệt giữa các WAV, không giải thích thống kê thay đổi giữa hai LAB của cùng WAV trùng byte. Quy trình tạo reference vẫn cần nguồn từ người phát hành. Không cần Jev để tính những bảng này; không gọi hoặc retry Jev.

## 5. Tái lập và kiểm tra

Từ thư mục repository:

```powershell
& 'C:/Users/violet/miniconda3/python.exe' 'research_workbench_2026_10_07/recording_conditions_analysis.py'
& 'C:/Users/violet/miniconda3/python.exe' 'research_workbench_2026_10_07/verify_recording_conditions.py'
```

Source ảnh kết quả đã nộp được đọc từ `../XLTN-BT1-BO-SUNG/baseline/submitted_results.json`; đây là lời xác nhận và ảnh người dùng, không phải một lần chạy lại notebook. Những source khác là H20_clean_per_file/H31_fixed_lofo/H41_metrics/H43_metrics. Receipt lưu hash tất cả đầu vào và output, runtime và resampling. Verifier PASS: 15 input hash, 5 output hash, năng lượng 998 khung native đối chiếu lại từ PCM, phân đoạn/gộp RMS, tổng tỷ lệ phổ và trung bình nhóm. WAV/LAB đầu vào giữ nguyên. Hash được kiểm tra, không chứng nhận ground truth hoặc metadata người nói.

Lượt đầu đã ghi CSV/receipt nhưng lỗi ở dòng in bảng vì `summary.mode` trùng tên phương thức pandas; sửa thành `summary['mode']` và chạy lại cùng phép đo thành công. [Failure record](results/recording_conditions_initial_failure.json) được giữ. Không đổi công thức đo để xử lý lỗi đó.

Các file: [features](results/recording_conditions_features.csv), [energy](results/recording_conditions_energy.csv), [saved metrics](results/recording_conditions_saved_metrics.csv), [groups](results/recording_conditions_groups.csv), [receipt](results/recording_conditions_receipt.json), [validation](results/recording_conditions_validation.json). Frame CSV giữ thời gian, nhãn, năng lượng và phổ cho kiểm tra lại.
