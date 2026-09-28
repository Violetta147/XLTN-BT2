"""Recalculate all training frame scores and compare with notebook summaries."""

from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

from validate_saved_results import ROOT, OUTPUT, acf_score, amdf_score, load_wav, read_lab


def main():
    rows = []
    for wav_path in sorted((ROOT / "TinHieuHuanLuyen").glob("*.wav")):
        fs, signal = load_wav(wav_path)
        segments, _ = read_lab(wav_path.with_suffix(".lab"))
        for frame_ms in (20, 25, 30):
            frame_length = round(fs * frame_ms / 1000)
            hop_length = round(fs * .01)
            for start in range(0, len(signal) - frame_length + 1, hop_length):
                time = (start + frame_length / 2) / fs
                label = next((lab for a, b, lab in segments if a <= time < b), None)
                if label not in {"v", "uv"}:
                    continue
                frame = signal[start:start + frame_length]
                for algorithm, scorer in (("ACF", acf_score), ("AMDF", amdf_score)):
                    score, lag = scorer(frame, fs)
                    rows.append({"algorithm": algorithm, "frame_ms": frame_ms,
                                 "file": wav_path.name, "time_s": time,
                                 "label": label, "score": score, "lag_samples": lag})
    scores = pd.DataFrame(rows)
    scores.to_csv(OUTPUT / "recomputed_training_scores.csv", index=False)
    summary = (scores.groupby(["algorithm", "frame_ms", "label"], sort=True)
               .score.agg(["count", "mean", lambda x: np.std(x, ddof=0)])
               .reset_index().rename(columns={"<lambda_0>": "std"}))
    summary.to_csv(OUTPUT / "validation_training_summary.csv", index=False)
    saved_path = OUTPUT / "BT2_ACF_AMDF_GMM" / "cell_10" / "output_01.html"
    saved = pd.read_html(StringIO(saved_path.read_text(encoding="utf-8")))[0]
    for _, row in saved.iterrows():
        subset = summary[(summary.algorithm == row.Algorithm) &
                         (summary.frame_ms == row["Frame (ms)"])]
        v = subset[subset.label == "v"].iloc[0]
        uv = subset[subset.label == "uv"].iloc[0]
        print(row.Algorithm, row["Frame (ms)"], "counts", int(v["count"]), int(uv["count"]),
              "max mean/std delta", max(abs(v["mean"] - row.meanV),
                                        abs(v["std"] - row.stdV),
                                        abs(uv["mean"] - row.meanU),
                                        abs(uv["std"] - row.stdU)))


if __name__ == "__main__":
    main()
