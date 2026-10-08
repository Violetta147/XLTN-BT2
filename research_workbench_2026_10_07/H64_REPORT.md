# H64 — dừng ở kiểm tra synthetic

H64 global HPS3/5: **precheck FAIL, chưa đo bất kỳ file BT2 train/test nào**, không tạo H64_REGISTRY.json hoặc train receipt. Design và source được viết trước fixture; precheck là điều kiện đầu vào, chưa phải prereg commit cho phép đo BT2. Accepted `hard170` và notebook đã nộp giữ nguyên. Không rerun H00–H63.

Lệnh duy nhất: `C:/Users/violet/miniconda3/python.exe -X utf8 research_workbench_2026_10_07/global_hps_experiment.py precheck`, ngày08/10/2026, local CPU. Process exit1 tại assertion `Precheck failed; saved evidence; no BT2 measurement allowed`. JSON đầy đủ: `results/H64_precheck.json`. Sau lỗi chỉ thêm guard chống chạy lại precheck đã hoàn tất; không đổi algorithm hoặc threshold và không chạy lại fixture.

36 fixtures noise harmonic tổng hợp, fs16k/44.1k ×seed11/29/47 ×order3/5 ×F0 90/200/320. 30PASS,6FAIL: cả6 order5/F0=90Hz (mọi fs/seed) đều lỗi435.084095cents, tương ứng cực đại tại70Hz thay90Hz. Ngưỡng đã định<100cents không được nới. Mọi fixture vẫn khớp DFT trực tiếp toàn grid/score/argmax và gain/DC invariance; zero spectrum giữanchor đúng. Đây là giới hạn objective/window trên fixture này, không bằng chứng lỗi FFT triển khai, không kết quả accuracy trênBT2.

Order3 riêng có18/18fixturePASS. Dữ kiện này chỉ cho phép đề xuất một family mới chỉ cóorder3; không đổi H64 đã thất bại thànhPASS hoặc bỏ6failure khỏi báo cáo. Nếu đăng ký family mới, giữ hash của precheck và chỉ tái dùng18fixturePASS, không đo lại fixture hay H64.

Người dùng cung cấp khả năng chạy notebook Colab giúp nếu GPU local không đủ. H64 không thiếu GPU; GPU không giải quyết kiểm tra objective này. BT2 tiếp tục tuân thủ no deep learning và khôngGoogleDrive; quyền hỗ trợGPU dành cho nhu cầu được phép thực tế, không tạo thêm trainingDL tạiBT2.
