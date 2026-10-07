# H39 — RAPT native SPTK reference pipeline

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| accepted | lofo | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| accepted | nested | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| candidate | train | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| candidate | lofo | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| candidate | nested | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |

RAPT tạo ứng viên bằng normalized cross-correlation hai mức và nối đường qua thời gian bằng dynamic programming. Đây là wholepipeline comparison với control H30fixedPraatfiltered.45, không claim tác động riêng NCCF hoặc noise. Grid voicingbias−.3/0/.3/.6; source internalwindow7.5ms còn lag/lookahead, range70–400,hop10ms. Higherbias khuyến khíchV, không probability.

Adapter gửi nguyên PCM16 dưới doublefloat64 (audio normalized×32768). Native vendor tự thêm Gaussian std50PCMunits/seed1 và padcuối; behavior/hash giữ nguyên. Outputceil(N/hop), truncate/repeatlastnative, assigned0-origin grid; nearest-time to canonical25/10 trong5ms+mộtmẫu,tiesearlier. Không dịchtime đểkhớpGT, khôngagentnoise/smoothing/trimcount/file routing.

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
| rapt_b-0.3 | phone_F1.wav | 3.79303 | 0.000526101 | 5.97317 | 5.40541 | 0.934769 | 0.915033 | 0 | 1 |
| rapt_b-0.3 | phone_M1.wav | 4.97563 | 1.74402 | 6.28631 | 6.89655 | 0.87746 | 0.885246 | 0 | 1 |
| rapt_b-0.3 | studio_F1.wav | 3.70081 | 0.749802 | 1.69121 | 8.66142 | 0.921719 | 0.943089 | 0 | 1 |
| rapt_b-0.3 | studio_M1.wav | 3.03313 | 0.647617 | 3.57371 | 4.87805 | 0.832276 | 0.829787 | 0 | 1 |
| rapt_b0 | phone_F1.wav | 7.28161 | 0.507664 | 11.8777 | 9.45946 | 0.939904 | 0.993464 | 0 | 1 |
| rapt_b0 | phone_M1.wav | 3.86224 | 1.04696 | 4.50527 | 6.03448 | 0.887387 | 0.959016 | 0 | 1 |
| rapt_b0 | studio_F1.wav | 3.09011 | 0.848135 | 2.12299 | 6.29921 | 0.953274 | 0.96748 | 0 | 1 |
| rapt_b0 | studio_M1.wav | 2.69033 | 0.931708 | 4.70027 | 2.43902 | 0.888577 | 0.893617 | 0 | 1 |
| rapt_b0.3 | phone_F1.wav | 14.4052 | 0.151908 | 21.4419 | 21.6216 | 0.885802 | 0.993464 | 9 | 1 |
| rapt_b0.3 | phone_M1.wav | 7.55912 | 1.10587 | 5.19217 | 16.3793 | 0.765019 | 0.971311 | 1 | 1 |
| rapt_b0.3 | studio_F1.wav | 2.17211 | 0.808316 | 5.70801 | 0 | 0.893091 | 0.98374 | 0 | 1 |
| rapt_b0.3 | studio_M1.wav | 23.3546 | 3.87028 | 52.7789 | 13.4146 | 0.862745 | 0.93617 | 0 | 1 |
| rapt_b0.6 | phone_F1.wav | 57.2788 | 4.53579 | 117.976 | 49.3243 | 0.766136 | 0.993464 | 33 | 1 |
| rapt_b0.6 | phone_M1.wav | 24.351 | 1.31567 | 16.5649 | 55.1724 | 0.548339 | 0.995902 | 62 | 1 |
| rapt_b0.6 | studio_F1.wav | 7.03688 | 0.917971 | 9.95644 | 10.2362 | 0.719466 | 1 | 1 | 1 |
| rapt_b0.6 | studio_M1.wav | 44.9867 | 12.4524 | 92.02 | 30.4878 | 0.686842 | 0.957447 | 1 | 1 |

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

Mục tiêu mỗi file≤2% riêng. No actualfit; innerminimax/mean/ID chọnbias. Outerheld khôngselection; lịch sửn4 làmnestedexploratory. LAB chỉfile-stat/nhãnđoạn, khôngF0chuẩntừngkhung. Source/manualread khácfullchapter; khôngbịaDOI. Khôngpromote/test/Drive/deeplearning/PDF/retryJev. Failedoptions giữ nguyên.

![Nested](figures/H39_nested.png)

Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/rapt_reference.py H39
