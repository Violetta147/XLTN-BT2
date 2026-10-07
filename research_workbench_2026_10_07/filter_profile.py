import tuning
from tuning import HERE, audit, core, np, pd, sosfreqz


def main():
    rows = []
    profiles = tuning.registry('H18')[::9]
    for fs in (16000, 44100):
        for option in profiles:
            sos = tuning.sos_for(option, fs)
            frequencies = np.geomspace(10, 4000, 400)
            response = np.ones(len(frequencies), dtype=complex) if sos is None else sosfreqz(sos, worN=frequencies, fs=fs)[1]
            delta = .1
            if sos is None:
                delay = np.zeros(len(frequencies))
            else:
                before = sosfreqz(sos, worN=frequencies - delta, fs=fs)[1]
                after = sosfreqz(sos, worN=frequencies + delta, fs=fs)[1]
                delay = -np.angle(after / before) / (4 * np.pi * delta) * 1000
            for f, h, d in zip(frequencies, response, delay):
                rows.append({'fs': fs, 'kind': option['kind'], 'low_hz': option['low_hz'], 'high_hz': option['high_hz'],
                             'frequency_hz': f, 'magnitude_db': 20 * np.log10(max(abs(h), 1e-12)), 'group_delay_ms': d})
    p_response = audit.csv_write('filter_frequency_response.csv', rows)
    data = pd.DataFrame(rows)
    fig, axes = audit.plt.subplots(2, 3, figsize=(13, 7))
    for col, kind in enumerate(('hp', 'lp', 'bp')):
        for (low, high), part in data[(data.fs == 16000) & (data.kind == kind)].groupby(['low_hz', 'high_hz']):
            label = f'{kind} {low:g}/{high:g} Hz'
            axes[0, col].semilogx(part.frequency_hz, part.magnitude_db, label=label)
            axes[1, col].semilogx(part.frequency_hz, part.group_delay_ms, label=label)
        for ax in axes[:, col]:
            ax.axvspan(70, 400, alpha=.1, color='green')
        axes[0, col].set(title=kind.upper() + ': fs16kHz', ylabel='Magnitude (dB)', ylim=(-50, 2))
        axes[0, col].legend(fontsize=7)
        axes[1, col].set(xlabel='Frequency (Hz)', ylabel='Group delay (ms)')
    audit.save_figure('filter_response_and_delay', fig, [p_response], 'Đáp ứng bộ lọc causal N2; dải xanh là range tìm F0 70–400Hz.', 'BP có order thực4; group delay phụ thuộc tần số, không phải pitch error. Response44.1kHz cũng lưu CSV.')
    cycles = []
    for item in core.load_training():
        for frame_ms in (20, 25, 40):
            cycles.append({'file': item['file'], 'file_group': item['file'].split('_')[1][0], 'frame_ms': frame_ms,
                           'file_gt_mean_hz': item['stats']['F0mean'],
                           'cycles_at_file_gt_mean': item['stats']['F0mean'] * frame_ms / 1000,
                           'cycles_at_range_min_70hz': 70 * frame_ms / 1000})
    p_cycles = audit.csv_write('frame_cycles_at_file_mean.csv', cycles)
    fig, ax = audit.plt.subplots(figsize=(10, 4))
    for name, part in pd.DataFrame(cycles).groupby('file'):
        ax.plot(part.frame_ms, part.cycles_at_file_gt_mean, 'o-', label=name)
    ax.set(xlabel='Frame length (ms)', ylabel='Cycles at file GT mean', title='Why the same frame has different periodic support')
    ax.legend(fontsize=8)
    audit.save_figure('frame_cycles_FM', fig, [p_cycles], 'Số chu kỳ tại mean GT từng file = meanHz × frameSeconds.', 'Dùng mean cả file chỉ minh họa support, không phải mọi khung có F0 đúng bằng mean hoặc độ chính xác measured.')
    for figure in audit.ARTIFACTS:
        figure.update(generator='filter_profile.py', generator_sha256=audit.digest(__file__), command='python research_workbench_2026_10_07/filter_profile.py')
    audit.json_write(HERE / 'results/filter_profile_manifest.json', {'figures': audit.ARTIFACTS})
    (HERE / 'FILTER_AND_FRAME_EXPLANATION.md').write_text('\n'.join([
        '# Hiểu bộ lọc, frame/hop và nhóm F/M', '',
        'High-pass giảm thành phần dưới cutoff; low-pass giảm phần trên cutoff; band-pass giữ một dải. Cutoff Butterworth là điểm gain−3dB, không phải bức tường cắt tuyệt đối. N2 dùng SOS để ổn định số; band-pass từ prototypeN2 có order thực4.', '',
        '![Đáp ứng](figures/filter_response_and_delay.png)', '',
        'Lọc causal dùng quá khứ và trạng thái filter, có group delay phụ thuộc tần số. Lọc tiến–lùi zero-phase dùng cả tương lai trong file, magnitude bị bình phương; không thể nói giữ nguyên mọi dạng sóng. Phase/transient/boundary cần đối chiếu trong thí nghiệm riêng.', '',
        'Frame là cửa sổ tín hiệu dùng tìm chu kỳ. Hop là khoảng cách giữa hai lần tìm. Frame dài chứa nhiều chu kỳ hơn nhưng trộn chuyển tiếp nhiều hơn; hop nhỏ cho đường đi dày hơn nhưng không tự tạo thêm người nói hoặc dữ liệu độc lập.', '',
        '![Chu kỳ](figures/frame_cycles_FM.png)', '',
        audit.markdown_table(pd.DataFrame(cycles)), '',
        'Các file M có meanGT116.9/123.7Hz, F215.6/229.6Hz. Đây là dữ liệu bốn file theo tên, không là quy tắc sinh học tổng quát. 20ms ở70Hz chỉ có1.4chu kỳ, 40ms có2.8; vẫn chưa chứng minh estimator đúng từngkhung.', '',
        'Logistic regression là classifier cổ điển học cách kết hợp ACFscore và năng lượng để quyết định V/UV. C điều chỉnh regularization; C lớn giảm mức phạt hệ số. Nó không tự tạo reference F0. Threshold.5 đang giữ để giới hạn grid trước đo.', '',
        'Hard clipping cắt đỉnh vượt giới hạn biên độ. Center clipping bỏ phần gầnzero nhằm làm rõ tính tuần hoàn trướcACF; hai thao tác có tác dụng khác nhau và không được gọi chung như đã cùng thử.', '',
        'Chọn grid bằng innerLOFO, đánh giá quy trình bằng outerLOFO; không chọn bằngtest. Count native phụ thuộc hop, vì vậy H18/H19 có grid chấm chung và lưu nativecount riêng.', '',
        'Nguồn API: [SciPy butter](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.butter.html), [sosfilt](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.sosfilt.html). Các curve và chu kỳ ở đây là phép tính từ filter/GTfile, không là số đo pitch accuracy.'
    ]) + '\n', encoding='utf-8')
    print('Generated two figure pairs and source CSVs for filter/frame interpretation.')


if __name__ == '__main__':
    main()
