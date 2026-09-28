"""Inspect signed F0 errors and candidate distributions on training folds only."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from experiment_01_hysteresis import FILES, OUT, fit_core
from experiment_03_labeled_threshold import fit_labeled_threshold
from experiment_04_energy_gate import fit_energy_threshold, load_with_energy


def main():
    files = [load_with_energy(path) for path in FILES]
    rows, label_rows = [], []
    for held in files:
        other = [item for item in files if item is not held]
        fit_scores = np.concatenate([item["scores"][np.isin(item["labels"], ("v", "uv"))]
                                     for item in other])
        core, labeled, energy = (fit_core(fit_scores), fit_labeled_threshold(other),
                                 fit_energy_threshold(other))
        preds = {"GMM core": held["scores"] < core,
                 "Labeled + energy": ((held["scores"] < labeled)
                                      & (held["relative_rms"] >= energy))}
        gt_mean, gt_std = held["stats"]["F0mean"], held["stats"]["F0std"]
        for name, pred in preds.items():
            f0 = held["fs"] / held["lags"][pred]
            rows.append({"file": held["name"], "method": name, "NumF0": len(f0),
                         "LAB_F0mean": gt_mean, "est_F0mean": f0.mean(),
                         "signed_mean_error": f0.mean() - gt_mean,
                         "LAB_F0std": gt_std, "est_F0std": f0.std(),
                         "signed_std_error": f0.std() - gt_std,
                         "median_F0": np.median(f0),
                         "outside_LAB_mean_plusminus_2std": int((abs(f0 - gt_mean) > 2 * gt_std).sum())})
            for label in ("v", "uv", "sil"):
                subset = held["fs"] / held["lags"][pred & (held["labels"] == label)]
                label_rows.append({"file": held["name"], "method": name, "label": label,
                                   "count": len(subset),
                                   "mean_candidate_F0": subset.mean() if len(subset) else np.nan,
                                   "outside_2std": int((abs(subset - gt_mean) > 2 * gt_std).sum())})
    pd.DataFrame(rows).to_csv(OUT / "experiment_04_f0_diagnosis.csv", index=False,
                              float_format="%.10g")
    pd.DataFrame(label_rows).to_csv(OUT / "experiment_04_f0_by_label.csv", index=False,
                                   float_format="%.10g")
    print(pd.DataFrame(rows).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
