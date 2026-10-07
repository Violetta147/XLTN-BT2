# Notebook AMDF/Praat local

`AMDF_ANCHOR_LOCAL.ipynb` tính lại từ WAV các cấu hình đã đăng ký: 4 dòng control AMDF H24, 40 dòng fixed H41 và 4 dòng nested H41, tổng cộng 48 dòng. Fixed là dùng cùng một cấu hình trên bốn file. Nested là giữ riêng một file, chọn cấu hình bằng ba file khác rồi chấm file được giữ riêng.

H41 giữ quyết định hữu thanh của Praat và dùng các đáy NAMDF để tinh chỉnh cao độ. NAMDF là AMDF chuẩn hóa theo biên độ trên phần chồng lấp. Cấu hình được chọn trong benchmark là cửa sổ 25 ms, khoảng tìm kiếm 200 cents quanh cao độ Praat; 1200 cents tương ứng một octave, tức tần số gấp đôi. Notebook tái lập lựa chọn đã lưu, không mở grid hoặc chọn best bằng chính file đang chấm.

Benchmark đã đạt Average MAPE≤2% trên từng file train giữ riêng, nhưng chưa qua tiêu chí F0std của phone_F1: lỗi std tăng so với control. Vì vậy chưa thay frozen baseline. Average MAPE trung bình ba lỗi phần trăm của mean/std/count, không phải lỗi F0 từng khung; LAB hiện chứa thống kê cả file và nhãn V/UV/SIL theo đoạn.

Năm code cells phải được commit/push trước replay. Executor chạy nguyên source từng cell bằng Python exec với bộ hiển thị headless, không phải Jupyter kernel. Lệnh:

```
C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/execute_amdf_anchor_notebook.py
C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/verify_amdf_anchor_notebook.py
```

Source b05027d đã push và xác minh trước replay. Cả năm code cells đã chạy thành công; verifier kiểm tra đủ 48 dòng, contour/statistics/MAPE/VUV, nguồn, native binary/calls, fit exclusions, choices và status. Receipt: `results/amdf_anchor_notebook_verification.json`; execution log giữ đầy đủ. Figure PNG/SVG được kiểm tra cấu trúc và bố cục PNG được xem trực tiếp. Đây là Python exec/headless display, không phải một lần chạy Jupyter kernel. Curves của replay lưu với prefix riêng, giữ nguyên curves benchmark. Chỉ local train, giữ notebook gốc và frozen, không đọc test.

Đọc `H41_REPORT.md`, `H41_ERROR_ANALYSIS.md` và `AMDF_ANCHOR_SOURCE_NOTE.md`. Bài Aligned AMDF mới được đọc abstract HTML; H41 không phải tái hiện chính xác AAMDF của paper. Workflow Scientific Agent Skills đã được trích dẫn trong tài liệu nguồn; không extract PDF. Bốn file đã được xem nhiều lần khiến nested vẫn là nghiên cứu thăm dò, chưa chứng minh tổng quát hóa trên dữ liệu mới.
