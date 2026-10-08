"""Custom bounded log-HPS on unchanged 25 ms PCM frames; not an upstream port."""
import numpy as np


def refine(segment, fs, anchor, order):
    assert order in (3, 5) and 70 <= anchor <= 400
    lower, upper = max(70., anchor*2**(-100/1200)), min(400., anchor*2**(100/1200))
    grid = np.unique(np.r_[lower, np.arange(np.ceil(lower*10), np.floor(upper*10)+1)/10, anchor, upper])
    nfft = 1 << (16*len(segment)-1).bit_length()
    windowed = (segment-np.mean(segment))*np.hanning(len(segment))
    spectrum = np.abs(np.fft.rfft(windowed, n=nfft))
    scale = float(spectrum.max())
    if scale == 0:
        return dict(f0=float(anchor), score=0., grid=grid, scores=np.zeros(len(grid)),
                    nfft=nfft, at_boundary=False, silent_fallback=True)
    spectrum /= scale
    frequencies = np.fft.rfftfreq(nfft, 1/fs)
    scores = np.zeros(len(grid))
    for harmonic in range(1, order+1):
        scores += np.log(np.maximum(np.interp(harmonic*grid, frequencies, spectrum), 1e-12))
    best = int(np.argmax(scores))  # sorted grid: ties choose lowest frequency
    return dict(f0=float(grid[best]), score=float(scores[best]), grid=grid, scores=scores,
                nfft=nfft, at_boundary=bool(best in (0, len(grid)-1)), silent_fallback=False)
