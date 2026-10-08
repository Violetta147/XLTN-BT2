# Bắt đầu chat mới — XLTN / BT2

Cập nhật 08/10/2026, sau **R01, H67, H68, R02 và H69**: tất cả hoàn tất, chưa có thuật toán được promote, không có tiến trình thí nghiệm đang chạy. Không chạy lại H00–H69 hoặc R01/R02 để khôi phục. Bài phân đoạn mới trong `../XLTN-BT1-BO-SUNG/` vẫn làm sau BT2.

Thông tin mới từ người dùng: **thầy yêu cầu cửa sổ tín hiệu thực sự 25 ms, bước 10 ms**; người dùng cho phép khảo sát tham số tùy ý trong nghiên cứu. hard170 không đáp ứng cửa sổ thực sự 25 ms, dù metric được tính trên lưới 25/10 ms. Không gọi nó là bản nộp phù hợp. Đọc [audit cửa sổ](research_workbench_2026_10_07/FRAME_25MS_AUDIT.md) và quy tắc mới trong AGENTS.md trước phép thử tiếp theo.

## Khôi phục nhanh

1. Đọc hướng dẫn workspace XLTN của người dùng, [AGENTS.md](AGENTS.md) và file này. Không quét toàn bộ STATE hoặc chạy lại thí nghiệm.
2. Đọc [H69_REPORT](research_workbench_2026_10_07/H69_REPORT.md), [R02_DISTRIBUTION_REPORT](research_workbench_2026_10_07/R02_DISTRIBUTION_REPORT.md) và [REFERENCE_PROCEDURE_AUDIT](research_workbench_2026_10_07/REFERENCE_PROCEDURE_AUDIT.md). Khi cần ba hướng đã hoàn tất, đọc [H67_REPORT](research_workbench_2026_10_07/H67_REPORT.md) / [H68_REPORT](research_workbench_2026_10_07/H68_REPORT.md).
3. Kiểm tra Git branch, status, HEAD và SHA remote. Mốc kết quả H69 đã push và xác minh: `4f15a070dbb55b9b0761c0a37847ec5f8a95a9de`; quy tắc 25 ms tại `c2cb69520a2d178357dc36d43c4879f4956efa19`. Có commit bàn giao sau các mốc này; xác minh live, không coi chúng là HEAD bắt buộc.
4. Xem [coverage](research_workbench_2026_10_07/EXPERIMENT_COVERAGE.md), [protocol](research_workbench_2026_10_07/PROTOCOL_F0.md) nếu cần. [Bàn giao trước vòng mới](docs/handoff/START_NEXT_CHAT_before_R01_H67_H69_2026_10_08.md) và STATE chứa các trạng thái lịch sử như “H67 chưa đăng ký / PEFAC chưa đo”; không coi đó là trạng thái hiện tại.

Repo: `C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2`; branch `codex/train-mape-investigation`; remote `https://github.com/Violetta147/XLTN-BT2.git`. PowerShell; Python chính `C:/Users/violet/miniconda3/python.exe`. Venv pYIN: `C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/.venv-bt2-pyin/Scripts/python.exe` (librosa 0.11.0, Python 3.13.11). Không cần GPU hoặc Colab trong các vòng vừa rồi.

```powershell
git -c 'safe.directory=C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2' status --short --branch
git -c 'safe.directory=C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2' rev-parse HEAD
git -c 'safe.directory=C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2' ls-remote origin refs/heads/codex/train-mape-investigation
```

## Những việc đã hoàn tất

| Vòng | Phạm vi và kết quả | Giới hạn cần giữ |
|---|---|---|
| R01 | 16 suy luận train mới bằng Praat 6.1.38 raw AC/CC, bước mặc định/10 ms; đối chiếu Praat7/pYIN/Harvest đã lưu. Không phương án nào khớp cả ba thống kê ở cả bốn file. | Không biết phần mềm, phiên bản, ngưỡng hoặc cách đếm của thầy. Không có phân phối/F0 từng khung của thầy. |
| H67 | Custom harmonic regression với nhiễu residual AR4; 36 fixture PASS, 8 nhóm metric/588 nuisance fits, verifier PASS. AR4 MAPEs .441333/1.057928/1.254905/2.194889%; final hard170, outer studio_M1 chọn AR4 rồi thất bại. | Ba gate MAPE FAIL, không test/promote. Không joint-ML/reference implementation; mask/anchor vẫn kế thừa cửa sổ dài của hard170. |
| H68 | **PEFAC thật** từ Imperial sap-voicebox pin f671f6d, chạy Octave; bốn train native inferences, 20 nhóm metric. Final/mọi outer hard170; verifier GMM/DP/projection/metric PASS. Whole pv>.5 MAPEs 28.360641/19.356367/9.549223/9.605462%. | Cửa sổ native khoảng 90,5 ms, không phù hợp bài 25 ms. Precheck tích hợp PASS nhưng độ chính xác chỉ 4/6 fixture (300→150,57 Hz); giữ cả thất bại. Không độc lập tính lại toàn bộ spectrogram hoặc MATLAB parity. |
| R02 | Phân tích 60 nhóm từ cache, 44 kiểm tra native-stat parity và ba hình histogram/ECDF/ratio; không suy luận F0 mới. | Chỉ có ba thống kê chuẩn, không tự vẽ “phân phối chuẩn của thầy”. Initial registry-hash failure trước thống kê đã lưu; sửa hash rồi push trước phân tích. |
| H69 | pYIN **thực sự 25 ms**, ba beta priors `(2,8)/(2,18)/(2,38)`, 12 train inferences/16 metric groups. `(2,18)` tốt nhất thống nhất: 5.447286/6.056821/1.465577/.699716%, mean 3.417350%; 2/4 train dưới 2%. | `(2,38)` có 0 khung V trên studio_M1, metric NaN, không hợp lệ. V1 verifier dừng do NaN; v2 cuối PASS16 nhóm sau sửa parse/so giá trị thiếu, mọi lỗi trung gian lưu. Gate FAIL, không test/promote. |

H67 prereg `79538f49e4b47ecc23a4ab529b446e69fba73bf0`, results `a9e55b4fd54df974c37b4a461e021bbf56bee268`. H68 đo sau prereg và commit phục hồi `.gitattributes` `dffb1d44a1cbbfdb37b1800618a13207d89a30cd`, results `2793d22f583b392f7b1a9e9e256a4cc51b26b8af`. R01 prereg `8a7af15cfc2df4c89d769327e21b41c7d773dfa4`, results `9b760e9842a2c2f8abc87f0c11869cb6d5a8bed3`. R02 trước phân tích `93d5fac170e6d682b5d3005a0fd5672b2ddd8470`, results/audit `71adee56b7e5b35326eafd7a8ce6fb3ff8128679`. H69 prereg `ee4b08b682f69d29e37f7ed0725bb2823a514fe4`, results `4f15a070dbb55b9b0761c0a37847ec5f8a95a9de`. Các mốc trên đã push và xác minh remote trong phiên. Không sửa source/registry cũ sau đo; verifier H69v2 là file mới và có [ghi chú](research_workbench_2026_10_07/H69_VERIFICATION_NOTE.md).

GNU Octave 11.3.0 đã cài local, executable thực tế `C:/Users/LAPTOP T&T/AppData/Local/Programs/GNU Octave/Octave-11.3.0/mingw64/bin/octave-cli.exe`, image 2.20.0. Installer không dùng thư mục đích đề nghị; lấy path thực tế từ log. PEFAC vendor 520 m-files cùng giấy phép/provenance, không dùng hàm ACF mang tên PEFAC từ pyvoicebox đã bị loại ở source review. `.gitattributes` giữ **cả** rules MAPS và PEFAC `-text`.

## Pattern đã tìm thấy

- Praat raw AC 75–600 trên phone_M1: **9/235 F0 >400 Hz**, chiếm **90,981744%** tổng bình phương độ lệch; std 70,982954 Hz so chuẩn 16,8 Hz. Độ rộng (p95−p05)/3,2897073 =16,690747 Hz gần chuẩn, nhưng IQR không khớp. Đây là pattern đuôi phân phối, không chứng minh thầy đã trim hoặc dữ liệu Gaussian. Xóa chín điểm còn 226, không bằng count chuẩn 232.
- Praat filtered/pYIN native 40 ms có std gần chuẩn ở bốn train file nhưng count thiếu/thừa tùy file, không khớp cả ba thống kê. Praat CC auto bước khoảng 3,33 ms tạo count gần gấp ba so 10 ms; Praat AC auto ở floor75 là 10 ms và trùng kết quả 10 ms. Khác biệt count có thể đến từ mật độ thời gian và quyết định V/UV, chưa biết quy trình thầy.
- H69 pYIN25 mặc định: std 20,632340/16,578512/36,992202/26,576790 Hz gần chuẩn 20,6/16,8/36,8/26,4; count126/196/131/83 so148/232/127/82. Với `(2,8)`, count157/235/144/134: phone_M1 tốt riêng, nhưng SIL bị gọi V ở studio nhiều (15/45).
- Hai bản teacher stats thay đổi mean/std theo cả hai chiều; không có phép dịch hoặc scale thống nhất đã xác nhận. LAB V counts cũng không bằng teacher F0num ở cả tám file. Không suy diễn thầy dùng sai thuật toán hoặc GT sai.

Xem hình R02 trong `research_workbench_2026_10_07/figures/`. Không dùng thống kê cả file để chứng nhận F0 từng khung; không cắt giá trị để ép khớp GT.

## Baseline và mục tiêu còn thiếu

hard170 là **đối chứng nghiên cứu lịch sử không tuân thủ cửa sổ 25 ms**: Praat7 filtered ACF, range70–400, voicing .30; NAMDF gần Praat trong200 cents; có nhánh 40 ms khi high-frequency ratio<=.05 và Praat>=170 Hz; V/UV/anchor Praat cũng dùng cửa sổ dài hơn. Lưới chấm25/10ms và population std không làm native window trở thành25ms.

| File train | Average MAPE (%) | File test đã lưu H48 | Average MAPE (%) |
|---|---:|---|---:|
| phone_F1 | .340080 | phone_F2 | 4.197313 |
| phone_M1 | .776151 | phone_M2 | 6.833750 |
| studio_F1 | 1.473576 | studio_F2 | 5.063462 |
| studio_M1 | 1.909923 | studio_M2 | 2.114791 |

Mục tiêu **từng file trong cả tám file <2% vẫn FAIL**; 4/4 train và 0/4 test của đối chứng lịch sử không đủ. Test ở bảng này chỉ đọc số đã lưu; R01/H67/H68/R02/H69 không suy luận test mới. Nested trên bốn train vẫn exploratory do lịch sử chọn nhiều cấu hình và test đã từng xem. Không random-split frames, chọn theo test hoặc ghép cấu hình theo tên file.

Baseline ACF25 full-train đã lưu tại `research_3gt_2026_10_05/results/baseline_summary.json`: MAPE29,834711%, F1.848791, SIL45; AMDF_energy25:12,270267%, F1.869716, SIL0. pYIN25 mặc định H69 thấp hơn về MAPE mô tả nhưng F1.816298, SIL3; đây không phải phép so nested giống nhau hoặc baseline mới đã được chấp nhận. Chưa audit đầy đủ mọi pipeline lịch sử về cửa sổ thực sự25ms, không tuyên bố H69 tốt nhất toàn bộ lịch sử.

Notebook đã nộp: `../turn-in-assignment - Copy/BT2_ACF_best_no_energy_set.ipynb`, SHA256 `b643a1cdf6ac67d3e1dcacf9ce45ea4c49625da114e8c07f402c3fca5d13f85c`, outputs hiện bằng0. Source chọn frame từ20/25/30 bằngtrain, không hardcode25; không suy từ defaultframing30 rằng runtimecuối30. Không sửa notebook đó hoặc gọi source/charts nghiên cứu là output notebook đã nộp.

## Hướng tiếp theo, chưa đo

H70 **chưa đăng ký/chưa chạy**. Hướng hẹp hợp lý: từ cache H69 kiểm tra các khung dư của `(2,8)` có tập trung ở năng lượng thấp không, rồi đăng ký riêng phép loại bằng năng lượng trên cùng cửa sổ25ms nếu có bằng chứng. Không dùng mask Praat hoặc cửa sổ dài để đáp ứng25ms. Có thể nghiên cứu tham số khác, nhưng khóa giả thuyết/config/gate/hash và push/xác minh remote trước đo; giữ các failure và không chạy lại family đã hoàn tất. Ưu tiên một pipeline thống nhất, không routephone/studio theo tên file.

Nếu muốn thử MathWorks pitch NCF/PEF/CEP/LHS/SRH: docs hỗ trợ `WindowLength`/`OverlapLength` nên có thể cấu hình25/10, nhưng **chưa có MATLAB/license và chưa đo**; `loc` là vị trí mẫu cuối cửa sổ, không phải tâm. Không coi đây là phần mềm thầy đã dùng. Không mua license hoặc đòi GPU chỉ để chạy phép thử CPU này.

## Những ràng buộc giữ nguyên

Tuyệt đối khôngGoogleDrive/GDrive. Local; Colab chỉ khi cần và chuyển trực tiếp qua Chrome, không quaDrive. Khôngdeep learning, khôngPDF/extractPDF, khôngprose/reader-firstskill, khôngschedule/automaticretry. Không sửa WAV/LAB/teacher3GT, baselinefrozen hoặc notebookgốc. Mỗi thay đổi đã kiểm tra commit riêng, push và xác minh SHAremote; không merge main. Jev không tham gia các vòng vừa rồi; lỗi MCP lịch sử không tự retry. Đọc docs/jev/HUONG_DAN_JEV.md trước usecase mới.

Dùng experimental-design và literature-review local với HTML/abstract/mã nguồn, khôngclaim đọc fullpaper. [Scientific Agent Skills](https://arxiv.org/abs/2609.00065), DOI10.48550/arXiv.2609.00065. Mười skill ML/DL/research đã cài trong `docs/skills/ML_RESEARCH_SKILLS_2026-10-08.md`; có skilldeep learning không thay quy tắc cấmDL cho BT2.

## Prompt tiếp tục

> Đọc AGENTS.md và START_NEXT_CHAT.md trong XLTN-BT2, khôi phục sau H69/R02 rồi tiếp tục cải thiện BT2 trước bài phân đoạn mới. Không chạy lại H00–H69 hoặc R01/R02. Có thể khảo sát tham số tự do, nhưng pipeline cuối phải dùng cửa sổ tín hiệu thực sự25ms/bước10ms. Giữ mục tiêu mỗi file trong cả8file AverageMAPE<2%, chọn trêntrain theofile, prereg/commit/push/xác minhremote trướcđo; giữ failures và giới hạn test đã từng xem.
