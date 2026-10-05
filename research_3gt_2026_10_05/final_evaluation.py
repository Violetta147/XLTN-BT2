import datetime
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

import core
import standalone_pipeline as pipeline
from events import record
from notebook_helpers import attach_truth


def labeled(item, directory, stats_directory):
    # notebook_helpers dùng globals của notebook; inject đúng bộ đọc trước khi gọi.
    attach_truth.__globals__.update(np=np, read_segments=pipeline.read_segments, read_stats=pipeline.read_stats)
    return attach_truth(item, directory / Path(item['file']).with_suffix('.lab'),
                        stats_directory / Path(item['file']).with_suffix('.lab'))


def dataset_profile(items, directory, split):
    rows = []
    for item in items:
        fs, signal = pipeline.load_audio(directory / item['file'])
        spectrum = abs(np.fft.rfft(signal)) ** 2
        frequency = np.fft.rfftfreq(len(signal), 1 / fs)
        row = {'split': split, 'file': item['file'], 'fs': fs, 'duration_s': len(signal) / fs,
               'GT_mean': item['stats']['F0mean'], 'GT_std': item['stats']['F0std'], 'GT_num': item['stats']['F0num'],
               'band_above_1000_fraction': spectrum[frequency > 1000].sum() / spectrum.sum(),
               'clipped_fraction': (abs(signal) > .999).mean()}
        for label in ('v', 'uv', 'sil'):
            mask = item['labels'] == label
            row[label + '_frames'] = int(mask.sum())
            row[label + '_rms_median'] = float(np.median(item['rms'][mask]))
        row['V_to_SIL_rms_ratio_dB_proxy_not_SNR'] = (20 * np.log10(row['v_rms_median'] / row['sil_rms_median'])
                                                   if row['sil_rms_median'] > 0 else np.nan)
        row['sil_median_is_zero'] = row['sil_rms_median'] == 0
        rows.append(row)
    return rows


def main():
    frozen_path = core.RESULTS / 'frozen_config.json'
    frozen = json.loads(frozen_path.read_text(encoding='utf-8'))
    frozen_hash = core.sha256(frozen_path)
    for filename, key in [('core.py', 'inference_code_sha256'), ('results/candidate_registry.json', 'candidate_registry_sha256'),
                          ('results/selection_summary.json', 'selection_summary_sha256'), ('results/training_manifest.json', 'training_manifest_sha256')]:
        path = core.HERE / filename
        if not path.exists() and filename.endswith('training_manifest.json'):
            path = core.HERE / 'training_manifest.json'
        assert core.sha256(path) == frozen[key], (path, 'Changed after freeze')
    baseline = json.loads((core.RESULTS / 'baseline_summary.json').read_text(encoding='utf-8'))
    selected = json.loads((core.RESULTS / 'selection_summary.json').read_text(encoding='utf-8'))
    frames = sorted({x['config']['frame_ms'] for x in frozen['models'].values()})
    train = {frame: [labeled(pipeline.signal_features(path, frame), core.TRAIN, core.TRAIN_GT)
                     for path in sorted(core.TRAIN.glob('*.wav'))] for frame in frames}
    rows, fits = [], {}
    # So khớp gói notebook với baseline trước khi mở test.
    for model, spec in frozen['models'].items():
        config = spec['config']
        items = train[config['frame_ms']]
        fits[model] = pipeline.fit(items, config)
        assert all(np.isclose(fits[model][key], value, atol=1e-10) for key, value in spec['fitted'].items())
        result = pipeline.evaluate(items, config, fits[model])
        assert np.isclose(result.average_mape.mean(), selected[model]['train']['average_mape'], atol=1e-10)
        for item in items:
            prediction = pipeline.infer(item, config, fits[model])
            signal_only = {key: value for key, value in item.items() if key not in ('labels', 'stats', 'segments')}
            without_truth = pipeline.infer(signal_only, config, fits[model])
            assert np.array_equal(prediction[0], without_truth[0])
            assert np.allclose(prediction[1], without_truth[1], equal_nan=True)
        result['model'], result['version'], result['split'] = model, 'improved', 'train'
        rows.append(result)
    record('Kiểm chứng gói notebook trước khi mở TEST', '5 pipeline khớp train đã chốt và ngưỡng tới 1e-10; bỏ toàn bộ labels/stats/segments vẫn dự đoán giống hệt.',
           'Đủ điều kiện chạy một lượt test; không có chỉnh thuật toán sau freeze.')
    opened = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat(timespec='seconds')
    test_directory = core.REPO / 'TinHieuKiemThu'
    stats_directory = core.HERE / 'test_3gt'
    stats_directory.mkdir(exist_ok=True)
    access_path = core.RESULTS / 'test_access.json'
    if not access_path.exists():
        birth = datetime.datetime.fromtimestamp(stats_directory.stat().st_ctime, datetime.timezone(datetime.timedelta(hours=7)))
        access_path.write_text(json.dumps({'first_test_stats_directory_created_at': birth.isoformat(timespec='seconds'),
                                           'evaluation_attempt_at': opened, 'note': 'First attempt stopped after saving scores, due to zero SIL RMS in profile; no algorithm change.'}, indent=2), encoding='utf-8')
    for path in sorted((core.ROOT / '.validation-test-3gt').glob('*.lab')):
        shutil.copy2(path, stats_directory / path.name)
    assert len(list(stats_directory.glob('*.lab'))) == 4
    test_signals = {frame: [pipeline.signal_features(path, frame) for path in sorted(test_directory.glob('*.wav'))]
                    for frame in frames}
    predictions = {}
    for model, spec in frozen['models'].items():
        config = spec['config']
        reference_model = 'AMDF' if model == 'AMDF_no_energy' else model
        predictions[(model, 'improved')] = [pipeline.infer(item, config, fits[model]) for item in test_signals[config['frame_ms']]]
        reference = baseline[reference_model]
        predictions[(model, 'baseline')] = [pipeline.infer(item, reference['config'], reference['fit'])
                                             for item in test_signals[config['frame_ms']]]
    # Tất cả dự đoán đã cố định trước khi gắn ground truth test.
    test = {frame: [labeled(item, test_directory, stats_directory) for item in items]
            for frame, items in test_signals.items()}
    frame_rows = []
    for model, spec in frozen['models'].items():
        config = spec['config']
        items = test[config['frame_ms']]
        reference_model = 'AMDF' if model == 'AMDF_no_energy' else model
        for version in ('baseline', 'improved'):
            result = pd.DataFrame([pipeline.score_file(item, *prediction)
                                   for item, prediction in zip(items, predictions[(model, version)])])
            result['model'], result['version'], result['split'] = model, version, 'test'
            rows.append(result)
            for item, (pred, f0) in zip(items, predictions[(model, version)]):
                frame_rows.extend({'model': model, 'version': version, 'file': item['file'], 'time_s': time,
                                   'label': label, 'pred_v': bool(p), 'f0': float(value)}
                                  for time, label, p, value in zip(item['times'], item['labels'], pred, f0))
        reference = baseline[reference_model]
        original_train = pipeline.evaluate(train[config['frame_ms']], reference['config'], reference['fit'])
        original_train['model'], original_train['version'], original_train['split'] = model, 'baseline', 'train'
        rows.append(original_train)
    scores = pd.concat(rows, ignore_index=True)
    assert len(scores) == 5 * 2 * 2 * 4
    scores.to_csv(core.RESULTS / 'final_train_test_per_file.csv', index=False)
    pd.DataFrame(frame_rows).to_csv(core.RESULTS / 'final_test_frames.csv', index=False)
    profile = dataset_profile(train[25], core.TRAIN, 'train') + dataset_profile(test[25], test_directory, 'test')
    pd.DataFrame(profile).to_csv(core.RESULTS / 'final_dataset_profile.csv', index=False)
    summary = {}
    for model in frozen['models']:
        summary[model] = {}
        for version in ('baseline', 'improved'):
            summary[model][version] = {}
            for split in ('train', 'test'):
                subset = scores[(scores.model == model) & (scores.version == version) & (scores.split == split)]
                summary[model][version][split] = pipeline.summarize(subset)
            mape = summary[model][version]['test']['average_mape']
            summary[model][version]['final_score'] = 100 - mape
            summary[model][version]['grade_10'] = round((100 - mape) / 10, 1)
    assert np.isclose(summary['ACF']['baseline']['test']['average_mape'], 9.325770172805168, atol=1e-10)
    assert core.sha256(frozen_path) == frozen_hash
    gap = summary['ACF']['baseline']['train']['average_mape'] - summary['ACF']['baseline']['test']['average_mape']
    contributions = {metric: (summary['ACF']['baseline']['train'][metric + '_mape'] -
                             summary['ACF']['baseline']['test'][metric + '_mape']) / 3 for metric in ('F0mean', 'F0std', 'F0num')}
    result = {'test_opened_at_vietnam': opened, 'config_frozen_at_vietnam': frozen['frozen_at_vietnam'],
              'frozen_config_sha256': frozen_hash, 'no_test_based_changes': True, 'summary': summary,
              'baseline_acf_gap_pp': gap, 'gap_contribution_pp': contributions,
              'test_inputs': [{'file': path.name, 'wav_sha256': core.sha256(path),
                               'segment_sha256': core.sha256(path.with_suffix('.lab')),
                               'stats_sha256': core.sha256(stats_directory / path.with_suffix('.lab').name)}
                              for path in sorted(test_directory.glob('*.wav'))]}
    (core.RESULTS / 'final_evaluation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    brief = '; '.join(f'{model}: test {x["baseline"]["test"]["average_mape"]:.2f}→{x["improved"]["test"]["average_mape"]:.2f}%'
                      for model, x in summary.items())
    record('Đánh giá TEST sau freeze, không chỉnh tham số theo kết quả', brief,
           'Lưu cả cải thiện và suy giảm; lựa chọn giữ cấu hình dựa trên train/nested LOFO đã hoàn thành trước test.')
    print(brief)
    print('ACF gap decomposition:', gap, contributions)


if __name__ == '__main__':
    main()
