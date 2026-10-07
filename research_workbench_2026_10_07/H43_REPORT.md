# H43 — Chọn cửa sổ NAMDF theo phổ và cao độ

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | lofo | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | nested | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | train | 1.12493 | 0.586176 | 0.809907 | 1.97871 | 1.07062 | 0.19555 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | lofo | 1.12493 | 0.586176 | 0.809907 | 1.97871 | 1.07062 | 0.19555 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | nested | 1.27842 | 0.649597 | 1.20695 | 1.97871 | 1.14475 | 0.30037 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |

Tỷ lệ năng lượng trên1kHz từ raw40ms, bỏDC, Hann, FFT một phía có trọng số đối xứng. Dùng40ms khi tỷ lệ≤.05 vàgateF0≥ngưỡng0/140/170/200Hz; còn lại25ms, undefined dùng25ms. Band200cents/Praat.30/voicing/count và projection giữ H41. Không dựa tênfile/giới tính/device/LAB/GT lúc infer. Đây là engineering hypothesis, không paper replication.

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
| studio_M1.wav | amdf_pitch_spectral_p140 |

## Mọi cấu hình fixed

| option_id | file | average_mape | F0mean_mape | F0std_mape | F0num_mape | macro_f1 | recall_v | false_voiced_sil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| praat7_filtered_v0.3 | phone_F1.wav | 0.595007 | 0.257478 | 0.851866 | 0.675676 | 0.938333 | 0.941176 | 0 |
| praat7_filtered_v0.3 | phone_M1.wav | 1.01526 | 1.00921 | 1.60553 | 0.431034 | 0.928721 | 0.946721 | 0 |
| praat7_filtered_v0.3 | studio_F1.wav | 1.70384 | 0.67006 | 1.29187 | 3.14961 | 0.900407 | 0.96748 | 0 |
| praat7_filtered_v0.3 | studio_M1.wav | 3.17572 | 0.412037 | 5.45659 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_anchor_w25_b200 | phone_F1.wav | 1.08055 | 0.23347 | 2.33251 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_anchor_w25_b200 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_anchor_w25_b200 | studio_F1.wav | 1.53327 | 0.896051 | 0.554161 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_anchor_w25_b200 | studio_M1.wav | 1.94049 | 0.0045515 | 2.1584 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_anchor_w40_b200 | phone_F1.wav | 0.581162 | 0.239496 | 0.828316 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_anchor_w40_b200 | phone_M1.wav | 1.02675 | 1.02807 | 1.62114 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_anchor_w40_b200 | studio_F1.wav | 1.87103 | 0.958137 | 1.50536 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_anchor_w40_b200 | studio_M1.wav | 3.0074 | 0.411125 | 4.95254 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_pitch_spectral_p000 | phone_F1.wav | 0.34008 | 0.254931 | 0.0896324 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_pitch_spectral_p000 | phone_M1.wav | 0.809501 | 1.03647 | 0.960996 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_pitch_spectral_p000 | studio_F1.wav | 1.43556 | 1.10692 | 0.0501592 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_pitch_spectral_p000 | studio_M1.wav | 2.38 | 0.192009 | 3.28946 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_pitch_spectral_p140 | phone_F1.wav | 0.34008 | 0.254931 | 0.0896324 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_pitch_spectral_p140 | phone_M1.wav | 0.772627 | 0.98884 | 0.898007 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_pitch_spectral_p140 | studio_F1.wav | 1.43556 | 1.10692 | 0.0501592 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_pitch_spectral_p140 | studio_M1.wav | 2.52388 | 0.269847 | 3.64326 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_pitch_spectral_p170 | phone_F1.wav | 0.34008 | 0.254931 | 0.0896324 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_pitch_spectral_p170 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_pitch_spectral_p170 | studio_F1.wav | 1.47358 | 1.08487 | 0.186249 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_pitch_spectral_p170 | studio_M1.wav | 1.90992 | 0.0161649 | 2.05507 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_pitch_spectral_p200 | phone_F1.wav | 0.755296 | 0.137605 | 1.45261 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_pitch_spectral_p200 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_pitch_spectral_p200 | studio_F1.wav | 1.62955 | 1.02217 | 0.716871 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_pitch_spectral_p200 | studio_M1.wav | 1.94049 | 0.0045515 | 2.1584 | 3.65854 | 0.808446 | 0.861702 | 0 |

Mỗi nested file Average MAPE≤2%: False. MAPE là thống kê mean/std/count, không F0 từng khung. Nested exploratory trên4train đã xem nhiều lần.

H41 curves/gate được tái sử dụng có hash; H43 có0nativecall mới,4historicalsourcegroups. Source note: H43_SOURCE_NOTE.md. Dữ liệu QA test đã đọc mô tả ở lượt trước, không dùng chọn feature/grid/ngưỡng. Không test inference/tuning hoặc sửa ground truth. Giữ failures/original/frozen, không promote tự động, khôngMCP retry/Drive/PDF/deep learning.

Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/amdf_pitch_spectral_controller.py H43
