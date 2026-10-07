# Kiểm tra chất lượng bộ dữ liệu BT2 hiện tại

Đọc mới 8 WAV và 16 LAB, tổng 26.124694 giây. Đây là kiểm tra dữ liệu mô tả, không chạy thuật toán F0, không fit/chọn tham số, không sửa WAV/LAB. Test được đọc chỉ cho QA; kết quả này không được dùng để tune mô hình rồi gọi test là độc lập. Không gọi Jev/Gemini và không retry System One.

## Kết quả định dạng và tín hiệu

| split | file | fs | duration_s | peak_abs | rail_samples | near_rail_samples | tail_unlabeled_ms | unknown_frames |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | phone_F1.wav | 16000 | 3.24 | 0.8818 | 0 | 0 | 10 | 0 |
| train | phone_M1.wav | 16000 | 4.16 | 0.4927 | 0 | 0 | 10 | 0 |
| train | studio_F1.wav | 44100 | 2.863 | 0.5764 | 0 | 0 | 3.197 | 0 |
| train | studio_M1.wav | 44100 | 2.73 | 0.6855 | 0 | 0 | 0.1587 | 0 |
| test | phone_F2.wav | 16000 | 4.8 | 0.361 | 0 | 0 | 0 | 0 |
| test | phone_M2.wav | 16000 | 2.8 | 0.2838 | 0 | 0 | 0 | 0 |
| test | studio_F2.wav | 44100 | 3.149 | 0.8991 | 0 | 0 | 9.478 | 0 |
| test | studio_M2.wav | 44100 | 2.382 | 0.3379 | 0 | 0 | 1.859 | 0 |

Tất cả WAV được giải mã; xem `decode_warnings` trong CSV để giữ cả cảnh báo chunk phụ. 8/8 có mẫu hữu hạn. Tổng mẫu chạm min/max PCM: 0; tổng mẫu có biên độ tuyệt đối ≥99% full scale: 0. Không thấy clipping theo hai dấu hiệu này **không chứng minh** không có bão hòa analog, nén hoặc xử lý trước đó. RMS và DC được đo ở toàn bộ mẫu, không từ hình vẽ đã giảm điểm hiển thị.

Nhãn: tổng lỗi parse/bounds 0; gap nội bộ 0.000000 ms; overlap 0.000000 ms. Phần đuôi chưa phủ nhãn báo riêng; không tự điền SIL. Không có khung `unknown` trên grid hiện tại chỉ cho biết tâm khung được phủ, không chứng nhận mọi sample hoặc mọi biên nhãn đúng. Grid25/10 là quy ước QA hiện tại, không bắt các thuật toán phải dùng cửa sổ đó.

## Nhãn đoạn và hai bộ thống kê

| split | file | original_F0mean | reference_F0mean | original_F0std | reference_F0std | v_frames | reference_F0num | reference_count_minus_v_grid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | phone_F1.wav | 217 | 215.6 | 23 | 20.6 | 153 | 148 | -5 |
| train | phone_M1.wav | 122 | 123.7 | 18 | 16.8 | 244 | 232 | -12 |
| train | studio_F1.wav | 232 | 229.6 | 40 | 36.8 | 123 | 127 | 4 |
| train | studio_M1.wav | 113 | 116.9 | 26 | 26.4 | 94 | 82 | -12 |
| test | phone_F2.wav | 145 | 150.2 | 33.7 | 30.7 | 235 | 219 | -16 |
| test | phone_M2.wav | 129 | 130.2 | 18.6 | 15.4 | 134 | 123 | -11 |
| test | studio_F2.wav | 200 | 198.6 | 46.1 | 47.8 | 137 | 139 | 2 |
| test | studio_M2.wav | 155 | 154.7 | 30.8 | 30.3 | 128 | 116 | -12 |

LAB cạnh WAV có V/UV/SIL theo đoạn và mean/std cả file. LAB trong `research_3gt_2026_10_05/train_3gt` và `test_3gt` có mean/std/count, đang được dùng để chấm. Có giá trị khác nhau giữa hai nguồn; giữ nguyên và ghi hai cột, **không kết luận nguồn nào sai**. README dữ liệu chỉ giải thích định dạng/đơn vị, chưa cho quy trình tạo F0 reference, grid/thời điểm khung, quyết định V/UV, xử lý biên, hoặc ddof khi tính độ lệch chuẩn. Báo cáo trước cũng ghi thiếu quy trình này: `research_3gt_2026_10_05/PHAN_TICH_VA_CAI_TIEN_BT2_2026-10-05.md`, mục4.3–4.4. Truy xuất nguồn gốc 3GT chưa được chứng nhận lại từ phép đo gốc.

`reference_count_minus_v_grid` là chênh lệch định nghĩa cần đối chiếu, không phải số nhãn sai. Hai bộ có thể dùng khung/cách xác định hữu thanh khác nhau. Trong 16 LAB đã đọc **không có F0 chuẩn từng timestamp**; ba thống kê không thể chứng nhận contour cao độ của từng khung.

## Mức tiếng trong các vùng nhãn

| split | file | v_interior_rms | sil_interior_rms | v_sil_energy_ratio_db |
| --- | --- | --- | --- | --- |
| train | phone_F1.wav | 0.1895 | 0.009577 | 25.93 |
| train | phone_M1.wav | 0.05591 | 0.003434 | 24.23 |
| train | studio_F1.wav | 0.08349 | 0.0008017 | 40.35 |
| train | studio_M1.wav | 0.06118 | 0.0007011 | 38.82 |
| test | phone_F2.wav | 0.03721 | 0.001863 | 26.01 |
| test | phone_M2.wav | 0.06134 | 0.002192 | 28.94 |
| test | studio_F2.wav | 0.1586 | 0.0003621 | 52.83 |
| test | studio_M2.wav | 0.07276 | 0.0008156 | 39.01 |

RMS là căn trung bình bình phương biên độ. Bỏ cố định20ms ở mỗi biên đoạn để giảm ảnh hưởng chuyển tiếp; đoạn quá ngắn không góp mẫu. Tỷ lệ dB trên đây chỉ là proxy độ tách biệt năng lượng V/SIL, **không phải SNR** vì SIL có thể chứa âm nền, hơi thở hoặc nhãn chưa đúng, còn vùng V chứa cả tiếng nói lẫn nhiễu. Không dùng ngưỡng tỷ lệ này để tuyên bố nhãn sai hay tự bỏ file. Báo cáo chi tiết mọi đoạn trong `results/dataset_quality_segments.csv` để chọn đoạn nghe/rà bằng tay; chưa thực hiện nghe hoặc chỉnh nhãn trong QA này.

## Độ đa dạng và trùng lặp

Train có 4 file/12.993356s; test có 4 file/13.131338s. So 28 cặp (16 cặp train–test): 0 trùng byte WAV, 0 trùng native PCM cùng rate/shape/dtype. Điều này chưa loại trừ bản thu cùng nội dung đã đổi gain, resample, cắt dịch hoặc cùng người nói.

Tên file có F/M và phone/studio, mỗi split chỉ một file trong mỗi ô. Không có speaker_id/utterance_id/session_id đã xác minh trong metadata đang đọc; không gọi8file là8người. Phone16kHz và studio44.1kHz gắn với rate khác nhau, chưa thể tách riêng hiệu ứng microphone/rate/nội dung. Tổng thời lượng rất nhỏ; kết quả trên bốn train không chứng minh tổng quát hóa rộng, nhất là đã dùng nhiều vòng nghiên cứu trên chúng.

## Các bước để kiểm tra sâu hơn

1. Rà tay từng đoạn: nghe WAV và xem waveform/phổ ở biên V/UV/SIL, ghi timestamp, người rà, lý do và giữ nhãn gốc. Sửa nhãn phải có phiên bản riêng và chấm lại theo cùng protocol.
2. Đối chiếu nguồn3GT: cần cách tạo F0mean/std/num, length/hop/time_origin, đếm F0 hợp lệ, làm tròn và ddof. Với std20.6Hz, sai số0.412Hz đã tương đương2% lỗi std; mục tiêu thấp cần reference đủ rõ. Đây là phép tính, không ước lượng nhiễu nhãn đã đo.
3. Có contour F0 reference độc lập theo thời gian, được rà chu kỳ ở các đoạn khó; output ACF/AMDF/Praat chỉ là ứng viên để reviewer đối chiếu. Praat manual lưu ý kết quả voice analysis phụ thuộc pitch settings và phần âm thanh được phân tích: [Voice](https://www.fon.hum.uva.nl/praat/manual/Voice.html), đọc HTML ngày2026-10-07. Vì vậy phải lưu cấu hình và đoạn thời gian, không lấy kết quả một tool làm chuẩn mặc nhiên.
4. Bổ sung dữ liệu và metadata người nói/nội dung/phiên/thiết bị; thiết kế phần đánh giá mới tách người nói hoặc phiên thật sự. Đăng ký protocol trước đánh giá mới, không loại file khó dựa trên MAPE để tạo điểm đẹp.

Chưa có một điểm “chất lượng dataset” tổng hợp: phần định dạng/duplicate/rails có kiểm tra bằng code; độ đúng ngữ âm/cao độ và độc lập người nói cần nguồn/rà tay bổ sung. Cải thiện MAPE và chất lượng reference là hai việc cần theo dõi riêng. Verifier lần đầu phát hiện chênh một mẫu ở năm đoạn do biểu diễn số thập phân bằng float khi áp dụng guard20ms. Log lỗi được giữ; bản hiện tại dùng Decimal để ánh xạ biên chính xác, verifier dùng Fraction độc lập. Đây là sửa cách đo năng lượng QA, không sửa dữ liệu hay MAPE.

## Tái lập

Lệnh: `C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/dataset_quality_audit.py`. Policies, phiên bản runtime, input SHA256 và output SHA256: `results/dataset_quality_manifest.json`. CSV và PNG/SVG giữ dữ liệu đo thật; WAV/LAB không đổi. Verifier đọc PCM độc lập bằng thư viện wave, đối chiếu samples/rate/rails/hashes/grid/gaps/overlaps và profile train trước đó, không chạy F0.
