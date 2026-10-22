"""Training-only LOFO experiment using an RMS scale fit on training files."""

import json

import numpy as np
import pandas as pd

from experiment_01_hysteresis import FILES, OUT, metrics
from experiment_04_energy_gate import fit_energy_threshold, load_with_energy
from experiment_07_acf_amdf_25ms import fit_selector
from validate_saved_results import load_wav


def median5_f0(item, prediction):
    f0 = np.full(len(prediction), np.nan)
    f0[prediction] = item["fs"] / item["lags"][prediction]
    edges = np.diff(np.r_[False, prediction, False].astype(int))
    for start, stop in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        if stop - start >= 5:
            raw = f0[start:stop].copy()
            windows = np.stack((raw[:-4], raw[1:-3], raw[2:-2],
                                raw[3:-1], raw[4:]), axis=0)
            f0[start + 2:stop - 2] = np.median(windows, axis=0)
    return f0


def f0_errors(item, prediction):
    f0 = median5_f0(item, prediction)
    f0 = f0[np.isfinite(f0) & (f0 > 0)]
    return {
        "NumF0": int(len(f0)),
        "F0mean_MAE_hz": abs(float(f0.mean()) - item["stats"]["F0mean"]),
        "F0std_MAE_hz": abs(float(f0.std()) - item["stats"]["F0std"]),
    }


def raw_frame_rms(path):
    fs, signal = load_wav(path)
    frame_length, hop_length = round(fs * .025), round(fs * .010)
    values = np.asarray([
        np.sqrt(np.mean(signal[start:start + frame_length] ** 2))
        for start in range(0, len(signal) - frame_length + 1, hop_length)
    ])
    return values


def summarize(rows, prefix):
    group = pd.DataFrame(rows)
    return {
        "mean_macro_f1": float(group[f"{prefix}macro_f1"].mean()),
        "mean_balanced_accuracy": float(group[f"{prefix}balanced_accuracy"].mean()),
        "mean_recall_V": float(group[f"{prefix}recall_V"].mean()),
        "mean_recall_UV": float(group[f"{prefix}recall_UV"].mean()),
        "F0mean_MAE_hz": float(group[f"{prefix}F0mean_MAE_hz"].mean()),
        "F0std_MAE_hz": float(group[f"{prefix}F0std_MAE_hz"].mean()),
        "NumF0": int(group[f"{prefix}NumF0"].sum()),
        "FP_SIL": int(group[f"{prefix}FP_SIL"].sum()),
    }


def main():
    items = {item["name"]: item for item in (load_with_energy(path) for path in FILES)}
    baseline_rms = {name: item["relative_rms"].copy() for name, item in items.items()}
    rms = {path.name: raw_frame_rms(path) for path in FILES}
    assert all(len(items[name]["scores"]) == len(rms[name]) for name in items)
    baseline = pd.read_csv(OUT / "experiment_14_outer_lofo.csv").set_index("outer_held_file")

    rows = []
    for held_path in FILES:
        held_name = held_path.name
        other_paths = [path for path in FILES if path.name != held_name]
        other = [items[path.name] for path in other_paths]
        scale = float(np.quantile(np.concatenate([rms[p.name] for p in other_paths]), .95))
        assert scale > 0

        # Reconstruct the accepted per-file-normalized median5 baseline and
        # verify it reproduces the saved outer-LOFO result before comparing.
        base_item = items[held_name]
        base_row = baseline.loc[held_name]
        base_pred = ((base_item["scores"] < float(base_row.T_pitch))
                     & (baseline_rms[held_name] >= float(base_row.T_energy)))
        base_metrics = metrics(base_item, base_pred)
        base_f0 = f0_errors(base_item, base_pred)
        for key, expected in (("TP", base_row.TP), ("TN", base_row.TN),
                              ("FP", base_row.FP), ("FN", base_row.FN),
                              ("NumF0", base_row.NumF0), ("FP_SIL", base_row.FP_SIL)):
            assert int(base_metrics[key]) == int(expected), (held_name, key)
        assert np.isclose(base_f0["F0mean_MAE_hz"], base_row.median5_F0mean_MAE_hz, atol=1e-8)
        assert np.isclose(base_f0["F0std_MAE_hz"], base_row.median5_F0std_MAE_hz, atol=1e-8)

        method, pitch_threshold, _ = fit_selector(other, "AMDF")
        assert method == "Gaussian"
        for path in other_paths + [held_path]:
            items[path.name]["relative_rms"] = rms[path.name] / scale
        train_with_scale = [items[path.name] for path in other_paths]
        energy_threshold = fit_energy_threshold(train_with_scale)
        changed_pred = ((items[held_name]["scores"] < pitch_threshold)
                        & (items[held_name]["relative_rms"] >= energy_threshold))
        changed_metrics = metrics(items[held_name], changed_pred)
        changed_f0 = f0_errors(items[held_name], changed_pred)

        labels = items[held_name]["labels"]
        vu = np.isin(labels, ("v", "uv"))
        truth = labels[vu] == "v"
        pred = changed_pred[vu]
        tp, tn = int((truth & pred).sum()), int((~truth & ~pred).sum())
        fp, fn = int((~truth & pred).sum()), int((truth & ~pred).sum())
        changed_macro_f1 = .5 * (2 * tp / (2 * tp + fp + fn)
                                 + 2 * tn / (2 * tn + fp + fn))
        changed_ba = .5 * (tp / (tp + fn) + tn / (tn + fp))
        changed_recall_v = tp / (tp + fn)
        changed_recall_uv = tn / (tn + fp)

        rows.append({
            "file": held_name,
            "rms_scale_from_training": scale,
            "pitch_threshold": pitch_threshold,
            "energy_threshold": energy_threshold,
            "baseline_macro_f1": float(base_metrics["macro_f1"]),
            "baseline_balanced_accuracy": float(base_metrics["balanced_accuracy"]),
            "baseline_recall_V": float(base_metrics["TP"] / (base_metrics["TP"] + base_metrics["FN"])),
            "baseline_recall_UV": float(base_metrics["TN"] / (base_metrics["TN"] + base_metrics["FP"])),
            "baseline_NumF0": base_f0["NumF0"],
            "baseline_F0mean_MAE_hz": base_f0["F0mean_MAE_hz"],
            "baseline_F0std_MAE_hz": base_f0["F0std_MAE_hz"],
            "baseline_FP_SIL": int(base_metrics["FP_SIL"]),
            "fixed_scale_macro_f1": changed_macro_f1,
            "fixed_scale_balanced_accuracy": changed_ba,
            "fixed_scale_recall_V": changed_recall_v,
            "fixed_scale_recall_UV": changed_recall_uv,
            "fixed_scale_NumF0": changed_f0["NumF0"],
            "fixed_scale_F0mean_MAE_hz": changed_f0["F0mean_MAE_hz"],
            "fixed_scale_F0std_MAE_hz": changed_f0["F0std_MAE_hz"],
            "fixed_scale_FP_SIL": int(changed_metrics["FP_SIL"]),
        })

    base = summarize(rows, "baseline_")
    fixed = summarize(rows, "fixed_scale_")
    keep = (
        fixed["mean_macro_f1"] >= base["mean_macro_f1"] - .01
        and fixed["mean_balanced_accuracy"] >= base["mean_balanced_accuracy"] - .01
        and fixed["mean_recall_V"] >= base["mean_recall_V"] - .02
        and fixed["F0mean_MAE_hz"] <= base["F0mean_MAE_hz"] + .25
        and fixed["F0std_MAE_hz"] <= base["F0std_MAE_hz"] + .25
        and fixed["FP_SIL"] <= 3
    )
    result = {
        "data": "TinHieuHuanLuyen only",
        "frame_ms": 25,
        "hop_ms": 10,
        "cv": "four-fold LOFO; fold scale and energy threshold fit on other three files",
        "scale_rule": "95th percentile of pooled raw frame RMS from the three training files",
        "baseline": base,
        "fixed_training_scale": fixed,
        "keep_by_preregistered_rule": bool(keep),
        "folds": rows,
    }
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "experiment_21_lofo.csv", index=False, float_format="%.10g")
    (OUT / "experiment_21_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(frame.to_string(index=False))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
