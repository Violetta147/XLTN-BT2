# Dùng Jev / System One cho từng trường hợp

Ngày đối chiếu: 2026-10-06. Phạm vi cấu hình: workspace XLTN và repository XLTN-BT2. Đây là hướng dẫn làm việc, không phải kết quả benchmark chất lượng tổng quát.

## 1. Jev tham gia ở đâu?

Quy trình phù hợp:

1. Agent đọc nguồn, notebook, LAB, CSV và cấu hình; lấy đúng trích đoạn.
2. Code tính các số liệu và đối chiếu điều kiện chính xác.
3. Khi còn câu hỏi ngữ nghĩa hẹp, agent gửi bằng chứng đó cho Jev.
4. Agent kiểm tra ID/quote, đọc lại nguồn khi có bất đồng và giải thích cho người dùng.
5. Agent thực hiện hành động trong phạm vi yêu cầu của người dùng.

Ví dụ: code đếm SIL bị gán F0 là 45 và 1. Jev có thể rà câu “45 → 1 chứng minh toàn bộ cao độ đã đúng” có vượt bằng chứng không. Jev không tạo ra số đếm hoặc ground truth.

Không cần một lần discovery/status trước mỗi evaluation khi công cụ đã sẵn sàng. Nếu người dùng chỉ yêu cầu discovery thì chỉ đọc danh sách tools/resources, chưa evaluation. Nếu discovery lỗi thì dừng, không tự retry.

## 2. Chọn công cụ

| Nhu cầu | Công cụ | Đầu vào | Cách đọc và giới hạn |
|---|---|---|---|
| Kiểm tra một kết luận với bằng chứng | sysone_check | claim; evidence dạng text hoặc 1–32 item id/text | supported và contradicted độc lập; cả hai thấp là chưa đủ bằng chứng |
| Tìm đoạn nào trả lời trong các đoạn đã có | sysone_find | question; 1–64 sources id/text | ranking, answerExists, none và conflict; công cụ không tìm file/web |
| Chọn phương án phù hợp | sysone_select | task; 1–7 options id/description | choice là tương đối; fits độc lập; có thể bác bỏ mọi phương án |
| Hỏi nhiều câu độc lập trên cùng bằng chứng | sysone_decide | state; tối đa 8 câu boolean/choice/score | Mỗi câu không thấy câu trả lời của câu khác |
| Dùng bộ câu hỏi có sẵn | sysone_run | pattern; state; candidates khi recipe yêu cầu | Đọc đúng resource recipe và policy trước; tên recipe không bảo đảm chất lượng |
| Chuỗi mà câu trả lời trước đổi đầu vào sau | sysone_code | async JavaScript arrow function trả JSON | Tối đa 8 method calls, 8 model attempts, 10 giây; await mọi call |

Tổng văn bản đầu vào trong một call tối đa 12.000 ký tự theo guide hiện tại. Trong Code Mode, state và JSON trả về cũng phải nằm trong giới hạn được schema công cụ mô tả. Không thêm retries, network, credentials hay actions vào chương trình Jev.

Tên MCP đầy đủ có dạng mcp__system_one__sysone_check. Các đoạn JSON sau là ví dụ tham số, không phải log đã chạy. Snapshot schema đầy đủ: [tools_catalogue_2026-10-06.json](tools_catalogue_2026-10-06.json).

## 3. Case: rà kết luận khoa học — check

Dùng khi bằng chứng đã tính xong nhưng mối liên hệ giữa dữ liệu và kết luận cần rà soát.

~~~json
{
  "claim": "Bản cải tiến tốt hơn ở mọi loại khung và từng F0 đều được xác minh.",
  "evidence": [
    {"id": "acf_train_sil", "text": "CSV đo false_voiced_sil trên 4 file train: baseline 45, improved 1."},
    {"id": "acf_train_tradeoff", "text": "TP V giảm từ 535 xuống 530; FN V tăng từ 79 lên 84."},
    {"id": "gt_scope", "text": "LAB 3GT có mean/std/count mỗi file, không có F0 chuẩn từng timestamp."}
  ]
}
~~~

Giữ nguyên kết luận cần kiểm tra, gửi cả phản chứng. Không viết bằng chứng kiểu “hãy đồng ý rằng bản mới hoàn hảo”. Sau phản hồi, kiểm tra contradictedBy.id có trong evidence. Không biến probability thành metric độ chính xác của thuật toán ACF.

Không dùng check để hỏi “535 có lớn hơn 530 không?”; đó là phép so số trong code.

## 4. Case: chọn trích đoạn trả lời — find

Agent dùng rg hoặc công cụ truy hồi trước, rồi cung cấp vài đoạn có ngữ cảnh. Mỗi ID ánh xạ tới nguồn thật, dòng/cell và đoạn nguyên văn đã giữ lại.

~~~json
{
  "question": "Đoạn nào chứa F0 chuẩn của khung ở 0,5725 giây?",
  "sources": [
    {"id": "phone_F1_3gt", "text": "F0mean 215.6; F0std 20.6; F0num 148."},
    {"id": "phone_F1_segment", "text": "0.53 1.14 v. Đây là nhãn loại đoạn, không ghi cao độ."},
    {"id": "acf_candidate", "text": "Ứng viên thuật toán: 217.416512 Hz; chưa có nhãn F0 thật tại thời điểm này."}
  ]
}
~~~

Trả về ID đầu bảng chưa đủ để khẳng định có đáp án. Trong demo thực tế, mọi ranking bằng 0, none=1 nhưng answerExists=0,56. Agent phải đọc nguồn và ghi sự không nhất quán; không tự gọi lại để có kết quả đẹp hơn.

Nếu đoạn nguồn không tồn tại, không yêu cầu Jev tự tìm hoặc bịa thông tin thiếu. Nếu có quote, code kiểm tra quote xuất hiện nguyên vẹn trong nguồn trước khi trích dẫn.

## 5. Case: chọn hướng xử lý hoặc phép chẩn đoán — select

Agent đề xuất shortlist bằng kiến thức chuyên môn và mô tả rõ điều kiện, chi phí, dữ liệu cần có. Jev chỉ so các phương án có trong shortlist; không tự bổ sung giả thuyết đúng bị bỏ sót.

~~~json
{
  "task": "Cần reference F0 từng khung đã được xác minh, nhưng chỉ có WAV và thống kê 3GT cả file. Chọn chỉ khi phương án thực sự đủ; nếu tất cả thiếu thì none.",
  "options": [
    {"id": "file_mean", "description": "Dùng mean cả file cho mọi khung."},
    {"id": "old_acf", "description": "Dùng output ACF cũ làm chuẩn."},
    {"id": "smooth_contour", "description": "Dùng contour mượt của bản cải tiến làm chuẩn."}
  ]
}
~~~

Trong demo thực tế Jev chọn null/none và fits thấp ở cả ba. Không phương án nào tạo ra tham chiếu đã được xác minh. Nếu có lựa chọn, code đối chiếu ID, rồi agent kiểm tra điều kiện sử dụng; lựa chọn chưa cho phép chạy thử nghiệm hoặc thay đổi metric.

Đối với chẩn đoán lỗi, có thể chọn giữa kiểm tra nhãn, xem lag ứng viên và kiểm tra RMS trên số liệu đã có. Giữ cùng chia train/test, không dùng test để chọn tham số rồi gọi test đó độc lập.

## 6. Case: rà báo cáo theo nhiều tiêu chí — decide

Dùng cho các câu độc lập như “kết luận có vượt GT không?”, “có báo đánh đổi không?”, “phạm vi train/test được nêu đủ không?”. Gom cùng một state để không gửi lại dữ liệu nhiều lần.

~~~json
{
  "state": {
    "observations": "ACF train SIL 45→1; TP 535→530; FN 79→84. Có thay đổi path, RMS gate và median3.",
    "draft": "Tất cả F0 đã đúng và toàn bộ cải thiện do RMS."
  },
  "questions": {
    "scope_supported": {
      "type": "boolean",
      "instructions": "Bằng chứng có hỗ trợ toàn bộ nhận định tất cả F0 đã đúng không?"
    },
    "attribution": {
      "type": "choice",
      "instructions": "Chọn cách diễn giải tác động của bản cuối; unknown nếu không đủ.",
      "criteria": {
        "isolated_rms": "Đã cô lập và đo toàn bộ tác động riêng RMS.",
        "combined_pipeline": "Đo trước–sau của nhiều thay đổi kết hợp; cần ablation để tách đóng góp.",
        "unknown": "Không đủ xác định."
      }
    },
    "report_scope": {
      "type": "score",
      "instructions": "Chấm mức thể hiện phạm vi và đánh đổi trong bản nháp.",
      "criteria": [
        "0: Bỏ phạm vi và khẳng định vượt dữ liệu.",
        "1: Nêu phạm vi nhưng thiếu đánh đổi.",
        "2: Nêu phạm vi, đánh đổi và giới hạn."
      ]
    }
  }
}
~~~

boolean probability là P(true), không phải confidence riêng. score theo rubric có thể là số lẻ, không phải tỷ lệ đúng. Không đặt câu A và phủ định A chỉ để tạo một kiểm tra nhất quán giả.

Nếu câu B cần câu trả lời A để chọn bằng chứng, đây là chuỗi phụ thuộc, dùng Code Mode hoặc hai bước tuần tự, không coi hai câu decide là phụ thuộc nhau.

## 7. Case: bộ câu hỏi có sẵn — run

Recipe là một mẫu câu hỏi, không phải công cụ làm hành động. Nguồn: sysone://recipes và sysone://recipes/{id}.

Trước khi dùng recipe mới: đọc resource cụ thể, kiểm tra schema/questions, policy, requiresCandidates và validation. Chỉ đọc danh mục chưa chứng minh đã hiểu đầy đủ cách gọi từng recipe. Nếu resource đọc lỗi, không tự retry; dùng công cụ trực tiếp với câu hỏi tự viết nếu công cụ đó sẵn sàng.

Ví dụ writing-check đã đọc và thử:

~~~json
{
  "pattern": "writing-check",
  "state": "Thuật toán cực kỳ mạnh mẽ, mang lại chất lượng vượt trội và xử lý vấn đề hoàn hảo."
}
~~~

Các kiểm tra cụ thể, mơ hồ và có bước tiếp theo là gợi ý sửa văn. Chúng không xác minh toán, số liệu hoặc chất lượng khoa học toàn bài. Các recipe tool-approval, reply-review hay payment-review không cấp quyền hành động. Tôn trọng quyền người dùng đã cấp và quy tắc của phiên làm việc; không tạo yêu cầu xác nhận mới chỉ vì tên recipe.

Hiện danh mục có 42 recipe; tất cả metadata validation là unmeasured, nghĩa là chưa gắn đánh giá chất lượng trên bộ held-out có nhãn. Chỉ writing-check đã được chạy trong đợt khám phá này.

| Recipe | Trường hợp dùng | Cần candidates |
|---|---|---|
| next-tool | Chọn công cụ trong danh sách mô tả khả năng đã kiểm tra. | Có |
| tool-approval | Rà soát ý nghĩa của lệnh đề xuất; kết quả không cấp quyền thực thi. | Không |
| context-relevance | Xem đoạn ngữ cảnh có giúp trả lời câu hỏi không; giữ phần chưa chắc. | Không |
| clarification | Xác định thông tin thiếu có thực sự chặn bước tiếp theo không. | Không |
| evidence-check | So kết luận ngắn với bằng chứng đã thu thập. | Không |
| tool-result | Diễn giải đầu ra còn thiếu hoặc mơ hồ; PASS/FAIL rõ thì đọc bằng code. | Không |
| change-scope | Đề xuất hướng rà soát theo phạm vi thay đổi mã. | Không |
| acceptance | Hỏi nhiều tiêu chí độc lập trên kết quả thực tế đã kiểm tra. | Không |
| attention | Đề xuất khi nào thông tin cần người dùng chú ý; tuân theo yêu cầu thông báo. | Không |
| memory-candidate | Đề xuất sở thích có thể tái sử dụng; không tự cho phép lưu memory. | Không |
| freshness | Nhận ra thông tin có thể lỗi thời khi quy tắc thời gian chưa quyết định được. | Không |
| rubric | Chấm tiêu chí hẹp có mô tả rõ các mức điểm. | Không |
| intent | Phân biệt câu hỏi, yêu cầu thay đổi và yêu cầu trạng thái khi còn mơ hồ. | Không |
| palette-match | Chọn bảng màu từ mô tả; code kiểm tra tương phản, người dùng xem bản render. | Có |
| item-match | Chọn tài sản hoặc mẫu theo mô tả sau khi lọc các điều kiện chính xác. | Có |
| command-match | Ánh xạ lời yêu cầu sang ID lệnh đã tồn tại; kiểm tra quyền và đối số riêng. | Có |
| semantic-search | Chọn ID trích đoạn đã tìm được; bản thân recipe không tìm kiếm. | Có |
| entity-match | So hai bản ghi có khả năng nói về cùng thực thể; không tự gộp. | Không |
| citation-check | Kiểm tra đoạn nguồn có hỗ trợ ý được trích dẫn; đối chiếu chữ bằng code trước. | Không |
| writing-check | Phát hiện câu mơ hồ, thiếu chi tiết; không chứng nhận đúng khoa học. | Không |
| text-labels | Gán vai trò cấu trúc cho đoạn văn; giữ nguyên nội dung và code literal. | Không |
| structured-fields | Chọn giá trị từ các trường cho phép; code xác thực schema và số liệu. | Không |
| diagnostic-test | Xếp hạng các phép kiểm tra đã đề xuất từ bằng chứng lỗi hiện có. | Có |
| repair-check | So mô tả sửa lỗi với bất biến cần giữ; test thực thi vẫn là căn cứ chính. | Không |
| passage-policy | Nhận diện dữ liệu, phản chứng và chỉ dẫn nhúng; không dùng làm hàng rào bảo mật. | Không |
| ticket-triage | Đề xuất nhóm xử lý yêu cầu và mức khẩn cấp được nêu rõ. | Không |
| handler-route | Đề xuất dùng code, mô hình chuyên môn hay người rà soát. | Không |
| reply-review | Rà bản nháp với bằng chứng; khuyến nghị gửi không phải quyền liên hệ người khác. | Không |
| payment-review | Rà thông tin hoàn tiền; không thực hiện thanh toán. | Không |
| paper-screen | Sàng lọc abstract theo tiêu chí; đọc toàn văn trước kết luận quan trọng. | Không |
| duplicate-report | So hai báo lỗi; mô tả giống nhau chưa chứng minh chung nguyên nhân. | Không |
| computer-next-action | Đề xuất bước trình duyệt từ trạng thái đã quan sát. | Không |
| computer-target | Chọn ID điều khiển từ quan sát hiện tại; không bịa selector hoặc tọa độ. | Có |
| computer-form-ready | So biểu mẫu với yêu cầu; giá trị rõ ràng ưu tiên so chính xác. | Không |
| computer-progress | Diễn giải thay đổi UI thực tế sau hành động. | Không |
| computer-outcome | Xem màn hình cuối có hỗ trợ kết quả mong muốn; xác minh bản ghi riêng. | Không |
| computer-recovery | Đề xuất quan sát lại, chờ giới hạn hoặc trả việc về agent; không tự retry. | Không |
| corpus-next-action | Đề xuất bước tiếp theo trong quy trình tìm tài liệu. | Không |
| corpus-candidate-match | Chọn tài liệu từ ID và tóm tắt truy hồi đã có. | Có |
| corpus-grep-triage | Ưu tiên dòng grep cần đọc đầy đủ ngữ cảnh. | Không |
| corpus-evidence-check | So kết luận với đoạn tài liệu hoặc khoảng dòng đã đọc. | Không |
| corpus-query-reformulate | Đề xuất hướng đổi truy vấn khi kết quả tìm kiếm ít hoặc nhiễu. | Không |

Chi tiết policy và metadata nguyên gốc: [recipes_catalogue_2026-10-06.json](recipes_catalogue_2026-10-06.json). Đây là danh mục các trường hợp có sẵn, không phải 42 phép thử đã thành công.

## 8. Case: nhận diện hiểu nhầm rồi chọn bằng chứng — code

Demo thực tế có hai bước: phân loại câu hỏi của người học → chọn bộ bằng chứng tương ứng → kiểm tra nhận định đó. Ví dụ sau dùng API jev trong môi trường sysone_code, không phải JavaScript chạy ngoài shell:

~~~javascript
async () => {
  const route = await jev.choice({
    state: "Std chuẩn 20,6 Hz thì mọi F0 phải nằm trong mean ± 20,6 Hz?",
    instructions: "Phân loại hiểu nhầm, hoặc unknown.",
    criteria: {
      std_range: "Nhầm độ lệch chuẩn với giới hạn bắt buộc.",
      reference_scope: "Nhầm chuẩn cả file với chuẩn từng khung.",
      unknown: "Chưa xác định."
    }
  });
  const probes = {
    std_range: {
      claim: "Mọi F0 đúng phải nằm trong mean ± std.",
      evidence: "Std đo độ phân tán; không định nghĩa min/max."
    },
    reference_scope: {
      claim: "Mean/std/count xác định duy nhất F0 từng thời điểm.",
      evidence: "Hoán vị các phần tử giữ cả ba thống kê nhưng đổi gán theo thời điểm."
    }
  };
  const id = route.value.choice;
  if (!Object.prototype.hasOwnProperty.call(probes, id)) {
    return {status: "needs_review", route: route.value, meta: route.meta};
  }
  const review = await jev.check(probes[id]);
  return {
    category: id,
    route: route.value,
    review: review.value,
    routeMeta: route.meta,
    reviewMeta: review.meta
  };
}
~~~

Đây là ví dụ có nhánh unknown và validate ID, không phải hệ thống tự động đã được hiệu chỉnh độ tin cậy. Trong công việc thật, confidence thiếu hoặc tín hiệu không đủ rõ trả về agent để đọc lại nguồn. Không suy ra an toàn hay đúng chỉ vì một category đứng đầu.

API trực tiếp sysone_decide dùng type boolean, còn SDK jev.evaluate trong Code Mode dùng type noul cho câu có xác suất đúng/sai. Xem snapshot schema trước khi viết chương trình. Các câu độc lập trong Code Mode dùng jev.evaluate trên cùng state.

## 9. Những việc để code và nguồn quyết định

| Việc | Cách làm |
|---|---|
| 45 và 1, tổng TP/FN, số file | Parse CSV, lọc đúng model/version/split và cộng số nguyên |
| MAPE, MAE, std, lag→F0 | Công thức và code, nêu đơn vị, ddof, tập khung và GT |
| File LAB có cột F0 theo thời điểm không | Đọc toàn bộ format và parser đang dùng |
| Notebook đã chạy lại chưa | Source, execution metadata, output, log và hash |
| Quote/ID/citation có tồn tại không | So nguồn chính xác; sau đó mới cân nhắc vai trò ngữ nghĩa |
| Lệnh rõ PASS/FAIL, phiên bản, đường dẫn | Kiểm tra chính xác bằng code |
| Có quyền hành động không | Yêu cầu người dùng và quy tắc phiên; Jev không cấp quyền |

## 10. Ground truth của BT2 và 45 → 1

Các LAB đã đối chiếu trong repository ngày 2026-10-06:

- 8 LAB trong TinHieuHuanLuyen và TinHieuKiemThu: nhãn V/UV/SIL theo đoạn và F0mean/F0std.
- 8 LAB trong research_3gt_2026_10_05/train_3gt và test_3gt: F0mean/F0std/F0num cả file.
- Không có dòng F0 chuẩn từng timestamp trong 16 file này. Kết luận chỉ áp dụng cho nhóm file đã đọc, không phủ nhận một nguồn tham chiếu khác chưa được kiểm tra.

Có ground truth để chấm thống kê, không đủ ground truth để chứng nhận ứng viên F0 của từng khung. Ví dụ phone_F1 3GT là mean=215,6 Hz, std=20,6 Hz, count=148. Những số đó không bảo rằng khung ở 0,5725 s có F0 đúng 215,6 hay 217,416512 Hz.

SIL là khoảng lặng theo nhãn. V là hữu thanh, UV là vô thanh. Một khung có tâm trong đoạn SIL mà pred=true là một false_voiced_sil. Khung đang dùng trong so sánh ACF là cửa sổ 25 ms, bước 10 ms; các khung có thể chồng nhau.

| File train | Baseline | Improved |
|---|---:|---:|
| phone_F1.wav | 2 | 0 |
| phone_M1.wav | 0 | 0 |
| studio_F1.wav | 21 | 1 |
| studio_M1.wav | 22 | 0 |
| Tổng false_voiced_sil | 45 | 1 |

45 không phải riêng phone_F1, không phải 45 Hz hay 45% MAPE. 1 còn lại thuộc studio_F1. Giảm 44 là giảm số khung SIL bị gán hữu thanh; chưa chứng minh cao độ của tất cả khung V đã đúng. Không chuyển 44 khung chồng nhau thành 44 đoạn âm thanh độc lập.

Trong cùng so sánh, TP V=535→530 và FN V=79→84: bỏ sót thêm 5 khung hữu thanh thật. Ma trận V/UV của code loại SIL và báo false_voiced_sil riêng, không cộng con số này vào FP V/UV rồi gọi cùng metric.

Nguồn số đếm: research_3gt_2026_10_05/results/final_train_test_per_file.csv, lọc model=ACF, split=train và version=baseline/improved. Nguồn định nghĩa: standalone_pipeline.py, hàm classification, biểu thức ((labels == 'sil') & predicted).sum().

So sánh bản cuối kết hợp nhiều thay đổi không tự cô lập đóng góp RMS/path/median. Muốn khẳng định đóng góp riêng, đọc cấu hình và bảng ablation tương ứng. Jev chỉ có thể rà diễn giải khi agent gửi đủ các bảng đó.

## 11. Ghi log và xử lý lỗi

Giữ log input/output đầy đủ ở thư mục này hoặc thư mục kết quả của nhiệm vụ:

- Mục đích và điều chưa biết cần Jev đánh giá.
- Công cụ, arguments nguyên vẹn, source IDs và phiên bản/hash nếu phù hợp.
- Phản hồi gốc, requestId, model, số calls, tokens, latency, cached khi có.
- Kết luận do agent viết, kiểm tra ID/quote và tín hiệu không nhất quán.
- Phần đã đo thực tế, phần chưa được xác minh và giới hạn.

Không đưa token hoặc biến môi trường bí mật vào log. Nếu thiếu SYSONE_TOKEN, chỉ báo sự tồn tại/trạng thái, không in giá trị. Biến đặt bằng $env trong side PowerShell không tự truyền ngược vào tiến trình Codex đã chạy; ứng dụng phải được khởi động với môi trường phù hợp.

Lỗi discovery/evaluation: không tự retry, không backoff lặp, không chạy lại cùng prompt cho đến khi nhận câu trả lời mong muốn. Báo lỗi, giữ bằng chứng và tiếp tục phần độc lập. Thử lại khi người dùng yêu cầu. Tín hiệu mâu thuẫn thì đối chiếu nguồn, không coi đó là giấy phép gọi lại.

Nếu dự định dùng quyết định Jev tự động: tạo bộ ca có nhãn độc lập, chọn ngưỡng trên development, chốt ngưỡng trước held-out evaluation, báo coverage, lỗi ở quyết định được chấp nhận và review rate. Demo nhỏ không cung cấp bảo đảm hiệu chỉnh xác suất.

## 12. Áp dụng rules trong Codex

Quy tắc ngắn được đặt tại AGENTS.md ở workspace XLTN và bổ sung vào AGENTS.md tại Git root XLTN-BT2. Tài liệu dài nằm ở docs/jev; agent đọc khi cần trường hợp cụ thể, tránh nạp mọi ví dụ vào mỗi prompt.

Codex xây chuỗi hướng dẫn khi bắt đầu run/session; nếu không có project root, nó kiểm tra thư mục hiện tại. Vì XLTN chứa repository con XLTN-BT2, có hướng dẫn ở cả hai điểm bắt đầu. Bắt đầu phiên mới trong đúng thư mục khi cần kiểm tra discovery tự động. Phiên hiện tại đã đọc và áp dụng các file; không khẳng định đã kiểm thử một phiên mới.

Nguồn chính thức: [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md). Cách kiểm tra trên phiên mới: yêu cầu Codex liệt kê các AGENTS.md đã nạp và tóm tắt quy tắc Jev. Không cần cài plugin hay sửa cấu hình toàn cục để dùng hướng dẫn tại project.

## 13. Nguồn và log của đợt khám phá

- [System One guide đã đọc](system_one_guide_snapshot.md), từ sysone://guide.
- [Danh mục 42 recipe](recipes_catalogue_2026-10-06.json), từ sysone://recipes.
- Recipe writing-check đã đọc từ sysone://recipes/writing-check.
- [Schema 6 công cụ](tools_catalogue_2026-10-06.json), từ metadata MCP có trong phiên.
- [Báo cáo kết quả thử thực tế](KHAM_PHA_JEV_2026-10-06.md).
- [Input/output 6 lượt MCP](exploration_runs_2026-10-06.json).
- [Kiểm tra ID và tổng usage](exploration_validation_2026-10-06.json).
- [Đối chiếu LAB và số đếm bằng code](source_audit_2026-10-06.json).

Các resource và schema là snapshot ngày 2026-10-06. Kiểm tra khả năng đang cung cấp khi bắt đầu phiên khác, không xem snapshot là bảo đảm kết nối còn hoạt động.
