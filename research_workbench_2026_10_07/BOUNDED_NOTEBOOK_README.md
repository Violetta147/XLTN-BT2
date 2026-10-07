# Notebook H38: giới hạn bất đồng cao độ

`BOUNDED_PITCH_LOCAL.ipynb` giải thích và tính lại từ WAV train: control AMDF H24 (4 rows), toàn bộ sáu cấu hình H38 (24 rows), và nested choices đã chốt H38 (4 rows). Tổng32 rows. Notebook Praat/REAPER cũ và AMDF gốc giữ nguyên.

H38 giữ cổng V/UV Praat .30, dùng REAPER .9 trong band100/200cents, với trọng số.5/1; ngoài band hoặc thiếu REAPER giữ Praat. Trọng số.5 là trung bình hình học; một octave là1200cents. Grid có control và raw gated REAPER làm ablation. Không sửa octave, trim count hoặc chọn theo file đang chấm. Đồng thuận không chứng minh F0 đúng; LAB không có F0 chuẩn từng khung.

Nguồn tạo: `build_bounded_notebook.py`. Năm code cells đã được thực thi nguyên source bằng Python local; 32rows tính lại từ WAV khớp số đã lưu1e-8. Verify contour stats/MAPE/VUV/fit exclusions, 8nativecalls/PCM/source/binary/params/hashes/status/PNGSVG/layout đã qua; all_files_target_met=false. Thực thi bằng `execute_bounded_notebook.py`: Python exec nguyên code cells với headless display adapter, không Jupyter kernel. Kiểm độc lập bằng `verify_bounded_notebook.py`. Outputs/provenance/verification nằm `results/bounded_notebook_*`, figure `figures/bounded_notebook_H38_components` đã lưu sau thực thi.

H38 runner đã đo và verify riêng ở `H38_REPORT.md`: final fixed100cents/alpha1 có perfile0.560923/0.949165/1.790796/2.192465%; nested0.560923/0.949165/1.790796/3.175722%. Mục tiêu mỗi file≤2% chưa đạt, gateFAIL, không promote. Notebook sẽ tái lập các số này, không mở search mới. Native8calls và no-fitrule; AMDF fit phải giữ riêng file chấm. Không test/Drive/PDF/deep learning/retry Jev.
