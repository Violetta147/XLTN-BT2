# Validation và protocol trong bài F0

Thầy cung cấp train và test. Validation là vai trò của dữ liệu khi chọn cấu hình, không bắt buộc là một thư mục thứ ba. Trong các vòng BT2, ta tạo validation từ chính bốn file train bằng cách giữ riêng file, không lấy test để học tham số.

Ví dụ một lượt outer giữ riêng studio_M1: chỉ ba file phone_F1, phone_M1, studio_F1 được dùng để chọn cấu hình. Trong ba file này, inner lần lượt giữ riêng một file làm validation, học từ hai file còn lại nếu thuật toán cần học. Chọn cấu hình có Average MAPE tệ nhất thấp nhất qua ba lượt inner, rồi mean vàID. Sau đó học lại trên ba file để chấm studio_M1. Lặp với bốn outer held files. Đây là nested leave-one-file-out cross-validation, có bốn outerfold và ba innerfold mỗiouter. Lựa chọn final dùng bốn lượtLOFO trongtrain rồi fit toàntrain nếucần. Cácoption khôngcầnfit nhưPraat/hard170 chỉdùnginnerselection, không tựhọc từWAV.

Không phải randomKFold trênkhung. Các khung trongcùngWAV phụthuộc nhau; noisevariants cũngphụthuộcWAVgốc, nên tấtcả cùngorigin phải cùngfold. Chưa cóspeakeridentity xácminh đểgọi split hiện tại làleave-one-speaker-out; nếu cùngngười cóhai file thìphải groupchúng cùngfold trongprotocolspeakerindependent. Cùngtranscript khôngtựđộng làleakage pitch, nhưng chỉmộtcâu hạn chế phạmvingữâm/generalization.

NestedCV giảm rò rỉ ở từnglượtfit/selection, nhưng khôngxoá việcagent đãxem cùngbốntrain qua nhiềuvòng đểchọnhypothesis/grid. H47 fallbackhard170 và thaycandidate set phảiđượcgọi exploratory. TestBT2 cũngđãxemlịch sử; H48 chốtcấuhìnhtrướcđo khôngbiến bộtest thànhdữliệumới chưa từngxem. Khôngclaimnested4files làcertificationindependent.

Protocol là quy ước để kết quả có nghĩa: đơn vịchiafold, dữliệuđượcphépdùng đểhọc/chọn, phépbiếnđổi, nhãn, timestamps, metric/mẫusố vàquy tắcbáo failure. Bài tậpvẫn cầnnhữngquyướctối thiểu này, nhưng khôngcầnbê nguyênbốnprotocol củaFaceAntiSpoofing. TrongFAS,type thườngchỉloạitấncông; F0khôngcó attacktype. Nam/nữ, voiced/unvoiced hoặcphone/studio khôngtựđộng làtype theoFAS.

| Tên người dùng nêu | Ý nghĩa tổng quát | Áp dụng hợp lý vào F0 |
| --- | --- | --- |
| Intra-Dataset Intra-Type | Cùng corpus, cùng nhóm điều kiện | BT2 train→test theo split của thầy; chọn bằng CV trong train. Cần nêu giới hạn người nói và transcript. |
| Cross-Dataset Intra-Type | Corpus mới, tác vụ/nhóm điều kiện tương tự | Cấu hình chọn trên BT2→KEELE tiếng nói đọc, không fit/tune KEELE. Đây là kiểm tra ngoài corpus; không tự gọi là FAS protocol chuẩn. |
| Intra-Dataset Cross-Type | Cùng corpus, điều kiện giữ riêng chưa dùng để học/chọn | Có thể định nghĩa riêng phone→studio hoặc ngược lại, nhưng hiện chỉ hai file mỗi nhóm, khác người có thể lẫn với khác thiết bị. Không đủ để tách nguyên nhân môi trường. |
| Cross-Dataset Cross-Type | Corpus và điều kiện đều mới | Ví dụ tiếng nói đọc sạch→corpus mới có tiếng nói tự nhiên hoặc nhiễu. Cần định nghĩa điều kiện, reference/metrics và nguồn fit trước; chưa thực hiện trong H49. |

H49 khônghọc trênKEELE: chỉkiểmtra externalcorpus bằngfixedpipeline. Nếu dùngKEELE đểchỉnhpipeline thìKEELE trởthànhdevelopment vàcầnexternaldataset hoặc phầnngườinói khác chưađụngtới đểchấm tiếp. Không chọnbest theoKEELE rồi gọi kếtquảKEELE làindependentbenchmark.

Benchmark tốt không chứng minh lỗi BT2 chỉ do ít dữ liệu. Có thể cókhácngônngữ, giọng, nhiễu, cửa sổ, pitchrange hoặcquytrìnhtạoGT. Cần cảframepitchmetric vàVUV vìmean/std/count cóthể gầnđúng dùF0sai theo thời gian. Ngược lại framepitchkhá nhưngfileMAPElớn cóthể do mộtítkhung ởđuôiphânphối hoặccount/referenceprotocol. Ta chấmđểphânbiệt nhữngkhảnăngnày, khôngdùng mộtbenchmark đểquy lỗi data.

Nguồn và giới hạn truy cập: BENCHMARK_SOURCES.md. Tài liệu này là diễn giải từ code BT2 và thiết kế đánh giá của agent, không thay yêu cầu chấm của thầy.
