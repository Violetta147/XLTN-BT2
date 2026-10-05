import math
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal import correlate
from sklearn.mixture import GaussianMixture
EPS = 1e-12
F0_MIN, F0_MAX, HOP_MS = 70., 400., 10
HIST_BINS, HIST_SMOOTH_WINDOW, HIST_W = 20, 5, 1.
NEAR_ZERO_MEAN_ABS = 1e-8
FIT_CACHE = {}

def build_acf():
    def normalized_acf(frame):
        x = np.asarray(frame, dtype=np.float64)
        x = x - np.mean(x)
        n = len(x)
        if n == 0:
            return np.array([])
        numerator = correlate(x, x, mode='full', method='fft')[n - 1:]
        sq = x * x
        csum = np.concatenate(([0.0], np.cumsum(sq)))
        lags = np.arange(n)
        energy_left = csum[n - lags]
        energy_right = csum[n] - csum[lags]
        denominator = np.sqrt(energy_left * energy_right)
        acf = np.divide(numerator, denominator, out=np.zeros_like(numerator, dtype=np.float64), where=denominator > EPS)
        return acf

    def detect_pitch_acf(frame, fs, f0_min=F0_MIN, f0_max=F0_MAX):
        acf = normalized_acf(frame)
        lag_min = max(1, int(np.ceil(fs / f0_max)))
        lag_max = min(len(frame) - 2, int(np.floor(fs / f0_min)))
        if lag_min > lag_max:
            return (0.0, np.nan, acf)
        candidate_lags = np.arange(lag_min, lag_max + 1)
        local_mask = (acf[candidate_lags] >= acf[candidate_lags - 1]) & (acf[candidate_lags] >= acf[candidate_lags + 1])
        local_lags = candidate_lags[local_mask]
        if len(local_lags) > 0:
            best_lag_int = int(local_lags[np.argmax(acf[local_lags])])
        else:
            best_lag_int = int(lag_min + np.argmax(acf[lag_min:lag_max + 1]))
        periodicity_score = float(acf[best_lag_int])
        best_lag = float(best_lag_int)
        y_m1 = acf[best_lag_int - 1]
        y_0 = acf[best_lag_int]
        y_p1 = acf[best_lag_int + 1]
        denom = y_m1 - 2.0 * y_0 + y_p1
        if abs(denom) > EPS:
            delta = 0.5 * (y_m1 - y_p1) / denom
            if abs(delta) <= 1.0:
                best_lag += float(delta)
        return (periodicity_score, best_lag, acf)

    def lag_to_f0(best_lag, fs):
        if not np.isfinite(best_lag) or best_lag <= 0:
            return np.nan
        return fs / best_lag

    def gaussian_intersection(mu_v, std_v, mu_u, std_u):
        """Tìm nghiệm pV(x)=pU(x), ưu tiên nghiệm nằm giữa hai mean."""
        sv = max(float(std_v), EPS)
        su = max(float(std_u), EPS)
        a = 1.0 / su ** 2 - 1.0 / sv ** 2
        b = -2.0 * mu_u / su ** 2 + 2.0 * mu_v / sv ** 2
        c = mu_u ** 2 / su ** 2 - mu_v ** 2 / sv ** 2 + 2.0 * np.log(su / sv)
        if abs(a) < EPS:
            roots = [] if abs(b) < EPS else [-c / b]
        else:
            roots = np.roots([a, b, c])
        real_roots = [float(np.real(r)) for r in roots if abs(np.imag(r)) < 1e-09]
        lo, hi = sorted([mu_u, mu_v])
        between = [r for r in real_roots if lo <= r <= hi]
        if between:
            return between[0]
        if real_roots:
            midpoint = 0.5 * (mu_u + mu_v)
            return min(real_roots, key=lambda r: abs(r - midpoint))
        return 0.5 * (mu_u + mu_v)

    def histogram_threshold(scores, bins=HIST_BINS, smooth_window=HIST_SMOOTH_WINDOW, W=HIST_W):
        """
        Histogram-based threshold phỏng theo [5]:
          histogram -> smoothing -> local maxima -> T=(W*M1+M2)/(W+1)

        Hai local maxima mạnh nhất được chọn làm hai mode chính.
        Nếu histogram quá phẳng, fallback lấy hai bin có độ cao lớn nhất,
        có ràng buộc không chọn hai bin liền kề.
        """
        scores = np.asarray(scores, dtype=float)
        scores = scores[np.isfinite(scores)]
        if len(scores) < 2:
            raise ValueError('Không đủ score để tính histogram threshold.')
        hist, edges = np.histogram(scores, bins=bins)
        centers = 0.5 * (edges[:-1] + edges[1:])
        smooth_window = int(max(1, smooth_window))
        if smooth_window % 2 == 0:
            smooth_window += 1
        kernel = np.ones(smooth_window, dtype=float) / smooth_window
        smooth_hist = np.convolve(hist.astype(float), kernel, mode='same')
        local_idx = np.where((smooth_hist[1:-1] >= smooth_hist[:-2]) & (smooth_hist[1:-1] > smooth_hist[2:]))[0] + 1
        ranked = list(local_idx[np.argsort(smooth_hist[local_idx])[::-1]])
        if len(ranked) < 2:
            ranked = list(np.argsort(smooth_hist)[::-1])
        chosen = []
        for idx in ranked:
            if all((abs(int(idx) - int(j)) >= 2 for j in chosen)):
                chosen.append(int(idx))
            if len(chosen) == 2:
                break
        if len(chosen) < 2:
            chosen = [int(np.argmin(centers)), int(np.argmax(centers))]
        m1, m2 = sorted([float(centers[chosen[0]]), float(centers[chosen[1]])])
        threshold = (W * m1 + m2) / (W + 1.0)
        return {'threshold': float(threshold), 'M1': m1, 'M2': m2, 'hist': hist, 'smooth_hist': smooth_hist, 'centers': centers, 'edges': edges, 'peak_indices': np.array(chosen, dtype=int)}

    def class_histogram_threshold(v_scores, u_scores, bins=80, smooth_width=7):
        """Hai histogram density theo nhãn, smoothing rồi tìm giao điểm giữa mean V/UV."""
        all_scores = np.concatenate([v_scores, u_scores])
        x_min, x_max = (float(all_scores.min()), float(all_scores.max()))
        hist_v, edges = np.histogram(v_scores, bins=bins, range=(x_min, x_max), density=True)
        hist_u, _ = np.histogram(u_scores, bins=bins, range=(x_min, x_max), density=True)
        kernel = np.ones(smooth_width, dtype=float) / smooth_width
        smooth_v = np.convolve(hist_v, kernel, mode='same')
        smooth_u = np.convolve(hist_u, kernel, mode='same')
        centers = 0.5 * (edges[:-1] + edges[1:])
        lo, hi = sorted((float(v_scores.mean()), float(u_scores.mean())))
        candidate_idx = np.where((centers >= lo) & (centers <= hi))[0]
        if len(candidate_idx) == 0:
            return (0.5 * (lo + hi), centers, smooth_v, smooth_u)
        diff = smooth_v - smooth_u
        crossings = []
        for idx in candidate_idx[:-1]:
            if diff[idx] == 0 or diff[idx] * diff[idx + 1] < 0:
                best = idx if abs(diff[idx]) <= abs(diff[idx + 1]) else idx + 1
                crossings.append(best)
        if crossings:
            midpoint = 0.5 * (lo + hi)
            best_idx = min(crossings, key=lambda i: abs(centers[i] - midpoint))
        else:
            best_idx = candidate_idx[np.argmin(np.abs(diff[candidate_idx]))]
        return (float(centers[best_idx]), centers, smooth_v, smooth_u)
    return {'normalized_acf': normalized_acf, 'detect_pitch_acf': detect_pitch_acf, 'lag_to_f0': lag_to_f0, 'gaussian_intersection': gaussian_intersection, 'histogram_threshold': histogram_threshold, 'class_histogram_threshold': class_histogram_threshold}
ACF = build_acf()

def build_amdf():
    def lag_search_range(fs, frame_len, f0_min=F0_MIN, f0_max=F0_MAX):
        """Tính miền lag hợp lệ từ dải F0."""
        lag_min = max(1, int(np.floor(fs / f0_max)))
        lag_max = min(frame_len - 1, int(np.ceil(fs / f0_min)))
        if lag_min > lag_max:
            raise ValueError('Frame quá ngắn so với miền lag cần tìm.')
        return (lag_min, lag_max)

    def normalized_amdf(frame, fs, f0_min=F0_MIN, f0_max=F0_MAX):
        """
        Tính normalized AMDF trong miền lag hợp lệ.

        Vector hóa bằng NumPy theo cả trục lag và sample; chỉ tạo ma trận nhỏ
        tương ứng các lag 70–400 Hz, không tính các lag không cần thiết.
        """
        x = np.asarray(frame, dtype=np.float64)
        x = x - np.mean(x)
        lag_min, lag_max = lag_search_range(fs, len(x), f0_min, f0_max)
        lags = np.arange(lag_min, lag_max + 1, dtype=int)
        if np.mean(np.abs(x)) < NEAR_ZERO_MEAN_ABS:
            return (lags, np.ones_like(lags, dtype=np.float64))
        max_overlap = len(x) - lag_min
        n = np.arange(max_overlap)[None, :]
        lag_matrix = lags[:, None]
        valid = n < len(x) - lag_matrix
        idx2 = np.minimum(n + lag_matrix, len(x) - 1)
        x1 = np.broadcast_to(x[:max_overlap][None, :], idx2.shape)
        x2 = x[idx2]
        count = valid.sum(axis=1)
        diff_mean = (np.abs(x1 - x2) * valid).sum(axis=1) / count
        x1_mean_abs = (np.abs(x1) * valid).sum(axis=1) / count
        x2_mean_abs = (np.abs(x2) * valid).sum(axis=1) / count
        namdf = diff_mean / (x1_mean_abs + x2_mean_abs + EPS)
        return (lags, namdf)

    def deepest_local_dip(frame, fs, f0_min=F0_MIN, f0_max=F0_MAX):
        """
        Tìm lowest local dip của normalized AMDF.

        Returns
        -------
        dip_value : float
            Giá trị đáy AMDF dùng làm periodicity score.
        lag : int
            Lag nguyên tại đáy.
        refined_lag : float
            Lag tinh chỉnh bằng nội suy parabol để ước lượng F0 mượt hơn.
        lags, namdf : ndarray
            Dùng cho vẽ minh họa.
        """
        lags, namdf = normalized_amdf(frame, fs, f0_min, f0_max)
        if len(namdf) >= 3:
            local_mask = (namdf[1:-1] <= namdf[:-2]) & (namdf[1:-1] <= namdf[2:])
            local_idx = np.where(local_mask)[0] + 1
        else:
            local_idx = np.array([], dtype=int)
        if len(local_idx) == 0:
            best_idx = int(np.argmin(namdf))
        else:
            best_idx = int(local_idx[np.argmin(namdf[local_idx])])
        dip_value = float(namdf[best_idx])
        lag = int(lags[best_idx])
        refined_lag = float(lag)
        if 0 < best_idx < len(namdf) - 1:
            y1, y2, y3 = namdf[best_idx - 1:best_idx + 2]
            denominator = y1 - 2.0 * y2 + y3
            if abs(denominator) > EPS:
                delta = 0.5 * (y1 - y3) / denominator
                if abs(delta) <= 1.0:
                    refined_lag += float(delta)
        return (dip_value, lag, refined_lag, lags, namdf)

    def f0_from_lag(fs, lag):
        return fs / lag if lag > 0 else np.nan

    def gaussian_threshold(v_scores, u_scores):
        """Chọn giao điểm Gaussian nằm giữa meanV và meanU, giống quy tắc của ACF."""
        mu_v, sv = (float(v_scores.mean()), max(float(v_scores.std()), EPS))
        mu_u, su = (float(u_scores.mean()), max(float(u_scores.std()), EPS))
        a = 1.0 / su ** 2 - 1.0 / sv ** 2
        b = -2.0 * mu_u / su ** 2 + 2.0 * mu_v / sv ** 2
        c = mu_u ** 2 / su ** 2 - mu_v ** 2 / sv ** 2 + 2.0 * np.log(su / sv)
        if abs(a) < EPS:
            roots = [] if abs(b) < EPS else [-c / b]
        else:
            roots = np.roots([a, b, c])
        real_roots = [float(np.real(root)) for root in roots if abs(np.imag(root)) < 1e-09]
        lo, hi = sorted((mu_v, mu_u))
        between = [root for root in real_roots if lo <= root <= hi]
        midpoint = 0.5 * (mu_v + mu_u)
        if between:
            return min(between, key=lambda root: abs(root - midpoint))
        if real_roots:
            return min(real_roots, key=lambda root: abs(root - midpoint))
        return midpoint

    def histogram_threshold(v_scores, u_scores, bins=80, smooth_width=7):
        """
        Histogram smoothing cho hai lớp V/UV rồi tìm điểm giao density.
        Trả thêm dữ liệu histogram để vẽ.
        """
        all_scores = np.concatenate([v_scores, u_scores])
        x_min, x_max = (float(all_scores.min()), float(all_scores.max()))
        hist_v, edges = np.histogram(v_scores, bins=bins, range=(x_min, x_max), density=True)
        hist_u, _ = np.histogram(u_scores, bins=bins, range=(x_min, x_max), density=True)
        kernel = np.ones(smooth_width, dtype=float) / smooth_width
        smooth_v = np.convolve(hist_v, kernel, mode='same')
        smooth_u = np.convolve(hist_u, kernel, mode='same')
        centers = 0.5 * (edges[:-1] + edges[1:])
        lo, hi = sorted((float(v_scores.mean()), float(u_scores.mean())))
        candidate_idx = np.where((centers >= lo) & (centers <= hi))[0]
        if len(candidate_idx) == 0:
            threshold = 0.5 * (lo + hi)
            return (threshold, centers, smooth_v, smooth_u)
        diff = smooth_v - smooth_u
        crossings = []
        for idx in candidate_idx[:-1]:
            if diff[idx] == 0 or diff[idx] * diff[idx + 1] < 0:
                best = idx if abs(diff[idx]) <= abs(diff[idx + 1]) else idx + 1
                crossings.append(best)
        if crossings:
            midpoint = 0.5 * (lo + hi)
            best_idx = min(crossings, key=lambda i: abs(centers[i] - midpoint))
        else:
            best_idx = candidate_idx[np.argmin(np.abs(diff[candidate_idx]))]
        threshold = float(centers[best_idx])
        return (threshold, centers, smooth_v, smooth_u)

    def two_mode_histogram_threshold(scores, bins=HIST_BINS, smooth_window=HIST_SMOOTH_WINDOW, W=HIST_W):
        """Histogram gộp -> smoothing -> hai local maxima -> T=(W*M1+M2)/(W+1)."""
        scores = np.asarray(scores, dtype=float)
        scores = scores[np.isfinite(scores)]
        if len(scores) < 2:
            raise ValueError('Không đủ score để tính histogram hai mode.')
        hist, edges = np.histogram(scores, bins=bins)
        centers = 0.5 * (edges[:-1] + edges[1:])
        smooth_window = int(max(1, smooth_window))
        if smooth_window % 2 == 0:
            smooth_window += 1
        kernel = np.ones(smooth_window, dtype=float) / smooth_window
        smooth_hist = np.convolve(hist.astype(float), kernel, mode='same')
        local_idx = np.where((smooth_hist[1:-1] >= smooth_hist[:-2]) & (smooth_hist[1:-1] > smooth_hist[2:]))[0] + 1
        ranked = list(local_idx[np.argsort(smooth_hist[local_idx])[::-1]])
        if len(ranked) < 2:
            ranked = list(np.argsort(smooth_hist)[::-1])
        chosen = []
        for idx in ranked:
            if all((abs(int(idx) - int(j)) >= 2 for j in chosen)):
                chosen.append(int(idx))
            if len(chosen) == 2:
                break
        if len(chosen) < 2:
            chosen = [int(np.argmin(centers)), int(np.argmax(centers))]
        m1, m2 = sorted([float(centers[chosen[0]]), float(centers[chosen[1]])])
        return {'threshold': float((W * m1 + m2) / (W + 1.0)), 'M1': m1, 'M2': m2, 'hist': hist, 'smooth_hist': smooth_hist, 'centers': centers, 'edges': edges, 'peak_indices': np.array(chosen, dtype=int)}
    return {'lag_search_range': lag_search_range, 'normalized_amdf': normalized_amdf, 'deepest_local_dip': deepest_local_dip, 'f0_from_lag': f0_from_lag, 'gaussian_threshold': gaussian_threshold, 'histogram_threshold': histogram_threshold, 'two_mode_histogram_threshold': two_mode_histogram_threshold}
AMDF = build_amdf()

def build_gmm():
    def normal_pdf(x, mean, std):
        std = max(float(std), EPS)
        return np.exp(-0.5 * ((x - mean) / std) ** 2) / (std * np.sqrt(2.0 * np.pi))

    def fit_gmm_threshold(scores):
        scores = np.asarray(scores, dtype=float)
        scores = scores[np.isfinite(scores)]
        if len(scores) < 4 or np.std(scores) < 1e-10:
            raise ValueError('Score training quá ít hoặc không biến thiên để fit GMM hai thành phần.')
        model = GaussianMixture(n_components=2, covariance_type='spherical', reg_covar=1e-06, n_init=10, random_state=42).fit(scores.reshape(-1, 1))
        order = np.argsort(model.means_.ravel())
        means = model.means_.ravel()[order]
        stds = np.sqrt(model.covariances_[order])
        weights = model.weights_[order]
        grid = np.linspace(means[0], means[1], 10001)
        low_density = weights[0] * normal_pdf(grid, means[0], stds[0])
        high_density = weights[1] * normal_pdf(grid, means[1], stds[1])
        difference = low_density - high_density
        crossing_indices = np.where(difference[:-1] * difference[1:] <= 0)[0]
        if len(crossing_indices):
            midpoint = 0.5 * (means[0] + means[1])
            index = min(crossing_indices, key=lambda i: abs(grid[i] - midpoint))
            left, right = (difference[index], difference[index + 1])
            fraction = -left / (right - left) if right != left else 0.0
            threshold = float(grid[index] + fraction * (grid[index + 1] - grid[index]))
        else:
            threshold = float(grid[np.argmin(np.abs(difference))])
        return {'model': model, 'means': means, 'stds': stds, 'weights': weights, 'threshold': threshold}
    return {'normal_pdf': normal_pdf, 'fit_gmm_threshold': fit_gmm_threshold}
GMM = build_gmm()

def init_functions():
    return


def read_stats(path):
    stats = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        words = line.split()
        if words and words[0] in {'F0mean', 'F0std', 'F0num'}:
            stats[words[0]] = float(words[1])
    assert set(stats) == {'F0mean', 'F0std', 'F0num'}
    assert all((value > 0 for value in stats.values()))
    return stats

def read_segments(path):
    segments = []
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        words = line.split()
        if words and words[0] not in {'F0mean', 'F0std', 'F0num'}:
            segments.append((float(words[0]), float(words[1]), words[2].lower()))
    assert segments and all((a < b and label in ('v', 'uv', 'sil') for a, b, label in segments))
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
    return (int(fs), values)

def refine_lag(curve, index, lag):
    if 0 < index < len(curve) - 1:
        a, b, c = curve[index - 1:index + 2]
        denom = a - 2 * b + c
        if abs(denom) > EPS:
            delta = 0.5 * (a - c) / denom
            if abs(delta) <= 1:
                lag += float(delta)
    return lag

def classification(labels, predicted):
    mask = np.isin(labels, ('v', 'uv'))
    truth, pred = (labels[mask] == 'v', predicted[mask])
    tp, tn = (int((truth & pred).sum()), int((~truth & ~pred).sum()))
    fp, fn = (int((~truth & pred).sum()), int((truth & ~pred).sum()))
    rv, ru = (tp / max(tp + fn, 1), tn / max(tn + fp, 1))
    fv, fu = (2 * tp / max(2 * tp + fp + fn, 1), 2 * tn / max(2 * tn + fp + fn, 1))
    return {'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn, 'recall_v': rv, 'recall_uv': ru, 'balanced_accuracy': (rv + ru) / 2, 'macro_f1': (fv + fu) / 2, 'accuracy_vu': (tp + tn) / max(len(truth), 1), 'false_voiced_sil': int(((labels == 'sil') & predicted).sum())}

def threshold_options(items, algorithm):
    init_functions()
    v = np.concatenate([x[algorithm + '_score'][x['labels'] == 'v'] for x in items])
    u = np.concatenate([x[algorithm + '_score'][x['labels'] == 'uv'] for x in items])
    values = np.concatenate([x[algorithm + '_score'][np.isin(x['labels'], ('v', 'uv'))] for x in items])
    if algorithm == 'ACF':
        return {'gaussian': float(ACF['gaussian_intersection'](v.mean(), v.std(), u.mean(), u.std())), 'hist_modes': float(ACF['histogram_threshold'](values)['threshold']), 'hist_classes': float(ACF['class_histogram_threshold'](v, u)[0])}
    return {'gaussian': float(AMDF['gaussian_threshold'](v, u)), 'hist_modes': float(AMDF['two_mode_histogram_threshold'](values)['threshold']), 'hist_classes': float(AMDF['histogram_threshold'](v, u)[0])}

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
            return (metrics['balanced_accuracy'], metrics['accuracy_vu'])
        method = max(options, key=objective)
    return options[method]

def fit_energy(items):
    values = np.unique(np.concatenate([x['relative_rms'][np.isin(x['labels'], ('v', 'sil'))] for x in items]))
    thresholds = np.r_[np.nextafter(values[0], -np.inf), (values[:-1] + values[1:]) / 2, np.nextafter(values[-1], np.inf)]

    def objective(threshold):
        per_file = []
        for x in items:
            e, labels = (x['relative_rms'], x['labels'])
            per_file.append(((e[labels == 'v'] >= threshold).mean() + (e[labels == 'sil'] < threshold).mean()) / 2)
        return (np.mean(per_file), -threshold)
    return float(max(thresholds, key=objective))

def fit(items, config):
    algorithm = config['algorithm']
    key = (algorithm, config.get('threshold_method', 'original'), config.get('energy', False), tuple(sorted(((item['file'], item['frame_ms'], item['preprocess']) for item in items))))
    if key not in FIT_CACHE:
        FIT_CACHE[key] = {'pitch_threshold': fit_pitch_threshold(items, algorithm, config.get('threshold_method', 'original')), 'energy_threshold': fit_energy(items) if config.get('energy', False) else 0.0}
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
        candidates, strengths = (item[algorithm + '_candidate_f0'], item[algorithm + '_candidate_strength'])
        for index in np.flatnonzero(pred):
            valid = np.isfinite(candidates[index]) & (strengths[index] >= strengths[index].max() - config['margin'])
            if valid.any():
                f0[index] = candidates[index][valid].max()
    elif mode == 'path':
        candidates = item[algorithm + '_candidate_f0'].copy()
        strengths = item[algorithm + '_candidate_strength'].copy()
        empty = ~np.isfinite(candidates).any(axis=1)
        candidates[empty, 0] = np.clip(item['fs'] / item[algorithm + '_lag'][empty], 70, 400)
        strengths[empty, 0] = score[empty] if algorithm == 'ACF' else 1 - score[empty]
        octave, jump = (config.get('octave_cost', 0.0), config['jump_cost'])
        for start, stop in voiced_runs(pred):
            previous, backpointers = (None, [])
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
    return (pred, f0)

def score_file(item, pred, f0):
    valid = f0[np.isfinite(f0)]
    estimates = {'F0mean': float(valid.mean()) if len(valid) else np.nan, 'F0std': float(valid.std()) if len(valid) else np.nan, 'F0num': int(len(valid))}
    metrics = {key + '_mape': 100 * abs(estimates[key] - item['stats'][key]) / item['stats'][key] for key in ('F0mean', 'F0std', 'F0num')}
    return {'file': item['file'], **estimates, **metrics, 'average_mape': float(np.mean(list(metrics.values()))), 'F0mean_abs_error': abs(estimates['F0mean'] - item['stats']['F0mean']), 'F0std_abs_error': abs(estimates['F0std'] - item['stats']['F0std']), **classification(item['labels'], pred)}

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
    keys = ['average_mape', 'F0mean_mape', 'F0std_mape', 'F0num_mape', 'F0mean_abs_error', 'F0std_abs_error', 'macro_f1', 'balanced_accuracy', 'recall_v', 'recall_uv']
    result = {key: float(frame[key].mean()) for key in keys}
    result.update({key: int(frame[key].sum()) for key in ('TP', 'TN', 'FP', 'FN', 'false_voiced_sil', 'F0num')})
    return result

def signal_features(path, frame_ms=25):
    path = Path(path)
    fs, original = load_audio(path)
    frame_len, hop_len = round(fs * frame_ms / 1000), round(fs * .010)
    frames = np.lib.stride_tricks.sliding_window_view(original, frame_len)[::hop_len]
    times = (np.arange(len(frames)) * hop_len + frame_len / 2) / fs
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    relative_rms = rms / max(np.quantile(rms, .95), EPS)
    arrays = {'times': times, 'rms': rms, 'relative_rms': relative_rms}
    for algorithm, scope in [('ACF', ACF), ('AMDF', AMDF)]:
        scores, lags, candidates_f0, candidates_strength = ([], [], [], [])
        for frame in frames:
            if algorithm == 'ACF':
                score, lag, curve = scope['detect_pitch_acf'](frame, fs)
                lo, hi = (max(1, math.ceil(fs / 400)), min(len(frame) - 2, math.floor(fs / 70)))
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
            f0s, strengths = (f0s[valid], strengths[valid])
            order = np.argsort(strengths)[::-1][:12]
            f0s, strengths = (f0s[order], strengths[order])
            f = np.full(12, np.nan)
            s = np.full(12, -np.inf)
            f[:len(f0s)], s[:len(f0s)] = (f0s, strengths)
            scores.append(score)
            lags.append(lag)
            candidates_f0.append(f)
            candidates_strength.append(s)
        arrays[algorithm + '_score'] = np.array(scores)
        arrays[algorithm + '_lag'] = np.array(lags)
        arrays[algorithm + '_candidate_f0'] = np.array(candidates_f0)
        arrays[algorithm + '_candidate_strength'] = np.array(candidates_strength)
    return {'file': path.name, 'fs': fs, 'duration_s': len(original) / fs, 'frame_ms': frame_ms, 'preprocess': 'raw', **arrays}
