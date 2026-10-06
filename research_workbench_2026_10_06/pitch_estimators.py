import numpy as np
from scipy.signal import correlate


def parabolic_lag(curve, index):
    lag = float(index)
    if 0 < index < len(curve) - 1:
        left, middle, right = curve[index - 1:index + 2]
        denominator = left - 2 * middle + right
        if abs(denominator) > 1e-14:
            delta = .5 * (left - right) / denominator
            if abs(delta) <= 1:
                lag += float(delta)
    return lag


def yin_curve(frame, fs):
    x = np.asarray(frame, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('Expected a finite mono frame')
    high = min(int(np.ceil(fs / 70)), len(x) - 2)
    support = len(x) - high - 1
    if support < 2:
        raise ValueError('Insufficient fixed support')
    x = x - x.mean()
    square_sum = np.r_[0., np.cumsum(x * x)]
    shifts = np.arange(high + 2)
    dot = correlate(x, x[:support], mode='valid', method='fft')[:high + 2]
    difference = np.maximum(square_sum[support] + square_sum[shifts + support] - square_sum[shifts] - 2 * dot, 0.)
    difference[0] = 0.
    cumulative_mean = np.cumsum(difference[1:]) / np.arange(1, len(difference))
    cmnd = np.ones_like(difference)
    np.divide(difference[1:], cumulative_mean, out=cmnd[1:], where=cumulative_mean > 1e-20)
    return cmnd, difference, support


def yin(frame, fs, threshold=.1):
    if np.var(frame) <= 1e-20:
        return np.nan, np.nan
    cmnd, _, _ = yin_curve(frame, fs)
    low, high = max(1, int(np.floor(fs / 400))), min(int(np.ceil(fs / 70)), len(cmnd) - 2)
    indices = np.arange(low, high + 1)
    troughs = indices[(cmnd[indices] <= cmnd[indices - 1]) & (cmnd[indices] <= cmnd[indices + 1])]
    accepted = troughs[cmnd[troughs] < threshold]
    index = int(accepted[0]) if len(accepted) else int(indices[np.argmin(cmnd[indices])])
    lag = np.clip(parabolic_lag(cmnd, index), fs / 400, fs / 70)
    return float(fs / lag), float(1 - cmnd[index])
