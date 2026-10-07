# H46 — Augmentation trong fit pool của ensemble

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | lofo | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | nested | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | train | 1.12493 | 0.586176 | 0.809907 | 1.97871 | 1.07062 | 0.19555 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | lofo | 1.12493 | 0.586176 | 0.809907 | 1.97871 | 1.07062 | 0.19555 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | nested | 1.20386 | 0.605528 | 1.02733 | 1.97871 | 1.09324 | 0.25295 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |

Giữ toàn bộ9member H44, rank chỉ dùng fit_files, gộp clean và ba noise variants theo origin_file. TopK1/3/5/9 kết hợp F0 bằng trung bình log2, mask/count/range giữ Praat.30. Lựa chọn K vẫn dùng minimax inner và gate cũ, không dựa tên người/thiết bị hoặc GT held.

## Gate

~~~json
{
  "checks": {
    "train_mape_relative_10_percent": true,
    "lofo_mape_relative_5_percent": true,
    "lofo_f1_drop_at_most_01": true,
    "lofo_recall_v_drop_at_most_01": true,
    "lofo_sil_increase_at_most_1": true,
    "lofo_no_file_mape_worse_by_over_2pp": true,
    "lofo_phone_f1_std_not_worse": true,
    "selected_lofo_mape_relative_5_percent": true
  },
  "eligible": true,
  "nested_status": "Outer file excluded from every inner fit and selection; selected LOFO is separate.",
  "champion_promoted": false
}
~~~

## Selection

| outer_held | selected |
| --- | --- |
| final | amdf_ensemble_k01 |
| phone_F1.wav | amdf_ensemble_k01 |
| phone_M1.wav | amdf_ensemble_k01 |
| studio_F1.wav | amdf_pitch_spectral_p170 |
| studio_M1.wav | amdf_ensemble_k09 |

## Mọi cấu hình fixed

| option_id | file | average_mape | F0mean_mape | F0std_mape | F0num_mape | macro_f1 | recall_v | false_voiced_sil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| praat7_filtered_v0.3 | phone_F1.wav | 0.595007 | 0.257478 | 0.851866 | 0.675676 | 0.938333 | 0.941176 | 0 |
| praat7_filtered_v0.3 | phone_M1.wav | 1.01526 | 1.00921 | 1.60553 | 0.431034 | 0.928721 | 0.946721 | 0 |
| praat7_filtered_v0.3 | studio_F1.wav | 1.70384 | 0.67006 | 1.29187 | 3.14961 | 0.900407 | 0.96748 | 0 |
| praat7_filtered_v0.3 | studio_M1.wav | 3.17572 | 0.412037 | 5.45659 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_pitch_spectral_p170 | phone_F1.wav | 0.34008 | 0.254931 | 0.0896324 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_pitch_spectral_p170 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_pitch_spectral_p170 | studio_F1.wav | 1.47358 | 1.08487 | 0.186249 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_pitch_spectral_p170 | studio_M1.wav | 1.90992 | 0.0161649 | 2.05507 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_ensemble_k01 | phone_F1.wav | 0.34008 | 0.254931 | 0.0896324 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_ensemble_k01 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_ensemble_k01 | studio_F1.wav | 1.47358 | 1.08487 | 0.186249 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_ensemble_k01 | studio_M1.wav | 1.90992 | 0.0161649 | 2.05507 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_ensemble_k03 | phone_F1.wav | 0.448022 | 0.240231 | 0.428159 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_ensemble_k03 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_ensemble_k03 | studio_F1.wav | 1.52449 | 1.06186 | 0.362014 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_ensemble_k03 | studio_M1.wav | 1.94642 | 0.0019697 | 2.17876 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_ensemble_k05 | phone_F1.wav | 0.513518 | 0.209011 | 0.655869 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_ensemble_k05 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_ensemble_k05 | studio_F1.wav | 1.54499 | 1.01781 | 0.467544 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_ensemble_k05 | studio_M1.wav | 2.17292 | 0.0852998 | 2.77492 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_ensemble_k09 | phone_F1.wav | 0.388142 | 0.226048 | 0.262701 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_ensemble_k09 | phone_M1.wav | 0.784066 | 0.994255 | 0.926908 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_ensemble_k09 | studio_F1.wav | 1.40548 | 1.00412 | 0.0627233 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_ensemble_k09 | studio_M1.wav | 2.22562 | 0.0935708 | 2.92476 | 3.65854 | 0.808446 | 0.861702 | 0 |

Mỗi nested file Average MAPE≤2%: False. Nested exploratory trên4train đã xem nhiều lần. Không sửaGT, frozen/original, không dùngtest đểchọnK. Khôngpromote tựđộng.

Đầu vào9member H44 đã kiểmtra PCM/FFT; H46 có12call Praat trên12WAV augmented train; clean held WAV không đổi. Nhãn/statistics của augmentation là latent targets kế thừa, không GT mới. Đọc H46_REGISTRATION.md; membership/ranking từngfit trong H46_fits.json.

## Kiểm tra và kết luận

Preregistration `6810ec1` đã push và xác minh remote trước sinh augmentation/đo H46. Hai verifier PASS: 12 WAV/source hash, seed và waveform tái tạo, fs/số mẫu/độ dài/SNR/no clipping; 3518 curve rows từ PCM, FFT, 108 member metrics mới; 104 fit logs với origin exclusion và 144 metric comparisons inner/fixed/train/nested bằng công thức kết hợp độc lập. Layout hình đã xem. Tổng cộng12 lần gọi Praat mới cho12 bản augment, không gọi lại trên test.

So với H45 không augmentation, cả bốn Average MAPE nested không đổi: 0.340080 / 0.776151 / 1.473576 / 2.225623%. Mean1.203857%, tám gate PASS nhưng target≤2% từng file vẫn FAIL. Pipeline cuối và dự đoán hiệu dụng trên clean held files không thay đổi, dù tên cấu hình được chọn ở một fold có thể khác. Không kết luận augmentation vô ích nói chung: chỉ phép noise augmentation/ranking fit pool này chưa giúp trên dataset hiện có.

Bank này vẫn gồm bốn nhóm file gốc; không bổ sung người đọc, câu hoặc phiên thu mới, và chưa xác minh tính độc lập giữa các bản thu gốc. Đây là giới hạn dữ liệu, không phải bằng chứng rằng không thể cải thiện thuật toán. Lưu đầy đủ kết quả không đạt; giữ original/frozen/GT, chưa chuyển sang bài phân đoạn mới. Hướng tiếp theo phải đăng ký riêng trước đo; augmentation hiện chỉ tác động ranking member, chưa huấn luyện lại bộ quyết định hữu thanh/vô thanh.

[Bảng trước/sau](AUGMENTATION_RESULT.md), [dữ liệu tổng hợp](augmentation/H46_train/README.md) và manifest giữ nguồn/seed/nhãn kế thừa. Script summary lần đầu thiếu thư viện tabulate ở bước xuất Markdown; sửa phần hiển thị, không đổi metric hoặc chạy lại benchmark, failure record được giữ.
