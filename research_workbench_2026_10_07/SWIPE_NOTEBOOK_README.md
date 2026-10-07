# Đọc notebook SWIPE′ và Praat

`SWIPE_PRAAT_LOCAL.ipynb` được tạo riêng để giải thích và tính lại từ WAV các vòng đã hoàn tất. Nguồn được commit/push ở7ecffec trước chạy; **năm code cells đã chạy nguyên source,44 rows tính từ WAV khớp1e-8 và verifier PASS**. Không phải Jupyter kernel. Notebook AMDF và reference cũ giữ nguyên.

Đọc từ trên xuống: thuật ngữ và ground truth → cấu hình fixed → lựa chọn nested → figures → provenance. Fixed là chấm một cấu hình đã chốt. Nested chọn cấu hình bằng ba file khác rồi chấm file được giữ lại. Không chọn cấu hình theo chính kết quả của file đang chấm.

Số dòng đã kiểm tra: control AMDF H24 bốn dòng, H34 fixed20, H35 fixed12 và nested của hai vòng tám dòng, tổng44. Mọi dòng khớp số liệu đã lưu ở mức1e-8. Ba figures PNG/SVG hiển thị thành phần lỗi H34/H35 và V/UV/SIL của H34, hash/header/XML và layout đã kiểm tra; không dùng metric paper thay số liệu BT2. Provenance gồm32 native calls và44 fit/scoring logs; các file held được loại khỏi pool. Receipt: `results/swipe_notebook_verification.json`.

H34 khác H35 ở quyết định hữu thanh: H34 dùng strength SWIPE′ cho cả V/UV và F0; H35 giữ mask Praatfiltered.30 rồi lấy F0 SWIPE′ ở vị trí có output hợp lệ. Nếu thiếu SWIPE, giữ F0 Praat; số fallback lưu trong `results/H35_swipe_usage.csv`. Không cắt số khung theo ground truth, chọn theo giới tính hoặc tên file.

Average MAPE mỗi file là trung bình ba lỗi phần trăm mean/std/count. F0std dùng ddof=0. Một cấu hình có mean bốn file dưới2% vẫn có thể không đạt **mỗi file≤2%**. LAB có thống kê cả file và nhãn V/UV/SIL theo đoạn, không F0 chuẩn từng khung. Vì vậy không gọi contour này là ground truth hoặc tính chính xác pitch từng khung.

Chạy từ repo bằng Python local đã có numpy/scipy/sklearn/matplotlib/pandas/Pillow và portable binaries đã lưu trong SPTK_NATIVE_SETUP.md:

```powershell
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/execute_swipe_notebook.py
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/verify_swipe_notebook.py
```

Executor chạy nguyên source từng code cell bằng Python `exec` và display adapter, **không phải Jupyter kernel**. Output/error được lưu vào notebook, không sửa cell để làm khớp metric. Verifier tính lại mean/std/count/MAPE và V/UV từ contour, kiểm LAB/WAV/source/binary/call provenance, held exclusions, status và figures. Chỉ train local, không test/Drive/deep learning/PDF/MCP retry. Nested vẫn exploratory do lịch sử đã xem bốn file.
