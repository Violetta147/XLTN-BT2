# H21 — center clipping trước ACF

Đăng ký trước đo ngày 07/10/2026. Repository rollback: `35ba151`; champion accepted ACF `009fd2c`. Giữ notebook và các kết quả H18/H19/H20. Chỉ bốn file train local, không đọc test/Drive, không deep learning.

Giả thuyết: chọn mức center clipping bằng inner LOFO có thể giảm lỗi thống kê F0 của file ngoài quá trình chọn, đồng thời giữ chất lượng phân biệt hữu thanh (V), vô thanh (UV) và im lặng (SIL).

## Can thiệp duy nhất

Với từng khung raw, đặt L = r × max(abs(x)); y = sign(x) × max(abs(x) − L, 0). Grid r = 0, 0.3, 0.5; r=0 là accepted raw control. Dùng trước bước trừ trung bình/Hamming của detector ACF hiện có. Không ghép low-pass, logistic hoặc đổi frame/hop trong H21. Không gọi đây là bản sao toàn bộ pipeline Sondhi.

Center clipping đưa phần biên độ nhỏ về 0 và trừ L khỏi phần còn lại. Hard clipping H20 cắt đỉnh lớn tại ±L. Hai phép biến đổi có mục đích và tác động khác nhau. Mức r theo peak trong chính khung, không dùng nhãn held file để tính mức.

Frame25ms/hop10ms, range70–400Hz, path jump0.35/octave0.03/median3 như accepted. RMS và relative RMS luôn lấy raw; pitch/energy threshold refit trên training subset cùng preprocessing. Giữ grid chấm trùng native; không thay F0num GT hoặc cắt output để khớp count. H18/H19 đã thử geometry khác; cố định ở H21 là lựa chọn để cô lập cơ chế, không giới hạn chung cho các vòng sau.

## Lựa chọn và tiêu chí

Final: LOFO trên bốn file. Mỗi outer file: inner LOFO trên ba file còn lại, refit ba file rồi chấm outer; outer không tham gia chọn hay fit. Inner dùng accepted refit cùng pool làm đối chiếu. Chỉ cấu hình có toàn bộ AvgMAPE hữu hạn, macro F1/recall V không giảm quá0.01, tổng SIL false voiced không tăng quá1 mới được xếp theo AvgMAPE tăng dần; hòa chọn ID từ điển. Raw luôn là fallback.

Gate so accepted: train AvgMAPE giảm ít nhất10% tương đối; selected LOFO và nested giảm ít nhất5%; nested macro F1/recall V giảm không quá0.01; SIL tăng không quá1; không file nested AvgMAPE tăng quá2 điểm phần trăm; phone_F1 stdMAPE không tăng. Tất cả phải đạt. Không tự promote champion. Lưu cả thất bại và mọi inner trace/fit.

AvgMAPE là trung bình lỗi tương đối của mean/std/count so LAB thống kê cả file, rồi trung bình qua file. Không có F0 reference theo timestamp để đo pitch accuracy từng khung. Các file đã được xem nhiều lần: nested vẫn là thăm dò trên n=4, không xóa được lịch sử chọn hướng.

## Kiểm tra, hình và phạm vi dừng

Kiểm tra công thức, đối xứng dấu, tỉ lệ gain, zero input và raw feature identity; baseline LOFO phải khớp H16 trong1e-8. Kiểm tra độc lập các contour nested: LAB hashes/timestamps, counts, mean/std/MAPE, phân lớp, loại trừ held file, ID registry và figure source hashes.

Xuất PNG/SVG: nested metrics; tỉ lệ mẫu zero và năng lượng giữ lại theo nhãn (trung bình trong file rồi qua file); raw/center/hard waveform trên khung V nội bộ phone_F1 có RMS raw lớn nhất (không chọn theo điểm detector). Waveform minh họa cơ chế; không phải bằng chứng pitch accuracy. Không chạy noise H21 hoặc mở grid sau thấy kết quả. Kết thúc sau ba options và kiểm tra/báo cáo.

Nguồn cơ chế: [Columbia autocorrelation demonstration, dẫn Sondhi1968](https://www.ee.columbia.edu/~dpwe/classes/e6820-2001-01/matlab/MAD/auto/auto.htm). Công thức đối xứng và thứ tự cụ thể ở trên là đặc tả thực nghiệm này; không dựa vào mô tả một phía trên trang để xử lý mẫu âm.

Lệnh: `python research_workbench_2026_10_07/center_clipping.py register`, `check`, `H21`. Runner kế thừa cấu trúc chọn/score H18, giữ file runner cũ nguyên vẹn để không làm sai source hashes của kết quả trước.
