# Truy nguồn WAV, LAB gốc và LAB ba thống kê — 07/10/2026

Đã tìm được một bản công khai có **8 WAV giống hệt từng byte** với dữ liệu BT2 hiện tại: repository [dthle/TinHieuHuanLuyen](https://github.com/dthle/TinHieuHuanLuyen/tree/e38529d6485b59e49dddeccb44c129a6f93e48f3). Cả 8 LAB gốc và README cũng giống nội dung sau khi chuẩn hóa xuống dòng. Đây là bằng chứng cùng bộ dữ liệu, **chưa chứng minh tác giả repository là người thu âm hoặc người tạo nhãn**, và chưa chứng minh người dùng đã tải dữ liệu từ repository này.

Nguồn phát hành bộ train ba thống kê đã được người dùng xác nhận trong lịch sử chat là **từ thầy**. Log cũ ghi việc sao chép LAB vào cache local, sau đó mã nghiên cứu chép cache vào repository. Chưa tìm được quy trình thầy tạo F0mean/F0std/F0num, tên người thu âm hoặc định danh corpus gốc.

Lượt này chỉ đọc dữ liệu local, lịch sử đã lưu và GitHub công khai. Không truy cập Google Drive; các đường dẫn Drive trong lịch sử chỉ được đọc như văn bản. Không chạy F0, sửa dữ liệu, đổi reference chấm, tiếp tục H44 hoặc gọi Jev/Gemini. Phần văn xuôi do agent viết trực tiếp, không dùng skill reader-first-prose.

## 1. Những file đang được truy nguồn

| Nhóm | Đường dẫn trong repository | Nội dung |
| --- | --- | --- |
| WAV và LAB gốc train | `TinHieuHuanLuyen/` | 4 WAV; 4 LAB có nhãn đoạn sil/v/uv và mean/std; README |
| WAV và LAB gốc test | `TinHieuKiemThu/` | 4 WAV; 4 LAB có nhãn đoạn sil/v/uv và mean/std |
| LAB train ba thống kê | `research_3gt_2026_10_05/train_3gt/` | 4 LAB chỉ chứa F0mean/F0std/F0num |
| LAB test ba thống kê | `research_3gt_2026_10_05/test_3gt/` | 4 LAB chỉ chứa F0mean/F0std/F0num |

F0 là tần số cơ bản của tiếng nói. F0mean là trung bình các giá trị F0 hợp lệ; F0std là độ lệch chuẩn, thể hiện mức biến thiên của chúng; F0num là số giá trị F0 được tính vào bộ thống kê. Nhãn v/uv/sil lần lượt là hữu thanh, vô thanh và khoảng lặng theo đoạn thời gian.

## 2. Bản công khai đã đối chiếu trực tiếp

Pin đã kiểm tra: `e38529d6485b59e49dddeccb44c129a6f93e48f3` của `dthle/TinHieuHuanLuyen`.

- Đọc các file từ URL raw gắn commit, đối chiếu byte và SHA-256 với local: **8/8 WAV trùng tuyệt đối**.
- **8/8 LAB gốc và README trùng từng dòng** sau chuẩn hóa xuống dòng. SHA-256 byte của các file văn bản khác nhau vì cách biểu diễn xuống dòng; không báo chúng trùng byte.
- Trong repo công khai, các file train và test nằm chung thư mục gốc. Cách chia train/test hiện tại lấy từ bài tập local và thư mục đang dùng; không suy ra cách chia chỉ từ tên repository công khai.
- Lịch sử GitHub API của `phone_F1.wav`/LAB ghi commit `153765674a795d4be37db8d0aabc4b78a790a28e`, ngày tác giả/committer 09/10/2022 UTC. `studio_M2.wav` ghi `2aac39f9bdc86b99b1799a628d0bea74d9a61b2f`, ngày 06/10/2022 UTC. Đây là ngày trong lịch sử commit; không chứng nhận ngày thu âm hoặc ngày file lần đầu được công khai.
- README công khai giải thích định dạng LAB và hai thống kê. Không có quy trình tạo cao độ chuẩn, thông tin người nói, hoặc xác nhận tác giả bộ dữ liệu.

Link để kiểm tra: [WAV phone_F1](https://github.com/dthle/TinHieuHuanLuyen/blob/e38529d6485b59e49dddeccb44c129a6f93e48f3/phone_F1.wav), [LAB phone_F1](https://github.com/dthle/TinHieuHuanLuyen/blob/e38529d6485b59e49dddeccb44c129a6f93e48f3/phone_F1.lab), [README](https://github.com/dthle/TinHieuHuanLuyen/blob/e38529d6485b59e49dddeccb44c129a6f93e48f3/README).

Web search tên file chính xác không tìm được nguồn phát hành gốc. GitHub repository search với `XLTN`, `"xu ly tieng noi"`, `"TinHieuHuanLuyen"` tìm ra bản trùng nêu trên. Một số kết quả tài liệu bài tập trên website chia sẻ tài liệu không được dùng để xác nhận tác giả hoặc trường của dataset. Phạm vi tìm kiếm này không phải kiểm kê toàn bộ Internet.

## 3. Dấu vết ngay trong WAV

Đọc cấu trúc RIFF và metadata XMP nhúng trong WAV, không suy từ tên file hay timestamp trên Windows:

| File | Dấu vết nhúng |
| --- | --- |
| `studio_F1.wav` | Lịch sử `saved` ghi Adobe Audition 4.0.0.1815, ngày 05/12/2013 và 09/12/2013, múi giờ +07:00 |
| `studio_M2.wav` | Lịch sử `saved` ghi Adobe Audition 4.0.0.1815 ngày 06/12/2013 và 10/12/2013; Adobe Premiere Pro 5.5 ngày 11/12/2013, múi giờ +07:00 |
| 6 WAV còn lại | Chỉ thấy chunk `fmt ` và `data`, không thấy metadata tác giả/ngày lưu tương tự |

Các trường năm 2013 là manh mối về lịch sử xử lý file. Metadata có thể được kế thừa hoặc thay đổi; không gọi đó là ngày thu âm đã xác minh. Không có URL nguồn, tên người thu âm hoặc người nói trong các trường đã đọc. Cũng không suy từ Premiere rằng file chắc chắn được cắt từ một video cụ thể.

## 4. Chuỗi đưa dữ liệu vào workspace và Git

Mốc thời gian bên dưới dùng UTC+07:00; nguồn lịch sử chat là các bản ghi local đã lưu, không phải truy cập lại nguồn bên ngoài.

| Mốc | Bằng chứng | Kết luận có thể đưa ra |
| --- | --- | --- |
| 29/09/2026 01:15 | Commit gốc `874aca1a77a79b91c73be46ae3d1d91758baab4a` thêm 8 WAV, 8 LAB gốc, README | Đây là mốc lưu vào Git của repo người dùng, không phải mốc tạo âm thanh |
| 29/09 07:18 | Người dùng nói cần chạy notebook trên “tập dữ liệu của thầy” | Nguồn cung cấp theo lời người dùng là giảng viên; chưa có danh tính hoặc bản phát hành có chữ ký |
| 29/09 07:58 | Người dùng nói “tôi mới có tập huấn luyện mới từ thầy có thêm 1 groundtruth là số lượng giá trị F0 tìm được” | Train 3GT được người dùng nhận từ thầy, không phải output của vòng nghiên cứu 05–07/10 |
| 29/09 07:59 | Log so SHA-256 WAV của train cũ/mới: cả 4 `sameWav=True`; đọc README mới và bốn LAB | Trong phép đối chiếu lịch sử đó, WAV train không đổi; LAB mới có ba thống kê |
| 29/09 08:18 | Log sao chép bốn LAB train mới vào `.validation-3gt` sau lần tạo cache trước | Có đường đi từ bộ được cung cấp đến cache local; lượt này không truy cập lại nguồn gốc ngoài local |
| 29/09 08:23 | Người dùng cung cấp thư mục test 3GT và nói “Đã có thư mục tín hiệu kiểm thử” | Test mới được cung cấp trong cùng cuộc trao đổi; câu này không nêu riêng người tạo nhãn |
| 29/09 08:24 | Log so SHA-256 WAV test cũ/mới: cả 4 `sameWav=True` | Trong đối chiếu lịch sử, WAV test cũng không đổi |
| 29/09 08:29 | Log chép bốn LAB test mới vào `.validation-test-3gt` | Xác định cache local trực tiếp của test 3GT |
| 05/10 22:21 | Commit `1ea0d9db11ed4d22de46dcf5b99a01e77e63f942`; `init_baseline.py` chép LAB từ cache vào `train_3gt` | Xác định nguồn trực tiếp của LAB train trong repository |
| 05/10 23:02 | Commit `6f101945f6a7c56fd879eaba6ec3e5340e6c8464`; `final_evaluation.py` chép cache vào `test_3gt` | Xác định nguồn trực tiếp của LAB test trong repository |
| 07/10, audit này | Cả 8 LAB 3GT trùng byte/SHA-256 cache local hiện có; 17 file gốc khớp baseline theo byte WAV/nội dung văn bản | Không thấy dữ liệu gốc hoặc reference bị sửa trong các vòng nghiên cứu xét tại đây |

Các đoạn lịch sử dùng: session `01a0ea87-23ed-7562-a3aa-928524e13416`, file JSONL `rollout-2026-09-29T07-18-40-01a0ea87-23ed-7562-a3aa-928524e13416.jsonl`, dòng 9, 406, 430, 804, 882, 906, 1038. File nằm dưới thư mục sessions local của Codex, không được sao chép toàn bộ vào repository. Các log ngày 29/09 xác nhận thao tác khi đó; không chứng nhận nguồn ngoài local còn giữ nguyên hôm nay.

Tài liệu local `Hướng dẫn BT 2 - Tìm tần số cơ bản của tín hiệu tiếng nói.docx.txt`, mục 1 và 4, chỉ định hai thư mục train/test và dùng LAB để chấm. Tài liệu này không ghi người thu âm hay thuật toán tạo thống kê. Timestamp sửa file local tháng 09/2026 không được dùng như ngày thu âm.

## 5. “Hai nguồn thống kê F0” khác nhau thế nào?

Hai nguồn là **hai phiên bản LAB của cùng âm thanh**. LAB gốc có mean/std và nhãn đoạn; LAB 3GT mới có mean/std/count và không có nhãn đoạn. Không phải hai mô hình của agent đang cho ra hai đáp án.

| Split | WAV | Mean gốc (Hz) | Mean 3GT (Hz) | Std gốc (Hz) | Std 3GT (Hz) | Count 3GT |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| train | phone_F1.wav | 217 | 215.6 | 23 | 20.6 | 148 |
| train | phone_M1.wav | 122 | 123.7 | 18 | 16.8 | 232 |
| train | studio_F1.wav | 232 | 229.6 | 40 | 36.8 | 127 |
| train | studio_M1.wav | 113 | 116.9 | 26 | 26.4 | 82 |
| test | phone_F2.wav | 145 | 150.2 | 33.7 | 30.7 | 219 |
| test | phone_M2.wav | 129 | 130.2 | 18.6 | 15.4 | 123 |
| test | studio_F2.wav | 200 | 198.6 | 46.1 | 47.8 | 139 |
| test | studio_M2.wav | 155 | 154.7 | 30.8 | 30.3 | 116 |

Như vậy, bản mới **thay cả mean/std**, không chỉ thêm count. Ví dụ `phone_F1`: 217/23 chuyển thành 215.6/20.6. Đây cũng không đơn thuần là làm tròn cùng một giá trị: mean215.6 làm tròn đến số nguyên là216, không phải217; std20.6 làm tròn là21, không phải23. Tương tự, studio_F1 std36.8 làm tròn là37, không phải40.

Chưa có đủ bằng chứng để giải thích nguyên nhân. Khác thuật toán đo, cửa sổ/bước dịch, tập khung F0 hợp lệ hoặc cách xử lý biên đều là các khả năng cần kiểm tra, **không phải kết luận đã xác nhận**. Không có script đo reference, cấu hình, chuỗi F0 từng thời điểm hoặc biên bản sửa nhãn để chọn một cách giải thích.

Điểm chấm phụ thuộc bộ reference được dùng. Ví dụ giả định thuật toán trả std=23 Hz cho `phone_F1`: sai số tương đối so với LAB gốc là 0%, còn so với LAB 3GT là `|23−20.6|/20.6×100 ≈ 11.65%`. Đây là ví dụ toán học, không phải số đo mới của thuật toán. Không so điểm trước/sau giữa hai bộ chuẩn như thể chỉ thay thuật toán.

Các vòng nghiên cứu hiện tại dùng **mean/std/count từ 3GT để chấm ba thống kê**, còn nhãn đoạn gốc để đánh giá v/uv/sil. Không lấy số tâm khung nằm trong đoạn v làm count chuẩn thay thế. Cả hai phiên bản đều không cung cấp F0 chuẩn từng khung; cùng thống kê không chứng minh cùng contour hoặc cao độ từng khung đúng.

## 6. Điều đã xác định và điều còn thiếu

Đã xác định được bản công khai trùng dữ liệu, lịch sử xử lý nhúng của hai WAV, chuỗi sao chép LAB 3GT vào local/repository và việc các giá trị reference đã thay đổi. Chưa xác định được người tạo bộ dữ liệu ban đầu, người nói, ngày thu thật, thiết bị, nguồn thu âm/video, và quy trình tạo hai phiên bản reference.

Thông tin cần lấy từ người phát hành để khép kín nguồn gốc: nguồn/corpus ban đầu; metadata người nói/phiên thu; phần mềm và phiên bản tính F0; pitch range, frame length/hop/time origin; quy tắc nhận hữu thanh và xử lý biên; định nghĩa count, std dùng ddof nào; lý do cập nhật mean/std. Agent chưa gửi tin nhắn cho giảng viên.

## 7. Tái lập và kiểm tra

Chạy từ repository:

```powershell
& 'C:/Users/violet/miniconda3/python.exe' 'research_workbench_2026_10_07/dataset_provenance_audit.py'
```

Mã audit chỉ đọc local và GitHub, chốt pin source công khai. Nó đối chiếu byte/SHA-256, chuẩn hóa xuống dòng riêng cho văn bản, đọc RIFF/XMP và kiểm tra cache 3GT/baseline Git. [Receipt JSON](results/dataset_provenance.json) lưu URL, hash, metadata, lịch sử ba file công khai và các cặp thống kê. Kết quả: 8 WAV trùng byte, 8 LAB trùng nội dung, 8 LAB 3GT trùng byte cache, 17 file gốc khớp baseline; file gốc không đổi trong audit. Lịch sử chat được đối chiếu riêng với các dòng nêu ở mục 4; script không đọc hoặc chạy lại lệnh trong session cũ.

## 8. Tác giả repo công khai đã làm gì với dữ liệu?

Rà mã tại cùng pin `e38529d`, gồm 6 file Python/MATLAB và 4 code cell của `vu.ipynb`; không thực thi mã của repo công khai. Đọc đủ 14 commit trong lịch sử reachable từ pin. URL, hash source đã đối chiếu Git blob và danh sách thay đổi WAV/LAB được lưu tại [public_repo_usage_review.json](results/public_repo_usage_review.json).

Trong [vu.py](https://github.com/dthle/TinHieuHuanLuyen/blob/e38529d6485b59e49dddeccb44c129a6f93e48f3/vu.py#L54-L66), tác giả đọc WAV/LAB, tách hai dòng thống kê cuối rồi dùng nhãn đoạn v/uv để giữ phần tín hiệu ngoài khoảng lặng trong bộ nhớ. Chương trình chia khung, tính năng lượng ngắn hạn (STE) và số lần tín hiệu đổi dấu qua mức 0 (ZCR), tìm ngưỡng bằng tìm kiếm nhị phân rồi phân loại hữu thanh/vô thanh. Nó so kết quả với nhãn đoạn có sẵn và xuất đồ thị HTML. Mặc định cuối file gọi bốn tên có hậu tố1; [VU.m](https://github.com/dthle/TinHieuHuanLuyen/blob/e38529d6485b59e49dddeccb44c129a6f93e48f3/VU.m#L1-L46) có triển khai MATLAB dùng bốn tên hậu tố2. Những biến thể khác cũng xoay quanh STE/ZCR, biểu đồ và phân loại đoạn.

Đây là xử lý phân loại hữu thanh/vô thanh, chưa thấy pipeline tính cao độ bằng ACF/AMDF hoặc tạo lại F0mean/F0std/F0num trong các source đã đọc. Không thấy lệnh ghi WAV/LAB; việc cắt khoảng lặng trong mảng tín hiệu không đồng nghĩa tác giả sửa file âm thanh gốc. Trong 14 commit đã kiểm tra, cả 8 WAV và 8 LAB chỉ có thay đổi `added`, không có lần sửa sau đó: bốn cặp hậu tố2 được thêm ở `2aac39f9`, bốn cặp hậu tố1 ở `15376567`. Không có bằng chứng từ lịch sử repo này rằng tác giả đổi mean/std của LAB để tạo bộ 3GT. Không suy ra được những thao tác ngoài Git hoặc trước khi file lần đầu được thêm.

## 9. Có thể thầy thêm F0num rồi ghi nhầm mean/std không?

Người dùng xác nhận 3GT được thầy gửi để thi trên lớp và nghi có lỗi nhập số khi thêm count. Giả thuyết này có thể xảy ra nhưng chưa được chứng minh. Cả **8/8 mean và 8/8 std** đều khác giữa hai phiên bản, nên mẫu thay đổi ít giống một lỗi gõ nhầm đơn lẻ. Vẫn có thể có lỗi chuyển bảng, dùng nhầm phiên bản thống kê hoặc một lỗi có hệ thống; không loại trừ chỉ vì nhiều ô cùng đổi.

Cùng WAV không buộc mọi cách đo F0 phải cho cùng mean/std/count: ba thống kê được tính từ các giá trị F0 mà quy trình đo nhận là hợp lệ. Nếu đổi cách nhận khung, phương pháp đo hoặc cấu hình, chúng có thể đổi dù âm thanh không đổi. Chưa có bằng chứng quy trình đo thực sự đã đổi ở đây. Việc số mới có phần thập phân cũng không chứng minh nó chính xác hơn.

Theo đề thi hiện được người dùng xác nhận, giữ 3GT thầy cung cấp làm bộ thống kê để chấm; không thay bằng LAB cũ hoặc tự sửa các số nghi ngờ. LAB gốc vẫn là nguồn nhãn đoạn cho các kiểm tra v/uv/sil riêng. Câu cần đối chiếu với người phát hành: “Bản 3GT chỉ bổ sung F0num hay thầy đã tính lại cả mean/std? Ví dụ phone_F1 đổi 217/23 thành 215.6/20.6; bài thi chấm theo bản nào và bản mới được tính bằng cách nào?” Agent chưa gửi câu này cho giảng viên.

Chưa cần Jev để phân xử. Các phép đối chiếu số, byte và lịch sử Git đã được kiểm tra trực tiếp; Jev không có bằng chứng về ý định cập nhật của giảng viên hay cách tạo reference chưa được cung cấp. Jev có thể rà một lời giải thích cụ thể sau khi có nguồn, nhưng không xác nhận thay giảng viên rằng một con số là lỗi ghi nhầm. Không gọi Jev trong lượt này và không thử lại nhánh MCP đã lỗi.

Người dùng cũng hỏi khả năng thầy dùng công cụ: có thể đo một chuỗi F0 rồi xuất ba thống kê bằng phần mềm. Tài liệu BT2 local gợi ý WaveSurfer để xem pitch contour, nhưng không nói ground truth được tạo bằng WaveSurfer. Đây là một giả thuyết về cách đo, không phải nguồn đã xác minh. Hướng truy nguồn bằng transcript cũng được người dùng đề xuất: cần lời nói thực được nghe/chép từ WAV, rồi tìm và đối chiếu bản thu ứng viên. Công cụ audio hiện tại không hỗ trợ nghe WAV trực tiếp; chưa có transcript đã xác minh và chưa có kết quả tìm nguồn theo lời nói. Không chạy ASR bằng deep learning để vượt giới hạn BT2.
