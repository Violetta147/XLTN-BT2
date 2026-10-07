# H28 — pipeline tham chiếu WORLD Harvest

Đăng ký trước đọc WAV BT2 bằng Harvest. Rollback 877eef9; control là H24 fixed AMDF gate25/pitch40. Giữ original 009fd2c và frozen_config. Nguồn: [abstract tác giả ISCA](https://www.isca-archive.org/interspeech_2017/morise17b_interspeech.html), [source tác giả pin d625e7](https://github.com/mmorise/World/blob/d625e7608ca23a870018f01e7c562ac683d9847f/src/harvest.cpp). Không extract PDF.

## Giả thuyết

Ứng viên filterbank, refine/quality và nối contour có thể bổ sung cho AMDF dùng ngưỡng độc lập. Đây là so sánh toàn bộ pipeline, không cô lập hiệu quả của bandpass. Mục tiêu người dùng vẫn là mỗi file Average MAPE ≤2%.

## Môi trường và kiểm tra trước đo

Dùng `.venv-bt2-world` ở workspace cha, Python 3.13.11/system site packages, PyWORLD 0.3.5 official PyPI cp313 Windows wheel. Không sửa môi trường Python gốc. Probe phiên bản 0.3.6 thiếu wheel phù hợp được giữ; đã tìm được phiên bản 0.3.5. Metadata wheel, source archive và native module hash lưu `results/pyworld_035_compatibility.json`. Harvest source trong sdist có SHA256 giống source tác giả pin đã đọc; chưa independently rebuild wheel để chứng minh từng dòng binary.

Synthetic giữ cả failure: tín hiệu 173 Hz chỉ hai harmonic, không noise, bị gọi UV gần toàn bộ. Grid synthetic riêng 2/12 harmonic × noise 0/0.003 × fs 16k/44.1k được lưu `Harvest_synthetic_probe.json`: 12 harmonic hoặc noise yếu nhận đủ 81/81 khung trung tâm, sai số tối đa dưới 0.03 Hz. Không coi đó là bảo đảm trên speech. Kiểm tra native provenance, tín hiệu 12 harmonic và silence đều qua; AMDF gốc tái lập. **Không thêm noise vào WAV thật.**

## Registry và adapter

Bốn lựa chọn: control và Harvest với `frame_period` 5/10/20 ms. Giữ F0 70–400 Hz, raw signal, không StoneMask, external energy gate, median hoặc thay classifier. `frame_period` là bước kết quả; Harvest tự quản lý filter/window và xử lý đường cơ sở 1 ms. Ghi frame_ms=null vì không có một cửa sổ cố định đã xác minh cho toàn bộ pipeline; không gọi bước đầu ra là frame length.

Ghép tâm native gần nhất về lưới chấm canonical25/10 ms trong nửa native hop cộng một mẫu; hòa chọn tâm sớm hơn. Ngoài support: pred=false/F0=NaN. Không padding/GT-count trim; báo native count và coverage. Với hop20 có thể một estimate ghép vào hai khung chấm; báo đó là adapter, không độc lập hai quan sát. F0 chuẩn vẫn chỉ thống kê file và nhãn đoạn, chưa có F0 chuẩn từng khung.

Harvest không fit: actual_fit_files=[]/requires_fit=false. Trace fit_files chỉ là tập danh nghĩa dùng cho chọn cấu hình; control fit đúng tập. Final inner LOFO bốn file; outer dùng inner LOFO ba file. Minimax file MAPE, rồi mean và ID. Eligibility: MAPE hữu hạn, F1/recall không thấp hơn control quá 0.01, SIL tăng không quá một. Không dùng outer held cho chọn cấu hình. Nested vẫn exploratory vì đã nghiên cứu lịch sử bốn file.

## Gates đã chốt

Train giảm ≥10%; selected LOFO/nested giảm ≥5%; nested F1/recall giảm ≤0.01; SIL tăng ≤1; không file MAPE xấu thêm >2 điểm phần trăm; phone_F1 std không xấu hơn. Mục tiêu mỗi file ≤2% báo riêng. Không hạ gates hoặc tự promote sau đo. Lưu failure.

Verify 64 traces/24 metric rows, baseline parity, no-fit provenance/native binary hash, replay minimax/gates, contour/LAB/source/WAV hashes, PNG/SVG. Chỉ train local; không test/Drive/deep learning/PDF extraction. Không gọi Jev cho các phép đếm hoặc quyết định số học đã kiểm bằng code.

Lệnh: `../.venv-bt2-world/Scripts/python.exe research_workbench_2026_10_07/harvest_reference.py register/check/H28`.
