# H63 — HPS có gain riêng nhưng không thắng lựa chọn theo file

Đã tiếp tục theo yêu cầu mới ngày08/10/2026, khôi phục local/remote `e06e382` sạch; không rerun H00–H62. Prereg `c62ba22beeeeeead694783134cb5c307c18c4b1e` commit/push/remoteSHA verified trước đo. H63 custom bounded log-HPS giữ mask/count: **final chọn hard170, ba outer chọn hard170, outer giữ studio_M1 chọn hps_5 rồi chấm file đó 2.678125%. Gate FAIL, không promote, không test mới.**

Average MAPE (%) là trung bình ba sai số tương đối của mean/std/count so teacher3GT, không sai số F0 từng khung.

| Train file | hard170 | HPS 3 | HPS 5 |
|---|---:|---:|---:|
| phone_F1.wav | 0.340080 | 1.817445 | 1.192487 |
| phone_M1.wav | 0.776151 | 1.091550 | 1.332293 |
| studio_F1.wav | 1.473576 | 1.728288 | 1.319059 |
| studio_M1.wav | 1.909923 | 3.618171 | 2.678125 |

HPS5 studio_F1 giảm1.473576→1.319059 nhờ F0mean MAPE1.084873→.414736, nhưng F0std MAPE.186249→.392833 xấu hơn. Cả ba file còn lại Average MAPE xấu hơn baseline. HPS3 phone_F1 meanMAPE tốt hơn .254931→.170736 nhưng stdMAPE tăng .089632→4.605924, nên Average MAPE tăng. Không lấy mean improvement làm kết luận toàn pipeline tốt.

Nested Average MAPE1.124932→1.316983%; train/finalLOFO giữ1.124932 vì chọnbaseline. Ba gate giảmMAPE train10%/nested5%/selectedLOFO5% FAIL; năm guard còn lại PASS. Nested candidate3/4file<2; finalbaseline4/4train<2, testH48 lịch sử0/4<2; **all8 vẫn FAIL**. Không dùng test chọn option hoặc tạo điểm test mới, không chọn algorithm riêng theo file.

Mask/VUV/SIL giữ nguyên trên588khung F0: phoneF1=147,phoneM1=233,studioF1=123,studioM1=85. MacroF1 trung bìnhfile .893977,recallV .929270,recallUV .899399,balancedaccuracy .914335; false_voiced_sil tổng0. F0numMAPE lần lượt .675676/.431034/3.149606/3.658537%, không được sửa vì thí nghiệm không thaymask. F0mean/F0std HzMAE nested từ1.070616/.195550 thành1.270082/.302608. CSV fullmetrics lưu TP/TN/FP/FN, count và cảba componentMAPE.

Boundary hits HPS3/HPS5: phoneF1 14/8 trên147; phoneM1 13/15 trên233; studioF1 8/4 trên123; studioM1 7/8 trên85. Đây là tới biên search±100cents, không chứng minh octaveerror hoặc pitch đúng/sai. Changed_cases chứa mọi originalV được xét, không chỉ khung có gain; label/time/anchor/output/score/bound/fallback đủaudit. Không có F0 chuẩn từngtimestamp trong BT2.

Verifier PASS12groups,1176frame-option decisions: trực tiếp DFT tại mọi FFTbin cần nội suy, scalarlog objective/toàngridargmax; PCM/grid/LAB/3GT,mask/count,metric,48innertraces và24summaryrows; independentminimaxselection; giữ támgatecode. ScipyFFT chỉ dùng maximum của toàn spectrum để normalize, không coi toànFFT independent implementation. Precheck36syntheticnoisefixtures PASS,zeroinputfallback/gainDCinvariance; noise seeds không MLtrainingseeds. Khôngfitmodel hoặc học nhãn. Hash sources/data/H47cache/frozen/notebookđãnộp đềuPASS; originalnotebookSHA b643a1cdf6ac67d3e1dcacf9ce45ea4c49625da114e8c07f402c3fca5d13f85c.

Chạy từ `C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2` bằng `C:/Users/violet/miniconda3/python.exe`:

```powershell
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/hps_experiment.py precheck
# commit/push và kiểm remote trước lệnh train
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/hps_experiment.py train
& 'C:/Users/violet/miniconda3/python.exe' research_workbench_2026_10_07/verify_hps.py
```

Runtime/source/config/data hashes trong H63_REGISTRY.json/H63_train_experiment.json; results H63_fixed/metrics/inner_traces/changed_cases/boundaries CSV, predictions NPZ,precheck/verification JSON. Timing1.015s là train-loop tại runtime trongreceipt, không gồm startup/verification và không suy thành benchmark tốc độ với pipeline khác. Rawfailures giữ nguyên. HPS_SOURCE_REVIEW.md ghi primaryHTML/code và softwarecitation ScientificAgentSkills đã xác minh; khôngPDF/Jev/Drive/DL/proseskill. Không đổi frozen/reference/notebook, không chuyển bài phân đoạn.

Giới hạn: đây chỉ là boundedHPS3/5 25ms, không thử toàn bộ HPS hoặc PEFAC. Zero-padding không tăng độ phân giải vật lý. Repeatedfile-selection và exposuretest cũ khiến số vẫnexploratory. Không quyfail cho ítdata/GT/test; hướng tiếp là referencePEFAC hoặc xác minh quy trình reference, cần prereg riêng trước BT2.
