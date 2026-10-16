"""Training-only LOFO comparison of 5-frame and 3-frame F0 median smoothing."""

from pathlib import Path
import json
import platform
import sys

import numpy as np
import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_04_energy_gate import FILES, load_with_energy
from experiment_05_median_f0 import median_f0_within_runs


def median5_within_runs(item, prediction):
    """Replace only interior F0 values of predicted voiced runs, from raw F0."""
    f0 = np.full(len(prediction), np.nan)
    f0[prediction] = item["fs"] / item["lags"][prediction]
    edges = np.diff(np.r_[False, prediction, False].astype(int))
    for start, stop in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        if stop - start >= 5:
            raw = f0[start:stop].copy()
            windows = np.stack(
                (raw[:-4], raw[1:-3], raw[2:-2], raw[3:-1], raw[4:]), axis=0
            )
            f0[start + 2:stop - 2] = np.median(windows, axis=0)
    return f0


def errors(f0, stats):
    valid = f0[np.isfinite(f0) & (f0 > 0)]
    return {
        "NumF0": int(len(valid)),
        "F0mean_MAE_hz": abs(float(valid.mean()) - stats["F0mean"]),
        "F0std_MAE_hz": abs(float(valid.std()) - stats["F0std"]),
    }


def main():
    thresholds = pd.read_csv(ROOT / "working_output" / "experiment_08_lofo.csv")
    thresholds = thresholds[thresholds.method == "Gaussian + energy"].set_index("file")
    previous = pd.read_csv(ROOT / "working_output" / "experiment_12_lofo.csv").set_index("file")
    rows = []
    for path in FILES:
        item = load_with_energy(path)
        ref = thresholds.loc[path.name]
        pred = ((item["scores"] < float(ref.threshold)) &
                (item["relative_rms"] >= float(ref.energy_threshold)))
        f0_3 = median_f0_within_runs(item, pred)
        f0_5 = median5_within_runs(item, pred)
        e3, e5 = errors(f0_3, item["stats"]), errors(f0_5, item["stats"])
        assert e3["NumF0"] == e5["NumF0"] == int(ref.NumF0)
        prev = previous.loc[path.name]
        assert np.isclose(e3["F0mean_MAE_hz"], prev.median3_F0mean_MAE_hz, atol=1e-8)
        assert np.isclose(e3["F0std_MAE_hz"], prev.median3_F0std_MAE_hz, atol=1e-8)
        rows.append({
            "file": path.name,
            "median3_F0mean_MAE_hz": e3["F0mean_MAE_hz"],
            "median5_F0mean_MAE_hz": e5["F0mean_MAE_hz"],
            "median3_F0std_MAE_hz": e3["F0std_MAE_hz"],
            "median5_F0std_MAE_hz": e5["F0std_MAE_hz"],
            "NumF0": e5["NumF0"],
            "macro_f1": float(ref.macro_f1),
            "balanced_accuracy": float(ref.balanced_accuracy),
            "recall_V": float(ref.recall_V),
            "recall_UV": float(ref.recall_UV),
            "FP_SIL": int(ref.FP_SIL),
        })

    frame = pd.DataFrame(rows)
    delta_mean = float((frame.median3_F0mean_MAE_hz - frame.median5_F0mean_MAE_hz).mean())
    delta_std = float((frame.median3_F0std_MAE_hz - frame.median5_F0std_MAE_hz).mean())
    summary = {
        "training_only": True,
        "frame_ms": 25,
        "hop_ms": 10,
        "cv": "four-fold leave-one-file-out; frozen per-fold thresholds from experiment 08",
        "baseline": "median3 from experiment 12",
        "files": len(frame),
        "mean_median3_F0mean_MAE_hz": float(frame.median3_F0mean_MAE_hz.mean()),
        "mean_median5_F0mean_MAE_hz": float(frame.median5_F0mean_MAE_hz.mean()),
        "mean_median3_F0std_MAE_hz": float(frame.median3_F0std_MAE_hz.mean()),
        "mean_median5_F0std_MAE_hz": float(frame.median5_F0std_MAE_hz.mean()),
        "median5_mean_improvement_F0mean_MAE_hz": delta_mean,
        "median5_mean_improvement_F0std_MAE_hz": delta_std,
        "max_per_file_F0mean_regression_hz": float(
            (frame.median5_F0mean_MAE_hz - frame.median3_F0mean_MAE_hz).max()
        ),
        "NumF0_total": int(frame.NumF0.sum()),
        "macro_f1_mean": float(frame.macro_f1.mean()),
        "balanced_accuracy_mean": float(frame.balanced_accuracy.mean()),
        "recall_V_mean": float(frame.recall_V.mean()),
        "recall_UV_mean": float(frame.recall_UV.mean()),
        "FP_SIL_total": int(frame.FP_SIL.sum()),
        "keep_by_preregistered_rule": bool(
            delta_std >= 0.25 and delta_mean >= -0.10 and
            (frame.median5_F0mean_MAE_hz - frame.median3_F0mean_MAE_hz).max() <= 1.0
        ),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
    }
    assert int(frame.NumF0.sum()) == int(thresholds.NumF0.sum())
    assert int(frame.FP_SIL.sum()) == int(thresholds.FP_SIL.sum())
    out = ROOT / "working_output"
    frame.to_csv(out / "experiment_13_lofo.csv", index=False, float_format="%.10g")
    (out / "experiment_13_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(frame.to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
