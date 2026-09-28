"""Training-only LOFO AMDF Gaussian plus energy gate versus 25 ms baselines."""

import json

import numpy as np
import pandas as pd

from experiment_01_hysteresis import FILES, OUT, metrics
from experiment_04_energy_gate import fit_energy_threshold, load_with_energy
from experiment_07_acf_amdf_25ms import fit_selector, summarize


def gated_row(item, pitch_threshold, energy_threshold):
    predicted = ((item["scores"] < pitch_threshold)
                 & (item["relative_rms"] >= energy_threshold))
    result = metrics(item, predicted)
    return {"file": item["name"], "algorithm": "AMDF+energy",
            "method": "Gaussian + energy", "threshold": pitch_threshold,
            "energy_threshold": energy_threshold, **result,
            "recall_V": result["TP"] / (result["TP"] + result["FN"]),
            "recall_UV": result["TN"] / (result["TN"] + result["FP"])}


def main():
    previous = pd.read_csv(OUT / "experiment_07_lofo.csv")
    assert len(previous) == 8 and set(previous.algorithm) == {"ACF", "AMDF"}
    previous["energy_threshold"] = np.nan
    files = [load_with_energy(path) for path in FILES]
    rows = []
    for held in files:
        other = [item for item in files if item is not held]
        method, pitch, _ = fit_selector(other, "AMDF")
        assert method == "Gaussian"
        energy = fit_energy_threshold(other)
        ungated = metrics(held, held["scores"] < pitch)
        saved = previous[(previous.algorithm == "AMDF") & (previous.file == held["name"])].iloc[0]
        assert abs(pitch - saved.threshold) < 1e-8
        for key in ("TP", "TN", "FP", "FN", "NumF0", "FP_SIL"):
            assert ungated[key] == saved[key], (held["name"], key)
        for key in ("macro_f1", "balanced_accuracy", "F0mean_abs_error_hz", "F0std_abs_error_hz"):
            assert np.isclose(ungated[key], saved[key], atol=1e-8), (held["name"], key)
        rows.append(gated_row(held, pitch, energy))
    frame = pd.concat([previous, pd.DataFrame(rows)], ignore_index=True)
    frame.to_csv(OUT / "experiment_08_lofo.csv", index=False, float_format="%.10g")
    acf, amdf, gated = (summarize(frame, name) for name in ("ACF", "AMDF", "AMDF+energy"))
    assert acf["TP"] == 533 and acf["FP_SIL"] == 44
    assert amdf["TP"] == 541 and amdf["FP_SIL"] == 51
    keep = (gated["mean_macro_f1"] - acf["mean_macro_f1"] >= .01
            and gated["mean_balanced_accuracy"] - acf["mean_balanced_accuracy"] >= -.01
            and gated["F0mean_MAE_hz"] <= acf["F0mean_MAE_hz"]
            and gated["F0std_MAE_hz"] <= acf["F0std_MAE_hz"]
            and gated["FP_SIL"] <= acf["FP_SIL"]
            and gated["FP_SIL"] < amdf["FP_SIL"]
            and gated["mean_macro_f1"] - amdf["mean_macro_f1"] >= -.01)
    summary = {"data": "TinHieuHuanLuyen only", "frame_ms": 25, "hop_ms": 10,
               "cv": "leave one file out, four folds", "ACF": acf,
               "AMDF_Gaussian": amdf, "AMDF_Gaussian_energy": gated,
               "keep_by_preregistered_rule": bool(keep)}
    if keep:
        method, pitch, _ = fit_selector(files, "AMDF")
        assert method == "Gaussian"
        summary["full_train_frozen_thresholds"] = {
            "T_pitch": pitch, "T_energy": fit_energy_threshold(files)}
    (OUT / "experiment_08_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
