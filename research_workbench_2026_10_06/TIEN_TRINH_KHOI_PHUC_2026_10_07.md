# Nối lại tiến trình BT2 sau khi phần chat không còn hiển thị

Ngày đối chiếu: 07/10/2026. Người dùng xác nhận hiện chỉ thấy mất câu trả lời/tiến trình trong chat. Đây là bản kể lại từ báo cáo, CSV, manifests và Git đã còn trên máy; không phải bản phục hồi nguyên văn phản hồi của model.

## 1. Kết quả tối qua còn ở đâu?

Mã, CSV và figures nằm trong research_workbench_2026_10_06. Trước bước phục hồi, GitHub đã có các commit đến fa759d0 lúc 22:44 ngày 06/10; H15/H17 có thêm 24 artifacts chưa commit, được ghi khoảng 22:47–22:48.

Đối chiếu sáng 07/10:

- H15 có đủ 1744 case, mỗi case hai model, tổng 3488 dòng; CSV có đúng case registry và không trùng case/model.
- Code/registry/WAV hashes H15 khớp với metadata phiên chạy; achieved SNR của noise khớp mức đăng ký.
- Code H17 khớp hash; 12 lựa chọn, 24 dòng metric, 112 inner traces, 7 phương án.
- Held file được loại khỏi fit và khỏi inner selection trong outer nested fold; ID trả về thuộc registry.
- Bốn cặp PNG/SVG H15/H17 còn đọc được; source CSV và generator hashes khớp manifests. Đã xem hai hình tổng quan để đối chiếu hiển thị.
- Kết quả H15 đã push ở 23bdb0c; H17 đã push ở 79c3830, trên codex/train-mape-investigation.

Toàn thư mục hiện có 45 PNG + 45 SVG. Việc có nhiều hình hoặc nhiều seed không làm tăng số đơn vị dữ liệu độc lập: bài vẫn chỉ có bốn file train.

Không đủ bằng chứng để xác định thao tác Retry cụ thể đã thay phần hội thoại thế nào. Các kiểm tra này chứng minh artifacts đang tồn tại và đã được lưu, không tái dựng sự kiện UI hoặc khẳng định mọi dòng chat cũ còn nguyên.

## 2. Bắt đầu từ câu hỏi nào?

Mục tiêu là giảm lỗi thống kê F0, đặc biệt std, đồng thời giữ chất lượng phân loại hữu thanh/vô thanh và giảm F0 giả trong khoảng lặng.

F0 là tần số cơ bản, đo bằng Hz. ACF (tự tương quan) tìm độ trễ lặp lại của tín hiệu để suy ra chu kỳ. V/UV/SIL lần lượt là hữu thanh/vô thanh/khoảng lặng theo nhãn đoạn.

Chuẩn trong LAB có hai vai trò khác nhau:

- Nhãn đoạn cho biết loại âm tại từng thời điểm.
- F0mean/F0std/F0num là mean, độ lệch chuẩn và số F0 chuẩn của cả file.

Các LAB đang dùng không có F0 reference từng timestamp. Do đó báo cáo không thể chứng minh từng cao độ thuật toán trả ra đều đúng. Std cả file gần chuẩn hơn có thể xuất hiện cả khi một số khung vẫn sai.

Baseline được tái lập trước khi thử phương pháp mới. ACF cũ có train AvgMAPE 29,834711%; bản accepted đã có từ trước vòng đêm đạt 6,177968%. AvgMAPE đang nói là metric tổng hợp trên thống kê cả file, không phải lỗi F0 của từng khung.

## 3. Đọc các phép đánh giá

LOFO là Leave One File Out: giữ một file để chấm, fit trên ba file còn lại, lặp qua bốn file. Nó giúp tránh fit rồi chấm chính cùng file.

Nếu dùng LOFO để chọn phương pháp rồi báo điểm LOFO của phương pháp vừa chọn, điểm đó đã chịu ảnh hưởng của việc chọn. Nested LOFO thêm vòng ngoài: giữ một file hoàn toàn khỏi bước chọn; chỉ dùng ba file kia để chọn phương án qua vòng trong, refit trên ba file và chấm file ngoài.

Nested không biến bốn file thành dữ liệu lớn hoặc xóa việc agent đã xem nhiều kết quả trên cùng dữ liệu để đặt registry. Vì vậy mọi kết luận vẫn là nghiên cứu thăm dò.

## 4. Tối qua đã thử những gì?

| Vòng | Thay đổi chính | Train AvgMAPE (%) | LOFO AvgMAPE (%) | Quyết định |
|---|---|---:|---:|---|
| Accepted ACF | Bản đối chiếu hiện có | 6,177968 | 7,279236 | Giữ làm baseline |
| H10 | YIN fixed-support trong frame 25 ms | 9,367355 | 12,237352 | Không đạt |
| H11 | NSDF/MPM để chọn F0 | 6,960350 | 8,188307 | Không đạt |
| H12 | Hysteresis cho quyết định voiced | 2,697086 | 6,182753 selected; 6,670683 nested | Đủ gate đã đăng ký, provisional |
| H13 | Chỉ đổi strength sang NSDF, giữ lags/path | 5,088629 | 7,207657 | Giảm LOFO chưa đủ 5% |
| H14 | Bỏ phiếu ba khung cho voiced mask | 4,225410 | 5,817675 | Std phone_F1 tăng, không đạt |
| H16 | Logistic cố định trên ACF score + RMS | 5,119156 | 5,470735 | Fixed-method gate đạt, chưa promote |
| H17 | Chọn trong ACF/hysteresis/logistic bằng inner fold | 5,119156 | 5,470735 selected; 7,374765 nested | Nested gate không đạt |

YIN và MPM là các phương pháp F0 cổ điển mới được thử trong vòng này. Kết quả kém hơn chỉ áp dụng cho adapter và cấu hình đã dùng; không kết luận hai thuật toán đó luôn kém ACF trong mọi điều kiện.

Hysteresis dùng ngưỡng bật/tắt khác nhau để tránh voiced run ngắt khi score dao động gần ngưỡng. Majority3 chọn lớp theo đa số ở ba khung. Logistic dùng hai đặc trưng ACF score và năng lượng RMS tương đối để quyết định lớp; scaler và hệ số fit trong training fold.

Một số lựa chọn có điểm tổng hợp thấp nhưng vẫn vi phạm gate ở file cụ thể. Không thay tiêu chí sau khi xem kết quả để biến chúng thành thành công.

## 5. Vì sao giảm std chưa đủ để nói F0 đã đúng?

H12 làm phone_F1 train std tiến gần 20,6 Hz. Phân tích tiếp tìm thấy hai khung có nhãn UV vẫn được dự đoán hữu thanh; F0 của chúng đổi từ giá trị thấp lên gần mean.

Sự thay đổi đó giảm ảnh hưởng của UV lên variance và làm std toàn file đẹp hơn, dù hai khung vẫn là false voiced. Với những khung có tâm nhãn V thật, std đã gần chuẩn ngay ở bản accepted.

Đây là phát hiện quan trọng: phải đọc đồng thời lỗi V/UV/SIL, contour, nguồn tạo F0 và thống kê cả file. Không chỉ tối ưu một số std rồi kết luận thuật toán đã tìm đúng mọi chu kỳ.

Đọc [phân tích liên hệ metric và nhãn](METRIC_LABEL_COUPLING_REPORT.md) và [phân tích cơ chế hysteresis](HYSTERESIS_MECHANISM_REPORT.md).

## 6. H15: kiểm tra khi tín hiệu bị biến đổi

H15 đã hoàn thành 1744 case trên bốn file train. Mỗi case so accepted ACF với hysteresis dùng margin từ nested fold đã chọn trên dữ liệu sạch.

Các điều kiện gồm noise trắng/hồng/nâu ở bảy mức SNR, nhiều seed, và gain/DC/clipping/impulses riêng. Đây là biến đổi mô phỏng, không phải tập thu âm nhiễu mới. Không fit lại hay chọn tham số theo noise.

Hysteresis thường tăng recall V, nhưng cũng có thể tăng SIL false voiced. Brown noise làm SIL false voiced và lỗi thống kê tăng mạnh; giữ nhiều V hơn chưa đủ để nói robust toàn diện. Các trường hợp không có đủ F0 để tính mean/std phải đọc cùng coverage, không tính lỗi bằng 0.

Đọc [báo cáo H15](ROBUSTNESS_REPORT.md). Figure nguồn:

![Robustness](figures/robustness_noise_curves.png)

## 7. H17: vì sao không chọn luôn logistic?

Một logistic cố định đạt LOFO 5,470735%, thấp hơn accepted 7,279236%. Nhưng H17 hỏi câu rộng hơn: nếu hệ thống được chọn family/margin trên training subset, quy trình chọn đó có tốt trên file ngoài không?

Vòng nested chọn các phương án khác nhau cho từng file giữ lại:

| File ngoài | Phương án được chọn từ ba file còn lại |
|---|---|
| phone_F1 | hysteresis 0,06 |
| phone_M1 | logistic C=1 |
| studio_F1 | hysteresis 0,04 |
| studio_M1 | hysteresis 0,02 |

Kết quả của toàn quy trình chọn là 7,374765%, so với accepted 7,279236%. Vì vậy H17 không đạt yêu cầu giảm ít nhất 5% tương đối. Giữ accepted; không lấy điểm selected LOFO đẹp để thay thế điểm nested của quy trình.

Điều này không chứng minh logistic cố định vô dụng. Nó cho thấy lựa chọn phương pháp trên các subset nhỏ có thể không ổn định, và cần giữ đúng câu hỏi đánh giá.

![Lựa chọn phương pháp](figures/family_selection_nested.png)

Đọc [báo cáo H17](FAMILY_SELECTION_REPORT.md).

## 8. Gemini và Jev đã tham gia thế nào?

Gemini reviewer01 đã phản biện protocol. Agent nhận ra và ghi các lỗi trong phản hồi, gồm nhầm metric cả file thành frame metric, suy diễn phoneme khi nhãn không có phoneme và giả định chưa nội suy dù source đã có.

Reviewer02 đã gửi câu hỏi có correction; lúc log được lưu chưa có nội dung phản hồi để đọc. Không xem “đã gửi” là “đã nhận và dùng phản biện đầy đủ”.

Jev có một call prospective để so shortlist H12, gợi ý hysteresis với relative choice 0,70 và fit 0,78. Đây là tín hiệu lựa chọn, không phải xác suất thuật toán sẽ đạt gate. Mã thí nghiệm và số đo quyết định việc giữ/bỏ.

Đọc [AI review log](AI_REVIEW_LOG.md) và [raw Jev H12](jev_h12_selection.json). Lượt phục hồi hiện tại không gọi lại AI để xác nhận các số đếm đã rõ.

## 9. Đang ở đâu và còn gì?

Champion vẫn là accepted ACF. H12 và H16 là ứng viên đáng nghiên cứu; H17 chưa hỗ trợ thay thế bằng quy trình chọn family. Test không được đọc lại trong bước phục hồi và các vòng đêm được log ở trên; test cũ đã từng được xem ở lịch sử trước đó.

Cần làm tiếp:

1. Đọc phản hồi Gemini reviewer02 nếu còn truy cập được.
2. Tổng hợp độ ổn định và mức chắc chắn theo file, gallery và giải thích từng figure.
3. Đặt giả thuyết/gate cho vòng mới, ưu tiên chênh protocol count, lỗi voicing/boundary và brown-noise failure.
4. Chốt cấu hình trước khi xem test mô tả; ghi rõ giới hạn dữ liệu và test history.

Schedule đã được người dùng xóa. Công việc tiếp theo thực hiện trực tiếp trong chat, theo STATE.md hiện tại và protocol đã cập nhật.

## 10. Giới hạn phục hồi

Lượt này đối chiếu artifacts đã có, không chạy thêm thuật toán mới. Source hashes/registry/cases/selection isolation và figures H15/H17 đã kiểm tra; chưa tái chạy toàn bộ kết quả H00–H17.

Không khẳng định screenshot Retry chứng minh file bị xóa hoặc biết chính xác vì sao UI chọn Luna. Câu trả lời cũ trong chat có thể không còn hiển thị; bản này nối lại nội dung khoa học từ bằng chứng, không phục hồi nguyên văn hội thoại.

Receipts: [H15](results/recovery_h15_checks_2026_10_07.json), [H17](results/recovery_h17_checks_2026_10_07.json). Quy trình thí nghiệm gốc vẫn nằm trong PROTOCOL.md, từng registration và scripts.
