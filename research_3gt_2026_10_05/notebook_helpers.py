def attach_truth(item, segment_path, stats_path):
    labels = np.array([next((lab for a, b, lab in read_segments(segment_path) if a <= t < b), 'unknown')
                       for t in item['times']])
    return {**item, 'labels': labels, 'segments': read_segments(segment_path), 'stats': read_stats(stats_path)}


def grading_table(rows):
    columns = {'file': 'File', 'F0mean_mape': 'MAPE F0mean (%)', 'F0std_mape': 'MAPE F0std (%)',
               'F0num_mape': 'MAPE F0num (%)', 'average_mape': 'Average MAPE (%)'}
    table = rows[list(columns)].rename(columns=columns).copy()
    total = {'File': 'TỔNG CỘNG', **{column: table[column].mean() for column in list(columns.values())[1:]}}
    assert len(rows) == 4 and np.isfinite(rows[list(columns)[1:]].to_numpy()).all()
    assert np.allclose(rows.average_mape, rows[['F0mean_mape', 'F0std_mape', 'F0num_mape']].mean(axis=1))
    return pd.concat([table, pd.DataFrame([total])], ignore_index=True)


def show_results(rows, title):
    print(title)
    display(grading_table(rows).round(2))
    display(rows[['file', 'F0mean', 'F0std', 'F0num', 'macro_f1', 'recall_v', 'recall_uv',
                  'balanced_accuracy', 'false_voiced_sil']].round(4))


def threshold_plot(items, config, fitted, title):
    algorithm = config['algorithm']
    fig, axes = plt.subplots(1, 2 if config.get('energy', False) else 1, figsize=(12, 4), squeeze=False)
    ax = axes[0, 0]
    for label, color in [('v', 'tab:blue'), ('uv', 'tab:orange')]:
        values = np.concatenate([x[algorithm + '_score'][x['labels'] == label] for x in items])
        ax.hist(values, bins=40, density=True, alpha=.45, label=label.upper(), color=color)
    ax.axvline(fitted['pitch_threshold'], color='black', ls='--', label='Ngưỡng từ TRAIN')
    if config.get('threshold_method') == 'gmm':
        scores = np.concatenate([x[algorithm + '_score'][np.isin(x['labels'], ('v', 'uv'))] for x in items])
        model = GMM['fit_gmm_threshold'](scores)
        grid = np.linspace(scores.min(), scores.max(), 500)
        for mean, std, weight in zip(model['means'], model['stds'], model['weights']):
            ax.plot(grid, weight * GMM['normal_pdf'](grid, mean, std))
    elif config.get('threshold_method') == 'hist_classes' or algorithm == 'ACF':
        v = np.concatenate([x[algorithm + '_score'][x['labels'] == 'v'] for x in items])
        u = np.concatenate([x[algorithm + '_score'][x['labels'] == 'uv'] for x in items])
        fn = ACF['class_histogram_threshold'] if algorithm == 'ACF' else AMDF['histogram_threshold']
        _, centers, hv, hu = fn(v, u)
        ax.plot(centers, hv, color='tab:blue')
        ax.plot(centers, hu, color='tab:orange')
    ax.set(title=title + ' — phân bố score TRAIN', xlabel=algorithm + ' score', ylabel='Density')
    ax.legend()
    if config.get('energy', False):
        ax = axes[0, 1]
        for label in ('v', 'sil'):
            values = np.concatenate([x['relative_rms'][x['labels'] == label] for x in items])
            ax.hist(values, bins=45, alpha=.5, density=True, label=label.upper())
        ax.axvline(fitted['energy_threshold'], color='black', ls='--', label='Ngưỡng RMS TRAIN')
        ax.set(xlabel='RMS / percentile 95 của RMS từng file', ylabel='Density', title='Cổng năng lượng')
        ax.legend()
    fig.tight_layout()
    plt.show()


def curve_examples(items, config):
    item = items[0]
    fs, signal = load_audio(TRAIN_DIR / item['file'])
    length, hop = round(fs * config['frame_ms'] / 1000), round(fs * .010)
    fig, axes = plt.subplots(2, 2, figsize=(12, 6))
    for row, label in enumerate(('v', 'uv')):
        indices = np.flatnonzero(item['labels'] == label)
        index = int(indices[len(indices) // 2])
        frame = signal[index * hop:index * hop + length]
        axes[row, 0].plot(np.arange(length) / fs * 1000, frame)
        axes[row, 0].set(title=item['file'] + ' — ' + label.upper(), xlabel='Thời gian trong khung (ms)')
        if config['algorithm'] == 'ACF':
            _, lag, curve = ACF['detect_pitch_acf'](frame, fs)
            x = np.arange(len(curve)) / fs * 1000
        else:
            _, _, lag, lags, curve = AMDF['deepest_local_dip'](frame, fs)
            x = lags / fs * 1000
        axes[row, 1].plot(x, curve)
        axes[row, 1].axvline(lag / fs * 1000, ls='--', color='red', label='Ứng viên mạnh nhất riêng khung')
        axes[row, 1].set(xlim=(1000 / 400, 1000 / 70), xlabel='Độ trễ (ms)', title=config['algorithm'])
        axes[row, 1].legend(fontsize=8)
    fig.tight_layout()
    plt.show()


def detailed_plot(item, config, fitted, signal_path, title):
    pred, f0 = infer(item, config, fitted)
    fs, signal = load_audio(signal_path)
    fig, axes = plt.subplots(4, 1, figsize=(13, 10), sharex=True)
    axes[0].plot(np.arange(len(signal)) / fs, signal, lw=.5)
    axes[0].set(ylabel='Biên độ', title=title + ' — ' + item['file'])
    axes[1].plot(item['times'], item[config['algorithm'] + '_score'], lw=.8)
    axes[1].axhline(fitted['pitch_threshold'], color='red', ls='--')
    axes[1].set(ylabel='Score chu kỳ')
    if config.get('energy', False):
        energy_ax = axes[1].twinx()
        energy_ax.plot(item['times'], item['relative_rms'], alpha=.3, color='green')
        energy_ax.axhline(fitted['energy_threshold'], color='green', ls=':')
        energy_ax.set(ylabel='RMS tương đối')
    truth_v = item['labels'] == 'v'
    axes[2].step(item['times'], pred.astype(int), where='mid', label='Dự đoán V')
    axes[2].step(item['times'], truth_v.astype(int), where='mid', ls='--', label='Nhãn LAB V (chỉ đối chiếu)')
    axes[2].set(ylabel='V / không V', yticks=[0, 1])
    axes[2].legend(fontsize=8)
    axes[3].scatter(item['times'], f0, s=9, label='F0 dự đoán')
    axes[3].axhline(item['stats']['F0mean'], color='black', ls='--', label='GT mean của file')
    axes[3].axhspan(item['stats']['F0mean'] - item['stats']['F0std'],
                    item['stats']['F0mean'] + item['stats']['F0std'], alpha=.1, color='black',
                    label='GT mean ± std; không phải GT từng khung')
    axes[3].set(ylabel='F0 (Hz)', xlabel='Thời gian (s)', ylim=(60, 410))
    axes[3].legend(fontsize=8)
    for ax in axes:
        ax.grid(alpha=.2)
    fig.tight_layout()
    plt.show()


def greedy_period_evidence(items):
    item = next(x for x in items if x['file'].lower() == 'phone_f1.wav')
    fs, signal = load_audio(TRAIN_DIR / item['file'])
    frame_len, hop_len = round(fs * .025), round(fs * .010)
    centers = (.5725, .5925, .6025)
    rows, examples = [], []
    for center in centers:
        frame_index = int(np.argmin(abs(item['times'] - center)))
        start = frame_index * hop_len
        frame = signal[start:start + frame_len]
        score, lag, curve = ACF['detect_pitch_acf'](frame, fs)
        grid = np.arange(max(1, math.ceil(fs / 400)), min(len(frame) - 2, math.floor(fs / 70)) + 1)
        peaks = grid[(curve[grid] >= curve[grid - 1]) & (curve[grid] >= curve[grid + 1])]
        chosen = int(peaks[np.argmax(curve[peaks])])
        for rank, peak in enumerate(peaks):
            refined = refine_lag(curve, int(peak), float(peak))
            rows.append({'Tâm khung (s)': float(item['times'][frame_index]),
                         'Nhãn LAB': item['labels'][frame_index].upper(),
                         'Đỉnh theo độ trễ': f'{rank + 1} (~{rank + 1}T)',
                         'Độ trễ nguyên (mẫu)': int(peak),
                         'Độ trễ nội suy (ms)': 1000 * refined / fs,
                         'F0 từ đỉnh (Hz)': fs / refined,
                         'ACF score': float(curve[peak]),
                         'Score_max − score': float(score - curve[peak]),
                         'Bản cũ chọn': 'CÓ' if peak == chosen else ''})
        examples.append((frame_index, frame, curve, peaks, chosen, fs / lag))
    evidence = pd.DataFrame(rows)
    printable = evidence.copy()
    for key in ('ACF score', 'Score_max − score'):
        printable[key] = printable[key].map(lambda x: f'{x:.10f}')
    for key in ('Độ trễ nội suy (ms)', 'F0 từ đỉnh (Hz)'):
        printable[key] = printable[key].map(lambda x: f'{x:.6f}')
    print('BẰNG CHỨNG TỪ WAV TRAIN: ACF gốc, khung 25 ms, bước 10 ms')
    display(printable)
    first = evidence[evidence['Tâm khung (s)'] == evidence['Tâm khung (s)'].iloc[0]]
    short = first.iloc[0]
    picked = first[first['Bản cũ chọn'] == 'CÓ'].iloc[0]
    print(f'Khung {short["Tâm khung (s)"]:.4f}s: đỉnh sớm khoảng {short["F0 từ đỉnh (Hz)"]:.6f} Hz; '
          f'bản cũ chọn khoảng {picked["F0 từ đỉnh (Hz)"]:.6f} Hz.')
    print(f'Đỉnh được chọn cao hơn đỉnh sớm chỉ {short["Score_max − score"]:.10f} điểm ACF.')
    index, frame, curve, peaks, chosen, old_f0 = examples[0]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    axes[0].plot(np.arange(len(frame)) / fs * 1000, frame, color='tab:blue')
    axes[0].set(title=f'phone_F1 — tâm khung {item["times"][index]:.4f}s',
                xlabel='Thời gian trong khung (ms)', ylabel='Biên độ')
    lo, hi = max(1, math.ceil(fs / 400)), min(len(frame) - 2, math.floor(fs / 70))
    grid = np.arange(lo, hi + 1)
    axes[1].plot(grid / fs * 1000, curve[grid], color='tab:blue')
    for rank, peak in enumerate(peaks):
        color = 'tab:red' if peak == chosen else ('tab:green' if rank == 0 else 'tab:gray')
        delay = peak / fs * 1000
        axes[1].scatter(delay, curve[peak], color=color, s=40, zorder=3)
        axes[1].axvline(delay, color=color, ls='--', alpha=.5)
        axes[1].annotate(f'~{rank + 1}T\n{curve[peak]:.7f}', (delay, curve[peak]),
                         xytext=(delay, .45), ha='center', color=color,
                         arrowprops={'arrowstyle': '->', 'color': color})
    axes[1].set(title=f'Đỉnh đỏ: bản cũ chọn {old_f0:.2f} Hz', xlabel='Độ trễ (ms)', ylabel='ACF chuẩn hóa')
    for ax in axes:
        ax.grid(alpha=.2)
    fig.tight_layout()
    plt.show()
    original_config = {'algorithm': 'ACF', 'frame_ms': 25}
    original_fit = fit(items, original_config)
    original_row = score_file(item, *infer(item, original_config, original_fit))
    display(pd.DataFrame([
        {'Nguồn': '3GT của thầy', 'F0mean (Hz)': item['stats']['F0mean'],
         'F0std (Hz)': item['stats']['F0std'], 'F0num': item['stats']['F0num']},
        {'Nguồn': 'ACF gốc: toàn bộ dự đoán hữu hạn', 'F0mean (Hz)': original_row['F0mean'],
         'F0std (Hz)': original_row['F0std'], 'F0num': original_row['F0num']}
    ]).round(6))
    print(f'MAPE F0std của cả file = {original_row["F0std_mape"]:.6f}%.')
    print('Bảng cả file gồm cả lỗi bội chu kỳ và lỗi UV/SIL; không quy toàn bộ MAPE std cho ba khung minh họa.')
    return evidence


def silence_f0_evidence(train_by_frame, configs, fitted_models):
    items = train_by_frame[25]
    item = next(x for x in items if x['file'].lower() == 'phone_f1.wav')
    config = {'algorithm': 'ACF', 'frame_ms': 25}
    fitted = fit(items, config)
    pred, f0 = infer(item, config, fitted)
    finite = np.isfinite(f0)
    false_sil = finite & (item['labels'] == 'sil')
    indices = np.flatnonzero(false_sil)
    assert len(indices), 'Không tìm thấy F0 trong SIL của baseline này'
    fs, signal = load_audio(TRAIN_DIR / item['file'])
    segments = read_segments(TRAIN_DIR / Path(item['file']).with_suffix('.lab'))
    length, hop = round(fs * .025), round(fs * .010)
    rows = []
    for index in indices:
        frame = signal[index * hop:index * hop + length]
        rows.append({'Tâm khung (s)': item['times'][index], 'Nhãn LAB': 'SIL',
                     'Sát ranh giới nhãn': any(abs(item['times'][index] - edge) < .0125
                                               for a, b, _ in segments for edge in (a, b)),
                     'ACF score': item['ACF_score'][index], 'Ngưỡng ACF TRAIN': fitted['pitch_threshold'],
                     'RMS khung': float(np.sqrt(np.mean(frame ** 2))),
                     'RMS tương đối': item['relative_rms'][index],
                     'F0 bản cũ (Hz)': f0[index], 'Bản cũ nhận V': bool(pred[index])})
    evidence = pd.DataFrame(rows)
    print('NHẬN NHẦM KHOẢNG LẶNG — ACF gốc 25 ms, phone_F1 TRAIN')
    display(evidence.round(8))
    mean, variance = float(f0[finite].mean()), float(f0[finite].var())
    contribution = float(np.sum((f0[false_sil] - mean) ** 2) / finite.sum())
    print(f'{false_sil.sum()} F0 trong SIL; chiếm {100 * contribution / variance:.6f}% phương sai quanh mean chung.')
    diagnostic_rows = []
    for name, mask in [('Bản cũ: mọi F0 hữu hạn (điểm chính thức)', finite),
                       ('Chẩn đoán: bỏ riêng F0 có nhãn SIL thật', finite & ~false_sil)]:
        values = f0[mask]
        std = float(values.std())
        diagnostic_rows.append({'Phép tính': name, 'F0mean (Hz)': values.mean(), 'F0std (Hz)': std,
                                'F0num': len(values), 'MAPE F0std (%)': 100 * abs(std - item['stats']['F0std']) / item['stats']['F0std']})
    display(pd.DataFrame(diagnostic_rows).round(6))
    print('Bỏ SIL thật chỉ đo ảnh hưởng thống kê; không dùng nhãn thật để sửa dự đoán hay điền bảng chấm điểm.')
    comparison = []
    for name, cfg, fitted_cfg, model_items in [('ACF gốc 25 ms', config, fitted, items)] + [
            (name, cfg, fitted_models[name], train_by_frame[cfg['frame_ms']]) for name, cfg in configs.items()]:
        model_item = next(x for x in model_items if x['file'].lower() == 'phone_f1.wav')
        model_pred, model_f0 = infer(model_item, cfg, fitted_cfg)
        sil = model_item['labels'] == 'sil'
        comparison.append({'Mô hình / cấu hình': name, 'Khung (ms)': cfg['frame_ms'],
                           'Có cổng năng lượng': cfg.get('energy', False),
                           'Ngưỡng RMS tương đối': fitted_cfg['energy_threshold'] if cfg.get('energy', False) else np.nan,
                           'Số khung SIL theo LAB': int(sil.sum()), 'SIL nhận V': int((sil & model_pred).sum()),
                           'F0 hữu hạn trong SIL': int((sil & np.isfinite(model_f0)).sum()),
                           'F0std toàn file (Hz)': float(np.nanstd(model_f0))})
    display(pd.DataFrame(comparison).round(6))
    print('So sánh cả pipeline; không quy toàn bộ cải thiện std chỉ cho cổng năng lượng.')
    index = int(indices[0])
    frame = signal[index * hop:index * hop + length]
    score, lag, curve = ACF['detect_pitch_acf'](frame, fs)
    fig, axes = plt.subplots(1, 3, figsize=(16, 4))
    center = float(item['times'][index])
    left, right = max(0., center - .15), min(len(signal) / fs, center + .15)
    start, stop = int(left * fs), int(right * fs)
    axes[0].plot(np.arange(start, stop) / fs, signal[start:stop], lw=.6)
    for a, b, label in segments:
        if label == 'sil' and b > left and a < right:
            axes[0].axvspan(max(a, left), min(b, right), color='gray', alpha=.2)
    axes[0].scatter(item['times'][indices], np.zeros(len(indices)), color='tab:red', label='F0 trong SIL', zorder=3)
    axes[0].set(xlim=(left, right), title='Vùng tô xám: nhãn SIL của LAB', xlabel='Thời gian (s)', ylabel='Biên độ')
    axes[0].legend(fontsize=8)
    axes[1].plot(np.arange(length) / fs * 1000, frame, lw=.8)
    axes[1].set(title=f'Khung SIL tại {center:.4f}s — biên độ nhỏ', xlabel='Thời gian trong khung (ms)', ylabel='Biên độ')
    lo, hi = max(1, math.ceil(fs / 400)), min(len(frame) - 2, math.floor(fs / 70))
    grid = np.arange(lo, hi + 1)
    peak = int(grid[np.argmax(curve[grid])])
    axes[2].plot(grid / fs * 1000, curve[grid])
    axes[2].axhline(fitted['pitch_threshold'], color='black', ls='--', label=f'Ngưỡng {fitted["pitch_threshold"]:.4f}')
    axes[2].scatter(peak / fs * 1000, score, color='tab:red', label=f'Score {score:.4f} → F0 {fs / lag:.2f} Hz')
    axes[2].set(title='ACF chuẩn hóa vượt ngưỡng dù LAB là SIL', xlabel='Độ trễ (ms)', ylabel='ACF score')
    axes[2].legend(fontsize=8)
    for ax in axes:
        ax.grid(alpha=.2)
    fig.tight_layout()
    plt.show()
    return evidence, pd.DataFrame(diagnostic_rows), pd.DataFrame(comparison)
