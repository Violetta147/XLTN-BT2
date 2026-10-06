# Khám phá Jev ngày 2026-10-06

Đã dùng đủ 6 công cụ System One trong 6 lượt MCP, có 7 lượt gọi mô hình Jev bên trong. Đây là demo có kiểm soát trên dữ liệu do agent cung cấp, không phải đánh giá độ chính xác tổng quát hoặc benchmark tiết kiệm thời gian.

## Kết quả thực tế

| Công cụ | Câu hỏi thử | Kết quả đo được | Điều rút ra |
|---|---|---|---|
| check | Bỏ SIL có giải quyết đầy đủ lỗi F0std phone_F1 không? | supported=0,05; contradicted=0,91; nêu đúng ID phép bỏ SIL vẫn còn sai số | Phản bác kết luận quá rộng trong ca này |
| find | Có đoạn nào ghi F0 chuẩn ở 0,5725 s không? | ranking của cả 3 đoạn=0; none=1; answerExists=0,56; conflict=0,15 | Các tín hiệu không nhất quán; phải đọc nguồn |
| select | Mean cả file/ACF cũ/contour mượt có tạo chuẩn từng khung đã xác minh không? | choice.id=null; none=1; fits lần lượt 0,03/0,07/0,05 | Có thể từ chối toàn bộ shortlist |
| decide | Rà bản nháp khẳng định mọi F0 đúng, chỉ RMS gây cải thiện | boolean=0,05; choice=multiple_changes; score=0,04 theo rubric 0–2 | Có thể gom 3 câu độc lập, phân biệt xác suất và điểm |
| run: writing-check | Đoạn quảng bá “mạnh mẽ/vượt trội/hoàn hảo” có cụ thể không? | specific=0,12; vague=0,97; actionable=0,03 | Hỗ trợ rà cách viết; không chứng nhận khoa học |
| code | Nhận diện hiểu nhầm std rồi chọn bằng chứng phù hợp | chọn std_range=0,98; check supported=0,04/contradicted=0,92; 2 calls | Đã chạy chuỗi phụ thuộc input thành công |

Các con số là tín hiệu do mô hình trả về, không phải tỷ lệ chính xác đã kiểm định. Không tính “5/6 đúng = 83,3% độ chính xác”: số ca nhỏ, do chính agent soạn, không phải held-out và có nhiều tín hiệu trong một ca.

## Điểm yếu đã quan sát

find trả none=1 nhưng answerExists=0,56. Guide mô tả answerExists là tín hiệu riêng về việc có nguồn trả lời câu hỏi. Trong ca này không thể dùng hai tín hiệu như một quyết định nhất quán. Agent đọc lại LAB và ứng viên ACF, xác nhận không đoạn nào cung cấp F0 chuẩn từng khung.

Không retry phép thử để thay kết quả. Giữ phản hồi thô cho người dùng kiểm tra. Điểm này cho thấy cần xem nguồn và các tín hiệu độc lập, không chỉ nhìn probability cao hoặc ID đứng đầu.

## Ground truth có thật, nhưng ở cấp nào?

Đối chiếu 16 LAB trong nhóm dữ liệu đang chấm: 8 file nhãn đoạn V/UV/SIL có thống kê cả file; 8 file 3GT có mean/std/count. Không có F0 chuẩn từng timestamp trong nhóm này.

Vì vậy câu “không có ground truth” là thiếu chính xác. Câu đúng: có ground truth thống kê cả file và nhãn loại đoạn, chưa có reference F0 từng khung trong các file đã đọc.

phone_F1 3GT: mean 215,6 Hz, std 20,6 Hz, count 148. Các ứng viên 72,183611 Hz và 217,416512 Hz ở 0,5725 s là kết quả thuật toán, không phải nhãn đo chuẩn. Jev không tự kiểm tra waveform hoặc LAB; agent gửi trích đoạn.

## 45 và 1

Cả hai là số đếm false_voiced_sil của ACF trên 4 file train, với nhãn SIL và cấu hình khung của thí nghiệm. Một khung được đếm nếu nhãn là SIL nhưng pipeline vẫn dự đoán hữu thanh/có F0.

| File | Baseline | Improved |
|---|---:|---:|
| phone_F1.wav | 2 | 0 |
| phone_M1.wav | 0 | 0 |
| studio_F1.wav | 21 | 1 |
| studio_M1.wav | 22 | 0 |
| Tổng | 45 | 1 |

1 còn lại là studio_F1. Giảm 44 khung SIL bị gán F0 không đồng nghĩa sửa đúng 44 cao độ, không phải giảm MAPE từ 45% xuống 1%. Các cửa sổ 25 ms, hop 10 ms chồng nhau, không phải 45 đoạn nhiễu độc lập.

Đánh đổi cùng bảng: TP V 535→530, FN V 79→84. Bản cải tiến bỏ sót thêm 5 khung V thật. SIL được báo riêng ngoài ma trận V/UV.

Nguồn: final_train_test_per_file.csv trong research_3gt_2026_10_05/results; định nghĩa trong standalone_pipeline.py, classification. Các số đếm được cộng bằng code, không nhờ Jev tính.

## Usage và phạm vi thử

- MCP calls: 6; model calls: 7; không có retry.
- Tokens mô hình báo: 5.200 input, 495 output.
- Tổng latency mô hình báo: 2.118 ms. Đây là tổng latency các call, không phải toàn thời gian làm nhiệm vụ.
- ID được trả về đều thuộc bằng chứng hoặc danh sách lựa chọn đã gửi; kiểm tra bằng code.
- Danh mục recipe có 42 mục, toàn bộ validation.status=unmeasured. Chỉ writing-check được thử.
- Chưa thử nghe âm thanh, tự đọc notebook, xác minh vật lý F0, kiểm chứng toàn bộ recipe hoặc điều khiển công cụ ngoài. Guide mô tả Jev không tự tìm kiếm/hành động.
- Notebook không được chạy lại hay thay thuật toán trong đợt khám phá này.

Lượt rà hướng dẫn trước đó là một call decide riêng, có log tại HUONG_DAN_BT2_A_DEN_Z/jev_review.json ở workspace XLTN. Nó không nằm trong 6 MCP calls của bảng trên.

## Dùng vào việc học BT2

Jev phù hợp để rà một câu giải thích có vượt số liệu không, chọn đoạn nguồn nào hỗ trợ một luận điểm, phân loại hiểu nhầm trong câu hỏi người học, hoặc chấm bản nháp theo vài tiêu chí rõ ràng.

Agent vẫn chịu trách nhiệm đọc notebook, tính metric, kiểm tra format GT, giữ split train/test, xác minh source/output và viết lời giải A tới Z. Người dùng có thể xem chính xác Jev đã được hỏi gì, không cần suy đoán từ phần tóm tắt.

Xem [hướng dẫn từng trường hợp](HUONG_DAN_JEV.md), [input/output nguyên vẹn](exploration_runs_2026-10-06.json) và [validation](exploration_validation_2026-10-06.json).

