# H33 — pipeline pYIN với cửa sổ40/60/80ms

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| accepted | lofo | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| accepted | nested | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| candidate | train | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| candidate | lofo | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| candidate | nested | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |

Pipeline mới: probabilistic YIN candidates và Viterbi F0/VUV qua librosa0.11.0. Control Praat7 filtered fixedvoicing.45. Frame40/60/80ms, hop10ms ở sample rate gốc; center=False, không padding, không resample/gate/median/noise. Các defaults được chốt trong registry registration và pyin_adapter.py.

Lưu F0/flag/voiced_probability native và full params. UV fillNaN được biểu diễn raw_f0_hz=0 trong CSV; probability giữ riêng, không áp thêm threshold. Projection nearest center về canonical25/10; unsupported=false/NaN. Frame dài mất support ở biên, không thêm padding để bù count. LAB chỉ file-stat/nhãn đoạn, không F0 chuẩn từng khung. Đây là whole pipeline comparison, không cô lập một filter.

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

| outer_held | id | frame_ms | hop_ms | pitch_frame_ms | method | voicing_threshold |
| --- | --- | --- | --- | --- | --- | --- |
| final | praat7_filtered_v0.45 | 42.8571 | 10 | 42.8571 | control | 0.45 |
| phone_F1.wav | praat7_filtered_v0.45 | 42.8571 | 10 | 42.8571 | control | 0.45 |
| phone_M1.wav | praat7_filtered_v0.45 | 42.8571 | 10 | 42.8571 | control | 0.45 |
| studio_F1.wav | praat7_filtered_v0.45 | 42.8571 | 10 | 42.8571 | control | 0.45 |
| studio_M1.wav | praat7_filtered_v0.45 | 42.8571 | 10 | 42.8571 | control | 0.45 |

## Mọi cấu hình fixed LOFO

| option_id | file | average_mape | F0mean_mape | F0std_mape | F0num_mape | macro_f1 | recall_v | false_voiced_sil | projection_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| praat7_filtered_v0.45 | phone_F1.wav | 2.76986 | 0.0766879 | 2.1518 | 6.08108 | 0.919971 | 0.901961 | 0 | 0.993789 |
| praat7_filtered_v0.45 | phone_M1.wav | 1.64701 | 0.797475 | 1.55734 | 2.58621 | 0.908301 | 0.922131 | 0 | 0.995169 |
| praat7_filtered_v0.45 | studio_F1.wav | 2.22688 | 0.871402 | 1.87223 | 3.93701 | 0.889796 | 0.95935 | 0 | 0.996479 |
| praat7_filtered_v0.45 | studio_M1.wav | 1.98422 | 0.0731761 | 3.44047 | 2.43902 | 0.799438 | 0.851064 | 0 | 0.99262 |
| pyin_f40 | phone_F1.wav | 2.30934 | 1.47178 | 0.726515 | 4.72973 | 0.84898 | 0.862745 | 0 | 0.996894 |
| pyin_f40 | phone_M1.wav | 2.81854 | 0.532764 | 2.31941 | 5.60345 | 0.809268 | 0.860656 | 0 | 0.997585 |
| pyin_f40 | studio_F1.wav | 3.35583 | 1.22423 | 0.969241 | 7.87402 | 0.818668 | 0.99187 | 4 | 0.996479 |
| pyin_f40 | studio_M1.wav | 2.39347 | 0.458177 | 3.0637 | 3.65854 | 0.79059 | 0.840426 | 2 | 0.99631 |
| pyin_f60 | phone_F1.wav | 8.16696 | 1.70628 | 2.52434 | 20.2703 | 0.763955 | 0.947712 | 1 | 0.990683 |
| pyin_f60 | phone_M1.wav | 3.22135 | 1.00698 | 1.76051 | 6.89655 | 0.720122 | 0.897541 | 0 | 0.992754 |
| pyin_f60 | studio_F1.wav | 8.07173 | 0.920435 | 5.18452 | 18.1102 | 0.689593 | 0.95122 | 18 | 0.989437 |
| pyin_f60 | studio_M1.wav | 3.91521 | 0.289624 | 0.480383 | 10.9756 | 0.743132 | 0.851064 | 3 | 0.98893 |
| pyin_f80 | phone_F1.wav | 10.1879 | 1.67021 | 1.86649 | 27.027 | 0.727364 | 0.960784 | 3 | 0.984472 |
| pyin_f80 | phone_M1.wav | 4.01202 | 0.896705 | 1.65661 | 9.48276 | 0.730501 | 0.918033 | 0 | 0.987923 |
| pyin_f80 | studio_F1.wav | 9.01225 | 0.697088 | 5.86723 | 20.4724 | 0.674058 | 0.934959 | 23 | 0.982394 |
| pyin_f80 | studio_M1.wav | 21.7893 | 5.89526 | 7.03372 | 52.439 | 0.720857 | 0.861702 | 34 | 0.98155 |

## Nested per file

| model | file | average_mape | F0std_mape | F0num_mape | recall_v | false_voiced_sil | projection_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | phone_F1.wav | 2.76986 | 2.1518 | 6.08108 | 0.901961 | 0 | 0.993789 |
| candidate | phone_F1.wav | 2.76986 | 2.1518 | 6.08108 | 0.901961 | 0 | 0.993789 |
| accepted | phone_M1.wav | 1.64701 | 1.55734 | 2.58621 | 0.922131 | 0 | 0.995169 |
| candidate | phone_M1.wav | 1.64701 | 1.55734 | 2.58621 | 0.922131 | 0 | 0.995169 |
| accepted | studio_F1.wav | 2.22688 | 1.87223 | 3.93701 | 0.95935 | 0 | 0.996479 |
| candidate | studio_F1.wav | 2.22688 | 1.87223 | 3.93701 | 0.95935 | 0 | 0.996479 |
| accepted | studio_M1.wav | 1.98422 | 3.44047 | 2.43902 | 0.851064 | 0 | 0.99262 |
| candidate | studio_M1.wav | 1.98422 | 3.44047 | 2.43902 | 0.851064 | 0 | 0.99262 |

Mục tiêu mỗi file≤2% riêng. Inner minmax/mean/ID, outer held không selection. Lịch sử bốn file làm kết quả exploratory. Không promote; chỉ train local, không test/Drive/deep learning/PDF. Jev error đã dừng MCP, không retry.

![Nested](figures/H33_nested.png)

Lệnh: ../.venv-bt2-pyin/Scripts/python.exe research_workbench_2026_10_07/pyin_reference.py H33
