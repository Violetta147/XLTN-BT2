"""Add the same read-only per-file diagnostic plot to all three notebooks."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = [
    "BT2_ACF_AMDF_GMM.ipynb",
    "BT2_implement_finished_v3_executed_original - Copy.ipynb",
    "BT2_AMDF_implement_executed_original - Copy.ipynb",
]

SOURCE = """# Metric theo file: tách tỷ lệ V/UV và sai số F0 để tránh trộn đơn vị.
# Chỉ minh họa kết quả TEST của cấu hình đã chọn trên training; không dò tham số từ biểu đồ.
plot_groups = (test_summary_df.groupby('Algorithm', sort=False)
               if 'Algorithm' in test_summary_df.columns
               else [('ACF' if 'ACF' in NOTEBOOK_TITLE else 'AMDF', test_summary_df)])
for algorithm_name, file_results in plot_groups:
    file_results = file_results.reset_index(drop=True)
    names = [name.replace('.wav', '') for name in file_results['file']]
    labels = [f'{name}\\nF0={int(n)} / V={int(tp + fn)}'
              for name, n, tp, fn in zip(names, file_results['NumF0'],
                                          file_results['TP'], file_results['FN'])]
    x = np.arange(len(file_results))
    width = 0.35
    f1 = file_results['macro_f1_vu'].to_numpy(dtype=float)
    ba = (file_results['TP'] / (file_results['TP'] + file_results['FN'])
          + file_results['TN'] / (file_results['TN'] + file_results['FP'])).to_numpy(dtype=float) / 2
    mean_error = file_results['abs_error_mean'].to_numpy(dtype=float)
    std_error = file_results['abs_error_std'].to_numpy(dtype=float)
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(9.4, 6.0), sharex=True,
                                      layout='constrained')
    for bars in (top.bar(x - width/2, f1, width, label='Macro F1 V/UV', color='#2166ac'),
                 top.bar(x + width/2, ba, width, label='Balanced accuracy', color='#67a9cf')):
        top.bar_label(bars, fmt='%.2f', padding=2, fontsize=8)
    top.set(ylabel='Tỷ lệ', ylim=(0, 1.18), title=f'{algorithm_name}: phân loại V/UV theo file')
    top.legend(loc='upper left', ncol=2, frameon=False)
    top.grid(axis='y', alpha=0.2)
    top.set_axisbelow(True)
    for bars in (bottom.bar(x - width/2, mean_error, width, label='|F0mean − LAB|', color='#b35806'),
                 bottom.bar(x + width/2, std_error, width, label='|F0std − LAB|', color='#f1a340')):
        bottom.bar_label(bars, fmt='%.1f', padding=2, fontsize=8)
    bottom.set(ylabel='Sai số tuyệt đối (Hz)',
               ylim=(0, max(np.nanmax(mean_error), np.nanmax(std_error)) * 1.35),
               title='Thống kê F0 theo file')
    bottom.set_xticks(x, labels)
    bottom.set_xlabel('F0/V là số đếm, không phải recall V')
    bottom.legend(loc='upper right', ncol=2, frameon=False)
    bottom.grid(axis='y', alpha=0.2)
    bottom.set_axisbelow(True)
    fig.suptitle('TEST: mỗi file có một trọng số như nhau trong macro metric')
    plt.show()
    plt.close(fig)
"""


def main():
    for name in NOTEBOOKS:
        path = ROOT / name
        notebook = json.loads(path.read_text(encoding="utf-8"))
        source = SOURCE.replace(
            "'ACF' if 'ACF' in NOTEBOOK_TITLE else 'AMDF'",
            repr("AMDF" if name.startswith("BT2_AMDF") else "ACF"),
        )
        cell = {
            "cell_type": "code", "id": "per-file-metric-plot", "metadata": {},
            "execution_count": None, "outputs": [], "source": source.splitlines(keepends=True),
        }
        if notebook["cells"][-1].get("id") == "per-file-metric-plot":
            notebook["cells"][-1] = cell
        else:
            assert all(item.get("id") != "per-file-metric-plot" for item in notebook["cells"])
            notebook["cells"].append(cell)
        path.write_text(json.dumps(notebook, ensure_ascii=False, separators=(",", ":")) + "\n",
                        encoding="utf-8")
        print(name, "cells", len(notebook["cells"]))


if __name__ == "__main__":
    main()
