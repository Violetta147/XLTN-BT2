import hashlib
import itertools
import json
import math
import os
import platform
import warnings
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
from pathlib import Path

os.environ['MPLBACKEND'] = 'Agg'
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.io import wavfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
RESULTS = HERE / 'results'
FIGURES = HERE / 'figures'
LABELS = ('v', 'uv', 'sil')
POLICY = {
    'scope': 'Read-only descriptive WAV/LAB quality audit of both splits; no F0 inference, fitting or tuning',
    'reference_grid': 'full frames, length round(fs*0.025), hop round(fs*0.010), center label',
    'exact_clipping': 'native integer min/max rails; float abs>=1',
    'near_rail': 'abs(normalized PCM)>=0.99; descriptive flag, not proof of clipping',
    'segment_energy': 'RMS from segment interiors with fixed 20 ms guard; exact decimal LAB boundaries mapped by ceil(time*fs); no denoising',
    'energy_ratio': '20log10(interior V RMS / interior SIL RMS); energy separation proxy, not clean-reference SNR',
    'duplicates': 'whole-file SHA256 and exact native PCM SHA256 including fs/dtype/shape; no near-duplicate or speaker claim',
    'stats': 'report original segment LAB and current 3GT separately, without changing either',
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def parse_lab(path):
    segments, stats, issues = [], {}, []
    for line_number, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        words = line.split()
        if not words:
            continue
        try:
            if words[0] in ('F0mean', 'F0std', 'F0num'):
                if words[0] in stats:
                    issues.append(f'duplicate statistic at line {line_number}')
                stats[words[0]] = float(words[1])
                if len(words) != 2 or not math.isfinite(stats[words[0]]) or stats[words[0]] <= 0:
                    issues.append(f'invalid statistic at line {line_number}')
            else:
                a, b, label = float(words[0]), float(words[1]), words[2].lower()
                if len(words) != 3 or not (math.isfinite(a) and math.isfinite(b) and 0 <= a < b) or label not in LABELS:
                    issues.append(f'invalid segment at line {line_number}')
                segments.append((a, b, label))
        except (ValueError, IndexError):
            issues.append(f'unparseable line {line_number}')
    return segments, stats, issues


def longest_true_run(mask):
    edges = np.diff(np.r_[False, mask, False].astype(np.int8))
    return int(np.max(np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1), initial=0))


def audit_file(path, split):
    stats_path = REPO / 'research_3gt_2026_10_05' / f'{split}_3gt' / path.with_suffix('.lab').name
    segments, original_stats, issues = parse_lab(path.with_suffix('.lab'))
    stat_segments, reference_stats, stat_issues = parse_lab(stats_path)
    issues += [f'3GT: {issue}' for issue in stat_issues]
    if stat_segments or set(reference_stats) != {'F0mean', 'F0std', 'F0num'}:
        issues.append('3GT is not exactly the three expected file statistics')
    if reference_stats.get('F0num', 0) % 1:
        issues.append('noninteger reference F0num')
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        fs, pcm = wavfile.read(path)
    if pcm.ndim != 1:
        raise ValueError(f'Unsupported audit input: expected mono, got {pcm.shape}: {path}')
    if np.issubdtype(pcm.dtype, np.integer):
        limits = np.iinfo(pcm.dtype)
        # PCM uint8 is unsigned with midpoint silence.
        if pcm.dtype == np.uint8:
            audio = (pcm.astype(float) - 128) / 128
        else:
            audio = pcm.astype(float) / max(abs(limits.min), limits.max)
        rails = (pcm == limits.min) | (pcm == limits.max)
    else:
        audio = pcm.astype(float)
        rails = np.abs(audio) >= 1
    duration = len(pcm) / fs
    gaps = sum(max(0., c - b) for (_, b, _), (c, _, _) in zip(segments, segments[1:]))
    overlaps = sum(max(0., b - c) for (_, b, _), (c, _, _) in zip(segments, segments[1:]))
    if any(b > duration + 1/fs for _, b, _ in segments):
        issues.append('segment extends beyond WAV by more than one sample')
    if any(c < a for (a, _, _), (c, _, _) in zip(segments, segments[1:])):
        issues.append('segments out of time order')
    length, hop = round(fs * .025), round(fs * .010)
    starts = np.arange(0, max(0, len(pcm) - length + 1), hop)
    times = (starts + length / 2) / fs
    frame_labels = [next((lab for a, b, lab in segments if a <= t < b), 'unknown') for t in times]
    near = np.abs(audio) >= .99
    rms = float(np.sqrt(np.mean(audio ** 2)))
    header = json.dumps({'fs': int(fs), 'dtype': str(pcm.dtype), 'shape': list(pcm.shape)}, sort_keys=True).encode()
    row = dict(split=split, file=path.name, fs=int(fs), channels=1, dtype=str(pcm.dtype),
               samples=len(pcm), duration_s=duration, finite_audio=bool(np.isfinite(audio).all()),
               peak_abs=float(np.max(np.abs(audio))), rms=rms,
               rms_dbfs=20*math.log10(rms) if rms else None,
               dc_mean=float(np.mean(audio)), exact_zero_samples=int((pcm == 0).sum()),
               rail_samples=int(rails.sum()), near_rail_samples=int(near.sum()),
               longest_near_rail_run_samples=longest_true_run(near),
               start_unlabeled_ms=1000*segments[0][0] if segments else 1000*duration,
               internal_gap_ms=1000*gaps, overlap_ms=1000*overlaps,
               tail_unlabeled_ms=1000*max(0., duration-segments[-1][1]) if segments else 1000*duration,
               frame_count=len(times), unknown_frames=frame_labels.count('unknown'),
               segment_count=len(segments), lab_issue_count=len(issues),
               lab_issues=json.dumps(issues, ensure_ascii=False),
               decode_warnings=json.dumps([str(w.message) for w in caught]),
               wav_sha256=digest(path), segment_lab_sha256=digest(path.with_suffix('.lab')),
               stats_lab_sha256=digest(stats_path), pcm_sha256=hashlib.sha256(header+pcm.tobytes()).hexdigest())
    details, energies = [], {label: [] for label in LABELS}
    for number, (a, b, label) in enumerate(segments, 1):
        lo = max(0, int(((Decimal(str(a))+Decimal('.020'))*fs).to_integral_value(rounding=ROUND_CEILING)))
        hi = min(len(audio), int(((Decimal(str(b))-Decimal('.020'))*fs).to_integral_value(rounding=ROUND_CEILING)))
        interior = audio[lo:hi] if hi > lo else np.array([])
        if label in energies:
            energies[label].append(interior)
        details.append(dict(split=split, file=path.name, segment=number, start_s=a, end_s=b,
                            label=label, interior_samples=len(interior),
                            interior_rms=float(np.sqrt(np.mean(interior**2))) if len(interior) else None))
    for label in LABELS:
        values = np.concatenate(energies[label]) if energies[label] else np.array([])
        row[f'{label}_seconds'] = sum(b-a for a,b,lab in segments if lab == label)
        row[f'{label}_frames'] = frame_labels.count(label)
        row[f'{label}_interior_samples'] = len(values)
        row[f'{label}_interior_rms'] = float(np.sqrt(np.mean(values**2))) if len(values) else None
    v, sil = row['v_interior_rms'], row['sil_interior_rms']
    row['v_sil_energy_ratio_db'] = 20*math.log10(v/sil) if v and sil else None
    for key in ('F0mean', 'F0std', 'F0num'):
        row[f'original_{key}'] = original_stats.get(key)
        row[f'reference_{key}'] = reference_stats.get(key)
    row['reference_count_minus_v_grid'] = reference_stats.get('F0num', 0)-row['v_frames']
    return row, details, (audio, fs, segments)


def table(frame):
    rows = ['| '+' | '.join(frame.columns)+' |', '| '+' | '.join(['---']*len(frame.columns))+' |']
    for values in frame.itertuples(index=False, name=None):
        rows.append('| '+' | '.join('—' if pd.isna(v) else f'{v:.4g}' if isinstance(v, float) else str(v) for v in values)+' |')
    return '\n'.join(rows)


def main():
    RESULTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    rows, segments, signals, inputs = [], [], {}, []
    for split, folder in (('train', 'TinHieuHuanLuyen'), ('test', 'TinHieuKiemThu')):
        paths = sorted((REPO / folder).glob('*.wav'))
        for path in paths:
            row, detail, signal = audit_file(path, split)
            rows.append(row)
            segments.extend(detail)
            signals[(split, path.name)] = signal
            for source in (path, path.with_suffix('.lab'), REPO / 'research_3gt_2026_10_05' / f'{split}_3gt' / path.with_suffix('.lab').name):
                inputs.append({'path': source.relative_to(REPO).as_posix(), 'sha256': digest(source)})
    frame = pd.DataFrame(rows)
    pairs = []
    for left, right in itertools.combinations(rows, 2):
        pairs.append(dict(left=f"{left['split']}/{left['file']}", right=f"{right['split']}/{right['file']}",
                          cross_split=left['split'] != right['split'],
                          identical_wav=left['wav_sha256'] == right['wav_sha256'],
                          identical_native_pcm=left['pcm_sha256'] == right['pcm_sha256']))
    frame.to_csv(RESULTS/'dataset_quality_per_file.csv', index=False)
    pd.DataFrame(segments).to_csv(RESULTS/'dataset_quality_segments.csv', index=False)
    pd.DataFrame(pairs).to_csv(RESULTS/'dataset_quality_duplicate_pairs.csv', index=False)
    figure, axes = plt.subplots(4, 2, figsize=(13, 10), sharey=True)
    for ax, row in zip(axes.T.flat, rows):
        audio, fs, labels = signals[(row['split'],row['file'])]
        step = max(1, len(audio)//2500)
        ax.plot(np.arange(0, len(audio), step)/fs, audio[::step], lw=.5, color='#173c58')
        for a,b,lab in labels:
            ax.axvspan(a,b,color={'v':'#4ab68c','uv':'#e5a346','sil':'#b8bec5'}.get(lab,'red'), alpha=.23)
        ax.set(title=f"{row['split']}: {row['file']} ({fs} Hz)", xlabel='Time (s)', ylabel='PCM / full scale', ylim=(-1,1))
    figure.suptitle('Dataset QA only; green V, orange UV, grey SIL. Display decimated; peaks measured on all samples.')
    figure.tight_layout(rect=(0,0,1,.965))
    for suffix in ('png','svg'):
        figure.savefig(FIGURES/f'dataset_quality_waveforms.{suffix}', dpi=160)
    plt.close(figure)
    total = float(frame.duration_s.sum())
    report = f'''# Kiểm tra chất lượng bộ dữ liệu BT2 hiện tại

Đọc mới {len(frame)} WAV và {len(inputs)-len(frame)} LAB, tổng {total:.6f} giây. Đây là kiểm tra dữ liệu mô tả, không chạy thuật toán F0, không fit/chọn tham số, không sửa WAV/LAB. Test được đọc chỉ cho QA; kết quả này không được dùng để tune mô hình rồi gọi test là độc lập. Không gọi Jev/Gemini và không retry System One.

## Kết quả định dạng và tín hiệu

{table(frame[['split','file','fs','duration_s','peak_abs','rail_samples','near_rail_samples','tail_unlabeled_ms','unknown_frames']])}

Tất cả WAV được giải mã; xem `decode_warnings` trong CSV để giữ cả cảnh báo chunk phụ. {int(frame.finite_audio.sum())}/{len(frame)} có mẫu hữu hạn. Tổng mẫu chạm min/max PCM: {int(frame.rail_samples.sum())}; tổng mẫu có biên độ tuyệt đối ≥99% full scale: {int(frame.near_rail_samples.sum())}. Không thấy clipping theo hai dấu hiệu này **không chứng minh** không có bão hòa analog, nén hoặc xử lý trước đó. RMS và DC được đo ở toàn bộ mẫu, không từ hình vẽ đã giảm điểm hiển thị.

Nhãn: tổng lỗi parse/bounds {int(frame.lab_issue_count.sum())}; gap nội bộ {frame.internal_gap_ms.sum():.6f} ms; overlap {frame.overlap_ms.sum():.6f} ms. Phần đuôi chưa phủ nhãn báo riêng; không tự điền SIL. Không có khung `unknown` trên grid hiện tại chỉ cho biết tâm khung được phủ, không chứng nhận mọi sample hoặc mọi biên nhãn đúng. Grid25/10 là quy ước QA hiện tại, không bắt các thuật toán phải dùng cửa sổ đó.

## Nhãn đoạn và hai bộ thống kê

{table(frame[['split','file','original_F0mean','reference_F0mean','original_F0std','reference_F0std','v_frames','reference_F0num','reference_count_minus_v_grid']])}

LAB cạnh WAV có V/UV/SIL theo đoạn và mean/std cả file. LAB trong `research_3gt_2026_10_05/train_3gt` và `test_3gt` có mean/std/count, đang được dùng để chấm. Có giá trị khác nhau giữa hai nguồn; giữ nguyên và ghi hai cột, **không kết luận nguồn nào sai**. README dữ liệu chỉ giải thích định dạng/đơn vị, chưa cho quy trình tạo F0 reference, grid/thời điểm khung, quyết định V/UV, xử lý biên, hoặc ddof khi tính độ lệch chuẩn. Báo cáo trước cũng ghi thiếu quy trình này: `research_3gt_2026_10_05/PHAN_TICH_VA_CAI_TIEN_BT2_2026-10-05.md`, mục4.3–4.4. Truy xuất nguồn gốc 3GT chưa được chứng nhận lại từ phép đo gốc.

`reference_count_minus_v_grid` là chênh lệch định nghĩa cần đối chiếu, không phải số nhãn sai. Hai bộ có thể dùng khung/cách xác định hữu thanh khác nhau. Trong 16 LAB đã đọc **không có F0 chuẩn từng timestamp**; ba thống kê không thể chứng nhận contour cao độ của từng khung.

## Mức tiếng trong các vùng nhãn

{table(frame[['split','file','v_interior_rms','sil_interior_rms','v_sil_energy_ratio_db']])}

RMS là căn trung bình bình phương biên độ. Bỏ cố định20ms ở mỗi biên đoạn để giảm ảnh hưởng chuyển tiếp; đoạn quá ngắn không góp mẫu. Tỷ lệ dB trên đây chỉ là proxy độ tách biệt năng lượng V/SIL, **không phải SNR** vì SIL có thể chứa âm nền, hơi thở hoặc nhãn chưa đúng, còn vùng V chứa cả tiếng nói lẫn nhiễu. Không dùng ngưỡng tỷ lệ này để tuyên bố nhãn sai hay tự bỏ file. Báo cáo chi tiết mọi đoạn trong `results/dataset_quality_segments.csv` để chọn đoạn nghe/rà bằng tay; chưa thực hiện nghe hoặc chỉnh nhãn trong QA này.

## Độ đa dạng và trùng lặp

Train có {int((frame.split=='train').sum())} file/{frame.loc[frame.split=='train','duration_s'].sum():.6f}s; test có {int((frame.split=='test').sum())} file/{frame.loc[frame.split=='test','duration_s'].sum():.6f}s. So {len(pairs)} cặp (16 cặp train–test): {sum(p['identical_wav'] for p in pairs)} trùng byte WAV, {sum(p['identical_native_pcm'] for p in pairs)} trùng native PCM cùng rate/shape/dtype. Điều này chưa loại trừ bản thu cùng nội dung đã đổi gain, resample, cắt dịch hoặc cùng người nói.

Tên file có F/M và phone/studio, mỗi split chỉ một file trong mỗi ô. Không có speaker_id/utterance_id/session_id đã xác minh trong metadata đang đọc; không gọi8file là8người. Phone16kHz và studio44.1kHz gắn với rate khác nhau, chưa thể tách riêng hiệu ứng microphone/rate/nội dung. Tổng thời lượng rất nhỏ; kết quả trên bốn train không chứng minh tổng quát hóa rộng, nhất là đã dùng nhiều vòng nghiên cứu trên chúng.

## Các bước để kiểm tra sâu hơn

1. Rà tay từng đoạn: nghe WAV và xem waveform/phổ ở biên V/UV/SIL, ghi timestamp, người rà, lý do và giữ nhãn gốc. Sửa nhãn phải có phiên bản riêng và chấm lại theo cùng protocol.
2. Đối chiếu nguồn3GT: cần cách tạo F0mean/std/num, length/hop/time_origin, đếm F0 hợp lệ, làm tròn và ddof. Với std20.6Hz, sai số0.412Hz đã tương đương2% lỗi std; mục tiêu thấp cần reference đủ rõ. Đây là phép tính, không ước lượng nhiễu nhãn đã đo.
3. Có contour F0 reference độc lập theo thời gian, được rà chu kỳ ở các đoạn khó; output ACF/AMDF/Praat chỉ là ứng viên để reviewer đối chiếu. Praat manual lưu ý kết quả voice analysis phụ thuộc pitch settings và phần âm thanh được phân tích: [Voice](https://www.fon.hum.uva.nl/praat/manual/Voice.html), đọc HTML ngày2026-10-07. Vì vậy phải lưu cấu hình và đoạn thời gian, không lấy kết quả một tool làm chuẩn mặc nhiên.
4. Bổ sung dữ liệu và metadata người nói/nội dung/phiên/thiết bị; thiết kế phần đánh giá mới tách người nói hoặc phiên thật sự. Đăng ký protocol trước đánh giá mới, không loại file khó dựa trên MAPE để tạo điểm đẹp.

Chưa có một điểm “chất lượng dataset” tổng hợp: phần định dạng/duplicate/rails có kiểm tra bằng code; độ đúng ngữ âm/cao độ và độc lập người nói cần nguồn/rà tay bổ sung. Cải thiện MAPE và chất lượng reference là hai việc cần theo dõi riêng. Verifier lần đầu phát hiện chênh một mẫu ở năm đoạn do biểu diễn số thập phân bằng float khi áp dụng guard20ms. Log lỗi được giữ; bản hiện tại dùng Decimal để ánh xạ biên chính xác, verifier dùng Fraction độc lập. Đây là sửa cách đo năng lượng QA, không sửa dữ liệu hay MAPE.

## Tái lập

Lệnh: `C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/dataset_quality_audit.py`. Policies, phiên bản runtime, input SHA256 và output SHA256: `results/dataset_quality_manifest.json`. CSV và PNG/SVG giữ dữ liệu đo thật; WAV/LAB không đổi. Verifier đọc PCM độc lập bằng thư viện wave, đối chiếu samples/rate/rails/hashes/grid/gaps/overlaps và profile train trước đó, không chạy F0.
'''
    (HERE/'DATASET_QUALITY_REPORT.md').write_text(report, encoding='utf-8')
    outputs = [RESULTS/f'dataset_quality_{name}.csv' for name in ('per_file','segments','duplicate_pairs')]
    outputs += [HERE/'DATASET_QUALITY_REPORT.md'] + [FIGURES/f'dataset_quality_waveforms.{s}' for s in ('png','svg')]
    write_json(RESULTS/'dataset_quality_manifest.json', {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'policy': POLICY,
        'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
        'generator_sha256': digest(__file__), 'inputs': inputs,
        'outputs': [{'path': p.relative_to(HERE).as_posix(), 'sha256': digest(p)} for p in outputs],
        'totals': {'files': len(frame), 'duration_s': total, 'rail_samples': int(frame.rail_samples.sum()),
                   'lab_issues': int(frame.lab_issue_count.sum()), 'pair_count': len(pairs)},
    })
    print(frame[['split','file','duration_s','rail_samples','tail_unlabeled_ms','v_sil_energy_ratio_db']].to_string(index=False))
    print('Wrote read-only QA outputs; no F0 model or parameter selection.')


if __name__ == '__main__':
    main()
