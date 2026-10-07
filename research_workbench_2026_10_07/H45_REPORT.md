# H45 — Kết hợp các cấu hình được chọn từ train

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | lofo | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | nested | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | train | 1.12493 | 0.586176 | 0.809907 | 1.97871 | 1.07062 | 0.19555 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | lofo | 1.12493 | 0.586176 | 0.809907 | 1.97871 | 1.07062 | 0.19555 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | nested | 1.20386 | 0.605528 | 1.02733 | 1.97871 | 1.09324 | 0.25295 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |

Giữ toàn bộ9member H44, rank chỉ dùng fit_files. TopK1/3/5/9 kết hợp F0 bằng trung bình log2, mask/count/range giữ Praat.30. Lựa chọn K vẫn dùng minimax inner và gate cũ, không dựa tên người/thiết bị hoặc GT held.

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
| amdf_ensemble_k01 | studio_M1.wav | 2.41325 | 0.19724 | 3.38397 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_ensemble_k03 | phone_F1.wav | 0.448022 | 0.240231 | 0.428159 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_ensemble_k03 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_ensemble_k03 | studio_F1.wav | 1.52449 | 1.06186 | 0.362014 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_ensemble_k03 | studio_M1.wav | 2.28935 | 0.136939 | 3.07257 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_ensemble_k05 | phone_F1.wav | 0.513518 | 0.209011 | 0.655869 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_ensemble_k05 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_ensemble_k05 | studio_F1.wav | 1.54499 | 1.01781 | 0.467544 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_ensemble_k05 | studio_M1.wav | 2.17292 | 0.0852998 | 2.77492 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_ensemble_k09 | phone_F1.wav | 0.388142 | 0.226048 | 0.262701 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_ensemble_k09 | phone_M1.wav | 0.784066 | 0.994255 | 0.926908 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_ensemble_k09 | studio_F1.wav | 1.40548 | 1.00412 | 0.0627233 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_ensemble_k09 | studio_M1.wav | 2.22562 | 0.0935708 | 2.92476 | 3.65854 | 0.808446 | 0.861702 | 0 |

Mỗi nested file Average MAPE≤2%: False. Nested exploratory trên4train đã xem nhiều lần. Không sửaGT, frozen/original, không dùngtest đểchọnK. Khôngpromote tựđộng.

Đầu vào9member H44 đã kiểmtra PCM/FFT; H45 không có nativecall mới. Đọc H45_REGISTRATION.md; membership/ranking từngfit trong H45_fits.json.

Prereg `2c5b539` remoteverified trướcđo. Verifier PASS: 104 fitlogs membership chỉfitpool, 144 so sánh metric từ96innertraces/24fixed/24train-lofo-nested, geometricmean đốichiếu bằngproduct/kthroot, hash/LAB/count/VUV/gates. Figurelayout đãxem. Studio_M1nested2.225623%, támgatePASS nhưng targetFAIL; khôngthay frozen hoặc gọi fixed≤2 lànestedđạt. Người dùng yêu cầu thử augmentation: H45 này là cleancontrol, vòngaug phảiđăngký riêng, không đổi H45 sauđo.
