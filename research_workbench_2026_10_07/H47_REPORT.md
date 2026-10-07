# H47 — Học quyết định hữu thanh với augmentation

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | lofo | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | nested | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | train | 1.12493 | 0.586176 | 0.809907 | 1.97871 | 1.07062 | 0.19555 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | lofo | 1.12493 | 0.586176 | 0.809907 | 1.97871 | 1.07062 | 0.19555 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | nested | 1.12493 | 0.586176 | 0.809907 | 1.97871 | 1.07062 | 0.19555 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |

Giữ pitch H43 hard170; logistic chỉ có thể loại khung Praat đã nhận hữu thanh. Học V so với UV/SIL trên fit origins, C=1, bốn đặc trưng âm học, threshold .25/.5. So clean với clean+3 noise variants kế thừa nhãn. Mỗi origin và variant có tổng trọng số bằng nhau; không cân bằng lớp. Không dùng F0num để cắt số khung. Inner minimax và gate cũ; yêu cầu mới strict <2%.

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
| final | amdf_pitch_spectral_p170 |
| phone_F1.wav | amdf_pitch_spectral_p170 |
| phone_M1.wav | amdf_pitch_spectral_p170 |
| studio_F1.wav | amdf_pitch_spectral_p170 |
| studio_M1.wav | amdf_pitch_spectral_p170 |

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
| voicing_clean_p25 | phone_F1.wav | 0.94522 | 0.300249 | 0.508383 | 2.02703 | 0.928565 | 0.928105 | 0 |
| voicing_clean_p25 | phone_M1.wav | 1.16064 | 1.1124 | 1.07641 | 1.2931 | 0.920879 | 0.934426 | 0 |
| voicing_clean_p25 | studio_F1.wav | 1.47358 | 1.08487 | 0.186249 | 3.14961 | 0.900407 | 0.96748 | 0 |
| voicing_clean_p25 | studio_M1.wav | 1.90992 | 0.0161649 | 2.05507 | 3.65854 | 0.808446 | 0.861702 | 0 |
| voicing_clean_p50 | phone_F1.wav | 1.28502 | 0.296621 | 0.855731 | 2.7027 | 0.923727 | 0.921569 | 0 |
| voicing_clean_p50 | phone_M1.wav | 2.2648 | 0.99969 | 1.48438 | 4.31034 | 0.901052 | 0.909836 | 0 |
| voicing_clean_p50 | studio_F1.wav | 1.97531 | 0.813227 | 1.17569 | 3.93701 | 0.914286 | 0.96748 | 0 |
| voicing_clean_p50 | studio_M1.wav | 1.90992 | 0.0161649 | 2.05507 | 3.65854 | 0.808446 | 0.861702 | 0 |
| voicing_aug_p25 | phone_F1.wav | 0.94522 | 0.300249 | 0.508383 | 2.02703 | 0.928565 | 0.928105 | 0 |
| voicing_aug_p25 | phone_M1.wav | 0.866451 | 1.026 | 1.14232 | 0.431034 | 0.929466 | 0.942623 | 0 |
| voicing_aug_p25 | studio_F1.wav | 1.47358 | 1.08487 | 0.186249 | 3.14961 | 0.900407 | 0.96748 | 0 |
| voicing_aug_p25 | studio_M1.wav | 1.90992 | 0.0161649 | 2.05507 | 3.65854 | 0.808446 | 0.861702 | 0 |
| voicing_aug_p50 | phone_F1.wav | 1.41286 | 0.393993 | 0.466203 | 3.37838 | 0.918919 | 0.915033 | 0 |
| voicing_aug_p50 | phone_M1.wav | 1.86455 | 1.04478 | 1.10059 | 3.44828 | 0.900107 | 0.913934 | 0 |
| voicing_aug_p50 | studio_F1.wav | 1.47358 | 1.08487 | 0.186249 | 3.14961 | 0.900407 | 0.96748 | 0 |
| voicing_aug_p50 | studio_M1.wav | 1.90992 | 0.0161649 | 2.05507 | 3.65854 | 0.808446 | 0.861702 | 0 |

Mỗi nested file Average MAPE<2%: True. Nested exploratory trên4train đã xem nhiều lần. Không sửa GT, frozen/original, không dùng test để chọn cấu hình. Khôngpromote tựđộng.

Tái sử dụng H44 pitch và H46 noise WAV/gate đã xác minh; 0 native call mới. Augmentation kế thừa nhãn, không tạo người nói mới. Chỉ 4 train; nested exploratory sau nhiều vòng đã xem. Candidate set đã thay đổi so với H45/H46; đạt target do fallback hard170 không tự chứng minh augmentation có ích. Đọc H47_REGISTRATION.md; membership/ranking từngfit trong H47_fits.json.
