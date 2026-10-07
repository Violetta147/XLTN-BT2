import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import wavfile
from verify_results import digest
from verify_amdf_soft_spectral import independent_pick

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def main():
    manifest = json.loads((HERE / 'results/H46_augmentation_manifest.json').read_text())
    assert manifest['origins'] == 4 and manifest['augmented_files'] == manifest['native_calls'] == 12
    assert not manifest['samples_are_independent'] and not manifest['test_used']
    assert len(manifest['cases']) == 12 and len({c['case_id'] for c in manifest['cases']}) == 12
    assert digest(HERE / 'results/H46_augmented_member_metrics.csv') == manifest['metrics_sha256']
    table = pd.read_csv(HERE / 'results/H46_augmented_member_metrics.csv')
    canonical = pd.read_csv(HERE / 'results/H46_nested_contours.csv')
    options = json.loads((HERE / 'H44_REGISTRY.json').read_text())['options']
    options_by_id = {o['id']: o for o in options}
    groups, curves_checked, metric_checks = {}, 0, 0
    for case in manifest['cases']:
        origin = case['origin_file']
        groups.setdefault(origin, []).append(case)
        assert case['origin_group'] == origin and case['inherited_reference']
        for key, root in (('labels_source', REPO), ('stats_source', REPO)):
            expected = case['labels_sha256' if key == 'labels_source' else 'stats_sha256']
            assert digest(root / case[key]) == expected
        assert digest(HERE / case['path']) == case['wav_sha256']
        assert digest(REPO / 'TinHieuHuanLuyen' / origin) == case['source_wav_sha256']
        fs, raw = wavfile.read(HERE / case['path'])
        source_fs, original = wavfile.read(REPO / 'TinHieuHuanLuyen' / origin)
        assert fs == source_fs == case['fs'] and len(raw) == len(original) == case['samples']
        assert raw.dtype == np.float32 and np.isfinite(raw).all() and abs(raw).max() < 1
        original = original.astype(np.float64) / 32768
        audio = raw.astype(np.float64)
        expected_seed = int(hashlib.sha256(f"H46|{origin}|{case['kind']}|{case['transformation']['snr_db']}".encode()).hexdigest()[:16], 16)
        assert case['transformation']['seed'] == expected_seed
        noise = np.random.default_rng(expected_seed).normal(size=len(original))
        if case['kind'] == 'pink':
            spectrum = np.fft.rfft(noise) / np.sqrt(np.maximum(np.arange(len(np.fft.rfft(noise))), 1))
            spectrum[0] = 0
            noise = np.fft.irfft(spectrum, n=len(original))
        noise -= noise.mean()
        noise *= np.linalg.norm(original) / np.linalg.norm(noise) * 10 ** (-case['transformation']['snr_db'] / 20)
        expected_waveform = ((original + noise) * case['transformation']['common_gain']).astype(np.float32)
        assert np.array_equal(raw, expected_waveform)
        perturbation = audio / case['transformation']['common_gain'] - original
        achieved = 20 * np.log10(np.linalg.norm(original) / np.linalg.norm(perturbation))
        assert abs(achieved - case['transformation']['snr_db']) < 1e-4
        call = case['native_call']
        assert call['returncode'] == 0 and Path(call['command'][3]).resolve() == (HERE / case['path']).resolve()
        assert call['command'][4:] == ['filtered', '0.3']
        assert digest(call['command'][0]) == call['exe_sha256']
        assert digest(call['command'][2]) == call['script_sha256']
        assert digest(HERE / case['features']['path']) == case['features']['sha256']
        features = dict(np.load(HERE / case['features']['path'], allow_pickle=False))
        nt, gate = features['times'], features['gate']
        short_long = {}
        for window in (25, 40):
            proof = case['curves'][str(window)]
            assert digest(HERE / proof['path']) == proof['sha256']
            data = dict(np.load(HERE / proof['path'], allow_pickle=False))
            assert np.array_equal(data['times'], nt) and np.array_equal(data['gate_frequency'], gate)
            length = round(fs * window / 1000)
            candidates = gate.copy()
            for i in np.flatnonzero((gate >= 70) & (gate <= 400)):
                start = round(nt[i] * fs - length / 2)
                assert start == data['starts'][i]
                if start < 0 or start + length > len(audio):
                    assert np.isnan(data['curve'][i]).all()
                    continue
                frame = audio[start:start + length]
                centered = frame - frame.mean()
                lags = data['lags']
                fresh = np.ones(len(lags)) if abs(centered).mean() < 1e-8 else np.array([
                    abs(centered[:-lag] - centered[lag:]).mean() / (abs(centered[:-lag]).mean() + abs(centered[lag:]).mean() + 1e-12) for lag in lags])
                np.testing.assert_allclose(fresh, data['curve'][i], atol=1e-12, rtol=1e-12)
                candidates[i], _, _ = independent_pick(fresh, lags, fs, gate[i])
                curves_checked += 1
            short_long[window] = candidates
        for i in np.flatnonzero((gate >= 70) & (gate <= 400)):
            length = round(fs * .040)
            start = round(nt[i] * fs - length / 2)
            if start < 0 or start + length > len(audio):
                assert np.isnan(features['ratio'][i])
                continue
            frame = audio[start:start + length]
            centered = frame - frame.mean()
            hann = .5 - .5 * np.cos(2 * np.pi * np.arange(length) / (length - 1))
            power = abs(np.fft.fft(centered * hann)) ** 2
            freq = abs(np.fft.fftfreq(length, 1 / fs))
            ratio = power[freq >= 1000].sum() / power[freq > 0].sum() if abs(centered).mean() >= 1e-8 else np.nan
            np.testing.assert_allclose(features['ratio'][i], ratio, atol=1e-12, equal_nan=True)
        gt = dict(line.split()[:2] for line in (REPO / case['stats_source']).read_text().splitlines())
        times = canonical[(canonical.file == origin) & (canonical.model == 'accepted')].time_s.to_numpy()
        labels = canonical[(canonical.file == origin) & (canonical.model == 'accepted')].label.to_numpy()
        index = np.array([int(np.argmin(abs(nt - t))) for t in times])
        support = abs(nt[index] - times) <= .005 + 1 / fs
        for identity, actual in zip(features['members'], features['member_frequencies']):
            option = options_by_id[str(identity)]
            expected = gate.copy()
            if option['method'] != 'control':
                for i in np.flatnonzero((gate >= 70) & (gate <= 400)):
                    ratio = features['ratio'][i]
                    if option['method'] == 'fixed_window' or not np.isfinite(ratio) or ratio > .05:
                        alpha = 0.
                    elif option['method'] == 'spectral_window':
                        alpha = float(gate[i] >= option['minimum_gate_hz'])
                    else:
                        alpha = max(0., min(1., (gate[i] - (option['center_hz'] - option['width_hz'] / 2)) / option['width_hz']))
                    a, b = short_long[25][i], short_long[40][i]
                    expected[i] = a if alpha == 0 else b if alpha == 1 else a ** (1 - alpha) * b ** alpha
            np.testing.assert_allclose(actual, expected, atol=1e-10, rtol=1e-12)
            pred = support & (actual[index] >= 70) & (actual[index] <= 400)
            values = actual[index][pred]
            saved = table[(table.case_id == case['case_id']) & (table.option_id == str(identity))].iloc[0]
            errors = []
            for key, value in {'F0mean': values.mean(), 'F0std': values.std(ddof=0), 'F0num': len(values)}.items():
                np.testing.assert_allclose(saved[key], value, atol=1e-8)
                errors.append(100 * abs(value - float(gt[key])) / float(gt[key]))
            np.testing.assert_allclose(saved.average_mape, np.mean(errors), atol=1e-8)
            assert saved.false_voiced_sil == int(((labels == 'sil') & pred).sum())
            metric_checks += 1
        print('Verified augmentation:', case['case_id'], flush=True)
    assert all(len(cases) == 3 for cases in groups.values()) and len(table) == 144
    receipt = dict(passed=True, augmented_wav_checks=12, origin_groups=4, member_metric_checks=metric_checks,
                   curve_rows_recomputed=curves_checked, latent_reference_assumption=True,
                   no_test_audio=True, manifest_sha256=digest(HERE / 'results/H46_augmentation_manifest.json'), verifier_sha256=digest(__file__))
    (HERE / 'results/H46_augmentation_verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
