# H40 — YAAPT reference port

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| accepted | lofo | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| accepted | nested | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| candidate | train | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| candidate | lofo | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| candidate | nested | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |

Thuật toán kết hợp ứng viên từ phổ và tương quan chuẩn hóa, rồi chọn chuỗi bằng dynamic programming. Đây là whole-pipeline comparison; chỉ grid frame_length 25/35/45 ms thay đổi trong YAAPT, tda_frame_length giữ 35 ms. Đọc YAAPT_SOURCE_NOTE.md và H40_REGISTRATION.md.

Raw samp_values giữ UV0; không dùng contour nội suy. Native frames_pos/fs, nearest canonical25/10 trong5ms+mộtmẫu, tie sớm; causal FIR giữ nguyên, không sửa offset bằng LAB. Không fit hoặc matching mean/std/count của held file.

## Gate

~~~json
{
  "checks": {
    "train_mape_relative_10_percent": false,
    "lofo_mape_relative_5_percent": false,
    "lofo_f1_drop_at_most_01": true,
    "lofo_recall_v_drop_at_most_01": true,
    "lofo_sil_increase_at_most_1": true,
    "lofo_no_file_mape_worse_by_over_2pp": true,
    "lofo_phone_f1_std_not_worse": true,
    "selected_lofo_mape_relative_5_percent": false
  },
  "eligible": false,
  "nested_status": "Outer file excluded from every inner fit and selection; selected LOFO is separate.",
  "champion_promoted": false
}
~~~

## Selections

| outer_held | selected |
| --- | --- |
| final | praat7_filtered_v0.45 |
| phone_F1.wav | praat7_filtered_v0.45 |
| phone_M1.wav | praat7_filtered_v0.45 |
| studio_F1.wav | praat7_filtered_v0.45 |
| studio_M1.wav | praat7_filtered_v0.45 |

## Tất cả cấu hình fixed

| option_id | file | average_mape | F0mean_mape | F0std_mape | F0num_mape | macro_f1 | recall_v | false_voiced_sil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| praat7_filtered_v0.45 | phone_F1.wav | 2.76986 | 0.0766879 | 2.1518 | 6.08108 | 0.919971 | 0.901961 | 0 |
| praat7_filtered_v0.45 | phone_M1.wav | 1.64701 | 0.797475 | 1.55734 | 2.58621 | 0.908301 | 0.922131 | 0 |
| praat7_filtered_v0.45 | studio_F1.wav | 2.22688 | 0.871402 | 1.87223 | 3.93701 | 0.889796 | 0.95935 | 0 |
| praat7_filtered_v0.45 | studio_M1.wav | 1.98422 | 0.0731761 | 3.44047 | 2.43902 | 0.799438 | 0.851064 | 0 |
| yaapt_f25 | phone_F1.wav | 1.0432 | 1.47765 | 0.976272 | 0.675676 | 0.938333 | 0.941176 | 0 |
| yaapt_f25 | phone_M1.wav | 1.16004 | 1.87895 | 0.308062 | 1.2931 | 0.902262 | 0.92623 | 0 |
| yaapt_f25 | studio_F1.wav | 3.15082 | 0.927207 | 5.37565 | 3.14961 | 0.914286 | 0.96748 | 1 |
| yaapt_f25 | studio_M1.wav | 6.33433 | 2.52211 | 7.94429 | 8.53659 | 0.893592 | 0.925532 | 0 |
| yaapt_f35 | phone_F1.wav | 1.61251 | 1.02293 | 2.46326 | 1.35135 | 0.933433 | 0.934641 | 0 |
| yaapt_f35 | phone_M1.wav | 2.04954 | 2.54467 | 1.87981 | 1.72414 | 0.908738 | 0.942623 | 1 |
| yaapt_f35 | studio_F1.wav | 1.98456 | 0.247004 | 4.13187 | 1.5748 | 0.886037 | 0.96748 | 1 |
| yaapt_f35 | studio_M1.wav | 8.66448 | 2.60249 | 9.9763 | 13.4146 | 0.83779 | 0.925532 | 0 |
| yaapt_f45 | phone_F1.wav | 2.66794 | 1.26709 | 3.35836 | 3.37838 | 0.936914 | 0.960784 | 0 |
| yaapt_f45 | phone_M1.wav | 2.13818 | 2.1601 | 2.09926 | 2.15517 | 0.913068 | 0.946721 | 1 |
| yaapt_f45 | studio_F1.wav | 2.10501 | 0.0352701 | 4.70495 | 1.5748 | 0.893091 | 0.98374 | 2 |
| yaapt_f45 | studio_M1.wav | 10.7436 | 3.48407 | 11.6735 | 17.0732 | 0.832955 | 0.93617 | 1 |

Mỗi nested file Average MAPE≤2%: False. Mean≤2% không thay thế điều kiện từng file. Bốn file và lịch sử đã xem khiến nested exploratory; không test tuning hoặc xác minh F0 từng khung.

Giữ probe sine/rich octave failures. Transport two-harmonic và zero kiểm tra dữ liệu/UV, không bảo đảm đúng trên tiếng nói. Không promote hoặc thay original baseline. Jev không tham gia vòng này; nhánh MCP vẫn dừng sau lỗi trước đó.

Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/yaapt_reference.py H40
