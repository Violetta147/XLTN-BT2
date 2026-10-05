# BT2 — notebook cải tiến chọn bằng TRAIN

## Chạy trên Colab

Upload bốn notebook ở ngay thư mục này và chọn Runtime → Run all:

| File | Phương pháp |
|---|---|
| BT2_ACF_improved_train_only.ipynb | ACF: chọn đường F0 + năng lượng + median3 |
| BT2_AMDF_improved_with_energy_train_only.ipynb | AMDF: chọn đường F0 + năng lượng |
| BT2_AMDF_improved_without_energy_train_only.ipynb | AMDF: chọn đường F0, không năng lượng |
| BT2_ACF_AMDF_GMM_improved_train_only.ipynb | In riêng ACF+GMM và AMDF+GMM |

ACF có validation nested LOFO thấp nhất nên nên chạy trước. Các cấu hình đã chọn từ train,
test chỉ được đánh giá sau khi khóa cấu hình; không đổi tham số theo điểm test.

Đường dẫn Colab giữ `/content/drive/.../Seventh Semester/Spoken Language Processing/BT2`.
Mọi notebook có `SHOW_DETAILED_TEST_PLOTS=True`.

Thư mục BT2 trên Drive cần có:

- TinHieuHuanLuyen: bốn WAV và bốn LAB cũ có nhãn v/uv/sil theo thời gian.
- TinHieuKiemThu: bốn WAV và bốn LAB cũ có nhãn v/uv/sil theo thời gian.
- TinHieuHuanLuyen-3groundtruth: bốn LAB có F0mean/F0std/F0num.
- TinHieuKiemThu-3groundtruth: bốn LAB có F0mean/F0std/F0num.

Notebook tự chứa thuật toán, không cần file Python khác. Ba thống kê chuẩn chỉ dùng để chấm,
không dùng để sửa F0 dự đoán. Nhãn train cũ vẫn cần để học ngưỡng; test dự đoán trước khi đọc nhãn.

## Đọc kết quả đã chạy

`executed_local/` chứa cùng notebook với output local đã kiểm chứng: tám cell mỗi notebook, tổng30 hình,
train/test khớp phép đánh giá tham chiếu tới1e-10. Source vẫn là Colab; output đã chạy bằng đường dẫn local trong bộ nhớ.
Các notebook ở ngay thư mục gốc là bản sạch để upload. Sáu notebook gốc của bạn vẫn giữ nguyên ở hai thư mục assignment.

Trong ZIP có báo cáo phân tích, nhật ký sự kiện, hình và CSV kết quả. Báo cáo chấm điểm:

MAPE mỗi đại lượng =100×|ước lượng−chuẩn|/|chuẩn|; Average MAPE file=trung bình ba MAPE;
TỔNG CỘNG=trung bình bốn file; FINAL SCORE=100−TỔNG CỘNG TEST; điểm thang10 làm tròn một chữ số.

Chỉ có bốn file mỗi tập và chưa có F0 chuẩn từng khung. Test baseline đã được biết trong phiên trước;
test lần này độc lập với bước chọn cải tiến, chưa phải bộ test hoàn toàn chưa từng xem.
