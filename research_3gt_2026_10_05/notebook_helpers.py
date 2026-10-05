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
