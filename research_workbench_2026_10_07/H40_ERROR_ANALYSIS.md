# H40 — Phân tích lỗi YAAPT

| option_id | mean | worst | SIL |
| --- | --- | --- | --- |
| praat7_filtered_v0.45 | 2.15699 | 2.76986 | 0 |
| yaapt_f25 | 2.9221 | 6.33433 | 1 |
| yaapt_f35 | 3.57777 | 8.66448 | 2 |
| yaapt_f45 | 4.41368 | 10.7436 | 4 |

YAAPT25 đạt phone_F1 1.043199% và phone_M1 1.160040%, nhưng studio_F1 3.150820%/studio_M1 6.334329%. Không được chọn YAAPT riêng cho phone dựa kết quả chính file đó. Final và cả outer folds chọn controlH30. Nestedmean2.156992%, worst2.769856%, targetfalse/gateFAIL.

## Studio nam: cửa sổ lớn chưa giúp

| option_id | F0mean_mape | F0std_mape | F0num_mape | average_mape | F0num | macro_f1 | recall_v | projection_coverage | false_voiced_sil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| praat7_filtered_v0.45 | 0.0731761 | 3.44047 | 2.43902 | 1.98422 | 84 | 0.799438 | 0.851064 | 0.99262 | 0 |
| yaapt_f25 | 2.52211 | 7.94429 | 8.53659 | 6.33433 | 89 | 0.893592 | 0.925532 | 1 | 0 |
| yaapt_f35 | 2.60249 | 9.9763 | 13.4146 | 8.66448 | 93 | 0.83779 | 0.925532 | 1 | 0 |
| yaapt_f45 | 3.48407 | 11.6735 | 17.0732 | 10.7436 | 96 | 0.832955 | 0.93617 | 0.99262 | 1 |

Cả count và std đều xấu hơn khi tăng frame_length25→35→45. Đây là lỗi thống kê cả file, không chứng minh những khung mất hay tần số nào sai nếu thiếu F0 chuẩn từng khung. Missing support ở đầu/cuối khác với quyết định UV; raw frames/support giữ để tách cơ chế. Không bù count/std bằng GT.

## Tất cả thành phần và đánh đổi

| option_id | file | F0mean_mape | F0std_mape | F0num_mape | average_mape | F0num | macro_f1 | recall_v | false_voiced_sil | projection_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| praat7_filtered_v0.45 | phone_F1.wav | 0.0766879 | 2.1518 | 6.08108 | 2.76986 | 139 | 0.919971 | 0.901961 | 0 | 0.993789 |
| praat7_filtered_v0.45 | phone_M1.wav | 0.797475 | 1.55734 | 2.58621 | 1.64701 | 226 | 0.908301 | 0.922131 | 0 | 0.995169 |
| praat7_filtered_v0.45 | studio_F1.wav | 0.871402 | 1.87223 | 3.93701 | 2.22688 | 122 | 0.889796 | 0.95935 | 0 | 0.996479 |
| praat7_filtered_v0.45 | studio_M1.wav | 0.0731761 | 3.44047 | 2.43902 | 1.98422 | 84 | 0.799438 | 0.851064 | 0 | 0.99262 |
| yaapt_f25 | phone_F1.wav | 1.47765 | 0.976272 | 0.675676 | 1.0432 | 147 | 0.938333 | 0.941176 | 0 | 1 |
| yaapt_f25 | phone_M1.wav | 1.87895 | 0.308062 | 1.2931 | 1.16004 | 229 | 0.902262 | 0.92623 | 0 | 1 |
| yaapt_f25 | studio_F1.wav | 0.927207 | 5.37565 | 3.14961 | 3.15082 | 123 | 0.914286 | 0.96748 | 1 | 1 |
| yaapt_f25 | studio_M1.wav | 2.52211 | 7.94429 | 8.53659 | 6.33433 | 89 | 0.893592 | 0.925532 | 0 | 1 |
| yaapt_f35 | phone_F1.wav | 1.02293 | 2.46326 | 1.35135 | 1.61251 | 146 | 0.933433 | 0.934641 | 0 | 1 |
| yaapt_f35 | phone_M1.wav | 2.54467 | 1.87981 | 1.72414 | 2.04954 | 236 | 0.908738 | 0.942623 | 1 | 1 |
| yaapt_f35 | studio_F1.wav | 0.247004 | 4.13187 | 1.5748 | 1.98456 | 125 | 0.886037 | 0.96748 | 1 | 1 |
| yaapt_f35 | studio_M1.wav | 2.60249 | 9.9763 | 13.4146 | 8.66448 | 93 | 0.83779 | 0.925532 | 0 | 1 |
| yaapt_f45 | phone_F1.wav | 1.26709 | 3.35836 | 3.37838 | 2.66794 | 153 | 0.936914 | 0.960784 | 0 | 0.993789 |
| yaapt_f45 | phone_M1.wav | 2.1601 | 2.09926 | 2.15517 | 2.13818 | 237 | 0.913068 | 0.946721 | 1 | 0.995169 |
| yaapt_f45 | studio_F1.wav | 0.0352701 | 4.70495 | 1.5748 | 2.10501 | 129 | 0.893091 | 0.98374 | 2 | 0.992958 |
| yaapt_f45 | studio_M1.wav | 3.48407 | 11.6735 | 17.0732 | 10.7436 | 96 | 0.832955 | 0.93617 | 1 | 0.99262 |

SIL thấp không đủ: count thiếu và phân bố F0 sai vẫn làm MAPE lớn. Hai file điện thoại/studio và nhãn F/M chỉ là bốn quan sát, không đủ suy rộng về giới tính hoặc thiết bị.

Nguồn: YAAPT_SOURCE_NOTE.md (abstract/manual/code, không fullpaper/PDF). Synthetic rich/sine octave failures giữ. H40 verifier:64traces/68fits/24metrics/16fixedsourcegroups; input normalizedPCM,UV0,timing/params/hash/source/control verified. Không mới WAV/test/backend/MCP call trong diagnostic.
