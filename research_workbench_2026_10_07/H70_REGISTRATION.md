# H70 — loại khung năng lượng thấp từ pYIN 25 ms đã lưu

Đăng ký ngày 09/10/2026. Rollback `dc6b265de387544ad897d0f787bc77c15562bf03`. Người dùng yêu cầu tiếp tục và trả lời theo prose style. Không chạy lại H00–H69 hoặc R01/R02; không gọi pYIN mới. Đây là bước lọc mới trên cache H69 `(2,8)`, chưa được đo trước đăng ký này.

Giả thuyết: các khung SIL mà prior `(2,8)` dự đoán hữu thanh có năng lượng thấp hơn tiếng nói. Một ngưỡng năng lượng tương đối thống nhất có thể giảm count dư ở studio mà giữ các khung phone đã phục hồi. Chỉ thay bước loại khung; giữ nguyên F0 của mọi khung còn lại, prior, temporal decoding, dải 70–400 Hz, phiên bản runtime, dữ liệu, metric và cửa sổ. Không cắt theo F0/mean/std chuẩn, không dùng mask Praat hoặc chọn theo tên file.

Năng lượng là RMS sau khi trừ mean từng cửa sổ thực sự 25 ms, bước 10 ms, không padding/resampling. Chuẩn hóa bằng p95 RMS của toàn file đó, quantile nội suy tuyến tính, mẫu số tối thiểu 1e-12. Chuẩn hóa này không dùng nhãn, không lấy thông tin từ file khác; cần toàn file và không phải mô hình streaming. Quy ước số mẫu Python round giữ từ H69 (400/160 hoặc 1102/441). Giữ khung nếu pYIN đã dự đoán V và relative_RMS >= q. Loại khung thì đặt F0=NaN; không sửa pitch hoặc thêm khung mới.

Bảy giá trị q cố định: 0, .01, .02, .04, .08, .16, .32. q=0 tái sử dụng raw pYIN `(2,8)` như đối chứng cached; hard170 là đối chứng nghiên cứu lịch sử không tuân thủ cửa sổ25ms. Tổng32 nhóm metric (8 cached controls và24 nhóm có bước lọc mới),128 inner traces,24 summary. Không suy luận native mới hoặc supervised fitting. Phân tích mô tả năng lượng theo LAB và khung loại được thực hiện cùng vòng, sau prereg; không dùng nó để thay grid của H70 sau đo.

Precheck chỉ tín hiệu tổng hợp ở16k/44.1kHz: RMS/quantile so phép tính scalar độc lập, bất biến gain/DC trong fixture cao hơn floor, zeros hữu hạn, boundary >=, số mẫu và lưới thời gian. Nếu thất bại thì giữ và dừng H70, không nới tiêu chí. Đây là kiểm tra toán học bước lọc, không chứng minh accuracy của pYIN hay tiếng nói thật.

Chọn theo file, bốn outer / ba inner / finalbốnfile; minimax worst MAPE → mean → ID cùng finite/F1/recall-V không giảm quá.01 và SIL tăng tối đa1 so hard170. Giữ nguyên tám gate lịch sử. Báo thêm lựa chọn hữu hạn minimax chỉ trong bảy pipeline25ms như chẩn đoán, không bỏ điều kiện gate để promote. Cấu hình cuối thống nhất trên bốn train được báo riêng; outer có thể chọn khác vì không nhìn heldfile. Không ghép cấu hình theo filename.

Không đo test khi chưa eligible, khóa/push/remoteverify và đáp ứng cửa sổ thực sự25ms. Mục tiêu vẫn từngfile trongcả8file AverageMAPE<2%; test đã xem lịch sử, nested vẫn exploratory với bốn filetrain và nhiều lần chọn. Nếu gateFAIL, giữ failure và baseline lịch sử, không chuyển nó thành notebook nộp tuân thủ25ms.

Verifier độc lập tính scalar RMS, linearp95, ngưỡng, mask, pitchgiữ, metrics, count khungloại/nhãn/timestamp, cachedcontrol parity, inner/summary/selection/gates và hashes. pYIN inference gốc dựa mãlibrosa đãkhóa, không tínhlại trong vòng này. Registry bảo vệ source/runtime/dữ liệu/GT/notebook từH69, các outputsH69 và sourcesH70. Commit/push/xác minhremote trước đọc BT2 để đo bước lọc.

Dùng experimental-design; tham chiếu Kassis,T., Agarwal,V., He,Y., Patel,D., & Brueckner,A.M. (2026), [Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents](https://arxiv.org/abs/2609.00065), DOI10.48550/arXiv.2609.00065. Metadata HTML v2 kiểm tra09/10/2026; không đọc PDF. Không Drive, deep learning, Jev, Colab, lịch tự động hoặc sửa notebookgốc.
