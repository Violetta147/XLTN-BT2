"""V_FXPEFAC - PEFAC pitch extraction algorithm."""

from __future__ import annotations
import numpy as np
from .v_enframe import v_enframe
from .v_rfft import v_rfft


def v_fxpefac(s, fs, tinc=0.01) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """PEFAC pitch extraction algorithm.

    Parameters
    ----------
    s : array_like
        Speech signal.
    fs : float
        Sample frequency in Hz.
    tinc : float
        Frame increment in seconds.

    Returns
    -------
    fx : ndarray
        Estimated pitch frequency per frame (0 = unvoiced).
    tt : ndarray
        Time of each frame centre (seconds).
    pv : ndarray
        Probability of voicing per frame.

    References
    ----------
    [1] Gonzalez & Brookes, PEFAC - A Pitch Estimation Algorithm
        Robust to High Levels of Noise, IEEE/ACM TASLP, 2014.
    """
    s = np.asarray(s, dtype=float).ravel()

    # Parameters
    fxmin = 60.0
    fxmax = 500.0
    n_fft = int(2 ** np.ceil(np.log2(2 * fs / fxmin)))
    ni = max(1, round(tinc * fs))

    # Window
    win_len = int(round(2 * fs / fxmin))
    if win_len > n_fft:
        win_len = n_fft
    win = np.hamming(win_len)

    # Enframe
    frames, tt, *_ = v_enframe(s, win, ni)
    tt = tt / fs
    nr = frames.shape[0]

    # Compute log power spectrum
    spec = v_rfft(frames, n_fft, 1)
    pw = np.real(spec * np.conj(spec))
    pw = np.maximum(pw, 1e-20)
    log_pw = np.log(pw)

    # Frequency bins
    freq_bins = np.arange(pw.shape[1]) * fs / n_fft
    min_bin = max(1, int(np.ceil(fxmin * n_fft / fs)))
    max_bin = min(pw.shape[1] - 1, int(np.floor(fxmax * n_fft / fs)))

    fx = np.zeros(nr)
    pv = np.zeros(nr)

    for i in range(nr):
        # Compute autocorrelation via IFFT of power spectrum
        # irfft reconstructs the negative-frequency half itself. Mirroring
        # here would nearly double the transform length and the pitch lag.
        acf = np.fft.irfft(pw[i, :], n=n_fft)[:n_fft // 2 + 1]
        acf = acf / (acf[0] + 1e-20)

        # Search for pitch in valid range
        min_lag = max(1, int(np.floor(fs / fxmax)))
        max_lag = min(len(acf) - 1, int(np.ceil(fs / fxmin)))

        if max_lag <= min_lag:
            continue

        acf_search = acf[min_lag:max_lag + 1]
        if len(acf_search) == 0:
            continue

        peak_idx = np.argmax(acf_search)
        peak_val = acf_search[peak_idx]

        if peak_val > 0.3:  # voicing threshold
            lag = peak_idx + min_lag
            # Parabolic interpolation
            if 0 < peak_idx < len(acf_search) - 1:
                a = acf_search[peak_idx - 1]
                b = acf_search[peak_idx]
                c = acf_search[peak_idx + 1]
                delta = 0.5 * (a - c) / (a - 2 * b + c + 1e-20)
                lag = peak_idx + min_lag + delta
            fx[i] = fs / lag
            pv[i] = peak_val

    return fx, tt, pv
