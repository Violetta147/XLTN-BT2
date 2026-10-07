# Mapping AMDF và giới hạn kiến thức từ paper

AMDF (Average Magnitude Difference Function) đo chênh lệch biên độ trung bình giữa tín hiệu và bản trễ. Đáy nhỏ gợi ý một chu kỳ; octave/subharmonic ambiguity xảy ra khi nhiều chu kỳ bội cũng tạo đáy. NAMDF của notebook là phiên bản chuẩn hóa theo biên độ trên phần chồng lấp, không tự đồng nhất với raw AMDF hay AAMDF của paper.

Rahman, M. Shahidur; Tanaka, Hirobumi; Shimamura, Tetsuya (2006), *Pitch determination using aligned AMDF*, Interspeech pp1714–1717, DOI10.21437/Interspeech.2006-476. [ISCA HTML abstract](https://www.isca-archive.org/interspeech_2006/rahman06_interspeech.html) xác nhận ý tưởng căn các đỉnh để xử lý falling trend. Chưa lấy được công thức đầy đủ hoặc authorimplementation quaHTML/code trong lượt discovery này. Không mở/tải/extractPDF; các PDFhits tự trả từsearch không được dùng làm bằng chứng công thức. H41 **không phải tái hiện AAMDF**. Paper abstract không đủ gán công thức mới cho tác giả.

Kernel thật lấy từ frozen research_3gt_2026_10_05/baselines/AMDF.ipynb, normalized_amdf; notebook gốc giữ. Với frame x đã loạiDC, phầnchồnglấp n=0..N−τ−1:

`D(τ)=mean(|x[n]−x[n+τ]|)/(mean(|x[n]|)+mean(|x[n+τ]|)+1e−12)`.

Miềnlag floor(fs/400)..ceil(fs/70), chặn≤N−1. Nearzero meanabs<1e−8 trảcurve1; vùngphẳng không tạo ứng viên trong H41. Localdip≤hai lân cận, fallbackargmin nếu không localdip; tinh chỉnh parabol như core.refine_lag. Khôngtop12truncation. Không cănpeak hoặc thêm envelope alignment trong H41, không lời hứa kernel này giải quyết octave của paper.

H41 engineeringhypothesis: giữ gate/F0anchor Praatfiltered.30; tính NAMDFraw tại tâmPraat bằng cửa sổ25/40/55ms. Chọn localdip thấp nhất cóF0 nằm trong50/100/200cents của anchor; tie khoảngcáchcents rồiF0. Cents=1200log2(candidate/anchor), 1200cents=octave. Missingwindow/flat/noallowedcandidate giữPraat, UVkhônghồi phục. Chỉ nguồn cao độ đổi, khôngAMDFvoicingfit. Không sử dụng tênfile/giới/device/LABstats để chọnframe hoặc ứngviên. Count/VUV/SIL phải ycontrol sauprojection; sựđồngthuận khôngGTtừngkhung.

PrimaryPraatmanual/source/version đã ghi tại PRAAT_NATIVE_SETUP.md và results/praat_native_7002_provenance.json; binary7.0.02/hash giữ, .30controlH31 cốđịnh. Curves toàn bộlag/nativegate/time/framepositions/hash lưuNPZ, source tags vàselectedindices giữ. Synthetictone known173Hz/zero/band/octave/time probes khácBT2file-statbenchmark. Không mớifilter/preprocess/pathmedian/resample/noise/GTcorrection.

Discovery scope engineering/single-reviewer: queries `"Aligned AMDF" Rahman Tanaka Shimamura formula implementation`, `"AAMDF" pitch detection alignment peaks algorithm source code`, `site:isca-archive.org rahman06 interspeech AMDF`, `"Pitch determination using aligned AMDF" -filetype:pdf -site:researchgate.net -site:semanticscholar.org`, `"aligned AMDF" algorithm -filetype:pdf site:github.com`, `"aligned AMDF" peak equation -filetype:pdf`, ngày07/10/2026. HTMLprimary retained; unrelatedAAMDFmedical/secondaryunknownsources excluded, PDFhits notopened/used. Không exhaustive coverage, không đổi citationrecords vòngđầu. AAMDFexactmapping vẫnpending nhưng không ngăn thửhypothesisNAMDF từsourceđãbiết.

Workflow: literature-reviewK-Dense1.11/pin92ace75ac21efe19a620434e0ca4e356081fe807, subsetinstructions/reference, không optionalCLI/scriptsinstall/paidAPI. Kassis,T.; Agarwal,V.; He,Y.; Patel,D.; Brueckner,A.M. (2026), *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*, [arXiv current](https://arxiv.org/abs/2609.00065), DOI10.48550/arXiv.2609.00065. Currentmetadata live07/10: revised02/09/v2, nojournalpublisherDOI, khôngPDF. Citationworkflow khôngđánhgiáaccuracyBT2.
