import json
import shutil
import zipfile

from core import HERE, ROOT, RESULTS, sha256
from events import record


def main():
    folder = ROOT / 'improved-training-only'
    readme = '''# BT2 — notebook cải tiến chọn bằng TRAIN

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
'''
    (folder / 'README.md').write_text(readme, encoding='utf-8')
    (HERE / 'deliverables' / 'README.md').write_text(readme, encoding='utf-8')
    record('Bàn giao notebook, output và báo cáo', '4 notebook tự chứa đã PASS, 5 pipeline; train ACF29,83→6,18%, test9,33→3,29%; sáu bản gốc giữ nguyên.',
           'Dừng thí nghiệm sau khi đủ kiểm chứng; không tune theo test. Âm thanh đã bấm phát lại nhưng vẫn chưa có xác nhận nghe được.')
    timeline = ROOT / 'BAO_CAO_SU_KIEN_BT2_2026-10-05.md'
    shutil.copy2(timeline, HERE / timeline.name)
    zip_path = ROOT / 'BT2_CAI_TIEN_TRAIN_ONLY_2026-10-05.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                archive.write(path, str(path.relative_to(folder)))
        report = HERE / 'PHAN_TICH_VA_CAI_TIEN_BT2_2026-10-05.md'
        archive.writestr(report.name, report.read_text(encoding='utf-8'))
        archive.write(timeline, timeline.name)
        for path in sorted((HERE / 'figures').glob('*.png')):
            archive.write(path, 'figures/' + path.name)
        for filename in ['final_train_test_per_file.csv', 'final_tradeoffs_summary.csv', 'frozen_config.json', 'delivery_validation.json']:
            archive.write(RESULTS / filename, 'results/' + filename)
    with zipfile.ZipFile(zip_path) as archive:
        assert archive.testzip() is None
        assert len([n for n in archive.namelist() if n.endswith('.ipynb')]) == 8
        sources = {p.name: p for p in folder.glob('*.ipynb')}
        for name, path in sources.items():
            assert archive.read(name) == path.read_bytes()
    checksum = sha256(zip_path)
    zip_path.with_suffix('.sha256.txt').write_text(checksum + '  ' + zip_path.name + '\n', encoding='utf-8')
    manifest = {'zip_path': str(zip_path), 'zip_sha256': checksum, 'zip_bytes': zip_path.stat().st_size,
                'zip_verified': True, 'clean_notebooks': list(sources), 'executed_notebooks': 4,
                'reports': ['PHAN_TICH_VA_CAI_TIEN_BT2_2026-10-05.md', timeline.name]}
    (RESULTS / 'delivery_bundle_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
