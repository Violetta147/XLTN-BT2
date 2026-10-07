import argparse
import itertools
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.fft import dct
from scipy.special import expit, logsumexp
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / 'research_workbench_2026_10_06'))
import audit
import core

OUT = HERE / 'results'
BASE_FEATURES = ['max_normalized_acf', 'log_relative_rms', 'zcr_crossings_per_second', 'high_frequency_ratio']
OPTIONS = [dict(id='hard170', method='control', mfcc=False)] + [
    dict(id=f'{method}_{tag}', method=method, mfcc=use)
    for method in ('logistic', 'gmm') for tag, use in [('base4', False), ('mfcc17', True)]]


def mel_bank(fs, nfft):
    frequencies = np.fft.rfftfreq(nfft, 1 / fs)
    upper = min(8000., fs / 2)
    points = 700 * (10 ** (np.linspace(2595 * np.log10(1 + 70 / 700), 2595 * np.log10(1 + upper / 700), 28) / 2595) - 1)
    bank = np.maximum(0., np.minimum((frequencies[None, :] - points[:-2, None]) / (points[1:-1] - points[:-2])[:, None],
                                    (points[2:, None] - frequencies[None, :]) / (points[2:] - points[1:-1])[:, None]))
    return bank


def design(audio, fs):
    length, hop = round(fs * .025), round(fs * .01)
    frames = np.lib.stride_tricks.sliding_window_view(audio, length)[::hop]
    centered = frames - frames.mean(axis=1, keepdims=True)
    nfft = 1 << (length - 1).bit_length()
    spectrum = abs(np.fft.rfft(centered * np.hanning(length), n=nfft)) ** 2
    weights = np.full(spectrum.shape[1], 2.)
    weights[0], weights[-1] = 0., 1.
    power = spectrum * weights
    total = np.maximum(power.sum(axis=1), 1e-20)
    high = power[:, np.fft.rfftfreq(nfft, 1/fs) >= 1000].sum(axis=1) / total
    mel = (power / total[:, None]) @ mel_bank(fs, nfft).T
    mfcc = dct(np.log(np.maximum(mel, 1e-12)), type=2, norm='ortho', axis=1)[:, 1:14]
    rms = np.sqrt(np.mean(centered ** 2, axis=1))
    energy = np.log(np.maximum(rms / max(np.quantile(rms, .95), 1e-12), 1e-6))
    zcr = np.mean(np.signbit(centered[:, 1:]) != np.signbit(centered[:, :-1]), axis=1) * fs
    lo, hi = int(np.ceil(fs / 400)), min(length - 2, int(np.floor(fs / 70)))
    lags = np.arange(lo - 1, hi + 2)
    curves = np.zeros((len(frames), len(lags)))
    for j, lag in enumerate(lags):
        left, right = centered[:, :-lag], centered[:, lag:]
        curves[:, j] = np.sum(left * right, axis=1) / np.maximum(np.sqrt(np.sum(left**2, axis=1) * np.sum(right**2, axis=1)), 1e-20)
    peaks = (curves[:, 1:-1] >= curves[:, :-2]) & (curves[:, 1:-1] >= curves[:, 2:])
    scores = np.where(peaks, curves[:, 1:-1], -np.inf)
    maximum = np.max(scores, axis=1)
    qualifying = peaks & (curves[:, 1:-1] >= .93 * maximum[:, None])
    index = np.argmax(qualifying, axis=1) + 1
    rows = np.arange(len(frames))
    strength = maximum
    valid = peaks.any(axis=1) & (strength > 0)
    a, b, c = curves[rows, index-1], curves[rows, index], curves[rows, index+1]
    denominator = a - 2*b + c
    delta = np.divide(.5*(a-c), denominator, out=np.zeros(len(frames)), where=abs(denominator) > 1e-12)
    lag = lags[index] + np.clip(delta, -.5, .5)
    f0 = np.where(valid, np.clip(fs/lag, 70, 400), np.nan)
    strength = np.where(valid, strength, 0.)
    x = np.column_stack((strength, energy, zcr, high, mfcc))
    assert np.isfinite(x).all()
    times = (np.arange(len(frames)) * hop + length/2) / fs
    return dict(x=x, pitch=f0, times=times, curves=curves, lags=lags)


def fit_model(bank, names, option):
    if option['method'] == 'control':
        return None
    n = min(len(bank[name]['x']) for name in names)
    indices = {name: np.round(np.linspace(0, len(bank[name]['x'])-1, n)).astype(int) for name in names}
    dimensions = 17 if option['mfcc'] else 4
    x = np.vstack([bank[name]['x'][indices[name], :dimensions] for name in names])
    scaler = StandardScaler().fit(x)
    z = scaler.transform(x)
    result = dict(fit_files=names, indices={name: value.tolist() for name, value in indices.items()},
                  mean=scaler.mean_.tolist(), scale=scaler.scale_.tolist(), method=option['method'], dimensions=dimensions)
    if option['method'] == 'logistic':
        y = np.concatenate([(bank[name]['labels'][indices[name]] == 'v').astype(int) for name in names])
        assert all(np.isin(bank[name]['labels'][indices[name]], ['v', 'uv', 'sil']).all() for name in names)
        model = LogisticRegression(C=1., max_iter=1000).fit(z, y)
        assert model.n_iter_[0] < 1000
        result.update(coefficient=model.coef_[0].tolist(), intercept=float(model.intercept_[0]), positive_frames=int(y.sum()))
        assert np.allclose(probability(x, result), model.predict_proba(z)[:, 1], atol=1e-12)
    else:
        model = GaussianMixture(n_components=3, covariance_type='diag', reg_covar=1e-3, n_init=5,
                                random_state=50, max_iter=500, tol=1e-4).fit(z)
        assert model.converged_
        means_raw = model.means_ * scaler.scale_ + scaler.mean_
        voiced = int(np.argmax(means_raw[:, 0]))
        result.update(weights=model.weights_.tolist(), centers=model.means_.tolist(), covariance=model.covariances_.tolist(),
                      voiced_component=voiced, component_raw_periodicity=means_raw[:, 0].tolist(), iterations=int(model.n_iter_))
        assert np.allclose(probability(x, result), model.predict_proba(z)[:, voiced], atol=1e-12)
    return result


def probability(x, model):
    z = (x[:, :model['dimensions']] - model['mean']) / model['scale']
    if model['method'] == 'logistic':
        return expit(z @ np.array(model['coefficient']) + model['intercept'])
    centers, covariance = np.array(model['centers']), np.array(model['covariance'])
    logp = np.log(model['weights']) - .5 * (np.sum(np.log(2*np.pi*covariance), axis=1)[None, :] +
                                           np.sum((z[:, None, :] - centers[None, :, :])**2 / covariance[None, :, :], axis=2))
    return np.exp(logp - logsumexp(logp, axis=1, keepdims=True))[:, model['voiced_component']]


def infer(features, option, model):
    pred, f0 = features['base_pred'].copy(), features['base_f0'].copy()
    probability_v = np.full(len(pred), np.nan)
    recover = np.zeros(len(pred), dtype=bool)
    if model is not None:
        probability_v = probability(features['x'], model)
        recover = (~pred) & (probability_v >= .5) & (features['x'][:, 0] >= .6) & (features['x'][:, 1] >= np.log(.01)) & np.isfinite(features['pitch'])
        pred[recover] = True
        f0[recover] = features['pitch'][recover]
    assert np.all(pred[features['base_pred']])
    assert np.array_equal(f0[features['base_pred']], features['base_f0'][features['base_pred']])
    return pred, f0, probability_v, recover


def choose(records):
    ranked = []
    control = pd.DataFrame([r for r in records if r['option_id'] == 'hard170'])
    for option in OPTIONS:
        table = pd.DataFrame([r for r in records if r['option_id'] == option['id']])
        valid = bool(np.isfinite(table.average_mape).all() and table.macro_f1.mean() >= control.macro_f1.mean() - .01
                     and table.recall_v.mean() >= control.recall_v.mean() - .01 and table.false_voiced_sil.sum() <= control.false_voiced_sil.sum() + 1)
        ranked.append((not valid, float(table.average_mape.max()) if valid else np.inf,
                       float(table.average_mape.mean()) if valid else np.inf, option['id']))
    return min(ranked)[3]


def gates(table):
    base = table[(table.split == 'nested') & (table.model == 'accepted')].set_index('file')
    candidate = table[(table.split == 'nested') & (table.model == 'candidate')].set_index('file')
    summaries = {model: {split: core.summarize(table[(table.model == model) & (table.split == split)]) for split in ('train', 'lofo', 'nested')}
                 for model in ('accepted', 'candidate')}
    a, b = summaries['accepted'], summaries['candidate']
    checks = dict(train_mape_relative_10_percent=b['train']['average_mape'] <= .9*a['train']['average_mape'],
                  nested_mape_relative_5_percent=b['nested']['average_mape'] <= .95*a['nested']['average_mape'],
                  nested_f1_drop_at_most_01=b['nested']['macro_f1'] >= a['nested']['macro_f1'] - .01,
                  nested_recall_v_drop_at_most_01=b['nested']['recall_v'] >= a['nested']['recall_v'] - .01,
                  nested_sil_increase_at_most_1=b['nested']['false_voiced_sil'] <= a['nested']['false_voiced_sil'] + 1,
                  nested_no_file_mape_worse_by_over_2pp=bool(((candidate.average_mape-base.average_mape) <= 2).all()),
                  nested_phone_f1_std_not_worse=bool(candidate.loc['phone_F1.wav', 'F0std_mape'] <= base.loc['phone_F1.wav', 'F0std_mape']),
                  selected_lofo_mape_relative_5_percent=b['lofo']['average_mape'] <= .95*a['lofo']['average_mape'])
    return summaries, dict(checks={k: bool(v) for k, v in checks.items()}, eligible=bool(all(checks.values())),
                            each_nested_file_below_2=bool((candidate.average_mape < 2).all()), champion_promoted=False)


def protected_paths():
    paths = [Path(__file__), HERE/'verify_voicing_recovery.py', HERE/'H50_REGISTRATION.md',
             OUT/'H47_nested_contours.csv', OUT/'H47_metrics.csv', OUT/'H47_verification.json', core.RESULTS/'frozen_config.json', Path(core.__file__)]
    paths += list(core.TRAIN.glob('*.wav')) + list(core.TRAIN.glob('*.lab')) + list(core.TRAIN_GT.glob('*.lab'))
    return paths


def check():
    assert not (HERE/'H50_REGISTRY.json').exists()
    tests = []
    for fs in (16000, 44100):
        t = np.arange(round(fs*.2))/fs
        tone = np.sin(2*np.pi*200*t)
        original, scaled = design(tone, fs), design(tone*3+1, fs)
        assert np.allclose(original['x'], scaled['x'], atol=1e-8)
        assert np.nanmax(abs(original['pitch']-200)) < 1
        silence = design(np.zeros(len(t)), fs)
        assert np.isfinite(silence['x']).all() and np.isnan(silence['pitch']).all()
        tests.append(dict(fs=fs, gain_dc_invariance=True, tone_200hz_within_1hz=True, silence_finite=True))
    audit.json_write(OUT/'H50_precheck.json', dict(synthetic_only=True, uses_BT2_WAV=False, tests=tests))
    audit.json_write(HERE/'H50_REGISTRY.json', dict(family='H50', options=OPTIONS, rollback='d148a2e0deb60442218002431f6494a16fad7e30',
                       source_hashes={str(p.relative_to(REPO)): audit.digest(p) for p in protected_paths()},
                       precheck_sha256=audit.digest(OUT/'H50_precheck.json')))
    print('PASS synthetic features/pitch/DC/gain/silence; registry written, no BT2 measurement')


def run():
    assert not (OUT/'H50_experiment.json').exists(), 'Preserve completed experiment'
    registry = json.loads((HERE/'H50_REGISTRY.json').read_text())
    assert registry['options'] == OPTIONS
    for relative, digest in registry['source_hashes'].items():
        assert audit.digest(REPO/relative) == digest, relative
    head = subprocess.check_output(['git', '-c', 'safe.directory='+str(REPO).replace('\\', '/'), '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
    started = time.perf_counter()
    items = core.load_training()
    by_name = {item['file']: item for item in items}
    names = sorted(by_name)
    contours = pd.read_csv(OUT/'H47_nested_contours.csv', float_precision='round_trip')
    bank, label_rows = {}, []
    for name in names:
        item = by_name[name]
        fs, audio = core.load_audio(core.TRAIN/name)
        features = design(audio, fs)
        old = contours[(contours.model == 'candidate') & (contours.file == name)]
        assert np.allclose(old.time_s, features['times'], atol=1e-12) and np.array_equal(old.label, item['labels'])
        features.update(labels=item['labels'], base_pred=old.pred_voiced.to_numpy(bool), base_f0=old.f0_hz.to_numpy())
        bank[name] = features
        path = OUT/f'H50_design_{Path(name).stem}.npz'
        assert not path.exists()
        np.savez_compressed(path, **features)
        for i, t in enumerate(features['times']):
            length = round(fs*.025)/fs
            overlap = {lab: sum(max(0., min(t+length/2,b)-max(t-length/2,a)) for a,b,label in item['segments'] if label == lab)/length
                       for lab in ('v','uv','sil')}
            majority = next((lab for lab in ('v','uv','sil') if overlap[lab] > .5), 'mixed')
            label_rows.append(dict(file=name, time_s=t, center_label=item['labels'][i], majority_label=majority, **overlap))
        print('H50 features:', name, len(features['times']), flush=True)
    models, predictions = {}, {}
    def score(option, fit_names, held):
        key = (option['id'], tuple(sorted(fit_names)), held)
        if key not in predictions:
            model_key = (option['id'], tuple(sorted(fit_names)))
            if model_key not in models:
                models[model_key] = fit_model(bank, sorted(fit_names), option)
            model = models[model_key]
            pred, f0, prob, recover = infer(bank[held], option, model)
            metrics = core.score_file(by_name[held], pred, f0)
            labels = by_name[held]['labels']
            metrics.update(recovered=int(recover.sum()), recovered_v=int((recover & (labels == 'v')).sum()),
                           recovered_uv=int((recover & (labels == 'uv')).sum()), recovered_sil=int((recover & (labels == 'sil')).sum()))
            predictions[key] = (metrics, pred, f0, prob, recover)
        return predictions[key]
    traces, selections = [], []
    for outer in ['final'] + names:
        pool = [name for name in names if name != outer]
        records = []
        for option in OPTIONS:
            for held in pool:
                fits = [name for name in pool if name != held]
                measured = score(option, fits, held)[0]
                row = dict(outer_held=outer, option_id=option['id'], inner_held=held, fit_files='|'.join(fits), **measured)
                traces.append(row)
                records.append(row)
        selected = choose(records)
        selections.append(dict(outer_held=outer, selection_files=pool, option_id=selected))
        print('H50 selected:', outer, selected, flush=True)
    selected = {entry['outer_held']: entry['option_id'] for entry in selections}
    options = {entry['id']: entry for entry in OPTIONS}
    rows, output = [], []
    for split in ('train', 'lofo', 'nested'):
        for held in names:
            fits = names if split == 'train' else [name for name in names if name != held]
            for model, identity in [('accepted', 'hard170'), ('candidate', selected[held] if split == 'nested' else selected['final'])]:
                measured, pred, f0, prob, recover = score(options[identity], fits, held)
                rows.append(dict(split=split, model=model, option_id=identity, **measured))
    fixed = []
    for option in OPTIONS:
        for held in names:
            fits = [name for name in names if name != held]
            measured, pred, f0, prob, recover = score(option, fits, held)
            fixed.append(dict(option_id=option['id'], **measured))
            for i,t in enumerate(bank[held]['times']):
                output.append(dict(option_id=option['id'], file=held, time_s=t, label=by_name[held]['labels'][i], pred_voiced=bool(pred[i]),
                                   f0_hz=f0[i], probability_v=prob[i], recovered=bool(recover[i])))
    for held in names:
        saved = pd.read_csv(OUT/'H47_metrics.csv').query('split == "nested" and model == "candidate" and file == @held').iloc[0]
        actual = score(OPTIONS[0], [name for name in names if name != held], held)[0]
        assert all(np.isclose(saved[key], actual[key], atol=1e-8) for key in ('average_mape','F0std','F0num','macro_f1'))
    table = pd.DataFrame(rows)
    summaries, decision = gates(table)
    artifacts = []
    for filename, value in [('H50_metrics.csv', rows), ('H50_fixed_lofo.csv', fixed), ('H50_contours.csv', output),
                            ('H50_inner_traces.csv', traces), ('H50_label_overlap.csv', label_rows)]:
        path = OUT/filename
        pd.DataFrame(value).to_csv(path, index=False)
        artifacts.append(path)
    fits = [dict(option_id=key[0], nominal_fit_files=list(key[1]), model=model) for key,model in models.items()]
    audit.json_write(OUT/'H50_fits.json', dict(fits=fits))
    artifacts += [OUT/'H50_fits.json'] + list(OUT.glob('H50_design_*.npz'))
    audit.json_write(OUT/'H50_experiment.json', dict(family='H50', prereg_commit=head, registry_sha256=audit.digest(HERE/'H50_REGISTRY.json'),
        decision=decision, summaries=summaries, selections=selections, new_native_calls=0, test_or_KEELE_used=False,
        artifacts={str(p.relative_to(REPO)): audit.digest(p) for p in artifacts},
        runtime=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, sklearn=sklearn.__version__, pandas=pd.__version__),
        wall_time_s=time.perf_counter()-started, actual_model_fits=sum(model is not None for model in models.values())))
    print(json.dumps(decision, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['check', 'run'])
    args = parser.parse_args()
    check() if args.action == 'check' else run()
