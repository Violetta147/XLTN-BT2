"""Execute notebooks in memory and save the final per-file diagnostic plots."""

import contextlib
import io
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from IPython.display import display


ROOT = Path(__file__).resolve().parent.parent
DEST = Path(__file__).resolve().parent / "visualization_review"
NOTEBOOKS = {
    "GMM": ROOT / "BT2_ACF_AMDF_GMM.ipynb",
    "ACF": ROOT / "BT2_implement_finished_v3_executed_original - Copy.ipynb",
    "AMDF": ROOT / "BT2_AMDF_implement_executed_original - Copy.ipynb",
}
EXPECTED = {"GMM": 8, "ACF": 4, "AMDF": 4}


def main():
    DEST.mkdir(exist_ok=True)
    for name, path in NOTEBOOKS.items():
        cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
        namespace = {"__name__": "__main__", "display": display}
        saved = []
        old_show = plt.show
        with contextlib.redirect_stdout(io.StringIO()):
            for number, cell in enumerate(cells):
                if cell["cell_type"] != "code":
                    continue
                if number == len(cells) - 1:
                    def save_plot(*_args, **_kwargs):
                        figure = plt.gcf()
                        target = DEST / f"{name}_per_file_{len(saved) + 1}.png"
                        figure.savefig(target, dpi=130)
                        saved.append(target)
                    plt.show = save_plot
                exec(compile("".join(cell["source"]), f"{path.name}:cell{number}", "exec"), namespace)
        plt.show = old_show
        summary = namespace["test_summary_df"]
        assert len(summary) == EXPECTED[name]
        assert saved and all(target.stat().st_size > 1000 for target in saved)
        print(name, "rows", len(summary), "plots", [p.name for p in saved])


if __name__ == "__main__":
    main()
