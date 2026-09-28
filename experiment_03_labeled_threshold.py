"""Training-only LOFO comparison of labeled and unsupervised AMDF thresholds."""

import json

import numpy as np
import pandas as pd

from experiment_01_hysteresis import FILES, OUT, fit_core, load_file, metrics


def classification_at(item, threshold):
    mask = np.isin(item["labels"], ("v", "uv"))
    truth = item["labels"][mask] == "v"
    pred = item["scores"][mask] < threshold
    tp, tn = int((truth & pred).sum()), int((~truth & ~pred).sum())
    fp, fn = int((~truth & pred).sum()), int((truth & ~pred).sum())
    f1_v = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    f1_uv = 2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else 0.0
    ba = (tp / (tp + fn) + tn / (tn + fp)) / 2
    return (f1_v + f1_uv) / 2, ba, fp


def fit_labeled_threshold(files):
    unique = np.unique(np.concatenate([
        item["scores"][np.isin(item["labels"], ("v", "uv"))] for item in files
    ]))
    candidates = np.r_[np.nextafter(unique[0], -np.inf),
                       (unique[:-1] + unique[1:]) / 2,
                       np.nextafter(unique[-1], np.inf)]

    def objective(threshold):
        per_file = [classification_at(item, threshold) for item in files]
        return (float(np.mean([row[0] for row in per_file])),
                float(np.mean([row[1] for row in per_file])),
                -sum(row[2] for row in per_file), -float(threshold))

    return float(max(candidates, key=objective))


def aggregate(frame, method):
    group = frame[frame.method == method]
    return {"mean_macro_f1": float(group.macro_f1.mean()),
            "mean_balanced_accuracy": float(group.balanced_accuracy.mean()),
            "F0mean_MAE_hz": float(group.F0mean_abs_error_hz.mean()),
            "F0std_MAE_hz": float(group.F0std_abs_error_hz.mean()),
            "TP": int(group.TP.sum()), "TN": int(group.TN.sum()),
            "FP": int(group.FP.sum()), "FN": int(group.FN.sum()),
            "NumF0": int(group.NumF0.sum()), "FP_SIL": int(group.FP_SIL.sum())}


def main():
    files = [load_file(path) for path in FILES]
    rows = []
    for held in files:
        other = [item for item in files if item is not held]
        scores = np.concatenate([item["scores"][np.isin(item["labels"], ("v", "uv"))]
                                 for item in other])
        thresholds = {"GMM core": fit_core(scores),
                      "Labeled": fit_labeled_threshold(other)}
        for method, threshold in thresholds.items():
            rows.append({"file": held["name"], "method": method,
                         "threshold": threshold,
                         **metrics(held, held["scores"] < threshold)})
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "experiment_03_lofo.csv", index=False, float_format="%.10g")
    baseline, changed = aggregate(frame, "GMM core"), aggregate(frame, "Labeled")
    assert baseline["TP"] == 490 and baseline["TN"] == 175
    assert baseline["FP"] == 5 and baseline["FN"] == 124
    classifier_gain = (changed["mean_macro_f1"] - baseline["mean_macro_f1"] >= .01
                       and changed["mean_balanced_accuracy"] - baseline["mean_balanced_accuracy"] >= -.01
                       and changed["FP"] - baseline["FP"] <= baseline["FN"] - changed["FN"])
    full_acceptance = (classifier_gain
                       and changed["F0mean_MAE_hz"] <= baseline["F0mean_MAE_hz"]
                       and changed["F0std_MAE_hz"] <= baseline["F0std_MAE_hz"]
                       and changed["FP_SIL"] <= baseline["FP_SIL"])
    result = {"data": "TinHieuHuanLuyen only", "frame_ms": 25, "hop_ms": 10,
              "cv": "leave one file out, four folds", "baseline": baseline,
              "labeled": changed, "classifier_gate": bool(classifier_gain),
              "full_acceptance_gate": bool(full_acceptance)}
    if full_acceptance:
        result["full_train_frozen_threshold"] = fit_labeled_threshold(files)
    (OUT / "experiment_03_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
