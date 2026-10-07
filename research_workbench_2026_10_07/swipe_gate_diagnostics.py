import json
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
REPO=HERE.parent
sys.path.insert(0,str(REPO/'research_workbench_2026_10_06'))
import audit

audit.HERE,audit.RESULTS,audit.FIGURES=HERE,HERE/'results',HERE/'figures'
audit.ARTIFACTS.clear()
assert not (HERE/'results/H35_gate_diagnostic_verification.json').exists(),'Preserve completed diagnosis'
inputs=[HERE/'results/H34_nested_contours.csv',HERE/'results/H35_nested_contours.csv',
        HERE/'results/H34_fixed_lofo.csv',HERE/'results/H35_fixed_lofo.csv',HERE/'results/H35_swipe_usage.csv']
a,b=[pd.read_csv(p).query("model=='accepted'") for p in inputs[:2]]
assert not a.duplicated(['file','time_s']).any() and not b.duplicated(['file','time_s']).any()
merged=a.merge(b,on=['file','time_s'],suffixes=('_45','_30'),validate='one_to_one')
assert len(merged)==len(a)==len(b) and np.array_equal(merged.label_45,merged.label_30)
fixed45=pd.read_csv(inputs[2]).query("option_id=='praat7_filtered_v0.45'").set_index('file')
fixed30=pd.read_csv(inputs[3]).query("option_id=='praat7_filtered_v0.3'").set_index('file')
summary=[]
for file,group in merged.groupby('file'):
    before,after=group.pred_voiced_45.to_numpy(),group.pred_voiced_30.to_numpy()
    added,removed=~before&after,before&~after
    shared=before&after
    changed=shared&~np.isclose(group.f0_hz_45,group.f0_hz_30,equal_nan=True,atol=1e-8,rtol=0)
    assert int(after.sum()-before.sum())==int(added.sum()-removed.sum())
    for suffix,saved in [('45',fixed45.loc[file]),('30',fixed30.loc[file])]:
        values=group['f0_hz_'+suffix].dropna().to_numpy()
        assert np.allclose([values.mean(),values.std(),len(values)],[saved.F0mean,saved.F0std,saved.F0num],atol=1e-8)
        assert np.array_equal(np.isfinite(group['f0_hz_'+suffix]),group['pred_voiced_'+suffix])
        counts={'TP':int(((group.label_30=='v')&group['pred_voiced_'+suffix]).sum()),
                'FN':int(((group.label_30=='v')&~group['pred_voiced_'+suffix]).sum()),
                'FP':int(((group.label_30=='uv')&group['pred_voiced_'+suffix]).sum()),
                'TN':int(((group.label_30=='uv')&~group['pred_voiced_'+suffix]).sum()),
                'false_voiced_sil':int(((group.label_30=='sil')&group['pred_voiced_'+suffix]).sum())}
        assert all(saved[k]==v for k,v in counts.items())
    summary.append({'file':file,'count_45':int(before.sum()),'count_30':int(after.sum()),
        'added_V_predictions':int(added.sum()),'removed_V_predictions':int(removed.sum()),
        'changed_pitch_at_shared_V':int(changed.sum()),
        'added_in_label_V':int((added&(group.label_30=='v')).sum()),
        'added_in_label_UV':int((added&(group.label_30=='uv')).sum()),
        'added_in_label_SIL':int((added&(group.label_30=='sil')).sum()),
        'std_45_hz':fixed45.loc[file,'F0std'],'std_30_hz':fixed30.loc[file,'F0std'],
        'std_mape_45':fixed45.loc[file,'F0std_mape'],'std_mape_30':fixed30.loc[file,'F0std_mape']})
mask=(merged.pred_voiced_45!=merged.pred_voiced_30)|(~np.isclose(merged.f0_hz_45,merged.f0_hz_30,equal_nan=True,atol=1e-8,rtol=0))
changed=merged[mask][['file','time_s','label_30','pred_voiced_45','pred_voiced_30','f0_hz_45','f0_hz_30']].copy()
changed['decision_change']=np.where(~changed.pred_voiced_45&changed.pred_voiced_30,'added',np.where(changed.pred_voiced_45&~changed.pred_voiced_30,'removed','pitch_changed'))
summary=pd.DataFrame(summary)
summary_path=audit.csv_write('H35_gate_changes_summary.csv',summary)
changes_path=audit.csv_write('H35_gate_changed_frames.csv',changed)
studio=changed[changed.file=='studio_M1.wav'].reset_index(drop=True)
assert len(studio)==3 and (studio.label_30=='v').all()
assert list(studio.decision_change)==['removed','added','added']
assert np.allclose(studio.time_s,[1.1824943310657596,1.6624943310657596,1.6724943310657596],atol=1e-8)
fig,axes=audit.plt.subplots(2,1,figsize=(12,7))
part=merged[merged.file=='studio_M1.wav']
for ax in axes:
    ax.plot(part.time_s,part.f0_hz_45,'o-',markersize=2,label='Praat filtered 0.45')
    ax.plot(part.time_s,part.f0_hz_30,'.-',markersize=2,label='Praat filtered 0.30')
    for row in studio.itertuples(index=False):
        frequency=row.f0_hz_45 if row.decision_change=='removed' else row.f0_hz_30
        ax.scatter([row.time_s],[frequency],s=45,color='black',zorder=5)
    ax.set(ylabel='Predicted F0 (Hz)',xlabel='Canonical time (s)')
    ax.grid(alpha=.2)
axes[0].set(title='studio_M1: fixed thresholds, predicted contours')
axes[0].legend(fontsize=9)
axes[1].set(xlim=(1.1,1.8),title='Three changed voicing frames: all have segment label V')
for row in studio.itertuples(index=False):
    frequency=row.f0_hz_45 if row.decision_change=='removed' else row.f0_hz_30
    offset=(8,20) if row.decision_change=='removed' else ((-105,20) if row.f0_hz_30>115 else (8,-20))
    axes[1].annotate(f'{row.decision_change}: {frequency:.1f} Hz',(row.time_s,frequency),xytext=offset,textcoords='offset points',fontsize=9)
audit.save_figure('H35_gate_changed_contour',fig,inputs[:2],
    'Contours cố định và ba khung đổi quyết định V/UV ở studio_M1.',
    'Nhãn đoạn V không cho biết F0 đúng ở từng khung; không xóa các khung này theo GT.')
audit.plt.close(fig)
for figure in audit.ARTIFACTS:
    figure.update(generator='swipe_gate_diagnostics.py',generator_sha256=audit.digest(__file__),command='python research_workbench_2026_10_07/swipe_gate_diagnostics.py')
audit.json_write(HERE/'results/H35_gate_diagnostic_manifest.json',{'figures':audit.ARTIFACTS})
for figure in audit.ARTIFACTS:
    for source in figure['sources']:
        assert audit.digest(HERE/source['path'])==source['sha256']
    png=(HERE/figure['png']).read_bytes()
    assert png[:8]==b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II',png[16:24]))>200
    ET.parse(HERE/figure['svg'])
report=['# Vì sao studio_M1 vẫn khó?', '',
    'Đây là phân tích mô tả các phép đo đã lưu, không thử ngưỡng mới hoặc thay registry. Đã tái lập count/mean/std và V/UV/SIL của cả hai control từ contour trước khi so sánh.', '',
    '## Đổi gate có thể đổi cả tập F0 được tính thống kê', '',
    audit.markdown_table(summary), '',
    'Praat filtered0.30 có count85, so0.45 có84 ở studio_M1. Tuy ròng chỉ tăng một, mask đổi ba vị trí: một khung V158.1Hz bị bỏ, hai khung V118.9/108.0Hz được thêm. Các F0 ở khung V chung không đổi trong file này. Vì mean/std được tính trên tập F0 khác, giảm threshold không bảo đảm std gần GT hơn.', '',
    audit.markdown_table(studio), '',
    'Cả ba vị trí có nhãn đoạn V. Điều đó không xác nhận tần số 158/119/108Hz đúng hoặc sai: LAB chưa có F0 chuẩn từng khung. Không gọi đây là ba false voiced SIL, octave errors hoặc ba pitch đã sửa đúng. Không xóa riêng các khung này hoặc route theo tên studio_M1 để đạt metric.', '',
    '## H35 sửa nguồn F0 nhưng giữ nguyên tập khung', '',
    'HybridSWIPE.3 dùng SWIPE tại76/85 khung nativeV và Praat fallback tại9/85 khung nativeV của studio_M1; không thiếu support thời gian tại khung gateV. FixedstdMAPE6.098275% so Praat.30 là5.456594%, countMAPE3.658537% giữ nguyên. AverageMAPE3.350733% so3.175722%. Do đó loại SIL dư của H34 chưa đủ để sửa vấn đề dispersion trong tập hữu thanh.', '',
    'Trên ba file khác, hybrid.3 có AverageMAPE.700504/.616993/1.574769%; inner chọn nó khi outerstudio_M1 bị giữ lại. Heldstudio_M1 xấu thêm, nestedmean1.666210% socontrol1.622457%. Đây là counterexample cụ thể cho việc suy từ ba file tốt sang file còn lại; không chọn theo kết quả held để đổi quyết định.', '',
    '![Contour và ba vị trí đổi gate](figures/H35_gate_changed_contour.png)', '',
    'Figures mọi threshold và components trong SWIPE_PRAAT_LOCAL.ipynb đã replay từ WAV. Các dòng CSV ở đây lấy từ output frozen, không đọc WAV/test, không chạy native mới. REAPER hoặc cổng thích nghi theo độ tin cậy/duration cần giả thuyết và registry riêng trước đo; chưa được chứng minh giúp BT2. Không dùng metadata giới tính làm selector từ bốn file.', '',
    'Input/output SHA, tái lập thống kê, đếm thay đổi mask, labels và PNG/SVG lưu trong results/H35_gate_diagnostic_verification.json. Mục tiêu mỗi file≤2% chưa đạt; original/frozen giữ, không PDF/Drive/deep learning/MCP retry.']
(HERE/'H35_ERROR_ANALYSIS.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
audit.json_write(HERE/'results/H35_gate_diagnostic_verification.json',{
    'control_groups_replayed':8,'changed_frames':len(changed),'studio_M1_changed_frames':3,
    'count_net_change_identity_checked':True,'control_statistics_and_voicing_matched':True,
    'new_wav_or_native_or_test_read':False,'new_threshold_or_hypothesis_selected':False,
    'generator_sha256':audit.digest(__file__),
    'input_output_sha256':{str(p.relative_to(HERE)):audit.digest(p) for p in inputs+[summary_path,changes_path,HERE/'H35_ERROR_ANALYSIS.md']}})
print(summary.to_string(index=False))
print('PASS eight control groups replayed, changed voicing frames and PNG/SVG verified; no new experiment.')
