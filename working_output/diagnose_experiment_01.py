"""Describe frames newly accepted by experiment 01; no model change or TEST use."""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from experiment_01_hysteresis import FILES, OUT, fit_core, hysteresis, load_file


def main():
    files = [load_file(path) for path in FILES]
    rows = []
    for held in files:
        other = [item for item in files if item is not held]
        scores = np.concatenate([item["scores"][np.isin(item["labels"], ("v", "uv"))]
                                 for item in other])
        uv = np.concatenate([item["scores"][item["labels"] == "uv"] for item in other])
        core = fit_core(scores)
        weak = max(core, float(uv.mean() - uv.std()))
        before = held["scores"] < core
        after = hysteresis(held["scores"], core, weak)
        assert np.all(~before | after)
        for index in np.flatnonzero(after & ~before):
            f0 = held["fs"] / held["lags"][index]
            mean, std = held["stats"]["F0mean"], held["stats"]["F0std"]
            rows.append({"file": held["name"], "frame_index": int(index),
                         "label": held["labels"][index], "score": held["scores"][index],
                         "candidate_F0_hz": f0,
                         "outside_LAB_mean_plusminus_2std": bool(abs(f0 - mean) > 2 * std)})
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "experiment_01_added_frames.csv", index=False, float_format="%.10g")
    summary = frame.groupby(["file", "label"], dropna=False).agg(
        frames=("frame_index", "size"),
        median_candidate_F0_hz=("candidate_F0_hz", "median"),
        min_candidate_F0_hz=("candidate_F0_hz", "min"),
        max_candidate_F0_hz=("candidate_F0_hz", "max"),
        outside_2std=("outside_LAB_mean_plusminus_2std", "sum"),
    ).reset_index()
    summary.to_csv(OUT / "experiment_01_added_summary.csv", index=False, float_format="%.10g")
    print(summary.to_string(index=False))
    print("Total new frames:", len(frame), "by label:", frame.label.value_counts().to_dict())


if __name__ == "__main__":
    main()
