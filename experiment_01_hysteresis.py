"""Preregistered AMDF 25 ms hysteresis experiment; training files only.

Run: .venv\Scripts\python.exe experiment_01_hysteresis.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.mixture import GaussianMixture

from validate_saved_results import amdf_score, load_wav, read_lab


ROOT = Path(__file__).resolve().parent
TRAIN = ROOT / "TinHieuHuanLuyen"
OUT = ROOT / "working_output"
FILES = sorted(TRAIN.glob("*.wav"))
assert len(FILES) == 4, "Expected four training files"


def normal_pdf(x, mean, std):
    std = max(float(std), 1e-12)
    return np.exp(-0.5 * ((x - mean) / std) ** 2) / (std * np.sqrt(2 * np.pi))


def fit_core(scores):
    model = GaussianMixture(
        n_components=2, covariance_type="spherical", reg_covar=1e-6,
        n_init=10, random_state=42,
    ).fit(np.asarray(scores).reshape(-1, 1))
    order = np.argsort(model.means_.ravel())
    means = model.means_.ravel()[order]
    stds = np.sqrt(model.covariances_[order])
    weights = model.weights_[order]
    grid = np.linspace(means[0], means[1], 10001)
    difference = (weights[0] * normal_pdf(grid, means[0], stds[0])
                  - weights[1] * normal_pdf(grid, means[1], stds[1]))
    crossings = np.where(difference[:-1] * difference[1:] <= 0)[0]
    if len(crossings):
        midpoint = 0.5 * (means[0] + means[1])
        index = min(crossings, key=lambda i: abs(grid[i] - midpoint))
        left, right = difference[index:index + 2]
        fraction = -left / (right - left) if right != left else 0.0
        return float(grid[index] + fraction * (grid[index + 1] - grid[index]))
    return float(grid[np.argmin(np.abs(difference))])


def load_file(path):
    fs, signal = load_wav(path)
    segments, stats = read_lab(path.with_suffix(".lab"))
    frame_length, hop_length = round(fs * .025), round(fs * .010)
    labels, scores, lags = [], [], []
    for start in range(0, len(signal) - frame_length + 1, hop_length):
        time = (start + frame_length / 2) / fs
        label = next((lab for a, b, lab in segments if a <= time < b), None)
        score, lag = amdf_score(signal[start:start + frame_length], fs)
        labels.append(label)
        scores.append(score)
        lags.append(lag)
    return {"name": path.name, "fs": fs, "labels": np.asarray(labels),
            "scores": np.asarray(scores), "lags": np.asarray(lags), "stats": stats}


def hysteresis(scores, core_threshold, weak_threshold):
    core = scores < core_threshold
    weak = scores <= weak_threshold
    prediction = np.zeros(len(scores), dtype=bool)
    edges = np.diff(np.r_[False, weak, False].astype(int))
    for start, stop in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        if core[start:stop].any():
            prediction[start:stop] = True
    return prediction


def metrics(item, prediction):
    labels = item["labels"]
    mask = np.isin(labels, ("v", "uv"))
    truth = labels[mask] == "v"
    pred = prediction[mask]
    tp, tn = int((truth & pred).sum()), int((~truth & ~pred).sum())
    fp, fn = int((~truth & pred).sum()), int((truth & ~pred).sum())
    f1_v = 2 * tp / (2 * tp + fp + fn)
    f1_uv = 2 * tn / (2 * tn + fp + fn)
    f0 = item["fs"] / item["lags"][prediction]
    f0 = f0[np.isfinite(f0) & (f0 > 0)]
    return {"TP": tp, "TN": tn, "FP": fp, "FN": fn,
            "macro_f1": (f1_v + f1_uv) / 2,
            "balanced_accuracy": (tp / (tp + fn) + tn / (tn + fp)) / 2,
            "NumF0": len(f0), "F0mean_abs_error_hz": abs(f0.mean() - item["stats"]["F0mean"]),
            "F0std_abs_error_hz": abs(f0.std() - item["stats"]["F0std"]),
            "FP_SIL": int(((labels == "sil") & prediction).sum())}


def main():
    files = [load_file(path) for path in FILES]
    rows = []
    for holdout in files:
        other = [item for item in files if item is not holdout]
        train_scores = np.concatenate([item["scores"][np.isin(item["labels"], ("v", "uv"))]
                                       for item in other])
        uv_scores = np.concatenate([item["scores"][item["labels"] == "uv"] for item in other])
        core_threshold = fit_core(train_scores)
        weak_threshold = max(core_threshold, float(uv_scores.mean() - uv_scores.std()))
        for method, prediction in (
            ("GMM core", holdout["scores"] < core_threshold),
            ("GMM hysteresis", hysteresis(holdout["scores"], core_threshold, weak_threshold)),
        ):
            rows.append({"file": holdout["name"], "method": method,
                         "T_core": core_threshold, "T_weak": weak_threshold,
                         **metrics(holdout, prediction)})
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "experiment_01_lofo.csv", index=False, float_format="%.10g")
    summary = {}
    for method, group in frame.groupby("method"):
        summary[method] = {
            "mean_macro_f1": float(group.macro_f1.mean()),
            "mean_balanced_accuracy": float(group.balanced_accuracy.mean()),
            "F0mean_MAE_hz": float(group.F0mean_abs_error_hz.mean()),
            "F0std_MAE_hz": float(group.F0std_abs_error_hz.mean()),
            "TP": int(group.TP.sum()), "TN": int(group.TN.sum()),
            "FP": int(group.FP.sum()), "FN": int(group.FN.sum()),
            "NumF0": int(group.NumF0.sum()), "FP_SIL": int(group.FP_SIL.sum()),
        }
    baseline, changed = summary["GMM core"], summary["GMM hysteresis"]
    keep = (changed["mean_macro_f1"] - baseline["mean_macro_f1"] >= .01
            and changed["mean_balanced_accuracy"] - baseline["mean_balanced_accuracy"] >= -.01
            and changed["FP"] - baseline["FP"] <= baseline["FN"] - changed["FN"])
    result = {"data": "TinHieuHuanLuyen only", "frame_ms": 25, "hop_ms": 10,
              "cv": "leave one file out, four folds", "sklearn_version": sklearn.__version__,
              "baseline": baseline, "hysteresis": changed, "keep_by_preregistered_rule": bool(keep)}
    (OUT / "experiment_01_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
