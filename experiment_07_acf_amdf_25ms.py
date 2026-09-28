"""Training-only LOFO comparison of original ACF/AMDF selectors at 25 ms.

Threshold functions are loaded from the saved notebooks, not reimplemented.
Run: .venv\Scripts\python.exe experiment_07_acf_amdf_25ms.py
"""

import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd

from validate_saved_results import acf_score, amdf_score, load_wav, read_lab


ROOT = Path(__file__).resolve().parent
TRAIN = ROOT / "TinHieuHuanLuyen"
OUT = ROOT / "working_output"
FILES = sorted(TRAIN.glob("*.wav"))
assert len(FILES) == 4


def notebook_functions(filename, cell_index, names):
    notebook = json.loads((ROOT / filename).read_text(encoding="utf-8"))
    source = "".join(notebook["cells"][cell_index]["source"])
    tree = ast.parse(source)
    selected = [node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in selected} == set(names)
    namespace = {"np": np, "EPS": 1e-12, "HIST_BINS": 20,
                 "HIST_SMOOTH_WINDOW": 5, "HIST_W": 1.0}
    exec(compile(ast.Module(body=selected, type_ignores=[]), filename, "exec"), namespace)
    return namespace


ACF = notebook_functions(
    "BT2_implement_finished_v3_executed_original - Copy.ipynb", 19,
    ("gaussian_intersection", "histogram_threshold", "class_histogram_threshold"),
)
AMDF = notebook_functions(
    "BT2_AMDF_implement_executed_original - Copy.ipynb", 9,
    ("gaussian_threshold", "two_mode_histogram_threshold", "histogram_threshold"),
)


def load_file(path, algorithm):
    fs, signal = load_wav(path)
    segments, stats = read_lab(path.with_suffix(".lab"))
    frame_length, hop = round(fs * .025), round(fs * .010)
    scorer = acf_score if algorithm == "ACF" else amdf_score
    labels, scores, lags = [], [], []
    for start in range(0, len(signal) - frame_length + 1, hop):
        center = (start + frame_length / 2) / fs
        labels.append(next((label for a, b, label in segments if a <= center < b), None))
        score, lag = scorer(signal[start:start + frame_length], fs)
        scores.append(score)
        lags.append(lag)
    return {"file": path.name, "algorithm": algorithm, "fs": fs,
            "labels": np.asarray(labels), "scores": np.asarray(scores),
            "lags": np.asarray(lags), "stats": stats}


def counts(labels, predicted):
    mask = np.isin(labels, ("v", "uv"))
    truth = labels[mask] == "v"
    pred = predicted[mask]
    tp, tn = int((truth & pred).sum()), int((~truth & ~pred).sum())
    fp, fn = int((~truth & pred).sum()), int((truth & ~pred).sum())
    return tp, tn, fp, fn


def fit_selector(training_files, algorithm):
    v = np.concatenate([item["scores"][item["labels"] == "v"] for item in training_files])
    uv = np.concatenate([item["scores"][item["labels"] == "uv"] for item in training_files])
    all_vu = np.concatenate([item["scores"][np.isin(item["labels"], ("v", "uv"))]
                             for item in training_files])
    if algorithm == "ACF":
        methods = {
            "Gaussian": ACF["gaussian_intersection"](v.mean(), v.std(), uv.mean(), uv.std()),
            "Histogram M1/M2": ACF["histogram_threshold"](all_vu)["threshold"],
            "Histogram V/UV intersection": ACF["class_histogram_threshold"](v, uv)[0],
        }
    else:
        methods = {
            "Gaussian": AMDF["gaussian_threshold"](v, uv),
            "Histogram M1/M2": AMDF["two_mode_histogram_threshold"](all_vu)["threshold"],
            "Histogram V/UV intersection": AMDF["histogram_threshold"](v, uv)[0],
        }

    def selector_score(threshold):
        if algorithm == "ACF":
            tp, fn = int((v >= threshold).sum()), int((v < threshold).sum())
            fp, tn = int((uv >= threshold).sum()), int((uv < threshold).sum())
        else:
            tp, fn = int((v < threshold).sum()), int((v >= threshold).sum())
            fp, tn = int((uv < threshold).sum()), int((uv >= threshold).sum())
        return ((tp / (tp + fn) + tn / (tn + fp)) / 2,
                (tp + tn) / (tp + tn + fp + fn))

    chosen = max(methods, key=lambda name: selector_score(methods[name]))
    return chosen, float(methods[chosen]), {name: float(value) for name, value in methods.items()}


def evaluate(item, method, threshold):
    pred = (item["scores"] >= threshold if item["algorithm"] == "ACF"
            else item["scores"] < threshold)
    tp, tn, fp, fn = counts(item["labels"], pred)
    f1_v = 2 * tp / (2 * tp + fp + fn)
    f1_uv = 2 * tn / (2 * tn + fp + fn)
    f0 = item["fs"] / item["lags"][pred]
    f0 = f0[np.isfinite(f0) & (f0 > 0)]
    return {"file": item["file"], "algorithm": item["algorithm"], "method": method,
            "threshold": threshold, "TP": tp, "TN": tn, "FP": fp, "FN": fn,
            "macro_f1": (f1_v + f1_uv) / 2,
            "recall_V": tp / (tp + fn), "recall_UV": tn / (tn + fp),
            "balanced_accuracy": (tp / (tp + fn) + tn / (tn + fp)) / 2,
            "NumF0": len(f0),
            "F0mean_abs_error_hz": abs(f0.mean() - item["stats"]["F0mean"]),
            "F0std_abs_error_hz": abs(f0.std() - item["stats"]["F0std"]),
            "FP_SIL": int(((item["labels"] == "sil") & pred).sum())}


def summarize(frame, algorithm):
    group = frame[frame.algorithm == algorithm]
    return {"mean_macro_f1": float(group.macro_f1.mean()),
            "mean_balanced_accuracy": float(group.balanced_accuracy.mean()),
            "mean_recall_V": float(group.recall_V.mean()),
            "mean_recall_UV": float(group.recall_UV.mean()),
            "F0mean_MAE_hz": float(group.F0mean_abs_error_hz.mean()),
            "F0std_MAE_hz": float(group.F0std_abs_error_hz.mean()),
            "TP": int(group.TP.sum()), "TN": int(group.TN.sum()),
            "FP": int(group.FP.sum()), "FN": int(group.FN.sum()),
            "NumF0": int(group.NumF0.sum()), "FP_SIL": int(group.FP_SIL.sum())}


def dominates(candidate, other):
    return (candidate["mean_macro_f1"] - other["mean_macro_f1"] >= .01
            and candidate["mean_balanced_accuracy"] - other["mean_balanced_accuracy"] >= -.01
            and candidate["F0mean_MAE_hz"] <= other["F0mean_MAE_hz"]
            and candidate["F0std_MAE_hz"] <= other["F0std_MAE_hz"]
            and candidate["FP_SIL"] <= other["FP_SIL"])


def main():
    by_algorithm = {name: [load_file(path, name) for path in FILES]
                    for name in ("ACF", "AMDF")}
    rows = []
    for algorithm, files in by_algorithm.items():
        for held in files:
            other = [item for item in files if item is not held]
            method, threshold, _ = fit_selector(other, algorithm)
            rows.append(evaluate(held, method, threshold))
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "experiment_07_lofo.csv", index=False, float_format="%.10g")
    acf, amdf = summarize(frame, "ACF"), summarize(frame, "AMDF")
    reference = {}
    for algorithm, files in by_algorithm.items():
        method, threshold, candidates = fit_selector(files, algorithm)
        reference[algorithm] = {"method": method, "threshold": threshold,
                                "candidate_thresholds": candidates}
    assert round(reference["ACF"]["threshold"], 4) == .6841
    assert round(reference["AMDF"]["candidate_thresholds"]["Gaussian"], 4) == .4125
    result = {"data": "TinHieuHuanLuyen only", "frame_ms": 25, "hop_ms": 10,
              "cv": "leave one file out, four folds", "ACF": acf, "AMDF": amdf,
              "full_train_parity_check_only": reference,
              "ACF_dominates": bool(dominates(acf, amdf)),
              "AMDF_dominates": bool(dominates(amdf, acf))}
    (OUT / "experiment_07_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
