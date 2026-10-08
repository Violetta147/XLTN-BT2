# SRH — nguồn và phạm vi triển khai

Đọc ngày 08/10/2026 theo workflow `.agents/skills/literature-review/SKILL.md` và PROVENANCE. Query: `Drugman Alwan 2011 Summation Residual Harmonics pitch SRH COVAREP github pitch_srh`. Đọc primary HTML/abstract và mã tác giả, không download/extract PDF, không coi abstract là full paper.

- Thomas Drugman và Abeer Alwan, *Joint robust voicing detection and pitch estimation based on residual harmonics*, Interspeech **2011**: [ISCA abstract/metadata](https://www.isca-archive.org/interspeech_2011/drugman11_interspeech.html). Abstract mô tả tiêu chí dựa trên họa âm của residual để ước lượng pitch và voicing; số benchmark của bài không phải kết quả BT2.
- [arXiv abstract](https://arxiv.org/abs/2001.00459), DOI10.48550/arXiv.2001.00459: bản đưa lên arXiv ngày 28/12/2019, không đổi năm conference thành2019.
- [COVAREP contributions](https://covarep.github.io/covarep/contributions.html); đọc toàn bộ `pitch_srh.m` và `lpcresidual.m` tại [commit5a2be5d6b776f14a0b275c69fde90eb13849e60d](https://github.com/covarep/covarep/tree/5a2be5d6b776f14a0b275c69fde90eb13849e60d). Bản local `sources/srh_5a2be5d/`, hash trong registry. Header hai hàm GPL3-or-later, copyright University of Mons/FNRS2011; LICENSE.txt repo nói license theo từng file. `srh_port.py` giữ attribution và SPDX GPL3-or-later, kèm GPL-3.0.txt.
- URL GNU license trả403; không dùng nội dung chưa lấy và không tự retry endpoint. Lấy văn bản GPL3 từ [GCC official source mirror COPYING3](https://raw.githubusercontent.com/gcc-mirror/gcc/master/COPYING3). Đây là văn bản license, không nguồn thuật toán.

Không có MATLAB/Octave executable local. Đây là **Python research port phỏng theo source**, không native reference execution hoặc bit-identical parity. SciPy resample_poly thay MATLAB resample; solve_toeplitz cho hệ Yule-Walker thay MATLAB lpc. Không regularize, không sửa ngưỡng theo dữ liệu BT2. Segment LPC giữ length+1 và overlap của source. Fourier1Hz và lệch chỉ số MATLAB one-based được giữ: index của h×F0 là h×F0−1 trong Python. Sample timestamp của source giữ one-based/fs, không dịch để khớp LAB.

Lưu 2000 spectral bins đầu nhưng chuẩn hóa theo toàn bộ fs/2 bins. Mọi index được dùng với5harmonics và F0<=400 nằm trong prefix này; precheck xác nhận 18 output cases không đổi so bản đầu lưu full spectrum. `pitch_srh` có2passes giới hạn theo median utterance và ngưỡng VUV. Port giữ cả F0 cho UV để thực hiện pitch-only ablation; không thêm temporal smoothing/DP.

Synthetic source-filter qualification:15/18 accuracy cases đạt median error<5Hz và voiced fraction>=.8; cả3 window của100Hz/fs44100 chọn300Hz. Lỗi lưu `H54_initial_synthetic_failure.json`, nguồn ban đầu snapshot riêng. Độc lập math qualification PASS không biến ba lỗi accuracy thành PASS. Kiểm tra hệ số dense đầu tiên thất bại vì LPC condition~3.09e10; ghi ở `H54_component_check_initial_failure.md`; kiểm tra sửa trước đo BT2 thành backward equation residual và so dense khi condition<=1e8. Residual filtering/convolution/fullFFT/SRH recomputed độc lập, resampler cùng SciPy nên không xác minh resampling độc lập.

Jev không tham gia; không câu trả lời Jev được dùng làm số liệu hay chọn cấu hình.
