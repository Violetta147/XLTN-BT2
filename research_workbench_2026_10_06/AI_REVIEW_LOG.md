# Gemini và Jev — nhật ký phản biện, không phải nguồn số đo

## Gemini reviewer01

- Chrome tab người dùng184651875: https://gemini.google.com/app/cd94cd87d07bc5c5; mode Pro.
- Mục đích: phản biện protocol trước YIN/MPM; gửi mô tả4file train, LAB segment và3GTstats, frame25/hop10, acceptedACF/path/RMS/median, các số đo baseline, LOFO/nested cũ và kế hoạch train-only.
- Câu hỏi gồm8bẫy định lượng, YIN/MPM25ms,5hướng cải tiến, gates, figures, giới hạn n=4. Không gửi WAV/credentials/thông tin cá nhân.
- Phản hồi đã đọc có8bẫy và dừng giữa phần2; không tuyên bố đã nhận đủ6phần yêu cầu. Đây là ghi chép các nhận định đã quan sát và đối chiếu, không phải full raw transcript.

Những ý có thể thử: ngưỡng năng lượng làm ngắt voiced run; median3 không sửa lỗi kéo dài; cửa sổ ngắn hỗ trợ ít chu kỳ ở70Hz; phân nhóm lỗi ở boundary. Chưa có kết quả chứng minh cơ chế.

Những lỗi cần sửa trước dùng:

- Gemini nói MAPE bị chi phối bởi khung F0 thấp, trong khi metric của bài chấm mean/std/count từng file, không frame MAPE.
- Gemini giả định có thể chưa nội suy parabol; source core/baseline đã có nội suy. Phone16kHz, studio44.1kHz phải tách.
- Gemini nói cộng10Hz ở nửa đầu và trừ10Hz ở nửa sau giữ mean/std: mean có thể giữ khi số khung bằng nhau, STD không được bảo đảm. H00b dùng hoán vị làm counterexample có kiểm tra chính xác.
- Gemini gán FN cho /m,n,l/ dù LAB không có nhãn phoneme; không dùng nhận định này trong báo cáo.
- Gemini gọi Viterbi đang nhớ chính xác quỹ đạo4file; dữ liệu nhỏ có nguy cơ overfit, nhưng chưa đo được memorization chính xác.
- Ví dụ chọn lag2T cho F0/2; cách diễn đạt T/2T và hướng octave trong phản hồi không rõ, phải đối chiếu công thức fs/lag.
- 25ms/70Hz chứa1.75chu kỳ; overlap còn khoảng10.714ms,42.86%, không phải một mệnh đề pitch accuracy.

## Gemini reviewer02

Đã gửi câu hỏi mới với các correction trên và số đo boundary từ H00; yêu cầu tối đa500từ,3hướng classical DSP một yếu tố, train-only fit, failure conditions và kiểm tra provenance count. UI đã xác nhận gửi/Ngừng tạo; lúc lưu log chưa thấy nội dung phản hồi. Không gọi lại câu hỏi cũ để ép đáp án.

Thông số gửi: V boundary33FN/66, interior51FN/548; UVboundary6FP/59, interior7FP/121; SILboundary1FP/14, interior0/483; manualV153/244/123/94 so với3GT148/232/127/82. Không tune bằng test.

## Jev prospective H12

Raw input/output và ID validation: [jev_h12_selection.json](jev_h12_selection.json). Request861be323-31f9-4871-9cc6-8685349ad66f;1call,2221input/182outputtokens,provider latency545ms.

Jev chọn ACF voicing hysteresis, relative choice.70, independent fit.78. Explicit none option fit.54 cho thấy vẫn có bất định dù tool none.02. Không có calibration dataset; các probability không phải độ chính xác hoặc chứng minh model sẽ tốt hơn.

Quyết định của agent: giữ hysteresis trong shortlist H12, đo nguyên nhân score/RMS/temporal neighbors trước. Chạy H10/H11 đã đăng ký; gates/code quyết định promotion. Jev không chạy thuật toán hoặc đọc workspace.
