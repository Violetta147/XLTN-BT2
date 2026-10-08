"""Write a compact stopped-state handoff; never launches experiments."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

REPO=Path(__file__).resolve().parent
WORK=REPO/'research_workbench_2026_10_07'
OUT=WORK/'results'
archive=REPO/'docs/handoff/START_NEXT_CHAT_before_H60_H62_2026_10_08.md'
assert not archive.exists(), 'Preserve handoff archive'
archive.parent.mkdir(parents=True,exist_ok=True)
archive.write_bytes((REPO/'START_NEXT_CHAT.md').read_bytes())
checkpoint=subprocess.check_output(['git','-c','safe.directory='+str(REPO).replace('\\','/'),'-C',str(REPO),'rev-parse','HEAD'],text=True).strip()
assert checkpoint=='bc42283fcb2ec76147a22241faf4c937aef606ba'
for family in ('H60','H61','H62'):
    receipt=json.loads((OUT/f'{family}_train_experiment.json').read_text())
    assert not receipt['decision']['eligible'] and not receipt['test_used']
    assert json.loads((OUT/f'{family}_verification.json').read_text())['status']=='PASS'

handoff=f'''# Bắt đầu chat mới — XLTN / BT2

Cập nhật 08/10/2026. **Loop đã dừng theo yêu cầu người dùng sau khi hoàn tất H62. Không còn vòng thí nghiệm đang chạy; H63 chưa đăng ký hoặc đo.** Đọc hồ sơ không tự cấp yêu cầu chạy tiếp. Chỉ tiếp tục khi người dùng yêu cầu trong chat mới.

Mục tiêu còn thiếu: cùng một pipeline cho **từng file trong cả tám file có Average MAPE <2%**. Cải thiện BT2 tìm F0 trước; bài phân đoạn tiếng nói/khoảng lặng mới của thầy trong `../XLTN-BT1-BO-SUNG/` làm sau. Chưa chuyển bài hoặc tạo notebook thay bản đã nộp.

## Khôi phục nhanh

1. Đọc quy tắc workspace XLTN của người dùng và [AGENTS.md](AGENTS.md) trong repository.
2. Đọc file này, [H62_REPORT.md](research_workbench_2026_10_07/H62_REPORT.md), rồi [ma trận ba vòng](research_workbench_2026_10_07/figures/LOOP_H60_H62_train_matrix.png). Không quét lại toàn bộ STATE hoặc rerun để lấy lại context.
3. Kiểm tra Git branch/status/HEAD/remote hiện tại. Mốc kết quả đã push và xác minh remote trước bàn giao: `{checkpoint}`. HEAD có thể có commit hồ sơ bàn giao sau mốc này; xác minh live, không coi checkpoint là HEAD bắt buộc.
4. Khi cần chi tiết: [H60_REPORT](research_workbench_2026_10_07/H60_REPORT.md), [H61_REPORT](research_workbench_2026_10_07/H61_REPORT.md), [coverage](research_workbench_2026_10_07/EXPERIMENT_COVERAGE.md), [protocol](research_workbench_2026_10_07/PROTOCOL_F0.md). [STATE](research_workbench_2026_10_07/STATE.md) và [handoff cũ](docs/handoff/START_NEXT_CHAT_before_H60_H62_2026_10_08.md) là lịch sử; các dòng cũ “tiếp tục/chưa hoàn tất” không thay trạng thái dừng hiện tại.

Repository: `C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2`; branch `codex/train-mape-investigation`; remote `https://github.com/Violetta147/XLTN-BT2.git`. PowerShell; Python `C:/Users/violet/miniconda3/python.exe`. Không thấy MATLAB/Octave trong PATH ở phiên này. Dùng safe.directory cho Git:

```powershell
git -c 'safe.directory=C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2' status --short --branch
git -c 'safe.directory=C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2' rev-parse HEAD
git -c 'safe.directory=C:/Users/LAPTOP T&T/VIOLETTA/Documents/ChatGPT/XLTN/XLTN-BT2' ls-remote origin refs/heads/codex/train-mape-investigation
```

## Cấu hình nghiên cứu vẫn được giữ

`hard170`: Praat7 filtered ACF voicing .30, range70–400; NAMDF ứng viên gần Praat trong200cents; pitch25ms chuyển40ms theo high-frequency ratio<=.05 và gatePraat>=170Hz. Canonical25ms/10ms, population std, nhãn LAB tại tâm. Đây là baseline nghiên cứu, **khác kết quả screenshot của notebook đã nộp**; không trộn MAPE hai pipeline.

| File | Train Average MAPE (%) | File | Test đã lưu Average MAPE (%) |
|---|---:|---|---:|
| phone_F1.wav | 0.340080 | phone_F2.wav | 4.197313 |
| phone_M1.wav | 0.776151 | phone_M2.wav | 6.833750 |
| studio_F1.wav | 1.473576 | studio_F2.wav | 5.063462 |
| studio_M1.wav | 1.909923 | studio_M2.wav | 2.114791 |

Baseline4/4train dưới2%,0/4test dưới2%: **all8 FAIL**. Số test lấy từ [H48 status](research_workbench_2026_10_07/ALL_FILES_STATUS.md), không đo lại trong H60–H62. Chưa promote/frozen rewrite và chưa có notebook mới được chấp nhận. Bản người dùng nộp là `../turn-in-assignment - Copy/BT2_ACF_best_no_energy_set.ipynb`; SHA256 giữ nguyên `b643a1cdf6ac67d3e1dcacf9ce45ea4c49625da114e8c07f402c3fca5d13f85c`.

## Ba vòng cuối đã hoàn tất

| Vòng | Giả thuyết và phạm vi đo | Kết luận |
|---|---|---|
| H60 | MAPS từ author Python; whole q=.2/.5/.8 và pitch-only;20 unique train groups | Final/outer hard170. Pitch-only studio_M1 37.506279%; không thắng. |
| H61 | Custom harmonic least-squares, order3/5, ±100cents;12 unique train groups; giữ mask/count | phone_F1 order5 .303953%,studio_F1 order3 1.254701% tốt riêng; studio_M1>2%. Final hard170; outer studio_M1 chọnorder3 rồi heldscore2.193784%. |
| H62 | Logistic PEZS4 so PEZS+coherence6; recovery và reject0/.1/.25;22 fits/140 groups/112 inner traces | Brier tốt hơn cả4heldtrain nhưng MAPE không tốt chung; final/outer hard170. studio_F1 có gain, phone/studio_M1 vẫn xấu. |

Tất cả tám gate chưa cùng đạt ở các vòng này; không đo test mới. Prereg đã commit/push/remoteSHAverify trước train: H60 `2488ef49087ab7fe026ee51075d05880091c763a`; H61 `079cbad1b9dcbf1e22e2b7ab927133fc72993c31`; H62 `b2af88eb635405a838d596d64b1b853a4ba1484c`. Reports đã commit riêng; không rerun.

Verifier H60v1 exact-path FAIL do tie; giữ `H60_path_tie_audit.json`. V2 kiểm log-objective độc lập khớp (0gap cả4file), projection/metric/selection PASS20groups; sửa verifier sau đo được ghi rõ, không đổi inference/config. MAPS vendor commitd51d0e870625b4b62152900cfe627b8127c522d7 byte-identical, GPLv3; ba runtime fixes,48kHz/2048nativewindow khác canonical, fixed spline clip. Initial25ms syntheticFAIL được giữ. Không claim exact upstream pipeline hoặc framepitchGT.

H61 QR/basis/Hann/grid/localbracket/metric PASS12groups; optimizer không refit độc lập. H62 QRfeature/scalarresponse/fitpool/designhash/gradient/mask/pitch/metric/selection PASS140groups/22models. H61/H62 là code custom, không fastF0Nls reference port. Algorithm deterministic; seed11/29/47 ở các syntheticfixtures là noise seed, không3MLtrainingseeds. H62 logistic học LABEL chỉ đúngfitpool; scaler cũng vậy.

Artifacts chính trong `research_workbench_2026_10_07/results/`: `H60/H61/H62_train_experiment.json`, `H60/H61/H62_verification.json`, CSV fullmetrics/innertraces/audits/changedcases, NPZproofs; `LOOP_H60_H62_SUMMARY.csv` tóm tắt số đã đo. Sources `maps_adapter.py/maps_experiment.py`, `harmonic_nls.py/nls_experiment.py`, `harmonic_voicing.py`, các registry/prereg/verifier tương ứng. Sources/config/data hash được kiểm trước đo; không chỉ có bảng cuối.

## Giới hạn và công việc còn mở

- Ground truth teacher3GT chỉ mean/std/count cả file; LAB V/UV/SIL theo đoạn. Không có F0 chuẩn từng timestamp. LABV không đồng nghĩa số khungF0 chuẩn; contourACF/MAPS/NLS và mean của file không thay framegroundtruth.
- Bốn trainingfiles tạo nested4outer/3inner, final4LOFO. Minimax worst-file MAPE→mean→ID và guard F1/recall/SIL; tám gate giữ nguyên. Repeated selection trên4train và lịch sử đã xem test khiến kết quả exploratory. Không tuyên bố độc lập mới vì vừa freeze hoặc dùngKfold. Không random split frames hoặc coi augmentation là thêm speaker mới.
- Nguồn dữ liệu: [provenance report](research_workbench_2026_10_07/DATASET_PROVENANCE_REPORT.md) đã thấy8WAV byte-identical với GitHubdthle; LAB nội dung khớp sau normalize newline. Hai bản stats khácmean/std, không chỉ thêmF0num; quy trình tạo reference/tác giả thu âm chưa rõ. Transcript “Anh vẫn có thể làm trọng tài”, giả thuyết4người/2nam2nữ và môi trườngphone/studio do người dùng cung cấp, speaker/session metadata chưa xác minh. Không kết luận thầy ghi nhầm hoặc testdata lỗi.
- Đã thử ML/MFCC/H51matrix, augmentation, KEELE10speaker, YAAPT/SRH/cepstrum/temporalpath/GMMmapping, H60–H62. Không chạy lại các vòng đã hoàn tất. PEFAC/HPS hoặc AR-noise harmonic model vẫn chưa đo đầy đủ; chỉ là lựa chọn cho giả thuyết mới sau khi user yêu cầu tiếp tục, không có H63 pending.
- Bước tiếp theo có giá trị: xác minh cách tạo reference/timing, hoặc dữ liệu có frameF0GT và speaker mới; nếu chọn algorithm mới cần một giả thuyết hẹp và prereg riêng. Không kết luận “data ít là nguyên nhân duy nhất” từ các failure.
- Jev toolkit đã chép `C:/Users/LAPTOP T&T/Downloads/Jev_System_One_Reusable_Kit`; không cần đóng gói lại. Jev không được gọi ởH60–H62. Nhánh MCP lỗi lịch sử không tự retry; chỉ thử lại khi user yêu cầu. Đọc docs/jev/HUONG_DAN_JEV.md trước usecase mới, không giao tính MAPE/hash/LAB cho Jev.

Local only; tuyệt đối khôngGoogleDrive, khôngdeep learning/PDF/PDFextraction; khôngprose/reader-firstskill. Literature-review local dùng HTML/abstract/mã tác giả, cósource/provenance, khôngfullpaperclaim. Không sửa WAV/LAB/teacher3GT/notebookgốc/frozen. Mỗi thay đổi đã kiểm tra commit riêng rồi push/remoteSHAverify; khôngmerge main. Khôngschedule/automaticretry hoặc khởi động lại loop khi chỉ đọc bàn giao.

## Prompt để tiếp tục trong chat mới

> Đọc AGENTS.md và START_NEXT_CHAT.md trong XLTN-BT2, khôi phục trạng thái sau H62 rồi tiếp tục cải thiện BT2 trước bài phân đoạn mới. Không chạy lại các thí nghiệm đã hoàn tất. Giữ mục tiêu mỗi file trong cả8file Average MAPE<2%, chọn trên train theo file, đăng ký và push/xác minh remote trước đo; giữ mọi failure, original/frozen/GT và giới hạn test đã từng xem.
'''
(REPO/'START_NEXT_CHAT.md').write_text(handoff,encoding='utf-8')
state=WORK/'STATE.md'
prefix='''# Trạng thái bàn giao 08/10/2026 — ĐÃ DỪNG THEO YÊU CẦU NGƯỜI DÙNG

Loop đã hoàn tất H60/H61/H62 và dừng, không có H63 hoặc thí nghiệm pending. Người dùng yêu cầu xong thì dừng và chuẩn bị chat mới. Đọc START_NEXT_CHAT.md ở root để khôi phục; các dòng tiếp tục hoặc pending bên dưới là lịch sử. Không tự chạy lại để lấy context.

H60 MAPS20groups, H61 harmonicNLS12groups, H62 logisticcoherence140groups/22fits đã đo train và kiểm. Cả ba final chọn hard170, chưa đạt tám gates; không promote, không test mới. H60 verifier v1 path tie FAIL giữ nguyên; v2 objective parity PASS và sửa sau đo được ghi. H61 QR/grid PASS12; H62 QRfeatures/scalarresponse/gradient/pools/metrics/selection PASS140. NLS có gains riêng .340080→.303953 phone_F1/order5 và1.473576→1.254701 studio_F1/order3, nhưng studio_M1>2. Coherence giảm Brier cả4heldtrain nhưng chưa MAPE tốt chung. No frameF0GT hoặc proof data/test là nguyên nhân duy nhất.

Baseline nghiên cứu vẫn4/4train<2%,0/4test<2%,all8FAIL; testH48 lịch sử4.197313/6.833750/5.063462/2.114791%. Originalnotebook SHA b643a1cdf6ac67d3e1dcacf9ce45ea4c49625da114e8c07f402c3fca5d13f85c giữ. Reports H60_REPORT/H61_REPORT/H62_REPORT và LOOP_H60_H62_train_matrix/CSV đã lưu; mốc kết quả bc42283fcb2ec76147a22241faf4c937aef606ba push/remoteverified. Hồ sơ bàn giao commit sau mốc này. H60prereg2488ef4/H61prereg079cbad/H62preregb2af88e đều remoteverified trước train. H61/H62 custom/deterministic, fixture noise seeds không trainingseeds. Khôngrerun hoặc chuyển bài segmentation trước khi user đổi ưu tiên. Local/noDrive/DL/PDF/Jevretry/proseskill giữ nguyên.

---

'''
state.write_text(prefix+state.read_text(encoding='utf-8'),encoding='utf-8')
coverage=WORK/'EXPERIMENT_COVERAGE.md'
coverage.write_text(coverage.read_text(encoding='utf-8')+'''

## Cập nhật H60–H62, hoàn tất và dừng 08/10/2026

| Hướng bổ sung | Phạm vi đã đo | Kết luận và nguồn |
|---|---|---|
| MAPS biên độ +pha | H60 reference-derived whole/pitch-only,20train groups, khôngtest mới | [H60_REPORT](H60_REPORT.md); khác nativewindow/canonical; failure giữ, finalhard170 |
| Harmonic least-squares | H61 custom order3/5,12train groups, same mask/count | [H61_REPORT](H61_REPORT.md); gain riêng nhưng studio_M1>2; không reference fastF0Nls port |
| Harmonic coherence choV/UV | H62 logistic base4/6 ×rejection0/.1/.25,22fits/140groups/112traces | [H62_REPORT](H62_REPORT.md); Brier tốt cả4heldfile nhưng MAPE không tốt chung; finalhard170 |

[Ma trận ba vòng](figures/LOOP_H60_H62_train_matrix.png) và [summary CSV](results/LOOP_H60_H62_SUMMARY.csv) có số đã đo. Không suy từ mục “harmonics” cũ rằng mọi harmonicmethod đã thử; không suy từH61/H62 rằng fastNLS/ARnoise của tác giả đã được benchmark. H63 chưa đăng ký, loop đã dừng theo user; chưa đo PEFAC/HPS đầy đủ hoặc corpus mới. Không “thử hết” ngoài registry và không rerun để khôi phụcchat.
''',encoding='utf-8')

sys.path.insert(0,str(WORK))
import maps_experiment,nls_experiment,harmonic_voicing
for module in (maps_experiment,nls_experiment,harmonic_voicing):module.check_registry()
notebook=REPO.parent/'turn-in-assignment - Copy/BT2_ACF_best_no_energy_set.ipynb'
notebook_sha=hashlib.sha256(notebook.read_bytes()).hexdigest()
assert notebook_sha=='b643a1cdf6ac67d3e1dcacf9ce45ea4c49625da114e8c07f402c3fca5d13f85c'
links=re.findall(r'\]\(([^)]+)\)',handoff)
for target in links:
    assert (REPO/target).exists(),target
files=[REPO/'START_NEXT_CHAT.md',state,coverage,archive,WORK/'H60_REPORT.md',WORK/'H61_REPORT.md',WORK/'H62_REPORT.md',
    WORK/'figures/LOOP_H60_H62_train_matrix.png',OUT/'LOOP_H60_H62_SUMMARY.csv']
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
receipt=dict(status='STOPPED_AT_USER_REQUEST',last_completed_round='H62',H63_registered=False,
    experiments_pending=[],new_test_evaluations=0,results_checkpoint=checkpoint,
    submitted_notebook_sha256=notebook_sha,three_registries_source_input_hashes_verified=True,
    checked_handoff_links=len(links),artifacts={str(p.relative_to(REPO)):digest(p) for p in files})
(OUT/'H62_STOP_HANDOFF_RECEIPT.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('PASS compact handoff, archive, stop state, source/input hashes, original notebook,',len(links),'file links')
