"""Independently recalculate saved test results with NumPy and WAV/LAB files.

Uses no notebook functions or fitted models; it applies only the thresholds and
frame lengths printed in the saved notebook outputs. Requires NumPy and pandas.
"""

from io import StringIO
from pathlib import Path
import wave

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "working_output"
TEST = ROOT / "TinHieuKiemThu"
MODELS = [
    ("GMM ACF", "ACF", 20, 0.8480, "BT2_ACF_AMDF_GMM", 16, 10, 12),
    ("GMM AMDF", "AMDF", 25, 0.3472, "BT2_ACF_AMDF_GMM", 16, 10, 12),
    ("ACF baseline", "ACF", 25, 0.6841, "BT2_implement_finished_v3_executed_original - Copy", 33, 5, 7),
    ("AMDF baseline", "AMDF", 30, 0.4204, "BT2_AMDF_implement_executed_original - Copy", 21, 5, 7),
]


def load_wav(path):
    with wave.open(str(path), "rb") as handle:
        fs = handle.getframerate()
        assert handle.getnchannels() == 1 and handle.getsampwidth() == 2
        signal = np.frombuffer(handle.readframes(handle.getnframes()), dtype="<i2")
    return fs, signal.astype(np.float64) / 32768.0


def read_lab(path):
    segments = []
    stats = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] in {"F0mean", "F0std"}:
            stats[parts[0]] = float(parts[1])
        else:
            segments.append((float(parts[0]), float(parts[1]), parts[2]))
    return segments, stats


def acf_score(frame, fs):
    x = frame - frame.mean()
    n = len(x)
    fft_size = 1 << (2 * n - 2).bit_length()
    spectrum = np.fft.rfft(x, fft_size)
    numerator = np.fft.irfft(spectrum * spectrum.conjugate(), fft_size)[:n]
    cumulative = np.r_[0.0, np.cumsum(x * x)]
    lags = np.arange(n)
    denominator = np.sqrt(cumulative[n - lags] * (cumulative[n] - cumulative[lags]))
    scores = np.divide(numerator, denominator, out=np.zeros(n), where=denominator > 1e-12)
    lo = max(1, int(np.ceil(fs / 400.0)))
    hi = min(n - 2, int(np.floor(fs / 70.0)))
    candidates = np.arange(lo, hi + 1)
    local = candidates[(scores[candidates] >= scores[candidates - 1]) &
                       (scores[candidates] >= scores[candidates + 1])]
    best = int(local[np.argmax(scores[local])]) if len(local) else int(lo + np.argmax(scores[lo:hi + 1]))
    lag = float(best)
    a, b, c = scores[best - 1:best + 2]
    denominator = a - 2 * b + c
    if abs(denominator) > 1e-12:
        delta = 0.5 * (a - c) / denominator
        if abs(delta) <= 1:
            lag += float(delta)
    return float(scores[best]), lag


def amdf_score(frame, fs):
    x = frame - frame.mean()
    n = len(x)
    lo = max(1, int(np.floor(fs / 400.0)))
    hi = min(n - 1, int(np.ceil(fs / 70.0)))
    lags = np.arange(lo, hi + 1)
    if np.mean(np.abs(x)) < 1e-8:
        scores = np.ones(len(lags))
    else:
        sample_index = np.arange(n - lo)[None, :]
        lag_matrix = lags[:, None]
        valid = sample_index < n - lag_matrix
        shifted_index = np.minimum(sample_index + lag_matrix, n - 1)
        left = np.broadcast_to(x[:n - lo][None, :], shifted_index.shape)
        right = x[shifted_index]
        count = valid.sum(axis=1)
        diff = (np.abs(left - right) * valid).sum(axis=1) / count
        left_abs = (np.abs(left) * valid).sum(axis=1) / count
        right_abs = (np.abs(right) * valid).sum(axis=1) / count
        scores = diff / (left_abs + right_abs + 1e-12)
    local = np.where((scores[1:-1] <= scores[:-2]) & (scores[1:-1] <= scores[2:]))[0] + 1
    best = int(local[np.argmin(scores[local])]) if len(local) else int(np.argmin(scores))
    lag = float(lags[best])
    if 0 < best < len(scores) - 1:
        a, b, c = scores[best - 1:best + 2]
        denominator = a - 2 * b + c
        if abs(denominator) > 1e-12:
            delta = 0.5 * (a - c) / denominator
            if abs(delta) <= 1:
                lag += float(delta)
    return float(scores[best]), lag


def saved_table(directory, cell, output):
    path = OUTPUT / directory / f"cell_{cell:02d}" / f"output_{output:02d}.html"
    return pd.read_html(StringIO(path.read_text(encoding="utf-8")))[0]


def main():
    frame_rows, summaries = [], []
    for model, algorithm, frame_ms, threshold, directory, cell, f0_output, cls_output in MODELS:
        f0_table = saved_table(directory, cell, f0_output)
        cls_table = saved_table(directory, cell, cls_output)
        if "Algorithm" in f0_table:
            f0_table = f0_table[f0_table.Algorithm == algorithm]
            cls_table = cls_table[cls_table.Algorithm == algorithm]
        for wav_path in sorted(TEST.glob("*.wav")):
            fs, signal = load_wav(wav_path)
            segments, gt_stats = read_lab(wav_path.with_suffix(".lab"))
            frame_length = round(fs * frame_ms / 1000)
            hop_length = round(fs * .01)
            scores, voiced, f0, labels = [], [], [], []
            for start in range(0, len(signal) - frame_length + 1, hop_length):
                frame = signal[start:start + frame_length]
                time = (start + frame_length / 2) / fs
                label = next((lab for a, b, lab in segments if a <= time < b), None)
                score, lag = acf_score(frame, fs) if algorithm == "ACF" else amdf_score(frame, fs)
                predicted = score >= threshold if algorithm == "ACF" else score < threshold
                estimate = fs / lag if predicted and np.isfinite(lag) and lag > 0 else np.nan
                scores.append(score)
                voiced.append(predicted)
                f0.append(estimate)
                labels.append(label)
                frame_rows.append({"model": model, "file": wav_path.name, "time_s": time,
                                   "label": label, "score": score, "lag_samples": lag,
                                   "predicted_voiced": predicted, "f0_hz": estimate})
            labels = np.array(labels)
            voiced = np.array(voiced)
            f0 = np.array(f0)
            mask_vu = np.isin(labels, ["v", "uv"])
            mask_all = np.isin(labels, ["v", "uv", "sil"])
            correct_vu = int(np.sum((labels[mask_vu] == "v") == voiced[mask_vu]))
            correct_all = int(np.sum((labels[mask_all] == "v") == voiced[mask_all]))
            valid_f0 = f0[np.isfinite(f0)]
            saved_f0 = f0_table[f0_table["TEST WAV"] == wav_path.name].iloc[0]
            saved_cls = cls_table[cls_table["TEST WAV"] == wav_path.name].iloc[0]
            summary = {"model": model, "file": wav_path.name, "frame_ms": frame_ms,
                       "threshold_displayed": threshold,
                       "n_frames": len(labels), "n_vu": int(mask_vu.sum()),
                       "correct_vu": correct_vu, "correct_all": correct_all,
                       "num_f0": len(valid_f0), "f0mean_hz": float(valid_f0.mean()),
                       "f0std_hz": float(valid_f0.std()),
                       "false_voiced_sil": int(np.sum((labels == "sil") & voiced)),
                       "gt_f0mean_hz": gt_stats["F0mean"], "gt_f0std_hz": gt_stats["F0std"],
                       "delta_f0mean_vs_saved_hz": float(valid_f0.mean() - saved_f0["Pred F0mean"]),
                       "delta_f0std_vs_saved_hz": float(valid_f0.std() - saved_f0["Pred F0std"]),
                       "delta_correct_vu_vs_saved": correct_vu - int(saved_cls["Correct V/UV"]),
                       "delta_correct_all_vs_saved": correct_all - int(saved_cls["Correct V/UV/SIL"]),
                       "delta_num_f0_vs_saved": len(valid_f0) - int(saved_f0["NumF0"]),
                       "delta_false_voiced_sil_vs_saved": int(np.sum((labels == "sil") & voiced)) - int(saved_cls["False voiced on SIL"])}
            summaries.append(summary)
            print(model, wav_path.name, "V/UV delta", summary["delta_correct_vu_vs_saved"],
                  "F0mean delta Hz", round(summary["delta_f0mean_vs_saved_hz"], 4))
    pd.DataFrame(frame_rows).to_csv(OUTPUT / "recomputed_test_frames.csv", index=False)
    pd.DataFrame(summaries).to_csv(OUTPUT / "validation_summary.csv", index=False)


if __name__ == "__main__":
    main()
