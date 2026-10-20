"""Compare notebook LAB labels with the LOFO parser on training frames only."""

import ast
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "TinHieuHuanLuyen"
OUT = Path(__file__).resolve().parent / "lofo_label_parity.json"
sys.path.insert(0, str(ROOT))

from validate_saved_results import load_wav, read_lab as lofo_read_lab


def compile_functions(notebook_path, cells, names, namespace):
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    for index, wanted in zip(cells, names):
        source = "".join(notebook["cells"][index]["source"])
        tree = ast.parse(source)
        definitions = [node for node in tree.body
                       if isinstance(node, ast.FunctionDef) and node.name in wanted]
        assert {node.name for node in definitions} == wanted
        exec(compile(ast.Module(body=definitions, type_ignores=[]),
                     f"{notebook_path.name}:cell_{index}", "exec"), namespace)
    return namespace


def compare(file_name, centers, notebook_labels, lofo_labels, differences):
    if len(notebook_labels) != len(centers) or len(lofo_labels) != len(centers):
        differences.append({"file": file_name, "issue": "label/frame count mismatch",
                            "frames": len(centers),
                            "notebook_labels": len(notebook_labels),
                            "lofo_labels": len(lofo_labels)})
        return
    for index, (time, notebook_label, lofo_label) in enumerate(
            zip(centers, notebook_labels, lofo_labels)):
        if notebook_label != lofo_label:
            differences.append({"file": file_name, "frame_idx": index,
                                "center_time_s": float(time),
                                "notebook_label": notebook_label,
                                "lofo_label": lofo_label})


def main():
    acf_path = ROOT / "BT2_implement_finished_v3_executed_original - Copy.ipynb"
    amdf_path = ROOT / "BT2_AMDF_implement_executed_original - Copy.ipynb"
    acf = compile_functions(acf_path, (7, 9),
                            ({"parse_lab_file"}, {"framing", "label_at_time"}),
                            {"os": __import__("os"), "np": np})
    amdf = compile_functions(amdf_path, (3,),
                             ({"read_lab", "framing", "label_at_time"},),
                             {"np": np, "HOP_MS": 10})

    files = sorted(TRAIN.glob("*.wav"))
    assert len(files) == 4, f"Expected four training WAVs, got {len(files)}"
    differences = []
    compared_frames = 0
    for path in files:
        fs, signal = load_wav(path)
        _, centers = acf["framing"](signal, fs, frame_ms=25, hop_ms=10)
        acf_segments, _, _ = acf["parse_lab_file"](path.with_suffix(".lab"))
        amdf_segments, _, _ = amdf["read_lab"](path.with_suffix(".lab"))
        lofo_segments, _ = lofo_read_lab(path.with_suffix(".lab"))
        acf_labels = [acf["label_at_time"](t, acf_segments) for t in centers]
        amdf_labels = [amdf["label_at_time"](t, amdf_segments) for t in centers]
        lofo_labels = [next((label for start, end, label in lofo_segments
                             if start <= t < end), None) for t in centers]
        compare(path.name, centers, acf_labels, lofo_labels, differences)
        compare(path.name, centers, amdf_labels, lofo_labels, differences)
        compared_frames += len(centers)

    result = {"data": "TinHieuHuanLuyen only",
              "files": [path.name for path in files],
              "frame_ms": 25, "hop_ms": 10,
              "compared_frames_per_notebook": compared_frames,
              "comparisons": 2,
              "label_differences": len(differences),
              "first_differences": differences[:10],
              "numpy": np.__version__}
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
