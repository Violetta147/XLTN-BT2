from pathlib import Path
import sys
import pandas as pd
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_04_energy_gate import FILES, load_with_energy

rows = []
folds = pd.read_csv(ROOT / "working_output" / "experiment_08_lofo.csv")
folds = folds[folds["method"] == "Gaussian + energy"]
assert len(folds) == len(FILES) == 4
for path in FILES:
    item = load_with_energy(path)
    saved = folds[folds.file == path.name].iloc[0]
    pred = ((item["scores"] < float(saved.threshold)) &
            (item["relative_rms"] >= float(saved.energy_threshold)))
    labels, lags, fs = item["labels"], item["lags"], item["fs"]
    f0 = fs / lags
    valid = pred & np.isfinite(f0) & (f0 > 0)
    row = {"file": path.name, "frames_total": len(labels),
           "frames_unlabeled": int((labels == None).sum()),
           "LAB_V": int((labels == "v").sum()), "LAB_UV": int((labels == "uv").sum()),
           "LAB_SIL": int((labels == "sil").sum()),
           "pred_voiced_all": int(pred.sum()),
           "TP_V_pred": int((pred & (labels == "v")).sum()),
           "FP_UV_pred": int((pred & (labels == "uv")).sum()),
           "FP_SIL_pred": int((pred & (labels == "sil")).sum()),
           "pred_unlabeled": int((pred & (labels == None)).sum()),
           "NumF0": int(valid.sum()),
           "validF0_LAB_V": int((valid & (labels == "v")).sum()),
           "validF0_LAB_UV": int((valid & (labels == "uv")).sum()),
           "validF0_LAB_SIL": int((valid & (labels == "sil")).sum()),
           "validF0_unlabeled": int((valid & (labels == None)).sum()),
           "invalidF0_predicted": int((pred & (~np.isfinite(f0) | (f0 <= 0))).sum()),
           "saved_NumF0": int(saved.NumF0)}
    assert row["NumF0"] == row["saved_NumF0"], (path.name, row["NumF0"], row["saved_NumF0"])
    assert row["NumF0"] == row["validF0_LAB_V"] + row["validF0_LAB_UV"] + row["validF0_LAB_SIL"] + row["validF0_unlabeled"]
    rows.append(row)
out = pd.DataFrame(rows)
out.to_csv(ROOT / "working_output" / "numf0_training_audit.csv", index=False)
print(out.to_string(index=False))
print("TOTALS\n", out.select_dtypes(include="number").sum().to_string())
