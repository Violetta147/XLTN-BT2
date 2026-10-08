# H65 — global HPS3 không cải thiện BT2

**FAIL; không promote và không test mới.** H65 được prereg tại `b9f472521d9a0a86a2668054bb92aca45c97e3f5`, push và remoteSHA khớp trước train. Rollback `5668306620062a9fde8fc71648563aec371e3bb3`; baseline `hard170` giữ nguyên. Vòng mới chỉ đo globalHPS3 trên train một lần; accepted inference và synthetic H64 không chạy lại.

## Kết quả train đã đo

Average MAPE (%) dưới đây là trung bình lỗi tương đối F0mean/F0std/F0num so teacher3GT thống kê cả file; không là độ chính xác F0 từng khung. File-level population std, cùng PCM25ms/hop10ms và mask baseline.

| File train | hard170 | global_hps_3 | Số khung F0 cả hai |
|---|---:|---:|---:|
| phone_F1.wav | 0.340080 | 63.276892 | 147 |
| phone_M1.wav | 0.776151 | 57.729610 | 233 |
| studio_F1.wav | 1.473576 | 6.303452 | 123 |
| studio_M1.wav | 1.909923 | 25.385793 | 85 |
| Mean bốn file | 1.124932 | 38.173937 | Tổng588 |

MAE F0mean trung bình file1.070616→15.494402Hz, MAE F0std .195550→21.097656Hz. Mask giữ nguyên nên F0num/MAPEcount, macroF1 .893977, recallV .929270, recallUV .899399, balancedaccuracy .914335 và false_voiced_sil0 giống nhau; full per-filemetrics trong `results/H65_fixed.csv`.

Minimax chọn hard170 ởfinal và mọiouterheldfile. Train/LOFO/nested selectedcandidate đều làbaseline, mean1.124932%; không được gọi là globalHPS3 đạt cả4<2%. Ba relative-improvement gatesFAIL (train10%,nested5%,selectedLOFO5%); nămguardkhácPASS. `eligible=false`, `each_nested_file_below_2=true` chỉ vìselector giữbaseline; không chứng minhall8PASS.

Changedcases:144/588khung đổi hơn100cents và93/588hơn600cents so baseline. GlobalHPS3 chạm endpoint ở1/147phone_F1 và5/85studio_M1, khôngendpoint ởhai file còn lại. Đổi nhiều soanchor phù hợp nguy cơ sai octave/harmonic nhưng không có frameF0GT để xác định93khung thật sự sai octave. Không ép contour/thống kê hoặc chọnorder khác sau đo.

## Kiểm chứng và thực thi

- 8unique train metricgroups (4cachedbaseline +4newglobalHPS3),32innertraces,24summaryrows;0model/label fits. Nested4outer/3inner/final4LOFO chọnoption theofile; no random frame split.
- `results/H65_verification.json`: PASS8groups/588voicedframeoptions. DFT trực tiếp mọi harmonic bins cần dùng, scalarlinear interpolation/logproduct/fullgridargmax; toàn bộpitch/score/boundary/mask/count khớp. Scalarstatistics/selection/inner membership vàprotectedhashesPASS. ScipyFFT chỉreuse để lấy globalnormalizer; gatecode giữnguyên, khôngverifyindependentgateimplementation.
- Precheck tái dùng18order3PASS củaH64, không rerun; H64order5FAIL được bảo tồn. Check hashsource/data/registry/notebook trước đo; H63 sources không đổi.
- Lệnh localCPU: `C:/Users/violet/miniconda3/python.exe -X utf8 research_workbench_2026_10_07/global_hps3_experiment.py train`, rồi `.../verify_global_hps3.py`. Runtime versions/seconds/hashartifacts trong `results/H65_train_experiment.json`; registry trongH65_REGISTRY.json. Không huấn luyện deep learning hoặc thiếu GPU.

## Giới hạn và trạng thái

SyntheticPASS chỉcorrectness/fixture behavior, không bảo đảm dữ liệu tiếng nói thật. Repeatedselection trên4train vàtesthistory vẫnexploratory; khôngclaimspeakerindependent/generalization. Acceptedbaselineall8vẫnFAIL theoH48test đã lưu; không đo lại test/H00–H64, không sửa original/frozen/WAV/LAB/teacher3GT/notebook nộp.

Đã cài10skill ML/DL/research theo `docs/skills/ML_RESEARCH_SKILLS_2026-10-08.md`; chỉ `ml-pipeline-workflow` tham gia quản lýcontract/cache/ablation trongH64/H65. Không coi cài skill là runtimeGPUđã chạy hoặc chứng minh chất lượng nghiên cứu. Người dùng sẵn sàng hỗ trợ notebookColab khi localGPUkhông đủ; cần thiết kế một thí nghiệm cho phépGPUtrước, vẫnkhôngGoogleDrive/DLtrongBT2.

Không còn thí nghiệm đang chạy. Chưa đăng kýH66. Bước mở vẫn là xác minh referenceprocedure/timing hoặc thuật toán classical khác có nguồn và prereg riêng; không tự lặp globalHPS hay boundedHPS đã xong. Bài phân đoạn mới chưa chuyển sang.
