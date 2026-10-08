# H62 — đặc trưng khớp họa âm chưa cải thiện chung

H62 so sánh cùng learner logistic với bốn đặc trưng cũ và sáu đặc trưng có thêm mức khớp họa âm. Prereg `b2af88eb635405a838d596d64b1b853a4ba1484c` đã push và xác minh SHA remote trước đo. **Final và bốn outer folds đều chọn hard170. Ba gate giảm MAPE không đạt; không promote và không đo test mới.** Baseline giữ 4/4 train dưới 2%; kết quả test đã lưu vẫn 0/4. Mục tiêu cả tám file chưa đạt.

| File train held-out | baseline | base4 recovery | base4 reject .1 | base4 reject .25 | coherence6 recovery | coherence6 reject .1 | coherence6 reject .25 |
|---|---:|---:|---:|---:|---:|---:|---:|
| phone_F1.wav | 0.340080 | 13.870675 | 13.870675 | 13.870675 | 12.330039 | 12.330039 | 12.240090 |
| phone_M1.wav | 0.776151 | 8.823743 | 8.580106 | 8.348966 | 8.588018 | 8.501624 | 8.118297 |
| studio_F1.wav | 1.473576 | 1.291706 | 1.291706 | 0.502753 | 1.028830 | 1.028830 | 0.768353 |
| studio_M1.wav | 1.909923 | 4.149865 | 4.149865 | 4.149865 | 4.454627 | 4.454627 | 4.454627 |

Các giá trị là Average MAPE (%) so với teacher3GT. Thêm coherence giúp giảm một số lỗi trên hai file phone và ở studio_F1 khi chỉ recovery, nhưng studio_M1 tăng 4.149865→4.454627%. Với rejection .25, studio_F1 dùng base4 đạt 0.502753%, tốt hơn coherence6 0.768353%; cả hai đều không thắng trên toàn bộ file. Đây là ablation trực tiếp cho thấy thêm đặc trưng không tạo lợi ích nhất quán. Không chọn mô hình theo tên file hoặc môi trường thu âm.

Hai đặc trưng mới đo phần năng lượng được mô hình ba họa âm giải thích và phần tăng thêm khi dùng năm họa âm. Mô hình khớp từ WAV tại anchor hiện có, không dùng LAB để tạo đặc trưng. Logistic học LAB V so với UV/SIL của đúng fit pool; điểm này không phải xác suất chắc chắn rằng một khung có F0 chuẩn của thầy. Khung V giữ lại vẫn dùng pitch baseline; recovery dùng ACF bound200 của H56. Thay đổi count có thể đồng thời đổi mean/std. H62_fixed_label_audit.csv ghi rõ recovered/removed V/UV/SIL; H62_changed_cases.csv lưu các khung đổi quyết định, không gọi pitch ước lượng là frame ground truth.

Điểm Brier giảm trên cả bốn file khi thêm coherence: phone_F1 .034816→.032672; phone_M1 .044968→.037172; studio_F1 .019251→.018575; studio_M1 .028807→.024395. Vì vậy đặc trưng mới có thông tin hữu ích theo nhãn LAB, nhưng chưa tạo pipeline đạt thống kê F0. Ở q=.25, phone_M1 giảm recovery nhầm UV từ3 xuống0, vẫn hồi phục5V và loại4V; Average MAPE vẫn8.118297%, cao hơn baseline. studio_M1 hồi phục5V→6V nhưng count/mean/std chung xấu hơn. Những đánh đổi này giải thích vì sao không promote dù Brier cải thiện.

Đã đo 140 nhóm train, 22 logistic fits từ 11 fit pools ×2 bộ đặc trưng, 112 inner traces, 28 fixed LOFO và 24 summary rows. Chọn cấu hình theo minimax lỗi file trong inner folds, rồi mean và ID; có guard F1/recallV/SIL và tám gate hiện hành. Grouped nested dùng bốn outer files và ba inner files; không random split các khung. Solver LBFGS là deterministic, không giả ba seed thành ba lần học độc lập. Ba seed11/29/47 chỉ dùng cho18 synthetic noise fixtures trước đo.

Verifier PASS: QR độc lập đối chiếu đặc trưng từ PCM; kiểm grid/LAB/3GT, scalar response, scaler, đúng membership và hash của fit design; gradient logistic trên các mô hình đã serialize; masks, pitch, metric, inner traces, selection và gate. Không refit optimizer độc lập; PEZS cũ được dùng lại từ cache H50 đã xác minh. Điểm Brier theo file ở H62_held_score_quality.csv, không thay metric chính bằng Brier để gọi thành công.

H60/H61/H62 đều chưa thắng nên baseline và notebook đã nộp giữ nguyên. Không đo thêm test sau các vòng fail này, không sửa nhãn hoặc reference. Test đã có lịch sử exposure, nested cũng exploratory; chưa có bằng chứng quy toàn bộ nguyên nhân cho thiếu data, GT hoặc test. Hình LOOP_H60_H62_train_matrix.png và bảng tổng hợp LOOP_H60_H62_SUMMARY.csv chỉ chứa số đã đo, không có số test mới.

Theo yêu cầu cuối của người dùng, hoàn tất kiểm tra và bàn giao rồi dừng loop tại H62. Không khởi động H63, không schedule hay retry Jev. Chat mới đọc START_NEXT_CHAT.md; tiếp tục chỉ theo yêu cầu mới của người dùng. Bài phân đoạn mới vẫn đứng sau cải thiện BT2, chưa chuyển bài.
