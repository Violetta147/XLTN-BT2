import ast
import hashlib
import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal import correlate
from sklearn.mixture import GaussianMixture

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ROOT = REPO.parent
TRAIN = REPO / 'TinHieuHuanLuyen'
RESULTS = HERE / 'results'
BASELINES = HERE / 'baselines'
TRAIN_GT = HERE / 'train_3gt'
EPS = 1e-12


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_stats(path):
    stats = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        words = line.split()
        if words and words[0] in {'F0mean', 'F0std', 'F0num'}:
            stats[words[0]] = float(words[1])
    assert set(stats) == {'F0mean', 'F0std', 'F0num'}
    assert all(value > 0 for value in stats.values())
    return stats


def read_segments(path):
    segments = []
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        words = line.split()
        if words and words[0] not in {'F0mean', 'F0std', 'F0num'}:
            segments.append((float(words[0]), float(words[1]), words[2].lower()))
    assert segments and all(a < b and label in ('v', 'uv', 'sil') for a, b, label in segments)
    return segments


def load_audio(path):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        fs, values = wavfile.read(path)
    if values.ndim > 1:
        values = values.mean(axis=1)
    if np.issubdtype(values.dtype, np.integer):
        info = np.iinfo(values.dtype)
        values = values.astype(float) / max(abs(info.min), info.max)
    else:
        values = values.astype(float)
    return int(fs), values


def extract_functions(filename, names):
    book = json.loads((BASELINES / filename).read_text(encoding='utf-8'))
    scope = {'np': np, 'pd': pd, 'math': math, 'correlate': correlate,
             'GaussianMixture': GaussianMixture, 'EPS': EPS, 'F0_MIN': 70., 'F0_MAX': 400.,
             'HOP_MS': 10, 'HIST_BINS': 20, 'HIST_SMOOTH_WINDOW': 5, 'HIST_W': 1.,
             'NEAR_ZERO_MEAN_ABS': 1e-8}
    found = []
    for cell in book['cells']:
        if cell['cell_type'] != 'code':
            continue
        tree = ast.parse(''.join(cell['source']))
        selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        if selected:
            exec(compile(ast.Module(body=selected, type_ignores=[]), filename, 'exec'), scope)
            found.extend(node.name for node in selected)
    assert set(found) == set(names), (filename, set(names) - set(found))
    return scope


ACF = None
AMDF = None
GMM = None
FIT_CACHE = {}


def init_functions():
    global ACF, AMDF, GMM
    if ACF is not None:
        return
    ACF = extract_functions('ACF.ipynb', ['normalized_acf', 'detect_pitch_acf', 'lag_to_f0',
                            'gaussian_intersection', 'histogram_threshold', 'class_histogram_threshold'])
    AMDF = extract_functions('AMDF.ipynb', ['lag_search_range', 'normalized_amdf', 'deepest_local_dip',
                              'f0_from_lag', 'gaussian_threshold', 'histogram_threshold',
                              'two_mode_histogram_threshold'])
    GMM = extract_functions('GMM.ipynb', ['normal_pdf', 'fit_gmm_threshold'])


def refine_lag(curve, index, lag):
    if 0 < index < len(curve) - 1:
        a, b, c = curve[index - 1:index + 2]
        denom = a - 2 * b + c
        if abs(denom) > EPS:
            delta = 0.5 * (a - c) / denom
            if abs(delta) <= 1:
                lag += float(delta)
    return lag


def gaussian_lowpass(signal, fs, top=800., attenuation=.03):
    frequency = np.fft.rfftfreq(len(signal), 1 / fs)
    response = attenuation ** ((frequency / top) ** 2)
    return np.fft.irfft(np.fft.rfft(signal) * response, n=len(signal))


def frame_features(path, frame_ms=25, preprocess='raw', split='train'):
    path = Path(path)
    if split == 'train':
        assert path.resolve().parent == TRAIN.resolve(), 'Training loader rejects another split'
        stats_path = TRAIN_GT / path.with_suffix('.lab').name
    else:
        assert split == 'test' and (RESULTS / 'frozen_config.json').exists(), 'Test is locked'
        assert path.resolve().parent == (REPO / 'TinHieuKiemThu').resolve()
        stats_path = HERE / 'test_3gt' / path.with_suffix('.lab').name
    cache = HERE / 'cache' / f'{split}_{path.stem}_{frame_ms}_{preprocess}.npz'
    cache.parent.mkdir(exist_ok=True)
    init_functions()
    fs, original = load_audio(path)
    signal = original if preprocess == 'raw' else gaussian_lowpass(original, fs)
    segments = read_segments(path.with_suffix('.lab'))
    stats = read_stats(stats_path)
    frame_len, hop_len = round(fs * frame_ms / 1000), round(fs * .010)
    frames = np.lib.stride_tricks.sliding_window_view(signal, frame_len)[::hop_len]
    raw_frames = np.lib.stride_tricks.sliding_window_view(original, frame_len)[::hop_len]
    times = (np.arange(len(frames)) * hop_len + frame_len / 2) / fs
    labels = np.array([next((lab for a, b, lab in segments if a <= t < b), 'unknown') for t in times])
    rms = np.sqrt(np.mean(raw_frames ** 2, axis=1))
    relative_rms = rms / max(np.quantile(rms, .95), EPS)
    boundary = np.zeros(len(times), dtype=bool)
    for a, b, _ in segments:
        boundary |= (np.abs(times - a) < frame_ms / 2000) | (np.abs(times - b) < frame_ms / 2000)
    arrays = {'times': times, 'labels': labels, 'rms': rms, 'relative_rms': relative_rms, 'boundary': boundary}
    if cache.exists():
        with np.load(cache, allow_pickle=False) as handle:
            arrays.update({key: handle[key] for key in handle.files})
    else:
        for algorithm, scope in [('ACF', ACF), ('AMDF', AMDF)]:
            scores, lags, candidates_f0, candidates_strength = [], [], [], []
            for frame in frames:
                if algorithm == 'ACF':
                    score, lag, curve = scope['detect_pitch_acf'](frame, fs)
                    lo, hi = max(1, math.ceil(fs / 400)), min(len(frame) - 2, math.floor(fs / 70))
                    indices = np.arange(lo, hi + 1)
                    local = indices[(curve[indices] >= curve[indices - 1]) & (curve[indices] >= curve[indices + 1])]
                    strengths = curve[local]
                    lags_candidate = np.array([refine_lag(curve, idx, float(idx)) for idx in local])
                else:
                    score, _, lag, lag_grid, curve = scope['deepest_local_dip'](frame, fs)
                    local = np.where((curve[1:-1] <= curve[:-2]) & (curve[1:-1] <= curve[2:]))[0] + 1
                    strengths = 1 - curve[local]
                    lags_candidate = np.array([refine_lag(curve, idx, float(lag_grid[idx])) for idx in local])
                if not len(local):
                    lags_candidate = np.array([lag])
                    strengths = np.array([score if algorithm == 'ACF' else 1 - score])
                f0s = fs / lags_candidate
                valid = np.isfinite(f0s) & (f0s >= 70) & (f0s <= 400)
                f0s, strengths = f0s[valid], strengths[valid]
                order = np.argsort(strengths)[::-1][:12]
                f0s, strengths = f0s[order], strengths[order]
                f = np.full(12, np.nan)
                s = np.full(12, -np.inf)
                f[:len(f0s)], s[:len(f0s)] = f0s, strengths
                scores.append(score)
                lags.append(lag)
                candidates_f0.append(f)
                candidates_strength.append(s)
            arrays[algorithm + '_score'] = np.array(scores)
            arrays[algorithm + '_lag'] = np.array(lags)
            arrays[algorithm + '_candidate_f0'] = np.array(candidates_f0)
            arrays[algorithm + '_candidate_strength'] = np.array(candidates_strength)
        np.savez_compressed(cache, **arrays)
    return {'file': path.name, 'fs': fs, 'duration_s': len(original) / fs, 'frame_ms': frame_ms,
            'preprocess': preprocess, 'stats': stats, 'segments': segments, **arrays}


def load_training(frame_ms=25, preprocess='raw'):
    paths = sorted(TRAIN.glob('*.wav'))
    assert len(paths) == 4
    return [frame_features(path, frame_ms, preprocess) for path in paths]


def classification(labels, predicted):
    mask = np.isin(labels, ('v', 'uv'))
    truth, pred = labels[mask] == 'v', predicted[mask]
    tp, tn = int((truth & pred).sum()), int((~truth & ~pred).sum())
    fp, fn = int((~truth & pred).sum()), int((truth & ~pred).sum())
    rv, ru = tp / max(tp + fn, 1), tn / max(tn + fp, 1)
    fv, fu = 2 * tp / max(2 * tp + fp + fn, 1), 2 * tn / max(2 * tn + fp + fn, 1)
    return {'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn, 'recall_v': rv, 'recall_uv': ru,
            'balanced_accuracy': (rv + ru) / 2, 'macro_f1': (fv + fu) / 2,
            'accuracy_vu': (tp + tn) / max(len(truth), 1),
            'false_voiced_sil': int(((labels == 'sil') & predicted).sum())}


def threshold_options(items, algorithm):
    init_functions()
    v = np.concatenate([x[algorithm + '_score'][x['labels'] == 'v'] for x in items])
    u = np.concatenate([x[algorithm + '_score'][x['labels'] == 'uv'] for x in items])
    values = np.concatenate([x[algorithm + '_score'][np.isin(x['labels'], ('v', 'uv'))] for x in items])
    if algorithm == 'ACF':
        return {'gaussian': float(ACF['gaussian_intersection'](v.mean(), v.std(), u.mean(), u.std())),
                'hist_modes': float(ACF['histogram_threshold'](values)['threshold']),
                'hist_classes': float(ACF['class_histogram_threshold'](v, u)[0])}
    return {'gaussian': float(AMDF['gaussian_threshold'](v, u)),
            'hist_modes': float(AMDF['two_mode_histogram_threshold'](values)['threshold']),
            'hist_classes': float(AMDF['histogram_threshold'](v, u)[0])}


def fit_pitch_threshold(items, algorithm, method='original'):
    if method == 'gmm':
        values = np.concatenate([x[algorithm + '_score'][np.isin(x['labels'], ('v', 'uv'))] for x in items])
        return float(GMM['fit_gmm_threshold'](values)['threshold'])
    options = threshold_options(items, algorithm)
    if method == 'original':
        labels = np.concatenate([x['labels'] for x in items])
        scores = np.concatenate([x[algorithm + '_score'] for x in items])
        def objective(name):
            pred = scores >= options[name] if algorithm == 'ACF' else scores < options[name]
            metrics = classification(labels, pred)
            return metrics['balanced_accuracy'], metrics['accuracy_vu']
        method = max(options, key=objective)
    return options[method]


def fit_energy(items):
    values = np.unique(np.concatenate([x['relative_rms'][np.isin(x['labels'], ('v', 'sil'))] for x in items]))
    thresholds = np.r_[np.nextafter(values[0], -np.inf), (values[:-1] + values[1:]) / 2, np.nextafter(values[-1], np.inf)]
    def objective(threshold):
        per_file = []
        for x in items:
            e, labels = x['relative_rms'], x['labels']
            per_file.append(((e[labels == 'v'] >= threshold).mean() + (e[labels == 'sil'] < threshold).mean()) / 2)
        return np.mean(per_file), -threshold
    return float(max(thresholds, key=objective))


def fit(items, config):
    algorithm = config['algorithm']
    key = (algorithm, config.get('threshold_method', 'original'), config.get('energy', False),
           tuple(sorted((item['file'], item['frame_ms'], item['preprocess']) for item in items)))
    if key not in FIT_CACHE:
        FIT_CACHE[key] = {'pitch_threshold': fit_pitch_threshold(items, algorithm, config.get('threshold_method', 'original')),
                          'energy_threshold': fit_energy(items) if config.get('energy', False) else 0.}
    return dict(FIT_CACHE[key])


def voiced_runs(pred):
    edges = np.diff(np.r_[False, pred, False].astype(int))
    return zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))


def infer(item, config, fitted):
    algorithm = config['algorithm']
    score = item[algorithm + '_score']
    pred = score >= fitted['pitch_threshold'] if algorithm == 'ACF' else score < fitted['pitch_threshold']
    if config.get('energy', False):
        pred &= item['relative_rms'] >= fitted['energy_threshold']
    f0 = np.full(len(pred), np.nan)
    f0[pred] = item['fs'] / item[algorithm + '_lag'][pred]
    mode = config.get('candidate', 'best')
    if mode == 'near':
        candidates, strengths = item[algorithm + '_candidate_f0'], item[algorithm + '_candidate_strength']
        for index in np.flatnonzero(pred):
            valid = np.isfinite(candidates[index]) & (strengths[index] >= strengths[index].max() - config['margin'])
            if valid.any():
                f0[index] = candidates[index][valid].max()
    elif mode == 'path':
        candidates, strengths = item[algorithm + '_candidate_f0'], item[algorithm + '_candidate_strength']
        octave, jump = config.get('octave_cost', 0.), config['jump_cost']
        for start, stop in voiced_runs(pred):
            previous, backpointers = None, []
            for index in range(start, stop):
                c = candidates[index]
                valid = np.isfinite(c)
                if not valid.any():
                    c = c.copy()
                    c[0] = np.clip(f0[index], 70, 400)
                    valid[0] = True
                local = strengths[index].max() - strengths[index]
                local[valid] += octave * np.log2(400 / c[valid])
                local[~valid] = np.inf
                if previous is None:
                    costs = local
                    pointers = np.zeros(len(c), dtype=int)
                else:
                    previous_candidates = candidates[index - 1]
                    distance = np.abs(np.log2(c[:, None] / previous_candidates[None, :]))
                    distance[~np.isfinite(distance)] = np.inf
                    transitions = previous[None, :] + jump * distance
                    pointers = np.argmin(transitions, axis=1)
                    costs = local + transitions[np.arange(len(c)), pointers]
                previous = costs
                backpointers.append(pointers)
            state = int(np.argmin(previous))
            for index in range(stop - 1, start - 1, -1):
                candidate = candidates[index, state]
                if np.isfinite(candidate):
                    f0[index] = candidate
                state = int(backpointers[index - start][state])
    width = config.get('median', 1)
    if width > 1:
        radius = width // 2
        for start, stop in voiced_runs(pred):
            if stop - start >= width:
                original = f0[start:stop].copy()
                windows = np.lib.stride_tricks.sliding_window_view(original, width)
                f0[start + radius:stop - radius] = np.median(windows, axis=1)
    if mode != 'best' or config.get('clip_range', False):
        f0[(f0 < 70) | (f0 > 400)] = np.nan
    return pred, f0


def score_file(item, pred, f0):
    valid = f0[np.isfinite(f0)]
    estimates = {'F0mean': float(valid.mean()) if len(valid) else np.nan,
                 'F0std': float(valid.std()) if len(valid) else np.nan, 'F0num': int(len(valid))}
    metrics = {key + '_mape': 100 * abs(estimates[key] - item['stats'][key]) / item['stats'][key]
               for key in ('F0mean', 'F0std', 'F0num')}
    return {'file': item['file'], **estimates, **metrics,
            'average_mape': float(np.mean(list(metrics.values()))),
            'F0mean_abs_error': abs(estimates['F0mean'] - item['stats']['F0mean']),
            'F0std_abs_error': abs(estimates['F0std'] - item['stats']['F0std']),
            **classification(item['labels'], pred)}


def evaluate(items, config, fitted=None):
    fitted = fit(items, config) if fitted is None else fitted
    return pd.DataFrame([score_file(item, *infer(item, config, fitted)) for item in items])


def lofo(items, config):
    rows = []
    for held in items:
        other = [x for x in items if x is not held]
        fitted = fit(other, config)
        row = score_file(held, *infer(held, config, fitted))
        rows.append({**row, **fitted})
    return pd.DataFrame(rows)


def summarize(frame):
    keys = ['average_mape', 'F0mean_mape', 'F0std_mape', 'F0num_mape', 'F0mean_abs_error',
            'F0std_abs_error', 'macro_f1', 'balanced_accuracy', 'recall_v', 'recall_uv']
    result = {key: float(frame[key].mean()) for key in keys}
    result.update({key: int(frame[key].sum()) for key in ('TP', 'TN', 'FP', 'FN', 'false_voiced_sil', 'F0num')})
    return result

