# Đọc kiến thức paper mà không extract PDF

Áp dụng yêu cầu người dùng ngày 07/10/2026. Dùng workflow literature-review đã lưu trong `.agents/skills/literature-review/`. Bản tổng hợp hiện có: [LITERATURE_REVIEW.md](LITERATURE_REVIEW.md); danh tính và mức đọc: [literature_records.json](literature_records.json).

## Quy trình đang dùng

1. Xác minh paper qua DOI, trang nhà xuất bản hoặc trang tác giả: đúng tên, tác giả, năm và phiên bản.
2. Tìm bản HTML chính thức hoặc bản HTML trên arXiv. Đọc các mục liên quan đến giả thuyết: phương pháp, giả định, cách chấm và giới hạn; chỉ đưa trích đoạn cần thiết vào context.
3. Nếu chỉ có abstract, dùng nó để nhận diện cơ chế và tìm nguồn tiếp. Không suy ra công thức hay chi tiết triển khai còn thiếu.
4. Đối chiếu tài liệu thuật toán và mã tham chiếu của tác giả. Ghi commit/version, hàm, dòng và hash; phân biệt nội dung paper với hành vi của implementation.
5. Viết bằng lời của agent: cơ chế → giả thuyết BT2 → tham số/adapter → tiêu chí kiểm tra. Mỗi phát biểu có nguồn và mức bằng chứng. Kiểm tra synthetic trước khi đo dữ liệu thật.
6. Nếu vẫn thiếu chi tiết quyết định, ghi rõ chưa truy cập được full text. Tìm bản tác giả được công khai hợp pháp hoặc thử implementation đã xác minh trong vòng riêng. Không đoán chi tiết và không vượt paywall.

Đọc chọn lọc giảm lượng văn bản cần đưa vào context; chưa đo mức tiết kiệm token. Không dùng bản tóm tắt AI làm bằng chứng cho claim mà nguồn chưa hỗ trợ. Đây là narrative engineering review, chưa phải systematic review đầy đủ.

## Ví dụ đã thực hiện

**Praat:** [manual HTML raw autocorrelation](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_raw_autocorrelation.html) cho công thức hiệu chỉnh cửa sổ, ứng viên và chọn đường, cùng ý nghĩa các tham số. Cửa sổ phụ thuộc pitch floor, dài ba chu kỳ thấp nhất; với 70 Hz là khoảng 42.86 ms. H27 dùng API raw của Praat 6.1.38 đã có trên máy. Đây là tài liệu triển khai, không phải đã đọc toàn bộ Boersma (1993); không gọi API này là filtered autocorrelation đời mới.

**Harvest:** [abstract ISCA](https://www.isca-archive.org/interspeech_2017/morise17b_interspeech.html) cung cấp hướng filterbank và nối ứng viên. Đối chiếu tiếp [mã tác giả, commit d625e7](https://github.com/mmorise/World/blob/d625e7608ca23a870018f01e7c562ac683d9847f/src/harvest.cpp#L1189): sau tạo ứng viên là refine/score, loại ứng viên không tin cậy, sửa contour và làm mượt. Hàm xuất kết quả xử lý đường cơ sở ở bước 1 ms rồi lấy mẫu theo bước được yêu cầu; không thể xem `frame_period` là độ dài cửa sổ phân tích. Đây là nhận xét từ implementation này, chưa khái quát mọi bản Harvest. Hash và vị trí hàm lưu trong `results/harvest_source_probe.json`. Sau đó đã chạy H28 trên BT2 bằng PyWORLD 0.3.5 trong môi trường riêng. Mã harvest.cpp trong source archive có cùng SHA256 với source tác giả pin đã đọc. Kết quả chưa vượt control vì nhiều khung UV/SIL bị gọi hữu thanh; xem [H28_ERROR_ANALYSIS.md](H28_ERROR_ANALYSIS.md). Không lấy kết quả benchmark của paper thay số liệu BT2.

**pYIN:** [API chính thức librosa 0.11](https://librosa.org/doc/0.11.0/generated/librosa.pyin.html) giải thích ứng viên có xác suất và Viterbi chọn F0/V–UV, cùng frame length, padding và tham số. Dùng tài liệu này để kiểm adapter, nhưng không giả đã đọc full paper ICASSP 2014.

**Instantaneous F0:** đã lấy được [bản HTML arXiv](https://arxiv.org/html/1605.07809), đọc phần kiến trúc estimate–track–refine và cách phân biệt tracking với voicing. Các section đã đọc được ghi trong records; không claim mọi phụ lục đã đọc.

## Áp dụng vào thí nghiệm

H27 (Praat raw) và H28 (Harvest) đều so pipeline với control AMDF H24, đăng ký và push trước đo. Mọi cấu hình cố định được báo riêng với kết quả của bước chọn cấu hình; không chỉ trình bày đường baseline sau khi registry bị loại. Figures và kết quả thất bại đã lưu/push. Không dùng số liệu công bố trong paper thay số liệu BT2. Chấm cùng ground truth và lưới thời gian, báo coverage, mean/std/count và V/UV/SIL. Mục tiêu người dùng vẫn là **mỗi file Average MAPE ≤2%**; lựa chọn cấu hình không xem file outer đang chấm.

Không extract hoặc tải PDF cho quy trình này. Không tạo PDF báo cáo. Một nguồn chỉ có abstract vẫn được giữ trong review với giới hạn rõ ràng, thay vì bị loại hoặc được trình bày như full text.

## Nối tiếp bằng manual HTML và phép đo thật

[Praat filtered manual](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_filtered_autocorrelation.html) mô tả Gaussian low-pass trước ACF, sự khác nhau giữa pitch top và raw ceiling, voicing threshold và silence threshold. Đã đối chiếu lệnh native với source Praat7.0.02, lưu binary/script/hash và kiểm synthetic trước BT2. H30 thử whole pipeline filtered, không gọi đây là tác động cô lập của một filter. H31 chỉ thay voicing; H32 chỉ thay silence, giữ các tham số khác.

Kết quả triển khai không được suy ra từ manual: H30 nested2.422852%, H32 nested mean1.992154% nhưng worstfile3.175722%, chưa đạt từng file≤2%. [Notebook reference chạy từ WAV](REFERENCE_PIPELINES_LOCAL.ipynb) tính lại60fixed+16nested rows và hai figures, khớp kết quả đã lưu. [Hướng dẫn đọc](REFERENCE_NOTEBOOK_README.md) giải thích mean/std/count, V/UV/SIL và giới hạn hai loại ground truth. Đây là kết nối nguồn HTML/code → giả thuyết đăng ký → kiểm synthetic → đo BT2 → giữ cả thất bại; không cần extract PDF hoặc coi abstract/manual là full paper.

pYIN cũng đã được đưa vào H33 từ API/source chính thức librosa0.11.0, source pitch.py cài đặt có cùng SHA256 với release tag0.11.0. Tám synthetic probes qua; frame40/60/80ms, hop10ms, center=False/no-padding đã đăng ký trước BT2. Fixed meanMAPE2.719295/5.843812/11.250381%, không vượt control2.156992%; mọi outer chọn control. [Phân tích và figures mọi cấu hình](H33_ERROR_ANALYSIS.md) chỉ ra lỗi count/VUV/SIL còn tăng ở cửa sổ dài. Đây là kết quả BT2 thực, không lấy từ paper; vẫn chưa claim đã đọc full text ICASSP2014. Các runtime/params/source/hash/native raw/probability và failures được lưu/push riêng.

**SWIPE′** đã được đối chiếu [SPTK pitch manual](https://sp-nitech.github.io/sptk/latest/main/pitch.html) và bundled implementation trong [source pin0ebff5a](https://github.com/sp-nitech/SPTK/tree/0ebff5a9b1fb5851709130efa1d3efb186ef702a). Wrapper/native input PCM-scale float64, adaptive FFT windows và output time origin0 đã kiểm bằng code, source hash và tám synthetic probes trước đo. Build portable/source/provenance cùng lỗi MSVC/standard-header giữ tại [SPTK_NATIVE_SETUP.md](SPTK_NATIVE_SETUP.md). Không dùng abstract để đoán input unit hoặc claim đã đọc full paper Camacho–Harris2008.

H34 whole SWIPE′ giảm Average MAPE hai phone files tại threshold.2 nhưng có73SIL tổng; H35 giữ voicing Praat rồi thay F0 SWIPE′, loại SIL dư nhưng studio_M1 vẫn trên3%. Cả hai FAIL và chưa đạt mục tiêu từng file≤2%. [Notebook SWIPE/Praat/AMDF](SWIPE_PRAAT_LOCAL.ipynb) đã tính lại44 rows từWAV, năm code cells nguyênsource và baPNG/SVG pairs verified. [Hướng dẫn đọc](SWIPE_NOTEBOOK_README.md) phân biệt fixed/nested/fallback/count/std. Đây là source/manual→prereg→synthetic→BT2→failure analysis; REAPER vẫn chưa đo và không có claim fullpaper mới.

**REAPER** được nối tiếp ởH36/H37: [README tác giả David Talkin](https://github.com/google/REAPER) và [SPTK manual](https://sp-nitech.github.io/sptk/latest/main/pitch.html), wrapper cùng fullvendor source hashes đã đối chiếu; benchmark dùng SPTKpin0ebff5a, không giả giống toàn bộ authorpin1d6e9b9. Đọc cơ chế residual/epoch lattice/dynamic programming và actual highpass=True/Hilbert=False/inputcastint16/timeorigin0. [Source note và workflow citation](REAPER_SOURCE_NOTE.md) ghi mức đọc code/manual, không journal/fullpaper claim. Rawwholezero failures và half-frequency synthetic case giữ nguyên, adapter chỉ bypass input hoàn toàn0; mọi trainREAPERcall thực sự vào native.

H36 raw cost.6/.9/1.2/1.5 không vượtcontrol. H37 giữ cổng Praat rồi lấy pitchREAPER: fixed.9 studio_M1stdMAPE1.120784% và AverageMAPE2.138876%, nhưng phone_F1Avg29.460886% khiến pipeline chưađạt. [Notebook REAPER/Praat/AMDF](REAPER_PRAAT_LOCAL.ipynb) đã replay44rows từWAV,32nativecalls và baPNG/SVG pairs verified; [hướng dẫn](REAPER_NOTEBOOK_README.md) phân biệt fixed/nested và giới hạn GT. Không lấy số liệu README/paper làm số liệu BT2. Cả hai vòng FAIL, giữ frozen/original và không tune test.
