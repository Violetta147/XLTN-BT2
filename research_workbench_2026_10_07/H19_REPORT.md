# H19 — tuning có vòng chọn bên trong

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 6.17797 | 0.583562 | 11.3078 | 6.64251 | 0.854436 | 2.33158 | 0.850371 | 0.900215 | 0.869123 | 0.931306 | 530 | 167 | 13 | 84 | 1 | 544 |
| accepted | lofo | 7.27924 | 1.05571 | 14.6661 | 6.1159 | 1.84025 | 3.0133 | 0.841398 | 0.893149 | 0.865862 | 0.920437 | 527 | 164 | 16 | 87 | 3 | 546 |
| accepted | nested | 7.27924 | 1.05571 | 14.6661 | 6.1159 | 1.84025 | 3.0133 | 0.841398 | 0.893149 | 0.865862 | 0.920437 | 527 | 164 | 16 | 87 | 3 | 546 |
| candidate | train | 3.82202 | 1.03711 | 3.67285 | 6.75609 | 1.66997 | 0.827474 | 0.845629 | 0.894387 | 0.870631 | 0.918143 | 534 | 167 | 13 | 80 | 1 | 548 |
| candidate | lofo | 3.81576 | 0.75773 | 2.33931 | 8.35023 | 1.38297 | 0.500825 | 0.845408 | 0.896123 | 0.867974 | 0.924272 | 531 | 170 | 10 | 83 | 1 | 542 |
| candidate | nested | 8.51322 | 1.34596 | 14.2189 | 9.97482 | 2.02481 | 2.9621 | 0.838484 | 0.894746 | 0.854401 | 0.935091 | 513 | 171 | 9 | 101 | 1 | 523 |

## Tiêu chí đã đăng ký

~~~json
{
  "checks": {
    "train_mape_relative_10_percent": true,
    "lofo_mape_relative_5_percent": false,
    "lofo_f1_drop_at_most_01": true,
    "lofo_recall_v_drop_at_most_01": false,
    "lofo_sil_increase_at_most_1": true,
    "lofo_no_file_mape_worse_by_over_2pp": false,
    "lofo_phone_f1_std_not_worse": true,
    "selected_lofo_mape_relative_5_percent": true
  },
  "eligible": false,
  "nested_status": "Outer file excluded from every inner fit and selection; selected LOFO is separate.",
  "champion_promoted": false
}
~~~

## Lựa chọn theo fold

| outer_held | id | kind | low_hz | high_hz | frame_ms | hop_ms | C |
| --- | --- | --- | --- | --- | --- | --- | --- |
| final | lp_0_800_f25_h20_lr0.1 | lp | 0 | 800 | 25 | 20 | 0.1 |
| phone_F1.wav | lp_0_1500_f20_h5_lr0.1 | lp | 0 | 1500 | 20 | 5 | 0.1 |
| phone_M1.wav | hp_60_0_f40_h10_lr10 | hp | 60 | 0 | 40 | 10 | 10 |
| studio_F1.wav | raw_0_0_f25_h10 | raw | 0 | 0 | 25 | 10 | nan |
| studio_M1.wav | hp_60_0_f25_h20_lr0.1 | hp | 60 | 0 | 25 | 20 | 0.1 |

Giữ champion; các kết quả không đạt cũng được lưu. Selected LOFO có ảnh hưởng lựa chọn, đọc nested để đánh giá quy trình. Registry được đề xuất sau lịch sử đã xem bốn file nên nested vẫn là thăm dò.

Chấm trên cùng grid baseline25/10, native hop được thay đổi thật. Nearest center trong half-hop, ngoài hỗ trợ là abstention; không nội suy F0 qua khoảng vô thanh. Count trên grid này là output đại diện để đối chiếu 3GT cũ, không phải contour GT mới. Xem nativecount/projection coverage trong CSV.

RMS lấy từ raw frame; bộ lọc chỉ tác động pitch features. SOS causal initial-rest, không bù phase delay theo nhãn; transient/boundary có thể ảnh hưởng. Median3 và jump giữ cố định nên thay hop cũng thay thời gian smoothing; không kết luận nhân quả riêng từ cấu hình joint.

![Nested](figures/H19_nested.png)

Lệnh: `python research_workbench_2026_10_07/tuning.py H19`

Nguồn thiết kế: [SciPy butter](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.butter.html), [sosfilt](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.sosfilt.html). Phiên bản thực được lưu trong JSON.
