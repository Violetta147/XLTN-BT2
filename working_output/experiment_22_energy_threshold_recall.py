"""Training-only LOFO experiment 22: energy threshold objective with an SIL-FP cap."""

from pathlib import Path
import json
import platform
import sys

import numpy as np
import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiment_04_energy_gate import FILES, fit_energy_threshold, load_with_energy
from experiment_14_nested_median_f0 import evaluate, fit_gaussian_pitch

OUT = ROOT / "working_output"
TRAIN_FP_SIL_CAP = 1


def fit_recall_threshold(files, fp_sil_cap=TRAIN_FP_SIL_CAP):
    """Maximize mean per-file V recall under a training-only SIL-FP cap."""
    unique = np.unique(np.concatenate([
        item["relative_rms"][np.isin(item["labels"], ("v", "sil"))]
        for item in files
    ]))
    candidates = np.r_[
        np.nextafter(unique[0], -np.inf),
        (unique[:-1] + unique[1:]) / 2,
        np.nextafter(unique[-1], np.inf),
    ]

    feasible = []
    for threshold in candidates:
        recalls = []
        fp_sil = 0
        for item in files:
            labels = item["labels"]
            pred = item["relative_rms"] >= threshold
            v = labels == "v"
            sil = labels == "sil"
            recalls.append(float(pred[v].mean()))
            fp_sil += int((pred & sil).sum())
        if fp_sil <= fp_sil_cap:
            # Primary: per-file V recall. Secondary: fewer SIL errors. Final
            # tie-break: higher threshold, minimizing extra voiced decisions.
            feasible.append((float(np.mean(recalls)), -fp_sil,
                             float(threshold), fp_sil))

    if not feasible:
        raise RuntimeError("No energy threshold satisfies the training SIL-FP cap")
    best = max(feasible)
    return best[2], {"training_mean_recall_V": best[0],
                     "training_FP_SIL": best[3],
                     "feasible_thresholds": len(feasible)}


def metric_row(item, pitch, energy, method, fit_diagnostics=None):
    result = evaluate(item, pitch, energy)
    result.pop("prediction")
    row = {"file": item["name"], "method": method,
           "T_pitch": pitch, "T_energy": energy, **result}
    if fit_diagnostics:
        row.update(fit_diagnostics)
    return row


def main():
    files = [load_with_energy(path) for path in FILES]
    baseline_saved = pd.read_csv(OUT / "experiment_14_outer_lofo.csv")
    baseline_summary = json.loads((OUT / "experiment_14_summary.json").read_text(
        encoding="utf-8-sig"))
    baseline_saved = baseline_saved.set_index("outer_held_file")

    rows = []
    for held in files:
        train = [item for item in files if item is not held]
        pitch = fit_gaussian_pitch(train)

        # Refit EXP14's original threshold first and assert implementation parity.
        baseline_energy = fit_energy_threshold(train)
        baseline_row = metric_row(held, pitch, baseline_energy, "baseline_EXP14")
        saved = baseline_saved.loc[held["name"]]
        parity_fields = {
            "T_pitch": pitch,
            "T_energy": baseline_energy,
            "TP": baseline_row["TP"], "TN": baseline_row["TN"],
            "FP": baseline_row["FP"], "FN": baseline_row["FN"],
            "macro_f1": baseline_row["macro_f1"],
            "balanced_accuracy": baseline_row["balanced_accuracy"],
            "recall_V": baseline_row["recall_V"],
            "recall_UV": baseline_row["recall_UV"],
            "NumF0": baseline_row["NumF0"], "FP_SIL": baseline_row["FP_SIL"],
            "median5_F0mean_MAE_hz": baseline_row["median5_F0mean_MAE_hz"],
            "median5_F0std_MAE_hz": baseline_row["median5_F0std_MAE_hz"],
        }
        for field, value in parity_fields.items():
            if field in ("TP", "TN", "FP", "FN", "NumF0", "FP_SIL"):
                if int(saved[field]) != int(value):
                    raise AssertionError(f"EXP14 parity failed for {held['name']} {field}")
            elif not np.isclose(float(saved[field]), float(value), atol=1e-8, rtol=0):
                raise AssertionError(f"EXP14 parity failed for {held['name']} {field}")

        candidate_energy, diagnostics = fit_recall_threshold(train)
        candidate_row = metric_row(held, pitch, candidate_energy,
                                   "recallV_under_1_training_SIL_FP", diagnostics)
        rows.extend((baseline_row, candidate_row))

    frame = pd.DataFrame(rows)
    base = frame[frame.method == "baseline_EXP14"].set_index("file")
    candidate = frame[frame.method != "baseline_EXP14"].set_index("file")
    summary = {
        "training_only": True,
        "frame_ms": 25,
        "hop_ms": 10,
        "cv": "four-fold outer leave-one-training-file-out",
        "threshold_rule": (
            "maximize mean per-file V recall on the three training files; "
            "require total training FP_SIL <= 1; ties: fewer training FP_SIL, "
            "then higher T_energy"
        ),
        "baseline": {
            "commit": "942499810070c27c71ed338592ff2015b56faa2d",
            "source": "experiment_14_outer_lofo.csv and experiment_14_summary.json",
            "mean_macro_f1": baseline_summary["mean_macro_f1"],
            "mean_balanced_accuracy": baseline_summary["mean_balanced_accuracy"],
            "mean_recall_V": baseline_summary["mean_recall_V"],
            "mean_recall_UV": baseline_summary["mean_recall_UV"],
            "F0mean_MAE_hz": float(base["median5_F0mean_MAE_hz"].mean()),
            "F0std_MAE_hz": float(base["median5_F0std_MAE_hz"].mean()),
            "NumF0_total": baseline_summary["NumF0_total"],
            "FP_SIL_total": baseline_summary["FP_SIL_total"],
        },
        "candidate": {
            "mean_macro_f1": float(candidate["macro_f1"].mean()),
            "mean_balanced_accuracy": float(candidate["balanced_accuracy"].mean()),
            "mean_recall_V": float(candidate["recall_V"].mean()),
            "mean_recall_UV": float(candidate["recall_UV"].mean()),
            "F0mean_MAE_hz": float(candidate["median5_F0mean_MAE_hz"].mean()),
            "F0std_MAE_hz": float(candidate["median5_F0std_MAE_hz"].mean()),
            "NumF0_total": int(candidate["NumF0"].sum()),
            "FP_SIL_total": int(candidate["FP_SIL"].sum()),
        },
    }
    b, c = summary["baseline"], summary["candidate"]
    gates = {
        "macro_f1_drop_le_0_005": c["mean_macro_f1"] >= b["mean_macro_f1"] - .005,
        "balanced_accuracy_drop_le_0_005": c["mean_balanced_accuracy"] >= b["mean_balanced_accuracy"] - .005,
        "recall_V_gain_ge_0_01": c["mean_recall_V"] >= b["mean_recall_V"] + .01,
        "FP_SIL_total_le_3": c["FP_SIL_total"] <= 3,
        "F0mean_MAE_increase_le_0_25": c["F0mean_MAE_hz"] <= b["F0mean_MAE_hz"] + .25,
        "F0std_MAE_increase_le_0_25": c["F0std_MAE_hz"] <= b["F0std_MAE_hz"] + .25,
    }
    summary["preregistered_gates"] = gates
    summary["keep_candidate"] = all(gates.values())
    summary["environment"] = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
    }

    frame.to_csv(OUT / "experiment_22_lofo.csv", index=False, float_format="%.10g")
    (OUT / "experiment_22_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(frame.to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
