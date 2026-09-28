# Kiểm tra output và phân tích ACF/AMDF/GMM

## Phạm vi và kết luận kiểm tra tính đúng

Ba notebook trong working folder có **89 output đã lưu**: 32 từ notebook GMM, 27 từ notebook AMDF và 30 từ notebook ACF. Mỗi output được giữ nguyên dưới dạng JSON; phần có thể xem trực tiếp được xuất thêm thành 33 PNG, 21 HTML và các file văn bản. `manifest.json` ghi tên notebook, SHA-256 và danh sách file theo cell. Dữ liệu WAV/LAB và notebook gốc vốn đã nằm trong working folder; thao tác xuất không thay đổi chúng.

Không có traceback trong output đã lưu. Hai cảnh báo `WavFileWarning: Chunk (non-data) not understood` chỉ nói bộ đọc bỏ qua chunk metadata. Đọc độc lập cả 8 WAV và tính lại trên 4 file test cho kết quả trùng output, nên cảnh báo này chưa cho thấy âm thanh bị đọc sai.

Tôi tính độc lập ACF/AMDF bằng NumPy trên **toàn bộ 5.222 lượt khung** của 16 tổ hợp model × file test, không gọi hàm trong notebook. Số khung đúng V/UV, số khung đúng khi tính cả SIL, số F0 và số false voiced trên SIL đều **trùng chính xác** ở cả 16 lượt. F0mean/F0std khác bảng lưu tối đa **0,000044 Hz**, đúng mức làm tròn 4 chữ số. Tính lại MAE, RMSE, MAPE và macro accuracy từ bảng từng file cũng khớp sai số làm tròn. Mười hai score/lag ở ví dụ voiced/unvoiced cũng khớp đến 4 chữ số. Tôi cũng tính lại **4.764 score training** cho 2 thuật toán × 3 độ dài khung: mỗi cấu hình đều có đúng 614 V/180 UV; mean/std sai khác tối đa **0,000050** do làm tròn. Vì vậy **chưa phát hiện lỗi công thức hoặc lỗi cộng gộp số học trong các kết quả đã lưu**. Các file `validation_summary.csv`, `validation_training_summary.csv`, `recomputed_test_frames.csv` và `confusion_by_file.csv` cho phép kiểm tra từng trường hợp.

Giới hạn xác minh: GMM đã fit và các ngưỡng ứng viên được đọc từ output notebook; tôi xác minh cách áp dụng ngưỡng và các kết quả test, chưa fit lại mô hình sklearn hoặc tái hiện toàn bộ quá trình chọn ngưỡng. Dữ liệu LAB chỉ có F0mean/F0std theo file, không có F0 chuẩn theo từng khung, nên không thể xác nhận sai số F0 của từng khung.

## Kết quả hiện có

| Cấu hình | Ngưỡng | Accuracy V/UV, macro theo file | Balanced accuracy, macro theo file* | Macro F1 | F0mean MAE (Hz) | F0std MAE (Hz) |
|---|---:|---:|---:|---:|---:|---:|
| ACF + GMM, 20 ms | 0,8480 | 80,13% | 85,70% | 0,7524 | 7,5363 | 4,3347 |
| ACF gốc, 25 ms | 0,6841 | 87,08% | 84,56% | 0,8114 | 3,6965 | 4,7376 |
| AMDF + GMM, 25 ms | 0,3472 | 83,34% | 87,53% | 0,7858 | 3,7229 | 0,6372 |
| AMDF gốc, 30 ms | 0,4204 | 87,33% | 86,84% | 0,8220 | 2,2375 | 2,8172 |

\* Balanced accuracy trên test được tính lại từ nhãn LAB và dự đoán theo khung; notebook chỉ in balanced accuracy trên training. Các hàng dùng độ dài khung khác nhau, nên bảng này không tách riêng tác động của GMM khỏi tác động của frame length.

Confusion matrix gộp trên 4 file test, chỉ tính V/UV:

| Cấu hình | TP V | TN UV | FP UV→V | FN V→UV | V bị bỏ sót |
|---|---:|---:|---:|---:|---:|
| ACF + GMM | 474 | 168 | 7 | 160 | 25,2% |
| ACF gốc | 551 | 144 | 31 | 83 | 13,1% |
| AMDF + GMM | 503 | 164 | 11 | 131 | 20,7% |
| AMDF gốc | 543 | 153 | 22 | 91 | 14,4% |

Ngưỡng GMM giảm báo nhầm UV nhưng bỏ sót nhiều khung V hơn. Do training có 614 V và 180 UV ở 25/30 ms, còn test có 634 V và 175 UV, sự đánh đổi này làm accuracy/F1 giảm dù balanced accuracy có thể nhỉnh hơn. Đây là **khác biệt mục tiêu tối ưu**, không phải lỗi cộng số.

## Vấn đề phương pháp và nguyên nhân

### 1. Hai thành phần GMM không đảm bảo là hai nhãn V và UV — ưu tiên cao

Notebook GMM fit hai Gaussian **không dùng nhãn** trên score gộp rồi xem giao điểm hai thành phần là ngưỡng V/UV. Với ACF 20 ms, mean score theo nhãn là **UV 0,4710** và **V 0,8764**, trong khi mean hai thành phần GMM là **0,5923** và **0,9438**. Thành phần thấp có dấu hiệu chứa cả UV lẫn V khó; thành phần cao tập trung V có score mạnh. Ngưỡng **0,8480** gần mean V, khiến nhiều V thật bị loại. AMDF cũng có ngưỡng GMM 25 ms **0,3472**, thấp hơn ngưỡng Gaussian theo nhãn **0,4125**.

Để kiểm tra tác động của riêng ngưỡng, tôi áp các ngưỡng đã học từ training lên **cùng score và cùng frame length** của test (`threshold_ablation.csv`):

| Cùng score/frame | Ngưỡng GMM: Acc / BalAcc / F1 | Ngưỡng theo nhãn: Acc / BalAcc / F1 |
|---|---|---|
| ACF 20 ms | 80,13% / 85,70% / 0,7524 | 88,17% / 84,04% / 0,8202 (Gaussian 0,6846) |
| ACF 25 ms | 77,40% / 83,50% / 0,7250 | 87,08% / 84,56% / 0,8114 (histogram 0,6841) |
| AMDF 25 ms | 83,34% / 87,53% / 0,7858 | 86,59% / 85,86% / 0,8117 (Gaussian 0,4125) |
| AMDF 30 ms | 82,78% / 86,95% / 0,7796 | 87,33% / 86,84% / 0,8220 (Gaussian 0,4204) |

Các ngưỡng theo nhãn tăng accuracy/F1; ở một số trường hợp balanced accuracy giảm nhẹ. F0mean/F0std cũng đánh đổi: chẳng hạn ACF 20 ms Gaussian tăng F0mean MAE từ 7,54 lên 9,88 Hz, còn AMDF 25 ms Gaussian giảm F0mean MAE từ 3,72 xuống 2,76 Hz nhưng tăng F0std MAE từ 0,64 lên 4,35 Hz. **Quy trình hiện tại của các notebook là hợp lệ ở điểm này:** các ngưỡng được chọn trên training, rồi mới đánh giá trên test. Bảng so sánh thêm ở đây chỉ dùng để chẩn đoán ảnh hưởng của ngưỡng. Nếu sau khi xem bảng này ta đổi sang ngưỡng cho kết quả test tốt nhất, thì chính tập test đã tham gia chọn ngưỡng; lúc đó không thể dùng cùng bảng test làm ước lượng độc lập cho cấu hình mới. Muốn đánh giá cấu hình đã sửa, hãy chọn ngưỡng bằng validation trên training và giữ test cho lần đánh giá cuối, hoặc dùng một tập test mới.

### 2. Khung ở biên đoạn chứa tín hiệu của hai nhãn — ưu tiên cao

Nhãn của một frame lấy theo thời điểm tâm, dù frame có thể cắt qua đoạn khác. Trên training 25/30 ms, **90/794 khung V/UV (11,3%)** cắt qua biên nhãn; trên test là **94/809 (11,6%)**. Tỷ lệ tương ứng ở 20 ms là 45/794 và 47/809. Đây là nhãn nhiễu có hệ thống, đặc biệt cho UV ngắn. Nếu bỏ frame cắt biên lúc train/đánh giá, phải công bố rõ quy tắc và giữ test protocol cố định; có thể đánh giá thêm cả tập đầy đủ để phản ánh ứng dụng thực tế.

### 3. Tên metric và kiểm chứng F0 dễ gây hiểu sai — ưu tiên cao

`Accuracy V/UV/SIL` thực chất là **accuracy nhị phân V so với UV hoặc SIL**, vì cả UV và SIL đều được quy về `False`. Nó không đo phân loại ba lớp. Đổi tên thành `Accuracy voiced/nonvoiced (including SIL)`; nếu bài yêu cầu đúng ba nhãn, cần bộ phân loại và confusion matrix 3×3.

F0mean/F0std được tính trên **mọi frame dự đoán V**, gồm cả false voiced ở UV/SIL, rồi so với hai thống kê F0 theo file trong LAB. Một mean gần LAB có thể do sai số triệt tiêu; F0std thấp không chứng minh contour đúng từng thời điểm. Cần thêm F0 ground truth theo frame, gross pitch error, voiced detection recall/precision và coverage. Nếu chỉ có LAB hiện tại, nên gọi rõ đây là **sai số thống kê theo file**, không phải pitch tracking error theo khung.

### 4. Chọn cấu hình trên cùng training và tập dữ liệu nhỏ — ưu tiên vừa

Notebook gốc thử 3 độ dài khung × 3 cách chọn ngưỡng rồi lấy balanced accuracy tốt nhất ngay trên dữ liệu fit. Điều này làm chỉ số training lạc quan. Chẳng hạn AMDF gốc training 91,54% balanced accuracy nhưng test macro balanced accuracy 86,84%. Tập chỉ có **4 file training và 4 file test**; các frame 10 ms từ cùng file phụ thuộc mạnh vào nhau. Không xem 794 frame training như 794 quan sát độc lập. Nên chọn tham số bằng leave-one-file-out trên 4 file training, tính trung bình theo file, chốt tiêu chí trước, sau đó chỉ dùng test một lần.

### 5. Miền lag, độ dài khung và xử lý biên — ưu tiên vừa/thấp

Ở 70 Hz, một chu kỳ dài khoảng 14,3 ms. Frame 20 ms chứa chưa tới 1,5 chu kỳ, khiến lag gần biên dưới có rất ít phần overlap; 30 ms chỉ vừa hơn hai chu kỳ. Thử 35–40 ms hoặc hạn chế lag sao cho còn ít nhất một chu kỳ overlap, rồi kiểm tra ảnh hưởng lên độ phân giải thời gian và ranh giới V/UV. Nội suy parabol hiện không chặn F0 sau nội suy; tôi thấy **1 frame ACF gốc cho F0 = 69,991 Hz**, hơi ngoài dải khai báo 70–400 Hz. Nên clamp lag/F0 sau nội suy hoặc loại ứng viên ngoài dải. AMDF chỉ xét cực tiểu cục bộ **bên trong** miền lag khi có cực tiểu; điểm biên không được xét, cũng nên xử lý minh bạch.

## Đề xuất thực hiện theo thứ tự

1. **Chốt mục tiêu chính**: nếu cần phát hiện V/UV, dùng macro F1 hoặc balanced accuracy theo file; báo thêm recall từng lớp và F0mean/F0std MAE như tiêu chí riêng. Không tối ưu một metric rồi kết luận thắng trên metric khác.
2. **Thay quy tắc đồng nhất thành phần GMM với nhãn**: dùng phân bố theo nhãn hoặc gán thành phần bằng tỷ lệ nhãn training, sau đó chọn ngưỡng bằng cross-validation theo file. Nếu cần mô hình không giám sát thật sự, kiểm tra purity của mỗi component theo nhãn chỉ để đánh giá, không mặc định một component bằng một class.
3. **Chuẩn hóa đánh giá**: xuất confusion matrix V/UV và V/(UV+SIL), tỷ lệ F0 hợp lệ và metric F0 theo file. Có thêm F0 chuẩn theo khung mới đánh giá pitch tracking chi tiết.
4. **Kiểm tra nhạy cảm độ dài khung và biên nhãn**: giữ cùng một tập test, báo theo từng file/channel/giới tính, thử khung dài hơn và chính sách loại hoặc giảm trọng số frame cắt biên trong training.
5. **Tối ưu hiệu năng sau khi đo thời gian**: AMDF hiện tạo ma trận lag × sample cho từng frame, nhất là ở 44,1 kHz. Benchmark trước; nếu đây là nút thắt, xử lý lag theo block hoặc giảm tần số lấy mẫu có kiểm soát, rồi kiểm tra lại score/ngưỡng vì giá trị có thể thay đổi.

## File để kiểm tra lại

- `manifest.json`: danh sách đầy đủ output gốc và file đã xuất.
- `validation_summary.csv`: đối chiếu 16 lượt test với bảng notebook.
- `validation_training_summary.csv` và `recomputed_training_scores.csv`: đối chiếu toàn bộ score training với bảng notebook.
- `recomputed_test_frames.csv`: score/lag/F0/nhãn/dự đoán từng khung.
- `confusion_by_file.csv`: TP/TN/FP/FN theo file và cấu hình.
- `threshold_ablation.csv`: so sánh ngưỡng trên cùng score/frame.
- `data_audit.csv`: sample rate, thời lượng, nhãn và khung cắt biên.
- `export_notebook_outputs.py`, `validate_saved_results.py` và `validate_training_scores.py` ở working folder: script tái tạo bản xuất và phép kiểm tra.
