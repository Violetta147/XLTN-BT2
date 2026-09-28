"""Training-only AMDF 25 ms single-frame gap fill, preregistered in plan 02."""

import json

import numpy as np
import pandas as pd

from experiment_01_hysteresis import FILES, OUT, fit_core, load_file, metrics


def fill_single_gap(scores, core_threshold, weak_threshold):
    core = scores < core_threshold
    predicted = core.copy()
    predicted[1:-1] |= ((scores[1:-1] <= weak_threshold)
                        & core[:-2] & core[2:])
    return predicted


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
        train_scores = np.concatenate([item["scores"][np.isin(item["labels"], ("v", "uv"))]
                                       for item in other])
        uv_scores = np.concatenate([item["scores"][item["labels"] == "uv"] for item in other])
        core_threshold = fit_core(train_scores)
        weak_threshold = max(core_threshold, float(uv_scores.mean() - uv_scores.std()))
        for method, prediction in (
            ("GMM core", held["scores"] < core_threshold),
            ("Single gap", fill_single_gap(held["scores"], core_threshold, weak_threshold)),
        ):
            rows.append({"file": held["name"], "method": method,
                         "T_core": core_threshold, "T_weak": weak_threshold,
                         **metrics(held, prediction)})
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "experiment_02_lofo.csv", index=False, float_format="%.10g")
    core, changed = aggregate(frame, "GMM core"), aggregate(frame, "Single gap")
    assert core["TP"] == 490 and core["TN"] == 175 and core["FP"] == 5 and core["FN"] == 124
    assert abs(core["mean_macro_f1"] - 0.8050679204258859) < 1e-12
    keep = (changed["mean_macro_f1"] - core["mean_macro_f1"] >= .01
            and changed["mean_balanced_accuracy"] - core["mean_balanced_accuracy"] >= -.01
            and changed["FP"] - core["FP"] <= core["FN"] - changed["FN"]
            and changed["F0mean_MAE_hz"] <= core["F0mean_MAE_hz"]
            and changed["F0std_MAE_hz"] <= core["F0std_MAE_hz"]
            and changed["FP_SIL"] <= core["FP_SIL"])
    summary = {"data": "TinHieuHuanLuyen only", "frame_ms": 25, "hop_ms": 10,
               "cv": "leave one file out, four folds", "baseline": core,
               "single_gap": changed, "keep_by_preregistered_rule": bool(keep)}
    (OUT / "experiment_02_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
