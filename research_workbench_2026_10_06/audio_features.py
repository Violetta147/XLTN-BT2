import math

import numpy as np

import core


def acf_features(audio, fs):
    core.init_functions()
    length, hop = round(fs * .025), round(fs * .010)
    frames = np.lib.stride_tricks.sliding_window_view(audio, length)[::hop]
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    scores, lags, frequencies, strengths = [], [], [], []
    for frame in frames:
        score, lag, curve = core.ACF['detect_pitch_acf'](frame, fs)
        lo, hi = max(1, math.ceil(fs / 400)), min(len(frame) - 2, math.floor(fs / 70))
        indices = np.arange(lo, hi + 1)
        peaks = indices[(curve[indices] >= curve[indices - 1]) & (curve[indices] >= curve[indices + 1])]
        values = curve[peaks]
        refined = np.array([core.refine_lag(curve, idx, float(idx)) for idx in peaks])
        if not len(peaks):
            refined, values = np.array([lag]), np.array([score])
        f0 = fs / refined
        valid = np.isfinite(f0) & (f0 >= 70) & (f0 <= 400)
        f0, values = f0[valid], values[valid]
        order = np.argsort(values)[::-1][:12]
        f, s = np.full(12, np.nan), np.full(12, -np.inf)
        f[:len(order)], s[:len(order)] = f0[order], values[order]
        scores.append(score)
        lags.append(lag)
        frequencies.append(f)
        strengths.append(s)
    return {'times': (np.arange(len(frames)) * hop + length / 2) / fs,
            'rms': rms, 'relative_rms': rms / max(np.quantile(rms, .95), core.EPS),
            'ACF_score': np.array(scores), 'ACF_lag': np.array(lags),
            'ACF_candidate_f0': np.array(frequencies), 'ACF_candidate_strength': np.array(strengths)}
