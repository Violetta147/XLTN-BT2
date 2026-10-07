# H42 — Nguồn và mức bằng chứng

Nguồn quyết định hướng thử là H41_REPORT.md/H41_ERROR_ANALYSIS.md: fixedNAMDF25/b200 đạt cả4AverageMAPE≤2% nhưngphone_F1std tăng; cửa sổ40ms có đánh đổi khác. Chưa có chứng minh rằng tỷ lệ phổ phân biệt được cửa sổ tốt. H42 đăng ký trước đo để kiểm tra giả thuyết, không chọn cấu hình riêng cho mỗi file bằng GT.

Kernel và rule H41 ởamdf_anchor.py/frozenAMDF.ipynb được giữ. AAMDFpaper trước chỉabstractHTML; H42 không được gọi làAlignedAMDF hay bản tái hiện paper. NAMDF chọnlag dựa trên difference chuẩn hóa, không dùng phổ để tính nhãn đúng; phổ chỉ điều khiển lengthms.

Primary documentation đọcHTML ngày07/10/2026:

- [NumPy hanning](https://numpy.org/doc/stable/reference/generated/numpy.hanning.html): symmetricHann formula và M−1 denominator. Đã đọc formula/API, không đọc sách tham khảo của page hoặcPDF.
- [NumPy rfft](https://numpy.org/doc/stable/reference/generated/numpy.fft.rfft.html): FFT realinput, lengthN, positivebins, binDC/Nyquist. Đã đọcAPI/conventions. Docs stable hiệnv2.5; runtime dùngNumPy2.4.3 vàprecheck/verifier kiểm tra conventions thực tế.

H42ratio dùng powerpositivebins symmetricweights, cutoff1000Hz vàthresholds. Hai documentation hỗ trợ phép tính, **không xác nhận feature này cải thiện F0**; cutoff/grid/route là giả thuyết kỹ thuật của agent, không công thức được trích từpaper. Không tìm/đọc paper mới trong vòng này; nối tiếp review đã lưu. Không mở/extractPDF.

Workflow literature-review subset K-Dense1.11 đã đọc lạiSKILL.md/PROVENANCE, chỉ instruction/reference. Theo provenance trích: Kassis etal(2026), [Scientific Agent Skills](https://arxiv.org/abs/2609.00065), DOI10.48550/arXiv.2609.00065. Không claim systematic review hoặc optionalCLI được cài.

QA dataset mới cho thấy thiếuprotocolreference/cácLABkhác thống kê vàspeakerIDs chưaverified; H42 không thayreference. Test được đọc trongQA mô tả ởlượt trước, H42features/grid chỉ từtrainH41 vàsignalengineering. Fourfile-nested sau nhiều vòng vẫnexploratory. Gemini/Jev không có call trongH42, nhánhMCP saulỗiH32 vẫn dừng.
