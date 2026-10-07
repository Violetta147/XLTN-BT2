# H41 — NAMDF candidates under fixed Praat voicing

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | lofo | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | nested | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | train | 1.33262 | 0.530702 | 1.48844 | 1.97871 | 0.947271 | 0.351726 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | lofo | 1.33262 | 0.530702 | 1.48844 | 1.97871 | 0.947271 | 0.351726 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | nested | 1.33262 | 0.530702 | 1.48844 | 1.97871 | 0.947271 | 0.351726 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |

AMDF gate không thay: Praatfiltered.30 giữ V/UV/count. NAMDF raw40/55/25ms được tính tại tâm Praat, dùng localdip có F0 trongband50/100/200cents. Chọn dip thấp nhất, tie khoảng cáchcents rồiF0; khôngứngviên hoặc thiếuwindow giữPraat. Đây là engineeringhypothesis từkernelnotebook, không AAMDFpaperreplication.

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
| studio_M1.wav | amdf_anchor_w25_b200 |

## Mọi cấu hình fixed

| option_id | file | average_mape | F0mean_mape | F0std_mape | F0num_mape | macro_f1 | recall_v | false_voiced_sil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| praat7_filtered_v0.3 | phone_F1.wav | 0.595007 | 0.257478 | 0.851866 | 0.675676 | 0.938333 | 0.941176 | 0 |
| praat7_filtered_v0.3 | phone_M1.wav | 1.01526 | 1.00921 | 1.60553 | 0.431034 | 0.928721 | 0.946721 | 0 |
| praat7_filtered_v0.3 | studio_F1.wav | 1.70384 | 0.67006 | 1.29187 | 3.14961 | 0.900407 | 0.96748 | 0 |
| praat7_filtered_v0.3 | studio_M1.wav | 3.17572 | 0.412037 | 5.45659 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_anchor_w25_b50 | phone_F1.wav | 0.581649 | 0.158957 | 0.910314 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_anchor_w25_b50 | phone_M1.wav | 0.849214 | 1.01189 | 1.10472 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_anchor_w25_b50 | studio_F1.wav | 1.55673 | 0.739199 | 0.781379 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_anchor_w25_b50 | studio_M1.wav | 2.59714 | 0.291399 | 3.84148 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_anchor_w25_b100 | phone_F1.wav | 1.16282 | 0.165821 | 2.64696 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_anchor_w25_b100 | phone_M1.wav | 0.955443 | 1.0629 | 1.37239 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_anchor_w25_b100 | studio_F1.wav | 1.57481 | 0.683719 | 0.891108 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_anchor_w25_b100 | studio_M1.wav | 2.20208 | 0.060379 | 2.88731 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_anchor_w25_b200 | phone_F1.wav | 1.08055 | 0.23347 | 2.33251 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_anchor_w25_b200 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_anchor_w25_b200 | studio_F1.wav | 1.53327 | 0.896051 | 0.554161 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_anchor_w25_b200 | studio_M1.wav | 1.94049 | 0.0045515 | 2.1584 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_anchor_w40_b50 | phone_F1.wav | 0.521932 | 0.304662 | 0.585459 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_anchor_w40_b50 | phone_M1.wav | 0.946308 | 0.994341 | 1.41355 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_anchor_w40_b50 | studio_F1.wav | 1.63643 | 1.01178 | 0.747919 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_anchor_w40_b50 | studio_M1.wav | 2.91433 | 0.270333 | 4.81413 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_anchor_w40_b100 | phone_F1.wav | 0.485782 | 0.32755 | 0.45412 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_anchor_w40_b100 | phone_M1.wav | 0.886857 | 0.937248 | 1.29229 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_anchor_w40_b100 | studio_F1.wav | 1.74598 | 1.022 | 1.06634 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_anchor_w40_b100 | studio_M1.wav | 2.92096 | 0.276097 | 4.82826 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_anchor_w40_b200 | phone_F1.wav | 0.581162 | 0.239496 | 0.828316 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_anchor_w40_b200 | phone_M1.wav | 1.02675 | 1.02807 | 1.62114 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_anchor_w40_b200 | studio_F1.wav | 1.87103 | 0.958137 | 1.50536 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_anchor_w40_b200 | studio_M1.wav | 3.0074 | 0.411125 | 4.95254 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_anchor_w55_b50 | phone_F1.wav | 0.433059 | 0.306901 | 0.316599 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_anchor_w55_b50 | phone_M1.wav | 0.792467 | 0.937457 | 1.00891 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_anchor_w55_b50 | studio_F1.wav | 1.63859 | 0.981035 | 0.78512 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_anchor_w55_b50 | studio_M1.wav | 3.00029 | 0.235488 | 5.10684 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_anchor_w55_b100 | phone_F1.wav | 0.701193 | 0.377613 | 1.05029 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_anchor_w55_b100 | phone_M1.wav | 1.07967 | 0.910598 | 1.89738 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_anchor_w55_b100 | studio_F1.wav | 1.64373 | 1.35726 | 0.424311 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_anchor_w55_b100 | studio_M1.wav | 2.53492 | 0.0277916 | 3.91845 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_anchor_w55_b200 | phone_F1.wav | 0.617139 | 0.407586 | 0.768156 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_anchor_w55_b200 | phone_M1.wav | 1.21112 | 0.955417 | 2.24692 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_anchor_w55_b200 | studio_F1.wav | 2.34268 | 1.2094 | 2.66904 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_anchor_w55_b200 | studio_M1.wav | 4.0484 | 0.804553 | 7.6821 | 3.65854 | 0.808446 | 0.861702 | 0 |

Mỗi nested file Average MAPE≤2%: True. Mean nhỏ không đủ. Bốn trainfiles/lịch sử đã xem làmnestedexploratory; LAB chỉfile-stat/nhãn đoạn, khôngF0chuẩntừngkhung.

Nguồn/mapping ở AMDF_ANCHOR_SOURCE_NOTE.md. Curvesinput/start/time/hash vàrawfusion giữ đểverify độc lập. Khôngclip/resample/noise/GTmatching/file routing/promote/test/Drive/deep learning/PDF hoặcMCP retry.

Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/amdf_praat_anchor.py H41
