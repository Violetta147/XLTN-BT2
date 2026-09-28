"""Training-only AMDF 25 ms energy gate, preregistered in plan 04."""

import json

import numpy as np
import pandas as pd

from experiment_01_hysteresis import FILES, OUT, fit_core, load_file, metrics
from experiment_03_labeled_threshold import aggregate, fit_labeled_threshold
from validate_saved_results import load_wav


def load_with_energy(path):
    item = load_file(path)
    fs, signal = load_wav(path)
    length, hop = round(fs * .025), round(fs * .010)
    rms = np.asarray([np.sqrt(np.mean(signal[start:start + length] ** 2))
                      for start in range(0, len(signal) - length + 1, hop)])
    assert len(rms) == len(item["scores"])
    item["relative_rms"] = rms / max(float(np.quantile(rms, .95)), 1e-12)
    return item


def fit_energy_threshold(files):
    unique = np.unique(np.concatenate([
        item["relative_rms"][np.isin(item["labels"], ("v", "sil"))]
        for item in files
    ]))
    candidates = np.r_[np.nextafter(unique[0], -np.inf),
                       (unique[:-1] + unique[1:]) / 2,
                       np.nextafter(unique[-1], np.inf)]

    def objective(threshold):
        values = []
        for item in files:
            labels = item["labels"]
            v, sil = labels == "v", labels == "sil"
            energy = item["relative_rms"]
            values.append(((energy[v] >= threshold).mean()
                           + (energy[sil] < threshold).mean()) / 2)
        return float(np.mean(values)), -float(threshold)

    return float(max(candidates, key=objective))


def main():
    files = [load_with_energy(path) for path in FILES]
    rows = []
    for held in files:
        other = [item for item in files if item is not held]
        train_scores = np.concatenate([item["scores"][np.isin(item["labels"], ("v", "uv"))]
                                       for item in other])
        core, labeled = fit_core(train_scores), fit_labeled_threshold(other)
        energy = fit_energy_threshold(other)
        predictions = {
            "GMM core": held["scores"] < core,
            "Labeled": held["scores"] < labeled,
            "Labeled + energy": ((held["scores"] < labeled)
                                 & (held["relative_rms"] >= energy)),
        }
        for method, pred in predictions.items():
            rows.append({"file": held["name"], "method": method,
                         "T_core": core, "T_label": labeled, "T_energy": energy,
                         **metrics(held, pred)})
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "experiment_04_lofo.csv", index=False, float_format="%.10g")
    base = aggregate(frame, "GMM core")
    labeled = aggregate(frame, "Labeled")
    changed = aggregate(frame, "Labeled + energy")
    assert base["TP"] == 490 and base["TN"] == 175 and base["FP"] == 5 and base["FN"] == 124
    assert labeled["TP"] == 559 and labeled["TN"] == 159 and labeled["FP"] == 21 and labeled["FN"] == 55
    keep = (changed["mean_macro_f1"] - base["mean_macro_f1"] >= .01
            and changed["mean_balanced_accuracy"] - base["mean_balanced_accuracy"] >= -.01
            and changed["FP"] - base["FP"] <= base["FN"] - changed["FN"]
            and changed["F0mean_MAE_hz"] <= base["F0mean_MAE_hz"]
            and changed["F0std_MAE_hz"] <= base["F0std_MAE_hz"]
            and changed["FP_SIL"] <= base["FP_SIL"]
            and changed["FP_SIL"] < labeled["FP_SIL"])
    result = {"data": "TinHieuHuanLuyen only", "frame_ms": 25, "hop_ms": 10,
              "cv": "leave one file out, four folds", "GMM_core": base,
              "labeled": labeled, "labeled_plus_energy": changed,
              "keep_by_preregistered_rule": bool(keep)}
    if keep:
        result["full_train_frozen_thresholds"] = {
            "T_label": fit_labeled_threshold(files),
            "T_energy": fit_energy_threshold(files)}
    (OUT / "experiment_04_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
