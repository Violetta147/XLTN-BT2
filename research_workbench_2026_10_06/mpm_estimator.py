import numpy as np
from scipy.signal import correlate

from pitch_estimators import parabolic_lag


def nsdf_curve(frame):
    x = np.asarray(frame, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('Expected finite mono frame')
    x = x - x.mean()
    n = len(x)
    lags = np.arange(n)
    autocorrelation = correlate(x, x, mode='full', method='fft')[n - 1:]
    squares = np.r_[0., np.cumsum(x * x)]
    denominator = squares[n - lags] + squares[n] - squares[lags]
    result = np.zeros(n)
    np.divide(2 * autocorrelation, denominator, out=result, where=denominator > 1e-20)
    return np.clip(result, -1., 1.)


def key_maxima(curve):
    index = 0
    while index < len(curve) and curve[index] > 0:
        index += 1
    peaks = []
    while index < len(curve):
        while index < len(curve) and curve[index] <= 0:
            index += 1
        start = index
        while index < len(curve) and curve[index] > 0:
            index += 1
        if start < index:
            peak = int(start + np.argmax(curve[start:index]))
            if 0 < peak < len(curve) - 1 and curve[peak] >= curve[peak - 1] and curve[peak] >= curve[peak + 1]:
                peaks.append(peak)
    return np.array(peaks, dtype=int)


def estimate(frame, fs, peak_fraction=.93):
    if np.var(frame) <= 1e-20:
        return np.nan, np.nan
    high = min(int(np.ceil(fs / 70)), len(frame) - 2)
    curve = nsdf_curve(frame)[:high + 2]
    peaks = key_maxima(curve)
    peaks = peaks[(peaks >= int(np.floor(fs / 400))) & (peaks <= high)]
    if not len(peaks):
        return np.nan, np.nan
    accepted = peaks[curve[peaks] >= peak_fraction * curve[peaks].max()]
    peak = int(accepted[0])
    lag = np.clip(parabolic_lag(curve, peak), fs / 400, fs / 70)
    return float(fs / lag), float(curve[peak])


if __name__ == '__main__':
    import json
    from pathlib import Path

    rng = np.random.default_rng(20261006)
    errors = []
    for n in (400, 1102):
        x = rng.normal(size=n)
        centered = x - x.mean()
        curve = nsdf_curve(x)
        direct = np.array([2 * np.dot(centered[:n - lag], centered[lag:]) /
                           (np.dot(centered[:n - lag], centered[:n - lag]) + np.dot(centered[lag:], centered[lag:]))
                           for lag in range(n)])
        errors.append(float(abs(curve - direct).max()))
        assert errors[-1] < 1e-10
        assert np.isclose(curve[0], 1.) and np.all(abs(curve) <= 1.)
    assert np.array_equal(key_maxima(np.array([1., .3, -.2, .2, .8, .2, -.3])), [4])
    assert not len(key_maxima(np.array([1., .2, -.1, .2, .4])))
    result = {'fft_direct_nsdf_max_errors': errors, 'nsdf_zero_lag_one': True,
              'bounded': True, 'zero_lobe_ignored': True, 'unfinished_lobe_without_local_peak_ignored': True}
    (Path(__file__).resolve().parent / 'results/mpm_numerical_validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
