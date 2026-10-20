"""Compare the notebook and reusable ACF scorer on training frames only."""

import ast
import json
from pathlib import Path
import sys

import numpy as np
import scipy
from scipy.signal import correlate

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "BT2_implement_finished_v3_executed_original - Copy.ipynb"
TRAIN = ROOT / "TinHieuHuanLuyen"
OUT = Path(__file__).resolve().parent / "acf_scorer_parity.json"
TOLERANCE = 1e-9
sys.path.insert(0, str(ROOT))

from validate_saved_results import acf_score, load_wav


def load_notebook_functions():
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    namespace = {"np": np, "EPS": 1e-12, "F0_MIN": 70, "F0_MAX": 400,
                 "correlate": correlate}
    for index, names in (
        (9, {"framing"}),
        (11, {"normalized_acf"}),
        (15, {"detect_pitch_acf"}),
    ):
        source = "".join(notebook["cells"][index]["source"])
        tree = ast.parse(source)
        definitions = [node for node in tree.body
                       if isinstance(node, ast.FunctionDef) and node.name in names]
        assert {node.name for node in definitions} == names
        exec(compile(ast.Module(body=definitions, type_ignores=[]),
                     f"notebook_cell_{index}", "exec"), namespace)
    return namespace


def main():
    functions = load_notebook_functions()
    max_score_delta = 0.0
    max_lag_delta = 0.0
    frames_checked = 0
    score_over_tolerance = 0
    lag_over_tolerance = 0
    frame_count_mismatches = []
    timestamp_mismatches = []

    files = sorted(TRAIN.glob("*.wav"))
    assert len(files) == 4, f"Expected four training WAVs, got {len(files)}"
    for path in files:
        fs, signal = load_wav(path)
        frames, times = functions["framing"](signal, fs, frame_ms=25, hop_ms=10)
        frame_length = round(fs * 0.025)
        hop_length = round(fs * 0.010)
        starts = np.arange(0, len(signal) - frame_length + 1, hop_length)
        reference_times = (starts + frame_length / 2.0) / fs
        if len(frames) != len(starts):
            frame_count_mismatches.append(path.name)
        if not np.array_equal(times, reference_times):
            timestamp_mismatches.append(path.name)

        for frame in frames:
            notebook_score, notebook_lag, _ = functions["detect_pitch_acf"](frame, fs)
            reused_score, reused_lag = acf_score(frame, fs)
            score_delta = abs(float(notebook_score) - float(reused_score))
            lag_delta = abs(float(notebook_lag) - float(reused_lag))
            max_score_delta = max(max_score_delta, score_delta)
            max_lag_delta = max(max_lag_delta, lag_delta)
            score_over_tolerance += score_delta > TOLERANCE
            lag_over_tolerance += lag_delta > TOLERANCE
            frames_checked += 1

    result = {
        "data": "TinHieuHuanLuyen only",
        "files": [path.name for path in files],
        "frames_checked": frames_checked,
        "frame_count_mismatches": frame_count_mismatches,
        "timestamp_mismatches": timestamp_mismatches,
        "tolerance": TOLERANCE,
        "max_abs_score_delta": max_score_delta,
        "max_abs_lag_delta_samples": max_lag_delta,
        "score_over_tolerance": score_over_tolerance,
        "lag_over_tolerance": lag_over_tolerance,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
