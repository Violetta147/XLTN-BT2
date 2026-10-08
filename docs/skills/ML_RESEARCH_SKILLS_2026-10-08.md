# Bộ skill ML, deep learning và nghiên cứu đã cài

Ngày 08/10/2026; người dùng cho phép “cái gì làm được thì làm luôn đi”. Cài bằng helper chính thức của `skill-installer`, tải các directory ở commit cố định vào `C:/Users/LAPTOP T&T/.codex/skills`. Đây là cài instruction/reference bundles, không phải cài thư viện Python, GPU, dịch vụ trả tiền hoặc chạy training. Codex nhận skill mới ở lượt/chat tiếp theo.

| Skill | Công việc phù hợp | Nguồn |
|---|---|---|
| scikit-learn | Pipeline học máy cổ điển, preprocessing, model selection | K-Dense-AI/scientific-agent-skills |
| pytorch-lightning | Tổ chức mô hình, data loader và training deep learning | K-Dense-AI/scientific-agent-skills |
| experimental-design | Thiết kế thí nghiệm, đơn vị độc lập, blocking và confounding | K-Dense-AI/scientific-agent-skills |
| scientific-critical-thinking | Đối chiếu claim, bằng chứng, bias và giới hạn suy luận | K-Dense-AI/scientific-agent-skills |
| brainstorming-research-ideas | Tạo và sàng lọc giả thuyết nghiên cứu | Orchestra-Research/AI-Research-SKILLs |
| nanogpt | Đọc, xây dựng, thay đổi kiến trúc GPT nhỏ | Orchestra-Research/AI-Research-SKILLs |
| mamba-architecture | Kiến trúc selective state-space và Mamba | Orchestra-Research/AI-Research-SKILLs |
| paper-to-code | Chuyển phương pháp paper thành thiết kế và mã | lingzhi227/agent-research-skills |
| experiment-code | Triển khai, kiểm tra và ghi nhận thí nghiệm | lingzhi227/agent-research-skills |
| ml-pipeline-workflow | Quản lý data/code/config, split, cache và ablation | wshobson/agents |

Các pin đầy đủ, đường dẫn local, SHA256 từng file, snapshot entrypoint gốc và sửa đổi nằm trong [manifest](ML_RESEARCH_SKILLS_2026-10-08.json). Không gọi tài liệu cộng đồng là ý kiến đã xác thực của tác giả thuật toán hoặc researcher được nhắc đến. Số benchmark và API trong reference cần kiểm chứng primary source/runtime khi thực sự dùng.

## Điều chỉnh để dùng trong Codex

- Bảo tồn entrypoint upstream tại `references/upstream-entrypoint.md`; chuyển metadata/tool names riêng nhà cung cấp khỏi top-level frontmatter. Không gán quyền tool từ tên tool của Claude.
- `paper-to-code` và `experiment-code`: sửa đường dẫn `~/.claude/...` thành liên kết tương đối; thay `$0/$1` bằng input tự nhiên; dùng runner phù hợp Windows; liên kết các skill đã cài.
- `experiment-code`: giữ kết quả 0% nếu metric đúng, giữ failure; không bắt tạo hai hình, chạy lại vòng hoàn tất hay retry vô hạn. Synthetic fixture chỉ kiểm correctness, không phải benchmark.
- `mamba` đổi directory thành `mamba-architecture` cho khớp name. Ba tên reference trong entrypoint không tồn tại ở source được thay bằng `architecture-details.md`, `training-guide.md`, `benchmarks.md` thực sự được kèm theo; không giả tài liệu Mamba-2 còn thiếu đã có.
- `ml-pipeline-workflow`: source directory chỉ có SKILL.md, thiếu bảy reference/assets mà entrypoint quảng cáo. Dùng entrypoint local cùng `references/research-pipeline.md` đã viết và kiểm tra; snapshot gốc được giữ. Không dựng lên tài liệu upstream không tồn tại.

## Đã kiểm tra và giới hạn

`skill-creator/scripts/quick_validate.py`: PASS 10/10; name/directory khớp, mọi reference Markdown ở entrypoint và mọi liên kết local Markdown ở entrypoint tồn tại. Manifest ghi hashes của toàn bộ file cài. Đây là kiểm cấu trúc/đường dẫn, chưa là benchmark chất lượng skill, audit mọi mệnh đề hoặc chạy ví dụ GPU.

Không cài optional dependency, không mua premium, không gửi dữ liệu ra dịch vụ, không tạo lịch tự chạy. Quy tắc repository vẫn quyết định phạm vi: BT2 dùng thuật toán tín hiệu/học máy cổ điển, không dùng deep learning; các skill deep learning phục vụ dự án khác hoặc yêu cầu tương lai cho phép DL. Không rerun H00–H63 để thử skill.

Ví dụ yêu cầu dùng sau khi nhận skill: “Dùng experimental-design và experiment-code để đăng ký một ablation trước đo”; “Dùng paper-to-code, pytorch-lightning và nanogpt để triển khai thay đổi kiến trúc theo paper, kiểm shape rồi so baseline trên split cố định”. Ví dụ thứ hai không áp dụng cho BT2 hiện tại.
