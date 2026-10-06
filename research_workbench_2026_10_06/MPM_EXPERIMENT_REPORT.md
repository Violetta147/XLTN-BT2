# MPM — thí nghiệm pitch estimator

Train-only; same frame25/hop10, ACF mask/RMS fold fit, median3. Fixed parameter, không tune/test. Accepted champion giữ nguyên.

## Số đo

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 6.17797 | 0.583562 | 11.3078 | 6.64251 | 0.854436 | 2.33158 | 0.850371 | 0.900215 | 0.869123 | 0.931306 | 530 | 167 | 13 | 84 | 1 | 544 |
| accepted | lofo | 7.27924 | 1.05571 | 14.6661 | 6.1159 | 1.84025 | 3.0133 | 0.841398 | 0.893149 | 0.865862 | 0.920437 | 527 | 164 | 16 | 87 | 3 | 546 |
| acf_single_peak_control | train | 14.6133 | 1.97526 | 35.222 | 6.64251 | 3.82444 | 7.40018 | 0.850371 | 0.900215 | 0.869123 | 0.931306 | 530 | 167 | 13 | 84 | 1 | 544 |
| acf_single_peak_control | lofo | 15.234 | 1.7409 | 37.8452 | 6.1159 | 3.20947 | 7.73108 | 0.841398 | 0.893149 | 0.865862 | 0.920437 | 527 | 164 | 16 | 87 | 3 | 546 |
| candidate | train | 6.96035 | 0.618255 | 13.6203 | 6.64251 | 0.798222 | 2.69035 | 0.850371 | 0.900215 | 0.869123 | 0.931306 | 530 | 167 | 13 | 84 | 1 | 544 |
| candidate | lofo | 8.18831 | 0.915878 | 17.5331 | 6.1159 | 1.5424 | 3.56387 | 0.841398 | 0.893149 | 0.865862 | 0.920437 | 527 | 164 | 16 | 87 | 3 | 546 |

## Validation synthetic

~~~json
{
  "silence_returns_nan": true,
  "constant_returns_nan": true,
  "gain_invariance": true,
  "dc_invariance": true,
  "synthetic_cases": 1600,
  "synthetic_abstentions": 12,
  "clean_interior_coverage": 1.0,
  "clean_interior_median_cents": 0.008496768760039314,
  "clean_interior_p95_cents": 0.0893245630290476
}
~~~

Synthetic error là conditional trên cases có estimate. Coverage được báo riêng; clean interior yêu cầu100% coverage theo gate đăng ký.

| signal_kind | snr_db | cases | answered | conditional_median_cents | coverage |
| --- | --- | --- | --- | --- | --- |
| harmonic | 0 | 100 | 100 | 20.7762 | 1 |
| harmonic | 10 | 100 | 96 | 3.86283 | 0.96 |
| harmonic | 20 | 100 | 97 | 0.769499 | 0.97 |
| harmonic | inf | 100 | 100 | 0.00577787 | 1 |
| missing_fundamental | 0 | 100 | 100 | 12.4126 | 1 |
| missing_fundamental | 10 | 100 | 100 | 2.93354 | 1 |
| missing_fundamental | 20 | 100 | 100 | 0.368091 | 1 |
| missing_fundamental | inf | 100 | 100 | 0.00690312 | 1 |
| sine | 0 | 100 | 100 | 43.2978 | 1 |
| sine | 10 | 100 | 98 | 9.70379 | 0.98 |
| sine | 20 | 100 | 97 | 1.64474 | 0.97 |
| sine | inf | 100 | 100 | 0.00753182 | 1 |
| weak_fundamental | 0 | 100 | 100 | 15.022 | 1 |
| weak_fundamental | 10 | 100 | 100 | 2.84731 | 1 |
| weak_fundamental | 20 | 100 | 100 | 0.349222 | 1 |
| weak_fundamental | inf | 100 | 100 | 0.00723947 | 1 |

## Gate đăng ký trước

~~~json
{
  "checks": {
    "train_mape_relative_10_percent": false,
    "lofo_mape_relative_5_percent": false,
    "lofo_f1_drop_at_most_01": true,
    "lofo_recall_v_drop_at_most_01": true,
    "lofo_sil_increase_at_most_1": true,
    "lofo_no_file_mape_worse_by_over_2pp": false,
    "lofo_phone_f1_std_not_worse": false
  },
  "eligible": false,
  "nested_status": "No newly tuned parameter: fixed candidate evaluated by LOFO; no distinct inner selection estimate.",
  "champion_promoted": false
}
~~~

Không có bước chọn tham số bên trong cho model fixed này, nên LOFO là đánh giá held-file; không tạo thêm nested score bằng việc chạy lại giống nhau. Với model tune tiếp theo, phải nested selection thật. Dữ liệu train đã dùng chọn champion trước đây, n=4 nên kết quả thăm dò.

## Tái lập

~~~powershell
python research_workbench_2026_10_06/estimator_experiment.py mpm
~~~

## Figures

![mpm_synthetic_accuracy](figures/mpm_synthetic_accuracy.png)

Không thay thế WAV thật; NaN/abstentions được báo riêng, không tính như lỗi0.

![mpm_lofo_metrics](figures/mpm_lofo_metrics.png)

Cùng voiced mask/RMS/median3. Chỉ bốn file; không có pitch GT từng khung.

![mpm_lofo_contours](figures/mpm_lofo_contours.png)

Không phải đường truth, không kết luận contour mượt là đúng.
