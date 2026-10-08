# Muốn dưới2% khi giữ số khung: phần sai số cao độ còn được phép là bao nhiêu?

Phân tích08/10/2026 từ `results/H48_all_files.csv` của **hard170 đã lưu**. Chỉ làm đại số trên các metric cũ, không chạy WAV, đo test mới, sửa nhãn/chuẩn hoặc chọn tham số bằng test. Test đã có lịch sử exposure; kết quả này giúp hiểu ràng buộc metric, không phải một evaluation độc lập mới.

Gọi E_mean, E_std, E_count là các MAPE (%) của F0mean, F0std và F0num cả file. Theo metric BT2:

`Average MAPE = (E_mean + E_std + E_count)/3`.

Nếu giữ nguyên quyết định hữu thanh thì F0num và E_count không đổi. Để Average MAPE **strict<2%**, cần `E_mean + E_std < 6 - E_count`. Nếu mean/std đều khớp chuẩn hoàn toàn, mức Average MAPE thấp nhất về mặt đại số là `E_count/3`. Đây không phải một thuật toán, dự đoán hiệu năng, hoặc F0 chuẩn từng khung.

| Split/file | E_count (%) | Mức thấp nhất nếu mean/std hoàn hảo (%) | Tổng E_mean+E_std phải nhỏ hơn (%) |
|---|---:|---:|---:|
| train/phone_F1 | 0.675676 | 0.225225 | 5.324324 |
| train/phone_M1 | 0.431034 | 0.143678 | 5.568966 |
| train/studio_F1 | 3.149606 | 1.049869 | 2.850394 |
| train/studio_M1 | 3.658537 | 1.219512 | 2.341463 |
| test/phone_F2 đã lưu | 0.456621 | 0.152207 | 5.543379 |
| test/phone_M2 đã lưu | 5.691057 | 1.897019 | 0.308943 |
| test/studio_F2 đã lưu | 4.316547 | 1.438849 | 1.683453 |
| test/studio_M2 đã lưu | 3.448276 | 1.149425 | 2.551724 |

Tất cả tám ngân sách còn dương: **không thể kết luận hướng chỉ sửa pitch là bất khả thi** từ E_count. Tuy nhiên, phone_M2 có ngân sách rất hẹp: tổng hai lỗi mean/std cần<.308943%, trong khi baseline lịch sử có E_mean≈.884189% và E_std≈13.926004%. Chỉ cải thiện một thống kê hoặc vài file train chưa đủ cho mục tiêu chung.

Vì vậy, các vòng pitch-only cần được diễn giải như ablation của estimator, không là bảo đảm all8. Nếu thử thay quyết định hữu thanh/count thì phải đăng ký một giả thuyết riêng và báo V/UV/SIL: giảm E_count bằng cách loại khung có thể làm mất LAB V, còn thêm khung có thể làm tăng false_voiced_sil. Teacher3GT F0num không đồng nghĩa tổng LAB V, nên không được coi thay count theo target là sửa nhãn đúng.

Sau H66, hướng đáng nghiên cứu tiếp là mô hình colored-noise nhiều độ trễ hoặc một bước joint/iterative estimation có nguồn, với nuisance-fit/độ ổn định được kiểm; đồng thời phải kiểm gate phone_F1 std, không chỉ minimax. Đây là backlog, **chưa đăng ký/đo H67**. Không chỉnh threshold/cap/search sau kết quả H66 hoặc rerun các family đã hoàn tất.

Code: `analyze_count_budget.py`; output: `results/H66_fixed_count_budget.csv` và `H66_count_budget_audit.json`, có source/outputhash và kiểm công thức cho cả8rows. Số này chỉ áp dụng đúng mask/count hard170 từ H48, không là lower bound cho mọi pipeline.
