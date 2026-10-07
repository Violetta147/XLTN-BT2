# Đọc và đối chiếu H51 trên máy local

Mở [H51_REPORT.md](H51_REPORT.md) để xem ma trận đầy đủ, [H51_INTERPRETATION.md](H51_INTERPRETATION.md) để hiểu lỗi, hoặc [H51_RESULTS_LOCAL.ipynb](H51_RESULTS_LOCAL.ipynb) để đọc kết quả theo từng phần. Notebook chỉ tính bảng từ các output đã kiểm tra; không tự chạy lại hàng nghìn lượt học. Các code cell được chạy nguyên source bằng Python `exec` và lưu stdout, không phải một phiên Jupyter kernel.

Ma trận gồm 31 tổ hợp khác rỗng từ P/E/Z/S/M, năm learner và ba seed. P=độ tuần hoàn, E=năng lượng tương đối, Z=ZCR, S=tỷ lệ phổ tần số cao, M=13 MFCC. Guard khôi phục và pitch dùng chung; GMM không đọc LAB trong fit/mapping nhưng validation chọn cấu hình vẫn có nhãn. Không coi toàn bộ pipeline là bỏ mọi thông tin giám sát.

Logistic là mô hình phân lớp tuyến tính; SVM tìm biên phân lớp, ở đây dùng kernel RBF; kNN dựa trên năm láng giềng gần nhất; RF là rừng cây quyết định; GMM là mô hình hỗn hợp phân phối chuẩn dùng phân cụm. MFCC mô tả phân bố năng lượng phổ theo thang mel, không phải F0 chuẩn. Các learner học nhận hữu thanh; cao độ khung khôi phục vẫn do ACF tính. Chưa có nhãn F0 chuẩn từng khung trên BT2 để học hồi quy cao độ trực tiếp.

Các lệnh dưới đây ghi lại quy trình **đã thực hiện**, chạy từ repository local XLTN-BT2. Các runner từ chối ghi đè experiment đã hoàn tất; giữ các kết quả thất bại. Một thí nghiệm mới cần run ID/registry mới.

```powershell
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/check_voicing_matrix.py
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/voicing_matrix.py register
# Commit/push source + registry + precheck, đối chiếu HEAD remote trước đo.
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/voicing_matrix.py train
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/verify_voicing_matrix_v2.py train
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/interpret_voicing_matrix.py
# Commit/push/remoteverify H51_FROZEN_SELECTION.json và verified train outputs trước external.
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/voicing_matrix.py external
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/verify_voicing_matrix_v3.py external
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/report_voicing_matrix.py
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/build_voicing_results_notebook.py
```

Verifier v1 đã lỗi đọc cột `repeat` do trùng tên method của pandas. Source v1, registry và mọi measurement giữ nguyên; v2 sửa truy cập cột và đã kiểm lại đầy đủ train. Khi đối chiếu KEELE, helper độc lập gặp đỉnh tương quan đều âm; v3 external thêm điều kiện peak dương giống quy ước pipeline và kiểm lại đầy đủ external. Xem [hồ sơ sửa](H51_VERIFICATION_REPAIR.md). Receipt ghi hashes của bộ kiểm tra thực tế; không đổi số liệu hoặc loại file gây lỗi.

Môi trường đã đo: Python3.13.11, NumPy2.4.3, SciPy1.17.1, scikit-learn1.8.0, pandas3.0.1, BLAS thread1. Không dùng deep learning, Drive, Jev hoặc PDF. Runtime và hashes nằm trong experiment/verification JSON. Version của tài liệu API online có thể khác bản đã cài; cấu hình dùng các tham số explicit của runtime local.

Input: WAV/LAB train/test local, file3GT trong research_3gt_2026_10_05, verified H50 features, H46 noise waveform/member bank, H48 test baseline và H49 KEELE native baseline/reference. Raw KEELE và một số nguyên liệu không nằm trong Git; manifest/checksum được lưu trong results/H49_dataset_manifest.json và H51_REGISTRY.json. Notebook đọc kết quả không cần chạy lại native engine hoặc tải corpus. Kiểm tra tái lập measurement cần đủ nguyên liệu đúng hashes; không chạy lại acquire của H49 để ghi đè manifest đã đăng ký.

K-fold giữ group=file; không random split frame. Ba seed chỉ thực sự đổi RF/GMM; các learner xác định được cache. Chọn minimax qua file và seed, không chọn seed đẹp. Noise/permutation/cross-condition không tham gia chọn cấu hình. Test/KEELE được chấm sau khóa cấu hình nhưng đã có lịch sử exposure, nên vẫn là đánh giá mô tả/thăm dò. Không có F0 chuẩn từng khung trên BT2.

Phạm vi và hướng chưa thuộc ma trận này: [EXPERIMENT_COVERAGE.md](EXPERIMENT_COVERAGE.md). Không tự sửa nhãn hoặc ba thống kê của thầy. Giữ notebook đã nộp `BT2_ACF_best_no_energy_set.ipynb` cùng toàn bộ baseline gốc.
