import hashlib
import json
import math
import platform
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.io import wavfile
from scipy.signal import resample_poly

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE / 'results'
NAMES = ('phone_F1.wav', 'phone_M1.wav', 'studio_F1.wav', 'studio_M1.wav')
BANDS = ((0, 70), (70, 1000), (1000, 4000), (4000, 8000))
INPUTS = {}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def track(path):
    INPUTS[str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)] = digest(path)
    return path


def measure(x, fs, segments, name, rate_mode):
    length, hop = round(fs * .025), round(fs * .010)
    freq = np.fft.rfftfreq(4096, 1 / fs)
    bins = [(freq >= low) & ((freq < high) if high < 8000 else (freq <= high)) for low, high in BANDS]
    rows = []
    for start in range(0, len(x) - length + 1, hop):
        end = start + length
        labels = [label for a, b, label in segments if start / fs >= a + .020 - 1e-12 and end / fs <= b - .020 + 1e-12]
        if not labels:
            continue
        assert len(labels) == 1
        frame = x[start:end]
        power = np.abs(np.fft.rfft((frame - frame.mean()) * np.hanning(length), n=4096)) ** 2
        band_power = [float(power[mask].sum()) for mask in bins]
        total = sum(band_power)
        row = dict(file=name, mode=rate_mode, fs=fs, label=labels[0], start_s=start / fs,
                   end_s=end / fs, samples=length, mean_square=float(np.mean(frame ** 2)),
                   zero_fraction=float(np.mean(frame == 0)), spectral_power_0_8000=total,
                   spectral_frequency_power=float(np.dot(freq[freq <= 8000], power[freq <= 8000])))
        for (low, high), value in zip(BANDS, band_power):
            row[f'power_{low}_{high}'] = value
        rows.append(row)
    assert rows
    return rows


def saved_results():
    rows = []
    submitted_path = REPO.parent / 'XLTN-BT1-BO-SUNG/baseline/submitted_results.json'
    submitted = json.loads(track(submitted_path).read_text(encoding='utf-8'))
    for row in submitted['train']:
        rows.append(dict(protocol='submitted_ACF_train_screenshot', file=row['file'],
                         average_mape=row['average_mape_percent'], F0mean_mape=row['F0mean_mape_percent'],
                         F0std_mape=row['F0std_mape_percent'], F0num_mape=row['F0num_mape_percent']))
    h20 = pd.read_csv(track(OUT / 'H20_clean_per_file.csv'))
    for model in ('accepted', 'H18_nested', 'H19_nested'):
        for row in h20[h20.model == model].to_dict('records'):
            row['protocol'] = 'H20_' + model + '_outer_train'
            rows.append(row)
    h31 = pd.read_csv(track(OUT / 'H31_fixed_lofo.csv'))
    for row in h31[h31.option_id == 'praat7_filtered_v0.3'].to_dict('records'):
        row['protocol'] = 'H31_fixed_0.30_train'
        rows.append(row)
    for experiment in ('H41', 'H43'):
        source = pd.read_csv(track(OUT / f'{experiment}_metrics.csv'))
        for row in source[(source.model == 'candidate') & (source.split == 'nested')].to_dict('records'):
            row['protocol'] = experiment + '_candidate_nested_train'
            rows.append(row)
    frame = pd.DataFrame(rows)
    for protocol, group in frame.groupby('protocol'):
        assert set(group.file) == set(NAMES) and len(group) == 4, protocol
    return frame


def main():
    track(Path(__file__).resolve())
    track(HERE / 'RECORDING_CONDITIONS_PLAN.md')
    frame_rows, originals, resampling = [], {}, []
    for name in NAMES:
        wav_path = track(REPO / 'TinHieuHuanLuyen' / name)
        lab_path = track(wav_path.with_suffix('.lab'))
        originals[name] = {'wav': digest(wav_path), 'lab': digest(lab_path)}
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', wavfile.WavFileWarning)
            fs, raw = wavfile.read(wav_path)
        assert raw.dtype == np.int16 and raw.ndim == 1
        x = raw.astype(np.float64) / 32768
        assert np.isfinite(x).all()
        segments = []
        for line in lab_path.read_text(encoding='utf-8-sig').splitlines():
            words = line.split()
            if len(words) == 3 and words[2].lower() in ('v', 'uv', 'sil'):
                segments.append((float(words[0]), float(words[1]), words[2].lower()))
        assert all(0 <= a < b <= len(x) / fs + 1e-9 for a, b, _ in segments)
        frame_rows.extend(measure(x, fs, segments, name, 'native'))
        common = x if fs == 16000 else resample_poly(x, 160, 441, window=('kaiser', 5.0), padtype='constant')
        assert len(common) == math.ceil(len(x) * 16000 / fs)
        frame_rows.extend(measure(common, 16000, segments, name, 'common_16k'))
        resampling.append(dict(file=name, input_fs=int(fs), input_samples=len(x), common_samples=len(common),
                               common_pcm_float64_sha256=hashlib.sha256(common.tobytes()).hexdigest()))
    frames = pd.DataFrame(frame_rows)
    summaries = []
    for (name, mode, label), group in frames.groupby(['file', 'mode', 'label']):
        total = group.spectral_power_0_8000.sum()
        row = dict(file=name, mode=mode, label=label, frames=len(group), rms=float(np.sqrt(group.mean_square.mean())),
                   zero_fraction=float(group.zero_fraction.mean()), centroid_0_8000_hz=float(group.spectral_frequency_power.sum() / total) if total else np.nan)
        for low, high in BANDS:
            row[f'fraction_{low}_{high}'] = float(group[f'power_{low}_{high}'].sum() / total) if total else np.nan
        summaries.append(row)
    summary = pd.DataFrame(summaries)
    ratios = []
    for (name, mode), group in summary.groupby(['file', 'mode']):
        rms = dict(zip(group.label, group.rms))
        ratios.append(dict(file=name, mode=mode, v_sil_rms_ratio_db=20 * np.log10(rms['v'] / rms['sil']) if rms.get('v', 0) and rms.get('sil', 0) else np.nan))
    metrics = saved_results()
    metrics['device_name'] = metrics.file.str.split('_').str[0]
    metrics['file_group'] = metrics.file.str.split('_').str[1].str[0]
    groups = metrics.groupby(['protocol', 'device_name']).agg(files=('file', 'count'), average_mape=('average_mape', 'mean'),
               F0mean_mape=('F0mean_mape', 'mean'), F0std_mape=('F0std_mape', 'mean'), F0num_mape=('F0num_mape', 'mean')).reset_index()
    outputs = {'recording_conditions_frames.csv': frames, 'recording_conditions_features.csv': summary,
               'recording_conditions_energy.csv': pd.DataFrame(ratios), 'recording_conditions_saved_metrics.csv': metrics,
               'recording_conditions_groups.csv': groups}
    for name, table in outputs.items():
        table.to_csv(OUT / name, index=False)
    for name in NAMES:
        assert digest(REPO / 'TinHieuHuanLuyen' / name) == originals[name]['wav']
        assert digest(REPO / 'TinHieuHuanLuyen' / Path(name).with_suffix('.lab')) == originals[name]['lab']
    receipt = dict(scope='Descriptive training audio only; no F0 inference, tuning, test audio, Jev or H44',
                   python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, pandas=pd.__version__,
                   input_sha256=INPUTS, output_sha256={name: digest(OUT / name) for name in outputs},
                   original_data_preserved=True, resampling=resampling, frames=len(frames), feature_rows=len(summary),
                   metric_rows=len(metrics), grouping='Names only, not verified device/speaker/environment identities')
    (OUT / 'recording_conditions_receipt.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(pd.DataFrame(ratios).to_string(index=False))
    print(summary[summary.mode == 'common_16k'][['file', 'label', 'frames', 'rms', 'fraction_1000_4000', 'fraction_4000_8000']].to_string(index=False))
    print(groups[['protocol', 'device_name', 'average_mape']].to_string(index=False))


if __name__ == '__main__':
    main()
