# H44 — Trộn mềm NAMDF25/40ms theo phổ và cao độ

| model | split | average_mape | F0mean_mape | F0std_mape | F0num_mape | F0mean_abs_error | F0std_abs_error | macro_f1 | balanced_accuracy | recall_v | recall_uv | TP | TN | FP | FN | false_voiced_sil | F0num |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted | train | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | lofo | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| accepted | nested | 1.62246 | 0.587195 | 2.30146 | 1.97871 | 0.95591 | 0.59029 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | train | 1.12493 | 0.586176 | 0.809907 | 1.97871 | 1.07062 | 0.19555 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | lofo | 1.12493 | 0.586176 | 0.809907 | 1.97871 | 1.07062 | 0.19555 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |
| candidate | nested | 1.25076 | 0.631445 | 1.14213 | 1.97871 | 1.12353 | 0.283257 | 0.893977 | 0.914335 | 0.92927 | 0.899399 | 575 | 167 | 13 | 39 | 0 | 588 |

Tỷ lệ năng lượng trên1kHz từ raw40ms, bỏDC, Hann, FFT một phía có trọng số đối xứng. Nếuratio≤.05, alpha40=clip((gateF0−center)/width+.5,0,1), cònlại0; F0=f25*2**(alpha*log2(f40/f25)), exactendpoints. Center140/170/200Hz,width20/40Hz. H43hard170ablation giữ. Band200cents/Praat.30/voicing/count và projection giữ H41. Không dựa tênfile/giới tính/device/LAB/GT lúc infer. Đây là engineering hypothesis, không paper replication.

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
| studio_M1.wav | amdf_soft_c140_w40 |

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
| amdf_pitch_spectral_p170 | phone_F1.wav | 0.34008 | 0.254931 | 0.0896324 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_pitch_spectral_p170 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_pitch_spectral_p170 | studio_F1.wav | 1.47358 | 1.08487 | 0.186249 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_pitch_spectral_p170 | studio_M1.wav | 1.90992 | 0.0161649 | 2.05507 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_soft_c140_w20 | phone_F1.wav | 0.34008 | 0.254931 | 0.0896324 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_soft_c140_w20 | phone_M1.wav | 0.750842 | 0.998913 | 0.822577 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_soft_c140_w20 | studio_F1.wav | 1.43556 | 1.10692 | 0.0501592 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_soft_c140_w20 | studio_M1.wav | 2.44939 | 0.220098 | 3.46955 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_soft_c140_w40 | phone_F1.wav | 0.34008 | 0.254931 | 0.0896324 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_soft_c140_w40 | phone_M1.wav | 0.747525 | 1.00057 | 0.810973 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_soft_c140_w40 | studio_F1.wav | 1.43556 | 1.10692 | 0.0501592 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_soft_c140_w40 | studio_M1.wav | 2.41325 | 0.19724 | 3.38397 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_soft_c170_w20 | phone_F1.wav | 0.358593 | 0.242158 | 0.157945 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_soft_c170_w20 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_soft_c170_w20 | studio_F1.wav | 1.47669 | 1.08282 | 0.197631 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_soft_c170_w20 | studio_M1.wav | 1.91235 | 0.0161087 | 2.06241 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_soft_c170_w40 | phone_F1.wav | 0.376718 | 0.238905 | 0.215574 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_soft_c170_w40 | phone_M1.wav | 0.775177 | 0.988918 | 0.905578 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_soft_c170_w40 | studio_F1.wav | 1.48532 | 1.07838 | 0.227976 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_soft_c170_w40 | studio_M1.wav | 2.02856 | 0.0258698 | 2.40128 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_soft_c200_w20 | phone_F1.wav | 0.679574 | 0.157818 | 1.20523 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_soft_c200_w20 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_soft_c200_w20 | studio_F1.wav | 1.64734 | 1.0099 | 0.782525 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_soft_c200_w20 | studio_M1.wav | 1.94049 | 0.0045515 | 2.1584 | 3.65854 | 0.808446 | 0.861702 | 0 |
| amdf_soft_c200_w40 | phone_F1.wav | 0.613071 | 0.168482 | 0.995055 | 0.675676 | 0.938333 | 0.941176 | 0 |
| amdf_soft_c200_w40 | phone_M1.wav | 0.776151 | 0.988737 | 0.908681 | 0.431034 | 0.928721 | 0.946721 | 0 |
| amdf_soft_c200_w40 | studio_F1.wav | 1.62826 | 1.01854 | 0.716626 | 3.14961 | 0.900407 | 0.96748 | 0 |
| amdf_soft_c200_w40 | studio_M1.wav | 1.94049 | 0.0045515 | 2.1584 | 3.65854 | 0.808446 | 0.861702 | 0 |

Mỗi nested file Average MAPE≤2%: False. MAPE là thống kê mean/std/count, không F0 từng khung. Nested exploratory trên4train đã xem nhiều lần.

H41 curves/gate được tái sử dụng có hash; H44 có0nativecall mới,4historicalsourcegroups. Source note: H44_REGISTRATION.md. Dữ liệu QA test đã đọc mô tả ở lượt trước, không dùng chọn feature/grid/ngưỡng. Không test inference/tuning hoặc sửa ground truth. Giữ failures/original/frozen, không promote tự động, khôngMCP retry/Drive/PDF/deep learning.

Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/amdf_soft_spectral_controller.py H44

## Kiểm tra và hướng nối tiếp

Preregistration `8ed9d7d` đã push và xác minh remote trước đo. Verifier độc lập PASS: 144 inner traces, 152 fit logs, 36 fixed groups, 1176 curve rows từ PCM, 588 spectral rows bằng FFT đầy đủ; lựa chọn, alpha/log-blend, thống kê, nhãn, gate và control H41/H43 khớp. Figure layout đã xem. Không có native call mới; đây là tính quy tắc mới trên evidence H41 đã kiểm tra hash, không phải thu âm mới.

Studio_M1 giảm từ H43nested2.523880% xuống H44nested2.413248%, chưa đạt2%. Count85 soGT82 giữ nguyên; F0std25.506633 soGT26.4 khiến stdMAPE3.383967%. Finalhard170 có kết quả fixed tốt nhưng outer chọnsoft140/w40 từ ba file khác. Không dùng fixed tốt để gọi nested đạt và không bỏ candidate đã thất bại sau đo. Giữ baseline/frozen, toàn bộ failure và source H44. Hướng kết hợp cấu hình để giảm độ nhạy lựa chọn là giả thuyết vòng sau, chưa đo trong H44.
