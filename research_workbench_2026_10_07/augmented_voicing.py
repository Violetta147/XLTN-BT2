import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import amdf_selection_ensemble as evidence

HERE = Path(__file__).resolve().parent
core, audit = evidence.core, evidence.audit
SOURCE_CACHE = evidence.SOURCE_CACHE
BANK = {}
MODELS = {}
FEATURE_NAMES = ['periodicity_at_praat_lag', 'log_relative_rms', 'zcr_per_sample', 'high_frequency_ratio']


def design(audio, fs, times, gate):
    length = round(fs * .025)
    rows = []
    rms = []
    for t, f in zip(times, gate):
        start = round(t * fs - length / 2)
        frame = np.zeros(length)
        a, b = max(0, start), min(len(audio), start + length)
        if b > a:
            frame[a-start:b-start] = audio[a:b]
        centered = frame - frame.mean()
        energy = np.mean(centered ** 2)
        rms.append(np.sqrt(energy))
        lag = round(fs / f) if 70 <= f <= 400 else 0
        if 0 < lag < length:
            x, y = centered[:-lag], centered[lag:]
            periodicity = np.dot(x, y) / max(np.sqrt(np.dot(x, x) * np.dot(y, y)), 1e-20)
        else:
            periodicity = 0.
        spectrum = abs(np.fft.rfft(centered * np.hanning(length))) ** 2
        weights = np.full(len(spectrum), 2.)
        weights[0] = 0
        if length % 2 == 0:
            weights[-1] = 1
        power = spectrum * weights
        ratio = power[np.fft.rfftfreq(length, 1/fs) >= 1000].sum() / max(power.sum(), 1e-20)
        zcr = np.mean(np.signbit(centered[1:]) != np.signbit(centered[:-1]))
        rows.append([periodicity, 0., zcr, ratio])
    result = np.array(rows)
    result[:, 1] = np.log(np.maximum(np.array(rms) / max(np.quantile(rms, .95), 1e-12), 1e-6))
    assert np.isfinite(result).all()
    return result


def labels_at(item, times):
    return np.array([next((lab for a, b, lab in item['segments'] if a <= t < b), 'unknown') for t in times])


def build_bank():
    assert not BANK
    manifest = json.loads((HERE / 'results/H46_augmentation_manifest.json').read_text())
    for item in core.load_training():
        _, audio = core.load_audio(core.TRAIN / item['file'])
        native = evidence.extract(item, audio, {})
        cases = [(Path(item['file']).stem + '__clean', audio, native['times'], native['member_frequencies'][0])]
        for case in manifest['cases']:
            if case['origin_file'] != item['file']:
                continue
            path = HERE / case['path']
            assert audit.digest(path) == case['wav_sha256']
            fs, augmented = core.load_audio(path)
            assert fs == item['fs'] and len(augmented) == len(audio)
            feature_path = HERE / case['features']['path']
            assert audit.digest(feature_path) == case['features']['sha256']
            with np.load(feature_path) as data:
                cases.append((case['case_id'], augmented, data['times'].copy(), data['gate'].copy()))
        BANK[item['file']] = []
        for identity, waveform, times, gate in cases:
            x = design(waveform, item['fs'], times, gate)
            labels = labels_at(item, times)
            valid = (gate >= 70) & (gate <= 400) & np.isin(labels, ['v', 'uv', 'sil'])
            BANK[item['file']].append(dict(case_id=identity, x=x, labels=labels, valid=valid))
            path = HERE / f'results/H47_design_{identity}.npz'
            assert not path.exists()
            np.savez_compressed(path, x=x, labels=labels, valid=valid, times=times, gate=gate)


def extract(item, audio, option):
    native = evidence.extract(item, audio, option)
    clean = BANK[item['file']][0]
    return dict(native, voicing_features=clean['x'])


def fit(names, augmented):
    key = (tuple(names), augmented)
    if key in MODELS:
        return MODELS[key]
    selected = [(name, case) for name in names for case in (BANK[name] if augmented else BANK[name][:1])]
    count = sum(int(case['valid'].sum()) for _, case in selected)
    xx, yy, ww, ids = [], [], [], []
    for name, case in selected:
        valid = case['valid']
        n_cases = 4 if augmented else 1
        xx.append(case['x'][valid])
        yy.append((case['labels'][valid] == 'v').astype(int))
        ww.append(np.full(valid.sum(), count / (len(names) * n_cases * valid.sum())))
        ids.append(dict(origin_file=name, case_id=case['case_id'], frames=int(valid.sum())))
    x, y, w = np.vstack(xx), np.concatenate(yy), np.concatenate(ww)
    scaler = StandardScaler().fit(x, sample_weight=w)
    model = LogisticRegression(C=1., max_iter=1000).fit(scaler.transform(x), y, sample_weight=w)
    assert model.n_iter_[0] < 1000
    result = dict(fit_files=names, augmented=augmented, fit_cases=ids, feature_names=FEATURE_NAMES,
                  mean=scaler.mean_.tolist(), scale=scaler.scale_.tolist(), coefficient=model.coef_[0].tolist(),
                  intercept=float(model.intercept_[0]), C=1., class_weight='natural prior, equal origin and variant weights',
                  positive_frames=int(y.sum()), negative_frames=int((1-y).sum()))
    assert np.allclose(probability(x, result), model.predict_proba(scaler.transform(x))[:, 1], atol=1e-12)
    MODELS[key] = result
    return result


def probability(x, classifier):
    return expit(((x - classifier['mean']) / classifier['scale']) @ np.array(classifier['coefficient']) + classifier['intercept'])


def infer(native, training, option, config):
    pred = native['native_pred'].copy()
    member = 'praat7_filtered_v0.3' if option['method'] == 'control' else 'amdf_pitch_spectral_p170'
    f0 = native['member_frequencies'][evidence.MEMBERS.index(member)].copy()
    classifier = None
    names = []
    if option['method'] == 'logistic':
        names = sorted(item['file'] for item in training)
        classifier = fit(names, option['augmented'])
        pred &= probability(native['voicing_features'], classifier) >= option['threshold']
    fitted = dict(requires_fit=bool(names), actual_fit_files=names, method=option['method'], selected_members=[member],
                  output_f0_sha256=hashlib.sha256(np.where(pred, f0, np.nan).tobytes()).hexdigest())
    return pred, np.where(pred, f0, np.nan), fitted, classifier


def check():
    fs = 16000
    times = np.array([.05, .08])
    sine = np.sin(2*np.pi*200*np.arange(3200)/fs)
    x = design(sine, fs, times, np.full(2, 200.))
    assert np.allclose(x[:, 0], 1.) and np.max(x[:, 3]) < 1e-5
    assert np.allclose(x, design(sine * 3, fs, times, np.full(2, 200.)), atol=1e-12)
    silent = design(np.zeros(3200), fs, times, np.zeros(2))
    assert np.isfinite(silent).all()
    dummy = dict(mean=[0]*4, scale=[1]*4, coefficient=[1,0,0,0], intercept=0.)
    assert np.allclose(probability(np.zeros((2,4)), dummy), .5)
    audit.json_write(HERE / 'results/H47_precheck.json', dict(synthetic_only=True, uses_BT2_WAV=False,
                      rule_sha256=audit.digest(__file__), scale_invariance=True, silent_finite=True))
    print('PASS synthetic periodicity/features/scaling/silence/logistic check')
