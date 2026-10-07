# Đọc notebook REAPER, Praat và AMDF

`REAPER_PRAAT_LOCAL.ipynb` tính lại từ WAV các vòng đã đăng ký H36/H37 và control AMDF H24. Nguồn đã commit/push5fb2394 trước chạy; **năm code cells chạy nguyên source,44 rows tính từ WAV khớp1e-8 và verifier PASS**. Không phải Jupyter kernel. Các notebook gốc, SWIPE và reference cũ giữ nguyên.

H36 dùng whole REAPER, gồm residual và đường chọn pitch/voicing. H37 giữ mask V/UV Praat rồi dùng REAPER ở các vị trí có output hợp lệ; nếu thiếu, giữ F0 Praat. Không sửa octave, ép count theo ground truth hoặc chọn algorithm theo giới tính/file. REAPER cost tăng có chiều khác SWIPE strength: khuyến khích thêm V, không phải xác suất đúng.

Notebook đã kiểm chứng44 dòng: H24control4, H36fixed20, H37fixed12 và nested8. Fixed là chấm cấu hình chốt; nested chọn bằng ba file khác rồi chấm held file. Lịch sử n4 khiến nested vẫn exploratory. Verifier tái lập mean/std/count/MAPE và V/UV từ contour, kiểm LAB/WAV/source/fullvendor/binary/native input/call hashes,32 native calls/44 fit logs, held exclusions và ba figures PNG/SVG. Đã kiểm header/XML/source hash và layout. Receipt: `results/reaper_notebook_verification.json`; mọi mục tiêu từngfile≤2% vẫn false.

Average MAPE là trung bình lỗi phần trăm mean/std/count của một file, std dùng ddof=0. LAB có file-stat và nhãn loại đoạn, chưa có F0 chuẩn từng khung. Giảm lỗi std studio_M1 không đủ để đạt mỗi file≤2% khi phone_F1 còn xấu. Không dùng số liệu paper thay số liệu BT2.

Chạy từ repo với Python local có numpy/scipy/sklearn/pandas/matplotlib/Pillow và portable binary đã lưu:

```powershell
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/execute_reaper_notebook.py
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/verify_reaper_notebook.py
```

Executor dùng Python `exec` nguyên source từng cell và display adapter, **không phải Jupyter kernel**. Error/output được giữ trong notebook. Chỉ local train, không test/Drive/deep learning/PDF/MCP retry. Xem REAPER_SOURCE_NOTE.md cho mức đọc README/manual/code, raw wholezero failures và half-frequency probe; không claim full paper hoặc mọi synthetic pitch đều đúng.
