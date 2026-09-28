"""Training-only LOFO evaluation of the existing labeled Gaussian AMDF threshold."""

import json

import numpy as np
import pandas as pd

from experiment_01_hysteresis import FILES, OUT, fit_core, load_file, metrics
from experiment_03_labeled_threshold import aggregate


EPS = 1e-12


def gaussian_threshold(v_scores, u_scores):
    """Same equal-prior Gaussian crossing rule as the AMDF notebook."""
    mu_v, sv = float(v_scores.mean()), max(float(v_scores.std()), EPS)
    mu_u, su = float(u_scores.mean()), max(float(u_scores.std()), EPS)
    a = 1.0 / su**2 - 1.0 / sv**2
    b = -2.0 * mu_u / su**2 + 2.0 * mu_v / sv**2
    c = mu_u**2 / su**2 - mu_v**2 / sv**2 + 2.0 * np.log(su / sv)
    if abs(a) < EPS:
        roots = [] if abs(b) < EPS else [-c / b]
    else:
        roots = np.roots([a, b, c])
    real_roots = [float(np.real(root)) for root in roots if abs(np.imag(root)) < 1e-9]
    lo, hi = sorted((mu_v, mu_u))
    between = [root for root in real_roots if lo <= root <= hi]
    midpoint = 0.5 * (mu_v + mu_u)
    if between:
        return min(between, key=lambda root: abs(root - midpoint))
    if real_roots:
        return min(real_roots, key=lambda root: abs(root - midpoint))
    return midpoint


def add_recall(result):
    return {**result,
            "recall_V": result["TP"] / (result["TP"] + result["FN"]),
            "recall_UV": result["TN"] / (result["TN"] + result["FP"])}


def main():
    files = [load_file(path) for path in FILES]
    rows = []
    for held in files:
        other = [item for item in files if item is not held]
        vu_scores = np.concatenate([item["scores"][np.isin(item["labels"], ("v", "uv"))]
                                    for item in other])
        v_scores = np.concatenate([item["scores"][item["labels"] == "v"] for item in other])
        uv_scores = np.concatenate([item["scores"][item["labels"] == "uv"] for item in other])
        thresholds = {"GMM core": fit_core(vu_scores),
                      "Labeled Gaussian": gaussian_threshold(v_scores, uv_scores)}
        for method, threshold in thresholds.items():
            rows.append({"file": held["name"], "method": method, "threshold": threshold,
                         **add_recall(metrics(held, held["scores"] < threshold))})
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "experiment_06_lofo.csv", index=False, float_format="%.10g")
    baseline, changed = aggregate(frame, "GMM core"), aggregate(frame, "Labeled Gaussian")
    assert baseline["TP"] == 490 and baseline["TN"] == 175
    assert baseline["FP"] == 5 and baseline["FN"] == 124
    keep = (changed["mean_macro_f1"] - baseline["mean_macro_f1"] >= .01
            and changed["mean_balanced_accuracy"] - baseline["mean_balanced_accuracy"] >= -.01
            and changed["FP"] - baseline["FP"] <= baseline["FN"] - changed["FN"]
            and changed["F0mean_MAE_hz"] <= baseline["F0mean_MAE_hz"]
            and changed["F0std_MAE_hz"] <= baseline["F0std_MAE_hz"]
            and changed["FP_SIL"] <= baseline["FP_SIL"])
    summary = {"data": "TinHieuHuanLuyen only", "frame_ms": 25, "hop_ms": 10,
               "cv": "leave one file out, four folds", "GMM_core": baseline,
               "labeled_Gaussian": changed,
               "mean_recall_V": {method: float(group.recall_V.mean())
                                 for method, group in frame.groupby("method")},
               "mean_recall_UV": {method: float(group.recall_UV.mean())
                                  for method, group in frame.groupby("method")},
               "keep_by_preregistered_rule": bool(keep)}
    if keep:
        v_all = np.concatenate([item["scores"][item["labels"] == "v"] for item in files])
        uv_all = np.concatenate([item["scores"][item["labels"] == "uv"] for item in files])
        summary["full_train_frozen_threshold"] = gaussian_threshold(v_all, uv_all)
    (OUT / "experiment_06_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
