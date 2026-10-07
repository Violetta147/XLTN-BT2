# Đọc và triển khai REAPER không qua PDF

Câu hỏi hẹp: pipeline residual/epoch tracking có sửa được std/count còn khó trên BT2 mà giữ V/UV/SIL? Đây là nối tiếp engineering review đã lưu, không một systematic review mới hoặc thêm các study độc lập.

Đã đọc ngày07/10/2026: [README của David Talkin](https://github.com/google/REAPER), [manual SPTK pitch](https://sp-nitech.github.io/sptk/latest/main/pitch.html), wrapper SPTK và vendor epoch_tracker.cc ở pin0ebff5a. Query là mở trực tiếp hai URL chính thức và API commit-master/author-source; requests/timestamp/hash ở results/reaper_author_source_discovery.json. Không search/full-text extraction PDF, không giả có journal DOI. Record REAPER trong literature_records.json là software, không paper; không đổi review/citation receipt cũ.

Từ README: residual dự đoán tuyến tính và tương quan chuẩn hóa tạo evidence; các điểm đóng thanh môn tạo lattice ứng viên, sau đó chọn đường bằng dynamic programming. Từ wrapper thực chạy: `-t2` đặt unvoiced_cost; highpass=True, Hilbert=False; input castint16; output được resample rồi giữ ceil(N/hop). Mốc output0 và endpoint padding theo implementation. Vì đây là whole pipeline, kết quả BT2 không chứng minh riêng filter hoặc residual là nguyên nhân cải thiện.

Twelve raw synthetic checks cho thấy giới hạn: all-zero native lỗi noresidualpeaks; tonehaiharmonic 44.1k/cost1.2 trả nửa frequency; cost.3 có thể abstain. Không đổi pitch của tone để làm probe khớp. Adapter xử lý riêng **toàn input bằng0** trước native, không xử lý RuntimeError chung và không đổi các khung silence trong một file có speech. Eight adapter checks tonegiàuharmonic/zero×fs×cost.9/1.5 qua; đây là transport/known-signal checks, không độ chính xác trên BT2.

Workflow dùng [literature-review1.11 local](../.agents/skills/literature-review/SKILL.md), subset instructions/references, không optional paid CLI/scripts/dependencies. Tham khảo software methodology: Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026), *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*, [arXiv:2609.00065](https://arxiv.org/abs/2609.00065), [DOI](https://doi.org/10.48550/arXiv.2609.00065). Metadata live kiểm07/10: v2, revised02/09/2026; đây là workflow reference, không evidence REAPER accurate.

H36_REGISTRATION.md chốt giả thuyết/cost grid/adapter/gates trước đo. Nếu benchmark thất bại vẫn giữ kết quả, không auto-promote. File-stat LAB và V/UV/SIL chưa cung cấp F0 chuẩn từng khung; không sửa thống kê hoặc dùng held-label để ép MAPE≤2%.
