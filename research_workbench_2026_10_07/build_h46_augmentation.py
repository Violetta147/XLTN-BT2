import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import wavfile
import amdf_soft_spectral_controller as reference
import amdf_anchor as anchor
import amdf_soft_spectral as soft

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results'
core, audit = reference.core, reference.audit
VARIANTS = (('white', 30), ('white', 20), ('pink', 20))


def augment(audio, origin, kind, snr):
    seed = int(hashlib.sha256(f'H46|{origin}|{kind}|{snr}'.encode()).hexdigest()[:16], 16)
    noise = np.random.default_rng(seed).normal(size=len(audio))
    if kind == 'pink':
        spectrum = np.fft.rfft(noise)
        spectrum /= np.sqrt(np.maximum(np.arange(len(spectrum)), 1))
        spectrum[0] = 0
        noise = np.fft.irfft(spectrum, n=len(audio))
    noise -= noise.mean()
    noise *= np.linalg.norm(audio) / np.linalg.norm(noise) * 10 ** (-snr / 20)
    mix = audio + noise
    gain = min(1., .95 / np.max(np.abs(mix)))
    stored = (mix * gain).astype(np.float32)
    actual_noise = stored.astype(np.float64) / gain - audio
    achieved = 20 * np.log10(np.linalg.norm(audio) / np.linalg.norm(actual_noise))
    assert abs(achieved - snr) < 1e-4 and np.max(np.abs(stored)) < 1
    return stored, dict(seed=seed, snr_db=snr, achieved_snr_db=float(achieved), common_gain=float(gain),
                        snr_definition='whole original waveform RMS versus injected noise; not speech-only clean SNR')


def main():
    manifest_path = OUT / 'H46_augmentation_manifest.json'
    assert not manifest_path.exists(), 'Preserve completed augmentation bank'
    root = HERE / 'augmentation/H46_train'
    root.mkdir(parents=True, exist_ok=True)
    anchor.OUTPUT_PREFIX = 'H46'
    anchor.CURVE_CACHE.clear()
    options = json.loads((HERE / 'H44_REGISTRY.json').read_text())['options']
    clean = pd.read_csv(OUT / 'H44_fixed_lofo.csv')
    rows = [dict(row, case_id='clean', variant='clean', inherited_reference=True) for row in clean.to_dict('records')]
    cases = []
    for item in core.load_training():
        origin = item['file']
        fs, original = core.load_audio(core.TRAIN / origin)
        for kind, snr in VARIANTS:
            case_id = f'{Path(origin).stem}__{kind}_snr{snr}'
            path = root / f'{case_id}.wav'
            assert not path.exists()
            stored, transformation = augment(original, origin, kind, snr)
            wavfile.write(path, fs, stored)
            actual_fs, audio = core.load_audio(path)
            assert actual_fs == fs and len(audio) == len(original)
            times, gate, call = reference.native_api.pitch(path, 'filtered', .3)
            variant_item = dict(item, file=path.name)
            data, curve_proofs = {}, {}
            for window in (25, 40):
                evidence = anchor.curves(variant_item, audio, times, gate, window)
                data[window] = dict(np.load(HERE / evidence['path'], allow_pickle=False))
                curve_proofs[str(window)] = {'path': evidence['path'], 'sha256': evidence['sha256']}
            ratios = np.full(len(times), np.nan)
            chosen = {window: gate.copy() for window in (25, 40)}
            for index in np.flatnonzero((gate >= 70) & (gate <= 400)):
                for window in (25, 40):
                    curve = data[window]['curve'][index]
                    if not np.isfinite(curve).all():
                        continue
                    f0, dips, _ = anchor.candidates(data[window]['lags'], curve, fs)
                    chosen[window][index], _, _ = anchor.choose(gate[index], f0, dips, 200)
                start, length = int(data[40]['starts'][index]), int(data[40]['frame_samples'])
                if 0 <= start and start + length <= len(audio):
                    ratios[index] = soft.high_frequency_ratio(audio[start:start + length], fs)
            outputs = []
            for option in options:
                frequency = gate.copy()
                if option['method'] != 'control':
                    for index in np.flatnonzero((gate >= 70) & (gate <= 400)):
                        alpha = soft.weight(ratios[index], option, gate[index])
                        frequency[index] = soft.blend(chosen[25][index], chosen[40][index], alpha)
                pred = (frequency >= 70) & (frequency <= 400)
                assert np.array_equal(pred, (gate >= 70) & (gate <= 400))
                projected, ff, support = reference.project({'times': times, 'fs': fs}, item, pred, np.where(pred, frequency, np.nan), 10)
                metrics = core.score_file(item, projected, ff)
                rows.append(dict(metrics, option_id=option['id'], case_id=case_id, variant=f'{kind}_{snr}', inherited_reference=True))
                outputs.append(frequency)
            feature_path = OUT / f'H46_aug_features_{case_id}.npz'
            np.savez_compressed(feature_path, times=times, gate=gate, f25=chosen[25], f40=chosen[40], ratio=ratios,
                                member_frequencies=np.stack(outputs), members=np.array([o['id'] for o in options]), fs=fs)
            cases.append(dict(case_id=case_id, origin_file=origin, origin_group=origin, kind=kind,
                              path=str(path.relative_to(HERE)), wav_sha256=audit.digest(path),
                              source_wav_sha256=audit.digest(core.TRAIN / origin), samples=len(audio), fs=fs,
                              labels_source=str((core.TRAIN / origin.replace('.wav', '.lab')).relative_to(HERE.parent)),
                              labels_sha256=audit.digest(core.TRAIN / origin.replace('.wav', '.lab')),
                              stats_source=str((core.TRAIN_GT / origin.replace('.wav', '.lab')).relative_to(HERE.parent)),
                              stats_sha256=audit.digest(core.TRAIN_GT / origin.replace('.wav', '.lab')),
                              inherited_reference=True, transformation=transformation, native_call=call,
                              features={'path': str(feature_path.relative_to(HERE)), 'sha256': audit.digest(feature_path)}, curves=curve_proofs))
            print('H46 augmentation bank ready:', case_id, flush=True)
    metrics_path = OUT / 'H46_augmented_member_metrics.csv'
    pd.DataFrame(rows).to_csv(metrics_path, index=False)
    proof = dict(cases=cases, origins=4, augmented_files=12, native_calls=12, variant_count_per_origin=3,
                 clean_reference_policy='Inherited V/UV/SIL and file mean/std/count are assumed latent targets under added noise; not newly measured ground truth',
                 samples_are_independent=False, fit_group_key='origin_file', test_used=False,
                 metrics_sha256=audit.digest(metrics_path), generator_sha256=audit.digest(__file__))
    manifest_path.write_text(json.dumps(proof, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return proof


def check():
    t = np.arange(16000) / 16000
    x = .2 * np.sin(2 * np.pi * 173 * t)
    for kind, snr in VARIANTS:
        a, proof = augment(x, 'synthetic.wav', kind, snr)
        b, _ = augment(x, 'synthetic.wav', kind, snr)
        assert np.array_equal(a, b) and len(a) == len(x)
        assert abs(proof['achieved_snr_db'] - snr) < 1e-4
    print('PASS deterministic augmentation/no clipping/length/achieved SNR on synthetic signal')
