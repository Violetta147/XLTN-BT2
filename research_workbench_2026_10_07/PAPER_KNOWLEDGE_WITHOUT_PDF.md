# Đọc kiến thức paper mà không extract PDF

Áp dụng yêu cầu người dùng ngày 07/10/2026. Dùng workflow literature-review đã lưu trong `.agents/skills/literature-review/`. Bản tổng hợp hiện có: [LITERATURE_REVIEW.md](LITERATURE_REVIEW.md); danh tính và mức đọc: [literature_records.json](literature_records.json).

## Quy trình đang dùng

1. Xác minh paper qua DOI, trang nhà xuất bản hoặc trang tác giả: đúng tên, tác giả, năm và phiên bản.
2. Tìm bản HTML chính thức hoặc bản HTML trên arXiv. Đọc các mục liên quan đến giả thuyết: phương pháp, giả định, cách chấm và giới hạn; chỉ đưa trích đoạn cần thiết vào context.
3. Nếu chỉ có abstract, dùng nó để nhận diện cơ chế và tìm nguồn tiếp. Không suy ra công thức hay chi tiết triển khai còn thiếu.
4. Đối chiếu tài liệu thuật toán và mã tham chiếu của tác giả. Ghi commit/version, hàm, dòng và hash; phân biệt nội dung paper với hành vi của implementation.
5. Viết bằng lời của agent: cơ chế → giả thuyết BT2 → tham số/adapter → tiêu chí kiểm tra. Mỗi phát biểu có nguồn và mức bằng chứng. Kiểm tra synthetic trước khi đo dữ liệu thật.
6. Nếu vẫn thiếu chi tiết quyết định, ghi rõ chưa truy cập được full text. Tìm bản tác giả được công khai hợp pháp hoặc thử implementation đã xác minh trong vòng riêng. Không đoán chi tiết và không vượt paywall.

Đọc chọn lọc giảm lượng văn bản cần đưa vào context; chưa đo mức tiết kiệm token. Không dùng bản tóm tắt AI làm bằng chứng cho claim mà nguồn chưa hỗ trợ. Đây là narrative engineering review, chưa phải systematic review đầy đủ.

## Ví dụ đã thực hiện

**Praat:** [manual HTML raw autocorrelation](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_raw_autocorrelation.html) cho công thức hiệu chỉnh cửa sổ, ứng viên và chọn đường, cùng ý nghĩa các tham số. Cửa sổ phụ thuộc pitch floor, dài ba chu kỳ thấp nhất; với 70 Hz là khoảng 42.86 ms. H27 dùng API raw của Praat 6.1.38 đã có trên máy. Đây là tài liệu triển khai, không phải đã đọc toàn bộ Boersma (1993); không gọi API này là filtered autocorrelation đời mới.

**Harvest:** [abstract ISCA](https://www.isca-archive.org/interspeech_2017/morise17b_interspeech.html) cung cấp hướng filterbank và nối ứng viên. Đối chiếu tiếp [mã tác giả, commit d625e7](https://github.com/mmorise/World/blob/d625e7608ca23a870018f01e7c562ac683d9847f/src/harvest.cpp#L1189): sau tạo ứng viên là refine/score, loại ứng viên không tin cậy, sửa contour và làm mượt. Hàm xuất kết quả xử lý đường cơ sở ở bước 1 ms rồi lấy mẫu theo bước được yêu cầu; không thể xem `frame_period` là độ dài cửa sổ phân tích. Đây là nhận xét từ implementation này, chưa khái quát mọi bản Harvest. Hash và vị trí hàm lưu trong `results/harvest_source_probe.json`. Sau đó đã chạy H28 trên BT2 bằng PyWORLD 0.3.5 trong môi trường riêng. Mã harvest.cpp trong source archive có cùng SHA256 với source tác giả pin đã đọc. Kết quả chưa vượt control vì nhiều khung UV/SIL bị gọi hữu thanh; xem [H28_ERROR_ANALYSIS.md](H28_ERROR_ANALYSIS.md). Không lấy kết quả benchmark của paper thay số liệu BT2.

**pYIN:** [API chính thức librosa 0.11](https://librosa.org/doc/0.11.0/generated/librosa.pyin.html) giải thích ứng viên có xác suất và Viterbi chọn F0/V–UV, cùng frame length, padding và tham số. Dùng tài liệu này để kiểm adapter, nhưng không giả đã đọc full paper ICASSP 2014.

**Instantaneous F0:** đã lấy được [bản HTML arXiv](https://arxiv.org/html/1605.07809), đọc phần kiến trúc estimate–track–refine và cách phân biệt tracking với voicing. Các section đã đọc được ghi trong records; không claim mọi phụ lục đã đọc.

## Áp dụng vào thí nghiệm

H27 (Praat raw) và H28 (Harvest) đều so pipeline với control AMDF H24, đăng ký và push trước đo. Mọi cấu hình cố định được báo riêng với kết quả của bước chọn cấu hình; không chỉ trình bày đường baseline sau khi registry bị loại. Figures và kết quả thất bại đã lưu/push. Không dùng số liệu công bố trong paper thay số liệu BT2. Chấm cùng ground truth và lưới thời gian, báo coverage, mean/std/count và V/UV/SIL. Mục tiêu người dùng vẫn là **mỗi file Average MAPE ≤2%**; lựa chọn cấu hình không xem file outer đang chấm.

Không extract hoặc tải PDF cho quy trình này. Không tạo PDF báo cáo. Một nguồn chỉ có abstract vẫn được giữ trong review với giới hạn rõ ràng, thay vì bị loại hoặc được trình bày như full text.
