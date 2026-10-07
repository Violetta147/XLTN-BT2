# H42 — Chọn cửa sổ NAMDF theo năng lượng phổ

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | lofo | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | nested | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | train | 1.33262 | 0.530702 | 1.48844 | 1.97871 | 0.947271 | 0.351726 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | lofo | 1.33262 | 0.530702 | 1.48844 | 1.97871 | 0.947271 | 0.351726 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | nested | 1.44249 | 0.577567 | 1.7712 | 1.97871 | 1.00205 | 0.426376 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |

Tỷ lệ năng lượng trên1kHz từ raw40ms, bỏDC, Hann, FFT một phía có trọng số đối xứng. Tỷ lệ thấp dùng40ms, còn lại25ms; undefined dùng25ms. Band200cents/Praat.30/voicing/count và projection giữ H41. Không dựa tênfile/giới tính/device/LAB/GT lúc infer. Đây là engineering hypothesis, không paper replication.

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
    "lofo_phone_f1_std_not_worse": false,
    "selected_lofo_mape_relative_5_percent": true
  },
  "eligible": false,
  "nested_status": "Outer file excluded from every inner fit and selection; selected LOFO is separate.",
  "champion_promoted": false
}
~~~

## Selection

| outer_held | selected |
| --- | --- |
| final | amdf_anchor_w25_b200 |
| phone_F1.wav | amdf_anchor_w25_b200 |
| phone_M1.wav | amdf_anchor_w25_b200 |
| studio_F1.wav | amdf_anchor_w25_b200 |
| studio_M1.wav | amdf_spectral_hf05 |

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
| amdf_spectral_hf05 | phone_F1.wav | 0.34008 | 0.254931 | 0.0896324 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_spectral_hf05 | phone_M1.wav | 0.809501 | 1.03647 | 0.960996 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_spectral_hf05 | studio_F1.wav | 1.43556 | 1.10692 | 0.0501592 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_spectral_hf05 | studio_M1.wav | 2.38 | 0.192009 | 3.28946 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_spectral_hf10 | phone_F1.wav | 0.452726 | 0.274646 | 0.407857 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_spectral_hf10 | phone_M1.wav | 0.823895 | 1.04144 | 0.999211 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_spectral_hf10 | studio_F1.wav | 1.56669 | 1.21895 | 0.331505 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_spectral_hf10 | studio_M1.wav | 3.05915 | 0.381754 | 5.13715 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_spectral_hf20 | phone_F1.wav | 0.463389 | 0.279131 | 0.43536 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_spectral_hf20 | phone_M1.wav | 1.0142 | 1.00117 | 1.61039 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_spectral_hf20 | studio_F1.wav | 1.44222 | 1.02123 | 0.155828 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_spectral_hf20 | studio_M1.wav | 3.02071 | 0.410863 | 4.99273 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_spectral_hf35 | phone_F1.wav | 0.581162 | 0.239496 | 0.828316 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_spectral_hf35 | phone_M1.wav | 1.04591 | 1.00126 | 1.70542 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_spectral_hf35 | studio_F1.wav | 1.8588 | 0.936985 | 1.48981 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_spectral_hf35 | studio_M1.wav | 3.00978 | 0.413275 | 4.95752 | 3.65854 | 0.808446 | 0.861702 | 0 |

Mỗi nested file Average MAPE≤2%: False. MAPE là thống kê mean/std/count, không F0 từng khung. Nested exploratory trên4train đã xem nhiều lần.

H41 curves/gate được tái sử dụng có hash; H42 có0nativecall mới,4historicalsourcegroups. Source note: AMDF_SPECTRAL_SOURCE_NOTE.md. Dữ liệu QA test đã đọc mô tả ở lượt trước, không dùng chọn feature/grid/ngưỡng. Không test inference/tuning hoặc sửa ground truth. Giữ failures/original/frozen, không promote tự động, khôngMCP retry/Drive/PDF/deep learning.

Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/amdf_spectral_controller.py H42
