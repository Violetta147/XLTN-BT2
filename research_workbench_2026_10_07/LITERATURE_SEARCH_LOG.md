# Search log — F0 classical,07/10/2026

Narrativeengineeringreview, complementaryprimarysources; rankedwebquery, directURLfollowup, metadataAPI. Khôngdatabasecompleteexport, khônginventtotalcount/PRISMA. `literature_records.json` là11records được agent chọnđểreview,10include/1excludeneural intervention; đây không phải sốmọihittrảvề hay10studiesđộc lập. Sốrecord/ID/DOI trùng kiểm bằngcode. KhôngextractPDFpaper sau yêu cầu; PDFhit tìnhcờ trongsearch bịbỏ, khôngopen/download đểđọc. AlignedAMDFpaper cónotes đãđọc trước chỉdẫn mới; khôngre-extract.

## Các truy vấn paper đã thực hiện bằngwebsearch

1. `YIN fundamental frequency estimator speech music 2002 de Cheveigne Kawahara PubMed`
2. `pitch extraction SWIPE RAPT REAPER classical source paper HTML`
3. `site:pubmed.ncbi.nlm.nih.gov SWIPE sawtooth waveform inspired pitch estimator 2008 Camacho Harris`
4. `site:github.com/google/REAPER epoch pitch tracker`
5. `site:github.com mmorise WORLD Harvest DIO pitch`
6. `site:isca-archive.org pYIN probabilistic YIN Mauch Dixon 2014`
7. `site:isca-archive.org "Harvest" "Morise" 2017`
8. `"pYIN" "Mauch" "2014" site:qmro.qmul.ac.uk`
9. `"Robust Algorithm for Pitch Tracking" "Talkin" 1995`
10. `site:pubmed.ncbi.nlm.nih.gov Zahorian Hu spectral temporal robust fundamental frequency tracking 2008`
11. `"pYIN" "10.1109" "2014" Mauch Dixon`
12. `site:code.soundsoftware.ac.uk pyin probabilistic YIN`
13. `site:isca-archive.org "Pitch Determination Using Aligned AMDF"`

Source mở/read: PubMed12002874/19045655/18537404/24815269; ISCArahman06HTML/morise17bHTML; arXivabs1605.07809/2507.11233/2609.00065 vàHTML1605.07809 (abstract/background/architecture sections); googleREAPERREADME; mmoriseWorldREADME/DIOsourceexcerpt từsearch; librosa0.11.0pyinHTMLdoc; Praatraw/filteredACFHTML. Sourcelevels trongcatalogue là mức đãđọc, không đánhdấu fulltextchoabstract.

ColumbiaYINHTML vàlibrosamainpyin directopen báointernalerror. Không giả nội dung củapage lỗi; YINmetadata dùngPubMed, pyinimplementation dùngversion0.11.0docđãretrieved. AuthorDixonbibliographysearchhit xác minh authors/title, Crossref xác minhDOI; không đọc PDFliên kết tạiđó. RAPTrecords từbibliographicsearch chỉ làlead, không dùngsecondarysource để suy ra cơchế; REAPERauthorREADME cung cấp nhánhNCCF/lattice đượcreview.

Crossref: `verify_literature.py`, mỗirecordtốiđa1requestkhôngretry; directworksDOI choYIN/AAMDF/SWIPE/YAAPT/pYIN; titlequeryrows1 choHarvest/Kalman. Giữrawpayload, requestURL/UTC/status/errors trongresults/literature_citation_verification.json. NhậnCrossrefmetadata khôngđồng nghĩa claimđúng hoặcpaperđãđọcfull. SWIPEAPI lỗi giữ nguyên, PubMedprimaryvẫn xác minhđược danh tính.

## Tìm và kiểm tra skill

Đọcfind-skillslocal, skillscatalogue/skills.sh, khámpháGitHubK-Dense; GitHubAPI xác minhsourceofficialrepository renamedscientific-agent-skills và pin92ace75ac21efe19a620434e0ca4e356081fe807. Đọcliterature-reviewSKILL1.11 vàcore_workflow/search_and_citation; giữMITLICENSE.md tảiđúngđườngdẫn saufirstLICENSEpath404, không chạyremotecode. Khônginstallall177skills hoặcpaidsearch/ImageAPI. Localinstruction subset/provenance ở.agents/skills/literature-review.

WorkflowreferenceKassisetal(2026) arXiv2609.00065 xác minhHTMLrecordauthors/year/currentv2. AnthropicClaudeSciencearticle được dùngđểxác định ý người dùng vềworkbench: auditableartifacts, code/environment/provenance; không tựnhận đangchạyClaudeScienceproduct hayclaim đãcàiworkbench.
