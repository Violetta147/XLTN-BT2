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
receipt_path=HERE/'results/H37_agreement_verification.json'
assert not receipt_path.exists(),'Preserve completed descriptive analysis'
source_path=HERE/'results/H37_source_native_frames.csv'
raw_path=HERE/'results/H37_raw_native_frames.csv'
usage_path=HERE/'results/H37_reaper_usage.csv'
source,raw,usage=[pd.read_csv(p) for p in (source_path,raw_path,usage_path)]
profile=pd.read_csv(REPO/'research_workbench_2026_10_06/results/training_data_profile.csv').set_index('file')
rows=[]
for (identity,file),candidate in source.groupby(['source_id','file']):
    if not identity.startswith('reaper_'):
        continue
    gate=source[(source.source_id=='praat7_filtered_v0.3')&(source.file==file)]
    gt,gf=gate.time_s.to_numpy(),gate.raw_f0_hz.to_numpy()
    ct,cf=candidate.time_s.to_numpy(),candidate.raw_f0_hz.to_numpy()
    right=np.minimum(np.searchsorted(ct,gt),len(ct)-1)
    left=np.maximum(right-1,0)
    index=np.where(abs(ct[left]-gt)<=abs(ct[right]-gt),left,right)
    support=abs(ct[index]-gt)<=.005+1/int(profile.loc[file,'fs'])
    gate_v=(gf>=70)&(gf<=400)
    used=gate_v&support&(cf[index]>=70)&(cf[index]<=400)
    identity_hybrid='praat_gate_'+identity
    saved=usage[(usage.option_id==identity_hybrid)&(usage.file==file)].iloc[0]
    assert int(used.sum())==saved.reaper_used
    assert int((gate_v&~used).sum())==saved.praat_fallback
    combined=raw[(raw.option_id==identity_hybrid)&(raw.file==file)]
    assert np.allclose(combined.time_s,gt,atol=1e-12)
    expected=np.where(gate_v,np.where(used,cf[index],gf),0.)
    assert np.allclose(combined.raw_f0_hz,expected,atol=1e-10)
    assert np.array_equal(combined.hybrid_source.to_numpy(),np.where(~gate_v,'unvoiced',np.where(used,'reaper','praat_fallback')))
    for j in np.where(gate_v)[0]:
        delta=float(1200*np.log2(cf[index[j]]/gf[j])) if used[j] else np.nan
        rows.append({'source_id':identity,'file':file,'native_praat_time_s':gt[j],'matched_reaper_time_s':ct[index[j]],
            'praat_f0_hz':gf[j],'reaper_f0_hz':cf[index[j]],'reaper_used':bool(used[j]),'support':bool(support[j]),
            'delta_cents':delta,'near_same_100c':bool(used[j] and abs(delta)<=100),
            'near_half_100c':bool(used[j] and abs(delta+1200)<=100),
            'near_double_100c':bool(used[j] and abs(delta-1200)<=100)})
frames=pd.DataFrame(rows)
summary=[]
for (identity,file),group in frames.groupby(['source_id','file']):
    defined=group[group.reaper_used]
    assert np.isfinite(defined.delta_cents).all()
    category=defined[['near_same_100c','near_half_100c','near_double_100c']].sum(axis=1)
    assert (category<=1).all()
    summary.append({'source_id':identity,'file':file,'gate_voiced_frames':len(group),'reaper_used':len(defined),
        'fallback':int((~group.reaper_used).sum()),'near_same_100c':int(defined.near_same_100c.sum()),
        'near_half_100c':int(defined.near_half_100c.sum()),'near_double_100c':int(defined.near_double_100c.sum()),
        'other_ratio':int((category==0).sum()),'median_delta_cents':float(defined.delta_cents.median()),
        'min_delta_cents':float(defined.delta_cents.min()),'max_delta_cents':float(defined.delta_cents.max())})
summary=pd.DataFrame(summary)
assert len(summary)==8
assert (summary.reaper_used==summary.near_same_100c+summary.near_half_100c+summary.near_double_100c+summary.other_ratio).all()
frames_path=audit.csv_write('H37_praat_reaper_agreement_frames.csv',frames)
summary_path=audit.csv_write('H37_praat_reaper_agreement_summary.csv',summary)
fig,axes=audit.plt.subplots(2,2,figsize=(12,7))
for ax,(file,part) in zip(axes.flat,frames[frames.source_id=='reaper_c0.9'].groupby('file')):
    delta=part.loc[part.reaper_used,'delta_cents'].to_numpy()
    lo=min(-1300,np.floor(delta.min()/50)*50)
    hi=max(1300,np.ceil(delta.max()/50)*50+50)
    histogram,edges=np.histogram(delta,bins=np.arange(lo,hi+50,50))
    assert histogram.sum()==len(delta)
    ax.stairs(histogram,edges,fill=True,alpha=.7)
    for x,label in [(-1200,'half'),(0,'same'),(1200,'double')]:
        ax.axvline(x,linestyle='--',color='black',alpha=.5)
    ax.set(title=f'{file}: n={len(delta)} REAPER used',xlabel='1200 log2(REAPER / Praat), cents',ylabel='Native gate V frames')
fig.suptitle('H37 default REAPER cost0.9: disagreement with Praat, not frame F0 error')
audit.save_figure('H37_praat_reaper_agreement',fig,[frames_path],
    'Tỷ số cao độ hai nguồn trong khung PraatV/nativeREAPERavailable; đủ mọi điểm, không cắt tail.',
    'Praat là anchor ứng viên, không F0 ground truth; nearhalf không chứng minh octave error.')
audit.plt.close(fig)
for figure in audit.ARTIFACTS:
    figure.update(generator='reaper_agreement_diagnostics.py',generator_sha256=audit.digest(__file__),command='python research_workbench_2026_10_07/reaper_agreement_diagnostics.py')
audit.json_write(HERE/'results/H37_agreement_manifest.json',{'figures':audit.ARTIFACTS})
for figure in audit.ARTIFACTS:
    png=(HERE/figure['png']).read_bytes()
    assert png[:8]==b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II',png[16:24]))>200
    ET.parse(HERE/figure['svg'])
    for source_record in figure['sources']:
        assert audit.digest(HERE/source_record['path'])==source_record['sha256']
report=['# H37 — hai nguồn F0 bất đồng ở đâu?', '',
    'Phân tích mô tả raw output đã đo, không apply correction hoặc tính lại MAPE cho pipeline chưa đăng ký. Cents là đơn vị tỷ số cao độ: một octave=1200cents, một semitone=100cents. Bảng dùng band±100cents quanh tỷ số1,1/2,2 để mô tả gần nhau; đây là lựa chọn diagnostic, không threshold được chứng minh tối ưu.', '',
    audit.markdown_table(summary), '',
    'Các số đếm trên nativePraatgrid, sau ghép REAPER bằng nearest time trong5ms+mộtmẫu và range70–400. Chỉ khung gateV và REAPERavailable có delta; fallback báo riêng. Usage/source tags/frequencies tái lập H37 trước tính tỷ số; không dùng file-stat GT để phân nhóm.', '',
    'Praat không phải ground truth từng khung. Nearhalf chỉ nói REAPER gần nửa frequency của Praat; chưa đủ kết luận REAPER sai octave hoặc Praat đúng. Histogram không phải pitch-error distribution. Mọi tail được giữ trong CSV và bins phủ toàn bộ finite values, không cắt âm thầm.', '',
    '![Tỷ số cao độ hai nguồn](figures/H37_praat_reaper_agreement.png)', '',
    'H37 fixedcost.9 studio_M1stdMAPE1.120784% nhưng countMAPE3.658537%/meanMAPE1.637307%, AverageMAPE2.138876%; phoneF1stdMAPE83.444579%/Avg29.460886%. Cổng giữ count/VUV giúp loại SIL dư, nhưng chưa loại bất đồng pitch trong các khung V. Không chọn riêng algorithm cho studio_M1 hoặc cắt khung theo GT.', '',
    'Một giả thuyết kế tiếp có thể chuẩn hóa octave của REAPER theo anchor Praat rồi so raw/guided/blended trên inner folds. Phải đăng ký rule/factors/band/fallback và selection/gates trước đo, giữ raw output; không coi anchor là F0 chuẩn và không tự suy rule sẽ đạt≤2%. Vòng đó chưa chạy trong phân tích này.', '',
    'Không đọc WAV/test hoặc gọi native mới; inputs chỉ H37raw/source/usage và profilefs đã lưu. Receipt có hashes/replay/categories/histogram/PNGSVG. Original/frozen giữ, không PDF/Drive/deep learning/MCP retry.']
report_path=HERE/'H37_ERROR_ANALYSIS.md'
report_path.write_text('\n'.join(report)+'\n',encoding='utf-8')
audit.json_write(receipt_path,{'source_groups_replayed':8,'native_gate_voiced_rows':len(frames),
    'usage_raw_frequencies_and_source_tags_matched':True,'category_counts_and_full_histogram_checked':True,
    'pitch_correction_applied':False,'new_mape_or_config_selected':False,'new_wav_native_or_test_read':False,
    'generator_sha256':audit.digest(__file__),
    'input_output_sha256':{str(p.relative_to(HERE)):audit.digest(p) for p in (source_path,raw_path,usage_path,frames_path,summary_path,report_path)}})
print(summary.to_string(index=False))
print('PASS eight source groups replayed and disagreement categories/figure checked; no pitch correction applied.')
