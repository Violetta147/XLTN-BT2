# Điểm nối tiếp cho chat mới — 07/10/2026

Ngày 07/10/2026, người dùng đã yêu cầu tiếp tục: **cải thiện BT2 tìm F0 trước, rồi làm bài phân đoạn mới thầy giao trong XLTN-BT1-BO-SUNG**. Yêu cầu mới thay trạng thái dừng trước đó; không schedule. Giữ mục tiêu mỗi file Average MAPE≤2%, kiểm tra các gate và notebook chạy thực; audit nguồn chỉ phục vụ mục tiêu này.

## Đọc tối thiểu

1. `AGENTS.md` của workspace XLTN và repository XLTN-BT2.
2. File này và `research_workbench_2026_10_07/STATE.md` (đọc phần mới nhất, không quét lại toàn lịch sử).
3. Với câu hỏi gần nhất về chất lượng dữ liệu: `research_workbench_2026_10_07/DATASET_QUALITY_REPORT.md` và `results/dataset_quality_verification.json`.
   Truy nguồn đã được bổ sung ở `research_workbench_2026_10_07/DATASET_PROVENANCE_REPORT.md` và `results/dataset_provenance.json`: 8 WAV trùng byte bản GitHub `dthle/TinHieuHuanLuyen`, LAB gốc trùng nội dung sau chuẩn hóa xuống dòng; lịch sử người dùng nhận train 3GT từ thầy và cache local đã đối chiếu. Hai phiên bản LAB đổi cả mean/std, không chỉ thêm count. Chưa rõ tác giả thu âm hoặc quy trình tạo reference; chỉ đọc log lịch sử, không truy cập lại Drive.
4. Nếu tiếp tục H44: `H44_REGISTRATION.md`, source và precheck cùng workbench.

## Trạng thái đã xác minh

- Repository local: `C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2`.
- Nhánh `codex/train-mape-investigation`; remote `https://github.com/Violetta147/XLTN-BT2.git`. Không merge main. Mỗi thay đổi đã kiểm tra phải commit/push riêng, xác minh HEAD remote.
- Mốc kết quả trước bàn giao: `29f712a2b6ccb3cd768b78f63a7d3a62d36c1ba7`. H42/H43 notebook đã chạy lại từ WAV và kiểm tra; không chạy lại các vòng hoàn tất.
- Mục tiêu là **mỗi file Average MAPE ≤2%**, trung bình ba lỗi tương đối F0mean/F0std/F0num; không chỉ mean bốn file. Giữ riêng std/count, V/UV/SIL và các gate đã đăng ký.
- H41 nested bốn file đều ≤2%, nhưng gate std phone_F1 FAIL. H43 fixed170 bốn file đều ≤2%, nhưng nested studio_M1 chọn140 rồi đạt 2.523880%; target FAIL dù tám gate PASS. Chưa có cùng pipeline đạt toàn bộ mục tiêu và gate. Không thay frozen baseline hoặc notebook gốc.
- Các kết quả nested vẫn exploratory: chỉ bốn train đã được xem nhiều vòng. Test đã xem lịch sử; QA dữ liệu đọc test chỉ mô tả, không dùng để chọn cấu hình.

## H44 đang nối tiếp — chưa có kết quả BT2 ở mốc đăng ký

Rule chuyển mềm AMDF25/40ms, runner và verifier đã rà; whitelist verifier được bổ sung H44 đúng objective minimax. Synthetic precheck PASS; `uses_BT2_WAV=false`, không native call mới. Đã tạo `H44_REGISTRY.json` gồm 9 options; chốt source/registry/precheck bằng commit/push và kiểm tra remote trước benchmark.

**Ở mốc đăng ký này chưa chạy benchmark H44, chưa có MAPE H44 hoặc notebook H44.** Không suy diễn synthetic PASS thành cải thiện dữ liệu thật.

Tiếp theo: chạy H44 một lần theo registry đã commit/push, verify độc lập, giữ failure, cập nhật báo cáo/figures/STATE và commit/push. Nếu kết quả đạt mục tiêu và gate, hoàn thiện notebook chạy thực trước chuyển sang bài mới. Không chạy lại `prepare_h44.py` tùy tiện vì generator đã tạo file.

## Câu hỏi gần nhất: kiểm tra chất lượng dataset

Đã có audit thực: 8 WAV/16 LAB, tổng 26.124694s; WAV giải mã được/mẫu hữu hạn; không mẫu chạm rail hoặc ≥99% full scale; nhãn không lỗi parse/bounds/gap/overlap; một số đuôi ngắn chưa phủ nhãn. Không thấy duplicate byte/native PCM giữa các cặp. Những kiểm tra này không chứng nhận nhãn ngữ âm hoặc F0 đúng.

Hai nguồn thống kê F0 có giá trị khác nhau và chưa đủ quy trình tạo reference. LAB hiện có mean/std/count cả file và V/UV/SIL theo đoạn, **không có F0 chuẩn từng timestamp**. Metadata speaker/session chưa xác minh; dataset rất nhỏ. Bước tiếp theo hợp lý nếu người dùng yêu cầu: giải thích báo cáo QA, đối chiếu nguồn reference và rà nghe/biên nhãn; không tự sửa GT hoặc loại file khó để hạ MAPE. Câu trả lời giải thích QA chưa gửi vì người dùng yêu cầu dừng.

## Giới hạn giữ nguyên

- Local only, tuyệt đối không Google Drive; không deep learning, không PDF hoặc extract PDF paper.
- Paper knowledge dùng HTML/abstract/mã tác giả, ghi đúng cấp độ nguồn. Không cần đọc lại toàn review nếu chưa có vòng literature mới.
- Jev/System One đã lỗi evaluation H32; nhánh MCP dừng, **không discovery/evaluation/retry tự động**. Chỉ thử lại khi người dùng yêu cầu trực tiếp. Không gọi Jev để tính toán chính xác hoặc làm ground truth.
- Gemini/Jev chỉ phản biện bằng chứng, không thay phép đo hoặc quyền người dùng. Không cần gọi ở mọi bước.
- Giữ mọi thất bại, các notebook gốc, WAV/LAB và frozen baseline. Không tune test, không bịa metric, không gọi contour thuật toán là reference F0.

## Prompt ngắn để dán vào chat mới

> Làm việc trong XLTN/XLTN-BT2, nhánh codex/train-mape-investigation. Đọc AGENTS.md, START_NEXT_CHAT.md và phần mới nhất của research_workbench_2026_10_07/STATE.md trước. Không chạy lại thí nghiệm đã hoàn tất. Trước tiên giải thích kết quả kiểm tra chất lượng dataset từ DATASET_QUALITY_REPORT.md. H44 mới có bản nháp/synthetic precheck, chưa đăng ký hoặc chạy BT2. Chỉ tiếp tục thí nghiệm khi tôi yêu cầu; giữ giới hạn local/no Drive/no deep learning/no PDF/no tự retry Jev.
