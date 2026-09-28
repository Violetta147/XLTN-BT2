"""Training-only median-3 F0 smoothing within predicted voiced runs."""

import json

import numpy as np
import pandas as pd

from experiment_01_hysteresis import FILES, OUT, fit_core, metrics
from experiment_03_labeled_threshold import aggregate, fit_labeled_threshold
from experiment_04_energy_gate import fit_energy_threshold, load_with_energy


def median_f0_within_runs(item, prediction):
    f0 = np.full(len(prediction), np.nan)
    f0[prediction] = item["fs"] / item["lags"][prediction]
    edges = np.diff(np.r_[False, prediction, False].astype(int))
    for start, stop in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        if stop - start >= 3:
            original = f0[start:stop].copy()
            f0[start + 1:stop - 1] = np.median(
                np.stack((original[:-2], original[1:-1], original[2:])), axis=0)
    return f0


def smoothed_metrics(item, prediction):
    result = metrics(item, prediction)
    f0 = median_f0_within_runs(item, prediction)
    valid = f0[np.isfinite(f0)]
    assert len(valid) == result["NumF0"]
    result["F0mean_abs_error_hz"] = abs(valid.mean() - item["stats"]["F0mean"])
    result["F0std_abs_error_hz"] = abs(valid.std() - item["stats"]["F0std"])
    return result


def main():
    files = [load_with_energy(path) for path in FILES]
    rows = []
    for held in files:
        other = [item for item in files if item is not held]
        fit_scores = np.concatenate([item["scores"][np.isin(item["labels"], ("v", "uv"))]
                                     for item in other])
        core, labeled, energy = (fit_core(fit_scores), fit_labeled_threshold(other),
                                 fit_energy_threshold(other))
        base = held["scores"] < core
        gated = (held["scores"] < labeled) & (held["relative_rms"] >= energy)
        for method, result in (
            ("GMM core", metrics(held, base)),
            ("Labeled + energy", metrics(held, gated)),
            ("Labeled + energy + median3", smoothed_metrics(held, gated)),
        ):
            rows.append({"file": held["name"], "method": method,
                         "T_core": core, "T_label": labeled, "T_energy": energy,
                         **result})
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "experiment_05_lofo.csv", index=False, float_format="%.10g")
    base, gated, changed = (aggregate(frame, name) for name in
                            ("GMM core", "Labeled + energy", "Labeled + energy + median3"))
    assert base["TP"] == 490 and base["TN"] == 175 and base["FP"] == 5 and base["FN"] == 124
    assert gated["TP"] == 551 and gated["TN"] == 166 and gated["FP"] == 14 and gated["FN"] == 63
    for key in ("mean_macro_f1", "mean_balanced_accuracy", "TP", "TN", "FP", "FN", "NumF0", "FP_SIL"):
        assert changed[key] == gated[key], f"Smoothing changed {key}"
    keep = (changed["mean_macro_f1"] - base["mean_macro_f1"] >= .01
            and changed["mean_balanced_accuracy"] - base["mean_balanced_accuracy"] >= -.01
            and changed["FP"] - base["FP"] <= base["FN"] - changed["FN"]
            and changed["F0mean_MAE_hz"] <= base["F0mean_MAE_hz"]
            and changed["F0std_MAE_hz"] <= base["F0std_MAE_hz"]
            and changed["FP_SIL"] <= base["FP_SIL"])
    summary = {"data": "TinHieuHuanLuyen only", "frame_ms": 25, "hop_ms": 10,
               "cv": "leave one file out, four folds", "GMM_core": base,
               "labeled_plus_energy": gated, "labeled_plus_energy_plus_median3": changed,
               "keep_by_preregistered_rule": bool(keep)}
    if keep:
        summary["full_train_frozen_thresholds"] = {
            "T_label": fit_labeled_threshold(files),
            "T_energy": fit_energy_threshold(files)}
    (OUT / "experiment_05_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
