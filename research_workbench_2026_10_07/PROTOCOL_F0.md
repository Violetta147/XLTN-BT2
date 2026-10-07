# Validation và protocol trong bài F0

Thầy cung cấp train và test. Validation là vai trò của dữ liệu khi chọn cấu hình, không bắt buộc là một thư mục thứ ba. Trong các vòng BT2, ta tạo validation từ chính bốn file train bằng cách giữ riêng file, không lấy test để học tham số.

Ví dụ một lượt ngoài giữ riêng studio_M1: chỉ ba file phone_F1, phone_M1, studio_F1 được dùng để chọn cấu hình. Trong ba file này, vòng trong lần lượt giữ riêng một file làm validation, học từ hai file còn lại nếu thuật toán cần học. Chọn cấu hình có Average MAPE tệ nhất thấp nhất qua ba lượt, rồi dùng trung bình và ID để phân xử khi bằng nhau. Sau đó học lại trên ba file để chấm studio_M1. Lặp với bốn file được giữ riêng. Đây là nested leave-one-file-out cross-validation: bốn lượt vòng ngoài, ba lượt vòng trong cho mỗi lượt ngoài. Lựa chọn cuối dùng bốn lượt giữ riêng file trong train, rồi học trên toàn bộ train nếu cần. Các cấu hình như Praat/hard170 không cần học hệ số: cross-validation chỉ chọn cấu hình của chúng.

Không chia ngẫu nhiên các khung bằng KFold. Các khung trong cùng WAV phụ thuộc nhau; bản thêm nhiễu cũng phụ thuộc WAV gốc, nên tất cả bản từ một file phải cùng lượt chia. Chưa xác minh danh tính người nói để gọi cách chia hiện tại là giữ riêng người nói. Nếu cùng một người có hai file thì phải giữ cả hai cùng nhóm khi muốn đánh giá trên người nói mới. Cùng lời đọc không tự động gây rò rỉ F0, nhưng chỉ một câu làm phạm vi ngữ âm được kiểm tra rất hẹp.

Cross-validation có hai vòng giảm rò rỉ ở từng lượt học/chọn, nhưng không xoá việc agent đã xem cùng bốn file train qua nhiều vòng để đặt giả thuyết và danh sách tham số. H47 chọn lại hard170 sau khi thay danh sách ứng viên vẫn là kết quả khám phá. Test BT2 cũng đã được xem trong lịch sử; việc H48 chốt cấu hình trước đo không biến bộ test thành dữ liệu mới chưa từng xem. Vì vậy không coi các kết quả này là chứng nhận độc lập.

Protocol là quy ước để kết quả có nghĩa: chia theo đơn vị nào, dữ liệu nào được dùng để học/chọn, phép biến đổi, nhãn, thời gian khung, cách tính metric và quy tắc báo thất bại. Bài tập cần những quy ước tối thiểu này, nhưng không cần bê nguyên bốn protocol của chống giả mạo khuôn mặt. Trong lĩnh vực đó, type thường chỉ loại tấn công; bài F0 không có loại tấn công. Nam/nữ, hữu thanh/không hữu thanh hoặc phone/studio không tự động là type theo cùng nghĩa. Đã đối chiếu phần 2.4 của survey bằng [bản HTML](https://ar5iv.labs.arxiv.org/html/2106.14948), không đọc PDF.

| Tên người dùng nêu | Ý nghĩa tổng quát | Áp dụng hợp lý vào F0 |
| --- | --- | --- |
| Intra-Dataset Intra-Type | Cùng corpus, cùng nhóm điều kiện | BT2 train→test theo split của thầy; chọn bằng CV trong train. Cần nêu giới hạn người nói và transcript. |
| Cross-Dataset Intra-Type | Corpus mới, tác vụ/nhóm điều kiện tương tự | Cấu hình chọn trên BT2→KEELE tiếng nói đọc, không fit/tune KEELE. Đây là kiểm tra ngoài corpus; không tự gọi là FAS protocol chuẩn. |
| Intra-Dataset Cross-Type | Cùng corpus, điều kiện giữ riêng chưa dùng để học/chọn | Có thể định nghĩa riêng phone→studio hoặc ngược lại, nhưng hiện chỉ hai file mỗi nhóm, khác người có thể lẫn với khác thiết bị. Không đủ để tách nguyên nhân môi trường. |
| Cross-Dataset Cross-Type | Corpus và điều kiện đều mới | Ví dụ tiếng nói đọc sạch→corpus mới có tiếng nói tự nhiên hoặc nhiễu. Cần định nghĩa điều kiện, reference/metrics và nguồn fit trước; chưa thực hiện trong H49. |

H49 không học trên KEELE: chỉ kiểm tra bộ dữ liệu ngoài bằng pipeline cố định. Nếu dùng KEELE để chỉnh pipeline thì KEELE trở thành dữ liệu development, và cần bộ dữ liệu khác hoặc phần người nói chưa đụng tới để đánh giá tiếp. Không chọn cấu hình tốt nhất theo KEELE rồi gọi kết quả trên chính KEELE là benchmark độc lập.

Benchmark tốt không chứng minh lỗi BT2 chỉ do ít dữ liệu. Có thể khác ngôn ngữ, giọng, nhiễu, cửa sổ, khoảng F0 cho phép hoặc quy trình tạo nhãn chuẩn. Cần cả metric F0 từng khung và quyết định hữu thanh vì mean/std/count có thể gần đúng dù F0 sai theo thời gian. Ngược lại, F0 từng khung khá tốt nhưng MAPE cả file lớn có thể do một ít khung ở đuôi phân phối, sai số đếm hoặc khác quy trình tham chiếu. Ta chấm để phân biệt các khả năng này, không dùng một benchmark để quy lỗi riêng cho data.

Nguồn và giới hạn truy cập: BENCHMARK_SOURCES.md. Tài liệu này là diễn giải từ code BT2 và thiết kế đánh giá của agent, không thay yêu cầu chấm của thầy.
