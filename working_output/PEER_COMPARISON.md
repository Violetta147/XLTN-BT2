# Đối chiếu kết quả tham khảo (29/09/2026)

Nguồn ảnh do người dùng cung cấp: [bảng của bạn thứ nhất](reference/friend_results.png), [bảng của Đạt](reference/dat_results.png), [ghi chú viết tay của thầy](reference/teacher_handwritten.png), [đề bài của thầy](reference/teacher_assignment.png). Không có code hoặc JSON của hai bạn đầu; các nhận định về phương pháp của họ chỉ là giới hạn suy luận từ bảng, không phải xác minh thuật toán.

## Bảng TEST của bạn thứ nhất

| File | LAB F0mean | Dự đoán | Sai số mean | LAB F0std | Dự đoán | Sai số std | NumF0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| phone_F2 | 145 | 149.0109 | 4.0109 | 33.7 | 34.6077 | 0.9077 | 175 |
| phone_M2 | 129 | 129.7638 | 0.7638 | 18.6 | 15.1807 | 3.4193 | 113 |
| studio_F2 | 200 | 195.2210 | 4.7790 | 46.1 | 51.5572 | 5.4572 | 131 |
| studio_M2 | 155 | 153.8416 | 1.1584 | 30.8 | 29.6683 | 1.1317 | 115 |

Tính lại từ bốn dòng: F0mean MAE = **2.6780 Hz**, RMSE = **3.1957 Hz**; F0std MAE = **2.7290 Hz**, RMSE = **3.3006 Hz**. Khớp số gộp trong ảnh sau làm tròn. Tổng NumF0 = **534**. Với chính quy tắc chia khung 25 ms/10 ms của dữ liệu local, số khung LAB V theo bốn file là 235, 134, 137, 128 (tổng 634), nên tỉ số NumF0/V là 74.5%, 84.3%, 95.6%, 89.8% (tổng 84.2%). Tỉ số này **không phải recall V**: dự đoán F0 có thể nằm trên khung UV/SIL, và quy tắc chia khung của bạn ấy chưa được biết. Ảnh ghi “LAB used after inference”; chưa có code để xác minh thứ tự sử dụng nhãn hoặc định nghĩa macro F1 = 0.7715.

AMDF notebook local hiện có F0mean MAE **2.2375 Hz**, F0std MAE **2.8172 Hz**, macro F1 V/UV **0.8220** trên cùng bốn tên file. Bạn ấy tốt hơn về sai số std khoảng 0.0882 Hz, local tốt hơn về mean khoảng 0.4405 Hz. Chưa thể xếp hạng F1 khi chưa biết cùng frame/nhãn/metric hay không.

## Bảng của Đạt

Bốn tên `phone_F1`, `phone_M1`, `studio_F1`, `studio_M1` thuộc **tập huấn luyện local**, không phải bốn file TEST `_F2/_M2`. Trung bình F1 từ bốn số hiển thị = **0.95975 ≈ 0.960**. Sai số tuyệt đối F0mean từng file = 1.8, 0.5, 1.3, 3.0 Hz; trung bình **1.65 Hz**. Sai số F0std = 2.6, 0.6, 3.0, 0.9 Hz; trung bình từ số đã làm tròn **1.775 Hz** (ảnh ghi 1.79, có thể do độ chính xác ẩn). Không có code, NumF0, định nghĩa F1 hoặc kết quả TEST; không thể kết luận tổng quát hóa tốt hơn hay suy ra thuật toán.

## Repo Cường

Đã đọc repo [FAC tại commit `1d1540f`](https://github.com/CuongBien/FAC/tree/1d1540fc93e16145ce43ce14f54760f039b4cf95), chỉ để đối chiếu; không sửa hay commit vào repo đó. WAV trùng hash với dữ liệu local; nội dung LAB trùng, khác byte do xuống dòng. [README](https://github.com/CuongBien/FAC/blob/1d1540fc93e16145ce43ce14f54760f039b4cf95/README.md) nêu frame 25 ms/hop 10 ms, ACF/AMDF và các plugin. [Ngưỡng Gaussian](https://github.com/CuongBien/FAC/blob/1d1540fc93e16145ce43ce14f54760f039b4cf95/src/analysis/threshold.py) được fit từ nhãn training V/UV, khác GMM không nhãn. Code có STE lọc silence, lọc trung vị F0, bandpass, center clipping, hysteresis, energy extension, Viterbi và YIN. YIN nằm ngoài lựa chọn ACF/AMDF nếu bám sát đề thầy.

[Hàm đánh giá](https://github.com/CuongBien/FAC/blob/1d1540fc93e16145ce43ce14f54760f039b4cf95/src/analysis/evaluation.py) tính voiced F1 cho V so với phần còn lại và accuracy ba lớp; macro F1 V/UV trong notebook local là metric khác. [Script so 32 cấu hình](https://github.com/CuongBien/FAC/blob/1d1540fc93e16145ce43ce14f54760f039b4cf95/scripts/05_compare_plugins.py#L237-L254) lấy `min` sai số và `max` F1 trên chính bốn file TEST rồi gọi cấu hình đó là tốt nhất. Số học không vì vậy mà sai, nhưng kết quả TEST của cấu hình được chọn không còn là đánh giá độc lập. Trong [báo cáo AMDF](https://github.com/CuongBien/FAC/blob/1d1540fc93e16145ce43ce14f54760f039b4cf95/outputs/reports/compare_plugins_amdf.csv), baseline TEST: mean MAE 1.60 Hz, std MAE 1.42 Hz, voiced F1 92.30%; cấu hình Energy Extension: 1.53/1.50 Hz, F1 93.83%. Chỉ dùng để hiểu hướng xử lý, không lấy các số TEST đó chọn tham số thí nghiệm local.

## Yêu cầu thầy và bước tiếp

Đề bài trong ảnh yêu cầu chọn **một** trong ACF/AMDF, frame **25 ms**, shift **10 ms**, số F0 ước lượng nằm giữa MinNumF0 và MaxNumF0, báo F0mean/F0std. Ảnh chưa cho giá trị hoặc cách tính MinNumF0/MaxNumF0; không tự đặt giới hạn. ACF local cuối dùng 25 ms; AMDF local cuối dùng 30 ms; GMM ACF 20 ms và GMM AMDF 25 ms. Các cấu hình khác 25 ms nên để ở phần khảo sát, chưa coi là cấu hình nộp cuối phù hợp đề.

Ưu tiên tiếp theo: kiểm tra thí nghiệm ngưỡng trễ AMDF **25 ms** đã đăng ký trong [kế hoạch 01](EXPERIMENT_01_PLAN.md) bằng leave-one-file-out trên bốn file training. Chỉ đưa vào notebook nếu đạt tiêu chí định trước; mọi số TEST đã xem được nêu như giới hạn khi diễn giải kết quả cuối.
