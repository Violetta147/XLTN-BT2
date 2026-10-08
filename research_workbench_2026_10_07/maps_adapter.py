"""MAPS author code adapter. Derived work distributed under GPL-3.0.

Vendor files remain byte-identical. Explicit source compatibility corrections
and a common complete-support block iterator are documented in H60 registration.
"""
from pathlib import Path
import types
import numpy as np
from math import gcd
from scipy.signal import resample_poly


def author_module():
    path = Path(__file__).parent/'vendor/maps/maps_f0.py'
    source = path.read_text()
    changes = {
        'windowfunc=scipy.signal.hann': 'windowfunc=scipy.signal.windows.hann',
        'step_probs[[max_prob_idx, numpy.arange(len(basefrequencies))]]':
        'step_probs[max_prob_idx, numpy.arange(len(basefrequencies))]',
        '        f_idx = idx_probability[t_idx, f_idx]':
        '        if t_idx > 0: f_idx = idx_probability[t_idx, f_idx]',
    }
    for before, after in changes.items():
        assert source.count(before) == 1, before
        source = source.replace(before, after)
    module = types.ModuleType('maps_author_adapted')
    exec(compile(source, str(path), 'exec'), module.__dict__)
    return module


def native(audio, fs):
    module = author_module()
    if fs != 48000:
        divisor=gcd(fs,48000)
        audio=resample_poly(audio,48000//divisor,fs//divisor)
    fs=48000
    length, hop = 2048, 480
    frequencies = module._basefrequencies
    extra = int(fs//frequencies[-1])
    count = max(0, (len(audio)-length-extra)//hop+1)
    assert count > 0

    class CompleteBlocks:
        def __init__(self, data, samplerate, blocksize=2048, hopsize=1024):
            self.data, self.samplerate = data, int(samplerate)
            self.blocksize, self.hopsize = int(blocksize), int(hopsize)
        def __len__(self):
            return count
        def __iter__(self):
            for i in range(count):
                start = i*self.hopsize
                yield self.data[start:start+self.blocksize]

    module.SignalBlocks = CompleteBlocks
    blocks = CompleteBlocks(np.asarray(audio), fs, length, hop)
    magnitude = module.magnitude_correlation(blocks, frequencies)
    phase = module.ifd_difference(blocks, frequencies)
    raw = module.value2posterior(magnitude, phase)
    assert np.isfinite(raw).all()
    # The cubic spline can overshoot its probability domain. Apply the declared
    # fixed numerical bound before multiplicative path decoding.
    probability = np.clip(raw, 1e-12, 1.)
    _, f0, confidence = module.max_track_viterbi(probability, hop/fs, frequencies)
    return dict(times=(np.arange(count)*hop+length/2)/fs, f0=f0,
                confidence=confidence, probability=probability,
                raw_probability=raw, magnitude=magnitude, phase=phase,
                frequencies=frequencies, frame_samples=length,
                hop_samples=hop, extra_samples=extra, native_fs=fs)


def project(proof, times, baseline, mode, threshold=.5):
    index = np.argmin(abs(proof['times'][:, None]-times[None, :]), axis=0)
    covered = abs(proof['times'][index]-times) <= .005+1/int(proof['native_fs'])
    values = proof['f0'][index]
    covered &= (values >= 70) & (values <= 400)
    if mode == 'pitch':
        pred = baseline['pred'].copy()
        f0 = np.where(pred & covered, values, baseline['f0'])
    else:
        pred = covered & (proof['confidence'][index] >= threshold)
        f0 = np.where(pred, values, np.nan)
    return pred, f0, covered
