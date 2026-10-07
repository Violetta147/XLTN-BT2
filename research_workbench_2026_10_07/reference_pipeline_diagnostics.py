import argparse
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

import harvest_reference as runner

HERE = Path(__file__).resolve().parent
audit = runner.audit


def main(family):
    path = HERE / f'results/{family}_fixed_lofo.csv'
    table = pd.read_csv(path)
    identities = json.loads((HERE / f'{family}_REGISTRY.json').read_text())['options']
    names = sorted(table.file.unique())
    assert len(table) == len(identities) * 4 and not table.duplicated(['option_id', 'file']).any()
    audit.ARTIFACTS.clear()
    fig, axes = audit.plt.subplots(1, 3, figsize=(14, 4))
    for ax, metric in zip(axes, ('average_mape', 'recall_v', 'false_voiced_sil')):
        for option in identities:
            group = table[table.option_id == option['id']].set_index('file').loc[names]
            ax.plot(np.arange(4), group[metric], 'o-', label=option['id'])
        ax.set_xticks(np.arange(4), [name.replace('.wav', '') for name in names], rotation=25)
        ax.set(title=metric)
    axes[0].axhline(2, color='black', linestyle='--', label='target 2%')
    axes[0].legend(fontsize=7)
    fig.suptitle(f'{family}: every fixed configuration; not selected best for held file')
    audit.save_figure(f'{family}_fixed_diagnostics', fig, [path],
                      'Mọi cấu hình đã đăng ký trên bốn file train; không chọn best bằng held file.',
                      'File-stat GT và nhãn đoạn; kết quả exploratory, không có F0 chuẩn từng khung.')
    for figure in audit.ARTIFACTS:
        figure.update(generator=Path(__file__).name, generator_sha256=audit.digest(__file__),
                      command=f'../.venv-bt2-world/Scripts/python.exe research_workbench_2026_10_07/reference_pipeline_diagnostics.py {family}')
        assert figure['sources'][0]['sha256'] == audit.digest(path)
        png = (HERE / figure['png']).read_bytes()
        assert png[:8] == b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II', png[16:24])) > 200
        ET.parse(HERE / figure['svg'])
    audit.json_write(HERE / f'results/{family}_fixed_diagnostics_manifest.json',
                     {'figures': audit.ARTIFACTS, 'all_registry_options_present': True, 'rows': len(table)})
    if family == 'H28':
        columns = ['option_id', 'file', 'average_mape', 'F0mean_mape', 'F0std_mape', 'F0num_mape',
                   'F0num', 'macro_f1', 'recall_v', 'FP', 'false_voiced_sil']
        chosen = table[table.option_id == 'harvest_h10']
        summary = chosen[['average_mape', 'macro_f1', 'recall_v']].mean()
        sil = int(chosen.false_voiced_sil.sum())
        report = ['# H28 — vì sao Harvest chưa đạt trên BT2?', '',
                  'Bảng dưới giữ mọi cấu hình cố định đã đăng ký; không phải chọn phương án tốt nhất cho từng held file.', '',
                  audit.markdown_table(table[columns]), '',
                  f'Nhánh Harvest 10 ms: mean Average MAPE {summary.average_mape:.6f}%, '
                  f'macro F1 {summary.macro_f1:.6f}, recall V {summary.recall_v:.6f}; '
                  f'tổng {sil} khung SIL bị gọi hữu thanh. Control H24 có một khung SIL trên fixed LOFO.', '',
                  'Recall V cao chỉ cho biết ít bỏ V. F1 thấp và nhiều UV/SIL bị gọi V cho thấy đánh đổi lớn; '
                  'không suy ra F0 đúng chỉ từ recall. F0num chấm trên lưới chung còn khác tổng nhãn V; không đồng nhất hai ground truth.', '',
                  'MAPE std cũng xấu. Chưa có F0 chuẩn từng khung để tách chính xác lỗi cao độ trong V khỏi ảnh hưởng của các khung false voiced. '
                  'Tên file không chứng minh nhiễu, clipping hoặc nguyên nhân vật lý; không kết luận từ nhóm nam/nữ chỉ có hai file mỗi nhóm.', '',
                  'Tất cả inner và final chọn AMDF control vì các nhánh Harvest không vượt eligibility. '
                  'Nested giữ 5.721646%, không phải Harvest cải thiện rồi được promote. Giữ thất bại của whole pipeline.', '',
                  'Hướng kế tiếp có thể kiểm tra riêng một cổng V/UV trước dùng contour Harvest, với ngưỡng fit ở các file còn lại. '
                  'Đây mới là đề xuất, chưa đăng ký hay đo; không cắt count theo GT held file và không thêm noise vào WAV để che lỗi synthetic.', '',
                  '![Fixed configurations](figures/H28_fixed_diagnostics.png)', '',
                  'Nguồn số liệu: results/H28_fixed_lofo.csv; runner/source/data/contour verification: results/H28_verification.json.']
        (HERE / 'H28_ERROR_ANALYSIS.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(f'PASS {family}: 16 fixed rows, all options and verified PNG/SVG/source manifest')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('family', choices=['H27', 'H28'])
    main(parser.parse_args().family)
