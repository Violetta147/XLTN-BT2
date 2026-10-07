# H34 — reference pipeline SWIPE prime

Audit: prereg dự kiến88 fit-log records; thực tế84 unique scoring records vì final chọn control, bốn full-train candidate calls trùng cache accepted. Toàn bộ80 inner traces và20 native calls đủ; không có bước fit nhãn trong SWIPE/Praat. Đây là khác biệt số record cache, không bỏ outer/inner fold. Vòng đã FAIL gates; mục tiêu từng file≤2% chưa đạt.

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| accepted | lofo | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| accepted | nested | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| candidate | train | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| candidate | lofo | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |
| candidate | nested | 2.15699 | 0.454685 | 2.25546 | 3.76083 | 0.809525 | 0.575542 | 0.879377 | 0.909652 | 0.908626 | 0.910678 | 561 | 170 | 10 | 53 | 0 | 571 |

SPTK4.4 SWIPE prime native, source commit0ebff5a. Registry threshold .2/.3/.4/.5; hop10ms, range70–400Hz, fs gốc. Adaptive FFT windows của SWIPE giữ theo nguồn; không giả frame25ms. Control H30 Praat filtered fixed.45.

Input float64 little-endian PCM-scale = normalized audio*32768; nativeoutputHz/UV0. Time origin0, countceil(samples/hop) theo source; internal window padding/truncation/repeatlast của SPTK giữ nguyên. Agent không thêm padding/resample/filter/gate/median/noise. Projection nearestcenter vềcanonical25/10, halfhop+1sample, tiesearlier; rangepolicy70–400, lưu mọi rawfrequency trướcpolicy.

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
| swipe_t0.2 | phone_F1.wav | 1.22968 | 0.939318 | 0.722682 | 2.02703 | 0.906109 | 0.934641 | 0 | 1 |
| swipe_t0.2 | phone_M1.wav | 0.839985 | 0.593676 | 0.633176 | 1.2931 | 0.889961 | 0.913934 | 3 | 1 |
| swipe_t0.2 | studio_F1.wav | 4.66682 | 1.45451 | 3.09713 | 9.44882 | 0.893091 | 0.98374 | 12 | 1 |
| swipe_t0.2 | studio_M1.wav | 33.4636 | 7.32042 | 18.6802 | 74.3902 | 0.78591 | 0.851064 | 58 | 1 |
| swipe_t0.3 | phone_F1.wav | 4.30305 | 0.945342 | 0.477322 | 11.4865 | 0.872975 | 0.843137 | 0 | 1 |
| swipe_t0.3 | phone_M1.wav | 6.42068 | 0.978692 | 1.47302 | 16.8103 | 0.795933 | 0.790984 | 0 | 1 |
| swipe_t0.3 | studio_F1.wav | 2.5898 | 0.388175 | 1.082 | 6.29921 | 0.909259 | 0.943089 | 2 | 1 |
| swipe_t0.3 | studio_M1.wav | 14.7426 | 6.18655 | 16.09 | 21.9512 | 0.811311 | 0.819149 | 22 | 1 |
| swipe_t0.4 | phone_F1.wav | 9.12745 | 1.63165 | 0.0750103 | 25.6757 | 0.799466 | 0.718954 | 0 | 1 |
| swipe_t0.4 | phone_M1.wav | 16.2581 | 3.96655 | 4.29065 | 40.5172 | 0.630822 | 0.565574 | 0 | 1 |
| swipe_t0.4 | studio_F1.wav | 6.88429 | 0.239598 | 3.87784 | 16.5354 | 0.832113 | 0.861789 | 0 | 1 |
| swipe_t0.4 | studio_M1.wav | 10.6086 | 0.571727 | 8.08345 | 23.1707 | 0.676253 | 0.638298 | 2 | 1 |
| swipe_t0.5 | phone_F1.wav | 20.2077 | 3.42141 | 15.3099 | 41.8919 | 0.696418 | 0.562092 | 0 | 1 |
| swipe_t0.5 | phone_M1.wav | 40.9 | 14.0825 | 23.7036 | 84.9138 | 0.311634 | 0.143443 | 0 | 1 |
| swipe_t0.5 | studio_F1.wav | 11.3405 | 0.0800836 | 2.44521 | 31.4961 | 0.7 | 0.707317 | 0 | 1 |
| swipe_t0.5 | studio_M1.wav | 25.8934 | 6.28434 | 4.3228 | 67.0732 | 0.436816 | 0.287234 | 0 | 1 |

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

Mục tiêu mỗi file≤2% riêng. No actualfit; inner minmax/mean/ID chỉ chọnthreshold. Outerheld khôngselection; lịch sửn4 làmnestedexploratory. LAB chỉfile-stat/nhãnđoạn, khôngF0từngkhung. Đây là wholepipeline comparison, không claim đãđọcfullpaper. Khôngpromote/test/Drive/deeplearning/PDF hoặcretryJev.

![Nested](figures/H34_nested.png)

Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/swipe_reference.py H34
