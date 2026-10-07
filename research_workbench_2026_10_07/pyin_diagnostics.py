import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0,str(REPO/'research_workbench_2026_10_06'))
import audit

audit.HERE, audit.RESULTS, audit.FIGURES = HERE,HERE/'results',HERE/'figures'
audit.ARTIFACTS.clear()
fixed_path = HERE/'results/H33_fixed_lofo.csv'
raw_path = HERE/'results/H33_raw_native_frames.csv'
contour_path = HERE/'results/H33_nested_contours.csv'
fixed, raw, contours = [pd.read_csv(path) for path in (fixed_path,raw_path,contour_path)]
profile = pd.read_csv(REPO/'research_workbench_2026_10_06/results/training_data_profile.csv').set_index('file')
assert not (HERE/'results/H33_error_analysis_verification.json').exists(), 'Preserve completed analysis'
probability_rows = []
for (identity,file),group in raw.groupby(['option_id','file']):
    if not identity.startswith('pyin_'):
        continue
    canonical = contours[(contours.model=='accepted')&(contours.file==file)]
    times,target = group.time_s.to_numpy(),canonical.time_s.to_numpy()
    right = np.minimum(np.searchsorted(times,target),len(times)-1)
    left = np.maximum(right-1,0)
    indices = np.where(abs(times[left]-target)<=abs(times[right]-target),left,right)
    support = abs(times[indices]-target)<=.005+1/int(profile.loc[file,'fs'])
    prediction = group.raw_voiced.to_numpy()[indices]&support
    frequency = group.raw_f0_hz.to_numpy()[indices]
    saved = fixed[(fixed.option_id==identity)&(fixed.file==file)].iloc[0]
    assert int(prediction.sum())==saved.F0num
    labels = canonical.label.to_numpy()
    counts = {'TP':int(((labels=='v')&prediction).sum()),'FN':int(((labels=='v')&~prediction).sum()),
              'FP':int(((labels=='uv')&prediction).sum()),'TN':int(((labels=='uv')&~prediction).sum()),
              'false_voiced_sil':int(((labels=='sil')&prediction).sum())}
    assert all(saved[k]==v for k,v in counts.items())
    assert np.isclose(saved.projection_coverage,support.mean())
    valid = frequency[prediction]
    assert np.allclose([valid.mean(),valid.std()],[saved.F0mean,saved.F0std],atol=1e-8)
    probabilities = group.voiced_probability.to_numpy()[indices]
    for label in ('v','uv','sil'):
        mask = labels==label
        supported = mask&support
        probability_rows.append({'option_id':identity,'file':file,'label':label,'canonical_frames':int(mask.sum()),
            'supported_frames':int(supported.sum()),'unsupported_frames':int((mask&~support).sum()),
            'predicted_voiced_frames':int((mask&prediction).sum()),
            'mean_probability_supported':float(probabilities[supported].mean()),
            'mean_probability_predicted_voiced':float(probabilities[mask&prediction].mean()) if (mask&prediction).any() else np.nan})
probability_path = audit.csv_write('H33_probability_by_label.csv',probability_rows)
summary = fixed.groupby('option_id',sort=False).agg(mean_mape=('average_mape','mean'),worst_mape=('average_mape','max'),
    mean_std_mape=('F0std_mape','mean'),mean_count_mape=('F0num_mape','mean'),macro_f1=('macro_f1','mean'),
    recall_v=('recall_v','mean'),false_voiced_uv=('FP','sum'),false_voiced_sil=('false_voiced_sil','sum'),
    worst_projection_coverage=('projection_coverage','min')).reset_index()
summary_path = audit.csv_write('H33_error_summary.csv',summary)
order = ['praat7_filtered_v0.45','pyin_f40','pyin_f60','pyin_f80']
labels = ['Praat filtered','pYIN40','pYIN60','pYIN80']
fig, axes = audit.plt.subplots(2,2,figsize=(11,7),sharey=True)
for ax,(file,part) in zip(axes.flat,fixed.groupby('file')):
    part = part.set_index('option_id').loc[order]
    bottom = np.zeros(len(order))
    for metric,label in [('F0mean_mape','mean'),('F0std_mape','std'),('F0num_mape','count')]:
        values = part[metric].to_numpy()/3
        ax.bar(labels,values,bottom=bottom,label=label)
        bottom += values
    assert np.allclose(bottom,part.average_mape)
    ax.axhline(2,color='black',linestyle='--',label='target2%')
    ax.set(title=file,ylabel='Average MAPE (%)')
    ax.tick_params(axis='x',rotation=15)
axes[0,0].legend(fontsize=8)
fig.suptitle('H33 fixed pipelines: all outcomes, no held-file best selection')
audit.save_figure('H33_fixed_components',fig,[fixed_path],
    'Mỗi lỗi mean/std/count chia3; cộng thành Average MAPE.', 'Chỉ file-stat, không đo accuracy cao độ từng khung.')
audit.plt.close(fig)
fig,axes = audit.plt.subplots(1,3,figsize=(13,4))
for file,part in fixed.groupby('file'):
    part = part.set_index('option_id').loc[order]
    for ax,metric in zip(axes,('macro_f1','recall_v','false_voiced_sil')):
        ax.plot(labels,part[metric],'o-',label=file.replace('.wav',''))
        ax.set(title=metric)
        ax.tick_params(axis='x',rotation=20)
axes[0].legend(fontsize=8)
audit.save_figure('H33_fixed_voicing',fig,[fixed_path],
    'V/UV F1/recall và SIL cùng các cấu hình cố định.', 'Không quy thành kết luận về giới/speaker từ bốn file.')
audit.plt.close(fig)
for figure in audit.ARTIFACTS:
    figure.update(generator='pyin_diagnostics.py',generator_sha256=audit.digest(__file__),
                  command='python research_workbench_2026_10_07/pyin_diagnostics.py')
audit.json_write(HERE/'results/H33_error_figure_manifest.json',{'figures':audit.ARTIFACTS})
report = ['# H33 — pYIN thất bại ở đâu?', '',
    'Phân tích mô tả kết quả đã hoàn tất, không search thêm hoặc đổi registry/gates. Native F0/voicing/probability được chiếu lại về canonical và tái lập fixed mean/std/count/TP/FN/FP/TN/SIL trước vẽ.', '',
    audit.markdown_table(summary), '',
    'Cửa sổ40ms cho mean2.719295% và worst3.355827%, so controlmean2.156992%. F1 .816876 và recallV .888924 thấp hơn control .879377/.908626. SIL6 so0. Cửa sổ60/80ms mean5.843812/11.250381%; count MAPE tăng và SIL22/60. Final và cảbốnouter chọn control; nested2.156992% không đồng nghĩa pYIN đạt mức ấy.', '',
    'Studio_M1 pYIN60 stdMAPE0.480383% nhưng countMAPE10.975610%, AverageMAPE3.915206%: chỉ giảmstd chưa đáp ứng mục tiêu. pYIN80 count125 so GT82, trong đó34SIL và10UV được nhận hữu thanh. Nhiều khung dư có nhãn UV/SIL; chưa có F0GTtừngkhung để phân loại toàn bộ lỗi cao độ. Không cắt count125 về82 theo GT.', '',
    'Mất support biên cũng được báo: worstcoverage pYIN40/60/80 lầnlượt .996310/.988930/.981550. Nó không giải thích việc count tăng khi cửa sổ dài; voiced decisions thay đổi đồng thời. Không gán quan hệ nhân quả độc lập cho padding, Viterbi hoặc một tham số riêng vì đây là whole pipeline/window comparison.', '',
    'Probability là output của pYIN trước/đi cùng decoding, không phải nhãn GT hoặc xác suất đã calibrated cho BT2. Bảng theo V/UV/SIL lưu mean probability với supported_frames và số flagV. Chưa dùng nó để áp threshold mới; giá trị sau Viterbi không được giả định bằng probability>0.5.', '',
    '![Thành phần lỗi mọi cấu hình](figures/H33_fixed_components.png)', '',
    '![Đánh đổi V/UV/SIL](figures/H33_fixed_voicing.png)', '',
    'Dữ liệu: results/H33_fixed_lofo.csv, H33_raw_native_frames.csv, H33_nested_contours.csv. Bảng mới: H33_probability_by_label.csv và H33_error_summary.csv. Không đọc WAV/test, không PDF/Drive/deep learning/MCP retry.', '',
    'Các pipeline SWIPE/REAPER vẫn chưa đo. Một cổng cho pYIN cần đăng ký và fit bằng training, không được lấy GT của heldfile làm ngưỡng hoặc coi ứng viên hiện tại là F0GT. Giữ cả thất bại và hạn chế lịch sử n4.']
(HERE/'H33_ERROR_ANALYSIS.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
audit.json_write(HERE/'results/H33_error_analysis_verification.json',{
    'fixed_pyin_groups_replayed':12,'fixed_stats_voicing_and_support_matched':True,'new_wav_or_test_read':False,
    'source_sha256':{str(p.relative_to(HERE)):audit.digest(p) for p in (fixed_path,raw_path,contour_path,probability_path,summary_path)},
    'generator_sha256':audit.digest(__file__),'new_hypothesis_or_threshold_selected':False})
print(summary.to_string(index=False))
print('PASS twelve pYIN groups replayed, two figure pairs generated; no new experiment or WAV read.')
