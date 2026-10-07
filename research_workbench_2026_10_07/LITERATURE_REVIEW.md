# Literature review F0 cổ điển để mở rộng BT2

Ngày tìm nguồn07/10/2026. Mục tiêu thực nghiệm: **Average MAPE≤2% ở mỗi file**, giữ cả mean/std/count và V/UV/SIL. Đây là narrative engineering review vòng đầu, phục vụ chọn thí nghiệm; không phải systematic review đầy đủ hay meta-analysis. Không extractPDF sau yêu cầu người dùng. Mức đọc thật của từng record có trong `literature_records.json`: HTMLabstract, tài liệu tác giả/mã nguồn tham chiếu, hoặc sectionHTML đã đọc. Không coi abstract là đã đọc toàn bộ paper.

## Câu hỏi và phạm vi

Phương pháp F0 cổ điển nào có thể cải thiện đồng thời đường cao độ và quyết định hữu thanh, thay vì tiếp tục chỉ tinh chỉnh ngưỡng ACF/AMDF? Bao gồm thuật toán time-domain, frequency-domain, kết hợp và mô hình xác suất cổ điển. Bao gồm nguồn primary có phương pháp hoặc implementation đủ xác minh; giữ cả nghiên cứu cũ nền tảng và preprint liên quan. Loại deep-learning intervention khỏi thí nghiệm, source chỉ quảng cáo hoặc thiếu danh tính khỏi kết luận kỹ thuật. Tìm qua PubMed/ISCA/arXiv, đối chiếu metadataCrossref và authorsoftware; websearch chỉ là discovery có xếp hạng, không phải export toàn database. Một agent đọc/đối chiếu, chưa double-review fulltext; không công bố độ bao phủ đầy đủ.

## Khái niệm để đọc bảng

**F0** là tần số cơ bản, Hz; chu kỳT tương ứngF0=1/T. **Octave error** là chọn bội/nửa chu kỳ nên cao độ gần gấpđôi/halving. **V/UV** là hữu thanh/vô thanh. **Ứng viên** là nhiều cao độ khả dĩ trong một khung. **Dynamic programming/Viterbi** chọn một chuỗi ứng viên bằng tổng chi phí địa phương và chuyển tiếp, thay vì chọn độc lập từng khung. **Aperiodicity** là mức không tuần hoàn; không đồng nghĩa trực tiếp với nhãnUV trong mọi giọng nói. **LP residual** là phần còn lại sau dự đoán tuyến tính, giúp quan sát xung kích thích. Những thuật ngữ này mô tả cơ chế, không tạo nhãn chuẩn choBT2.

## Bản đồ nguồn và cơ chế

| Nhánh | Nguồn primary đã đối chiếu | Kiến thức lấy được | Ý nghĩa cho BT2 và giới hạn |
|---|---|---|---|
| Hiệu số theo lag | [YIN, deCheveigné/Kawahara2002](https://pubmed.ncbi.nlm.nih.gov/12002874/) | Thuật toán từ cấu trúc tuần hoàn, sửa các bước để tránh lỗi; abstract có đánh giá với laryngograph. | AdapterYIN25ms cũ thất bại không loại bỏ mọi cấu hìnhYIN; muốn đánh giá lại phải kiểm implementation và support dài hơn. Không nhập số lỗi paper thành MAPE BT2. |
| Chuẩn hóa hìnhAMDF | [AlignedAMDF, Rahman/Tanaka/Shimamura2006](https://www.isca-archive.org/interspeech_2006/rahman06_interspeech.html) | Căn các peak để xử lý xu hướng giảm ở lag lớn và octave ambiguity. | AMDF hiện tại củaBT2 là NAMDFoverlap-normalized; không tự coi nó là rawAMDF trongpaper. Cần mapping công thức trước ablation. |
| Mô hình phổ hài | [SWIPE, Camacho/Harris2008](https://pubmed.ncbi.nlm.nih.gov/19045655/) | So phổ tín hiệu với mẫu sawtooth; SWIPE′ dùng hài đầu và hài prime nhằm giảm subharmonicerror. | Hướng mới khácAMDF/ACFthreshold. Nên dùng referenceimplementation, chấm cùnggrid; cần giữ voicing/count riêng, không lấy spectralstrength làmgroundtruth. |
| Kết hợp thời gian–phổ | [YAAPT, Zahorian/Hu2008](https://pubmed.ncbi.nlm.nih.gov/18537404/) | NCCF, thông tin nhiều harmonicpeak, nhiều ứng viên và dynamicprogramming; paper có telephone/high-qualityspeech. | Phù hợp để khảo sát tính bổ sung hai miền; chưa chứng minh thắng trênphoneBT2. Không suy phonefilebị clipping/nén từtên. |
| Xác suất + chuỗiV/UV | [pYIN, Mauch/Dixon2014, authorbibliography](https://webspace.eecs.qmul.ac.uk/s.e.dixon/), [implementationdoc](https://librosa.org/doc/0.11.0/generated/librosa.pyin.html) | Phân bố threshold tạo nhiều ứng viên có probability; Viterbi chọn chuỗiF0 vàvoicingflags. | KhácYINsinglethreshold và khácmedian sauF0. Frame/hop tính theo ms/fs, ghi rõpadding/center; kiểmprobability từsignal chứ không coi là calibratedtruth. Fullpaper chưa đọc. |
| Filterbank + nối contour | [Harvest, Morise2017](https://www.isca-archive.org/interspeech_2017/morise17b_interspeech.html), [author WORLDsoftware](https://github.com/mmorise/World) | Nhiều bandpasscenter lấyF0candidate; instantaneousfrequency refine/score; nối các ứng viên qua thời gian, hướng tới giảmVbị gọiUV. | Ưu tiên referencepipeline mới vì H24phoneM1 bỏ40V chỉdopitchgate. Đây là lý do chọn nghiên cứu, chưa là số đo cải thiệnBT2. |
| Xung kích thích + lattice | [REAPER, Talkin referencecode](https://github.com/google/REAPER) | LP residual, GCIcandidate, NCCF vàlatticecóV/UV; dynamicprogramming chọn chuỗi. | Hướng mới cảF0/voicing, không chỉ đổi ngưỡng. Cần build/version/formatinput và định nghĩa F0 output; READMEkhông thay paperfulltext. |
| ACF chuẩn với cửa sổ | [Praat rawACF](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_raw_autocorrelation.html), [filteredACF](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_filtered_autocorrelation.html) | ACFwindowcorrection r_signal≈r_windowed/r_window; chọn đường cóUVcandidate. Support gắn vớipitchfloor, khôngfix25ms. Filteredvariant dùng GaussianLP. | Referencebenchmark quan trọng để phân biệt hạn chếcustomACF và familyACF. Máy cóParselmouth0.4.7/Praat6.1.38; không gọi rawAPIđó là filteredvariant2023. |
| InstantaneousF0/refinement | [Kawahara/Agiomyrgiannakis/Zen2016 HTML](https://arxiv.org/html/1605.07809) | Táchestimate–track–refine vàaperiodicity; sectionevaluation phân biệt trackingfidelity vớivoicingdecision, dùng tín hiệu cótrajectory biết trước. | Gợi ý syntheticdiagnostic cóF0truth thật chojump/over-smoothing. Paperkhông tựchấmV/UV, không giải quyết countmetricBT2 trực tiếp. Section/architecture đãđọc, không mọiappendix. |
| Fusion cóqualityweight | [AdaptiveKalmanfusion2014](https://pubmed.ncbi.nlm.nih.gov/24815269/) | Kết hợp nhiềuF0estimate theoquality bằng adaptiveKalman; đánh giá sustainedvowel vàsyntheticphonation/EGG. | Hướng ensemble cổ điển, nhưng sustainedvowel khácconnected speech; không trung bình bừa hai output lệch octave. Cần mô hìnhquality và thao tác khiUV/none. |

MetadataDOI đã xác minh choYIN,AAMDF,YAAPT,pYIN,Harvest vàKalman; rawCrossrefpayload cùngtrạngtháicó trong `results/literature_citation_verification.json`. SWIPElookupCrossref lỗi được giữ; title/authors/DOI xác minh từPubMedprimary, không xóa paper doAPIlỗi. REAPER/Praat là softwaresources, không bịaDOI/year. DOI củaarXiv đối chiếu primaryrecord, không bắtCrossref chứa mọiagency.

## Tổng hợp theo cơ chế, không xếp hạng bằng số của paper

Có ba thay đổi lớn đáng nghiên cứu. Thứ nhất, **cách tạo ứng viên**: AMDF/YIN dùng hiệu số; SWIPE dùng harmonictemplate; Harvest dùngfilterbank; REAPER dùngresidual/GCI. Chúng quan sát các khía cạnh khác nhau của signal, vì vậy thất bại ở một family không đủ loại familykhác. Thứ hai, **quyết định theo chuỗi**: pYIN/REAPER/Praat/YAAPT đưa continuity vàvoicing vào chọnđường; BT2hiện fit ngưỡng độc lập rồipathchỉtrongvoicedruns, nên không thể hồi phụcframe đãbịngưỡngloại bằngpathF0. Thứ ba, **refinement vàquality**: aperiodicity/qualityweight có thể đánh dấu estimate không đángtin, nhưng abstain đổicount, phải báotradeoff.

Các paper dùng corpus,groundtruth vàmetrics khácBT2. Không lấyGPE/FPE/RMSE hay tỷlệgiảmcủapaper làm AverageMAPEfile-stat củaBT2. Không coiEGG hoặcsyntheticreference tươngđương LABtóm tắt; không gộp các cohorts chưa xác định để làmmeta-analysis. Các kết quả trongabstract là tuyên bố của tác giả, chưa có independentreplication tạiworkspace.

## Liên hệ bằng chứng local và hướng mở

H24 cải thiệnAMDF: nested6.767627→5.671863%, giữV/UV/count. H25nested5.629137 vàH26nested5.478347 chỉgainnhẹ, phoneF1stdxấu; finalminimaxvẫn chọnrawH24. Mục tiêu mỗi file≤2% chưa đạt. CountMAPEalone/3 củaphoneM1 vàstudioF1 hiện >2% ởcontrol, nên sửa riêngpitch không đủ cho cảbộ; đây là phân tíchcủacontrol, khônglowerboundmọithuậttoán.

**Ưu tiên mới:** benchmark một referencepipeline fullF0+voicing (Harvest hoặcPraat), đăng ký trước đo, adapter/timecoverage minh bạch; sau đó pYIN vàSWIPE′ nếu implementation/dependencies kiểm tra được. Chỉ chọn hyperparameters bằng train/innerLOFO; giữouterfile khỏifit/selection. Khi thay toànpipeline, gọi là comparisonpipeline, không khẳng định đãcôlậpmộtfilter. Một vòng sau có thểtáchAMDFpreemphasis/LP-residualcandidate để hiểu cơchế; không dùng nó đểné nhánhthuậttoánmới.

**Backlog cơ chế:** AAMDF mapping; fs-awarepreemphasis; qualityweightedfusion; syntheticF0sweeps cógroundtruth (pitchramp/octavechange/harmonics/noise), phân tíchrobustness riêng vớifile-statbenchmark. Chưa đăngký hayđo cácýtưởng này. Threshold/mediansampling/range có thểtune, khôngfix25/10 làmtham sốmodel; canonical25/10 chỉgiữmetriccountso sánh được.

## Nguồn workflow

Áp dụng [literature-review1.11 củaK-Dense](https://github.com/K-Dense-AI/scientific-agent-skills/tree/92ace75ac21efe19a620434e0ca4e356081fe807/skills/literature-review), instruction/reference subset lưu tại `.agents/skills/literature-review/`. Kassis,T.;Agarwal,V.;He,Y.;Patel,D.;Brueckner,A.M.(2026), [Scientific Agent Skills](https://arxiv.org/abs/2609.00065), DOI10.48550/arXiv.2609.00065; recordv2 kiểmtra07/10. Skillorganize quy trình, không bảođảm reviewcomplete/algorithmaccuracy. Searchlog: `LITERATURE_SEARCH_LOG.md`. KhôngpaidAPI, khôngPDFextract/export, khôngDrive.
