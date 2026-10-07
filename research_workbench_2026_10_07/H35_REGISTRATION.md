# H35 — tách V/UV Praat khỏi F0 SWIPE′

Đăng ký trước đo hybrid; rollback repository1261f77, original009fd2c/frozen/notebooks giữ. Control **H31 fixed Praat filtered voicing0.30** (không coi registryH31 là control). H34 fixedSWIPE.2 giảm mean/std ởphone nhưng nhiềuSILstudio; H35 kiểm giả thuyết thay nguồn F0 trong maskV tốt hơn sẽ giảm lỗi file-stat mà giữ V/UV vàcount.

Ba options: control và SWIPEstrength **0.2/0.3** cùng gatePraatfiltered.30. Chỉ thay nguồn F0, không search gate/globalvoicing/silence/filter. Nguồn/nativeparams/probes/binary/PCMscale củaH30/H34 giữ nguyên. Đây là hybridpipeline mới, không claim tác dụng cô lập một filter hoặc tăng pitchaccuracy từngkhung.

SWIPE→nativePraatnearesttime, nửa10ms+mộtmẫu, tiechọnsớm; SWIPEavailable khi supported và70≤Hz≤400. Tại PraatV70–400, lấy SWIPE nếuavailable, nếu thiếu giữPraatF0 (fallback). PraatUVkhông nhận thêmV dùSWIPE cópitch. Sau đó cùngprojectionPraat→canonical25/10. Khônginterpolate/smooth/trimcount/GTmatching/metadata/filegender-routing; không đọctest. Lưurawnativehai nguồn vàhybridfreq/source tags, fallbackcount cóthểtáitính. Hai cấpalignment đượccheckriêng.

Nativecalls cachemỗi trainfile mộtPraat.30 vàhaiSWIPE .2/.3=12calls, không đọcnhãnđểextract/fuse. Control/hybridnofitactual_fit_files=[]; innerLOFO4file vàouterselection3file, heldchấmsau. EligibilityfiniteMAPE, meanF1/recallV≥control−.01, SIL≤control+1; rankmaxfileMAPE rồi mean/ID. Cùng8gatesgốc relativecontrolH31fixed.30: traingain≥10%, selectedLOFO/nestedgain≥5%, F1/recalldrop≤.01, SIL+1, nofileworse>2pp, phoneF1stdnotworse. Target**mỗi nestedfile≤2%** riêng; khôngautopromote.

PrereqAMDFparity/nativePraat/SPTKbinary/source/eightSWIPEprobes vàpurefusiontests choUV/missing/outofrange/unsupported/tie. KhôngđoBT2hybridtrướcregistrycommit/push. Verify48innertraces/24metricrows, uniquefitlogs52nếufinalcontrolhoặc56nếufinalhybrid(do cache),12 source calls, 12 source groups và 12 hybrid/control groups, rawPCMunchangedinputSHA/sourceparams/gates/minimax/exclusions/sourceWAVLAB/PNGSVG, allfixedMAPE/VUV/range/projection. MọifixedhybridV/count/F1/SILphảibằngcontroltừngfile; socontrolH31fixed.30 exact1e-8. Poisonheldlabels/statphảikhôngđổiinference.

Nguồn: H34/SPTK_NATIVE_SETUP.md (manual/source pin0ebff5a), PraatfilteredHTML/native7.0.02. Khôngpaperfulltextclaim/PDF/Drive/deeplearning/test/MCPretry. Lịch sửđãxembốntrainfiles làmnestedexploratory; không coi đây làindependentunseen dataset. REAPERchưađo. Lệnh `python research_workbench_2026_10_07/swipe_praat_hybrid.py register/check/H35`; verify `verify_swipe_hybrid.py`.
