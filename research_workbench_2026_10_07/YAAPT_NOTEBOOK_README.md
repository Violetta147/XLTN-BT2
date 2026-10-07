# Notebook local YAAPT/AMDF

YAAPT_AMDF_LOCAL.ipynb tính lại từ WAV các cấu hình đã đăng ký: H24 AMDFcontrol4 + H40fixed16 + nested4 =24 rows. Source phải commit/push trước replay; không grid hoặc lựa chọn mới. Năm code cells; execute_yaapt_notebook.py chạy nguyên cell source vớiPythonexec/headlessdisplay, không Jupyter kernel. Giữ notebook gốc/frozen và không đọc test.

Lệnh local: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/execute_yaapt_notebook.py, rồi verify_yaapt_notebook.py. Script lưu lỗi trong notebook nếu cell thất bại; không tự rerun bỏ lỗi. Verifier độc lập statsddof0/MAPE/LAB/VUV/hash/calls/params/fitexclusions/choices/status/PNGSVG. Các nguồn tại YAAPT_SOURCE_NOTE.md, kết quả tại H40_REPORT.md và H40_ERROR_ANALYSIS.md. Groundtruth là file-stat/nhãn đoạn, không F0 chuẩn từng khung. Fixed không thay nested, mỗi file≤2% chưa đạt khi benchmarkH40.

Hiện đây là source chờ execution. Sau replay chỉ ghi đã chạy/verified nếu đủ receipt và kiểm tra layout.
