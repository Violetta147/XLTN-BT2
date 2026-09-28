"""Make full-file TEST waveform/F0 figures opt-in in all three notebooks."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CHANGES = {
    "BT2_ACF_AMDF_GMM.ipynb": (16, "test_rows = []\n", "        plot_test_result(result)\n"),
    "BT2_implement_finished_v3_executed_original - Copy.ipynb":
        (32, "test_summaries = []\n", "    plot_test_result(wav_path, signal, fs, segments, result, summary)\n"),
    "BT2_AMDF_implement_executed_original - Copy.ipynb":
        (21, "test_summaries = []\n", "    plot_test_result(wav_path.name, result)\n"),
}


def main():
    for name, (loop_cell, marker, call) in CHANGES.items():
        path = ROOT / name
        notebook = json.loads(path.read_text(encoding="utf-8"))
        cells = notebook["cells"]
        source = "".join(cells[loop_cell]["source"])
        assert source.count(marker) == 1 and source.count(call) == 1
        source = source.replace(marker,
            "# Bật True khi cần xem từng waveform/F0; mặc định chỉ xem bảng và hình tổng hợp.\n"
            "SHOW_DETAILED_TEST_PLOTS = False\n" + marker)
        indentation = call[:len(call) - len(call.lstrip())]
        source = source.replace(call, indentation + "if SHOW_DETAILED_TEST_PLOTS:\n" +
                                "    " + call)
        cells[loop_cell]["source"] = source.splitlines(keepends=True)
        plot_cell = 30 if name.startswith("BT2_implement_finished") else (19 if name.startswith("BT2_AMDF") else 16)
        plot_source = "".join(cells[plot_cell]["source"])
        assert plot_source.count("    plt.show()\n") == 1
        plot_source = plot_source.replace("    plt.show()\n", "    plt.show()\n    plt.close(fig)\n")
        cells[plot_cell]["source"] = plot_source.splitlines(keepends=True)
        path.write_text(json.dumps(notebook, ensure_ascii=False, separators=(",", ":")) + "\n",
                        encoding="utf-8")
        print(name, "detailed plots now optional")


if __name__ == "__main__":
    main()
