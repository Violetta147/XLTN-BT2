import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parent
cells=[]


def add(kind,source):
    cell={'cell_type':kind,'metadata':{},'source':source.strip()+'\n'}
    if kind=='code':
        cell.update(execution_count=None,outputs=[])
    cells.append(cell)


add('markdown','''# SWIPE′, Praat và AMDF: kiểm chứng từ WAV

F0 là tần số cơ bản của giọng. V/UV/SIL lần lượt là hữu thanh, vô thanh và khoảng lặng. AMDF tìm chu kỳ bằng hiệu biên độ theo độ trễ; Praat filtered dùng tự tương quan sau lọc thông thấp Gaussian. SWIPE′ so phổ với các mẫu harmonic, có FFT windows thay đổi theo tần số; strength threshold quyết định có đủ bằng chứng để nhận hữu thanh hay không.

H34 dùng toàn bộ pipeline SWIPE′. H35 giữ quyết định V/UV của Praat và chỉ thay nguồn F0 bằng SWIPE′ khi có cao độ hợp lệ gần cùng thời điểm; nếu thiếu, giữ F0 Praat. Điều này gọi là fallback, không cắt/thêm số khung theo ground truth. Notebook tính lại mọi cấu hình đã đăng ký và lựa chọn nested đã lưu; không mở một grid mới.

Average MAPE = trung bình ba lỗi phần trăm của F0mean, F0std và F0num. Std dùng ddof=0; num là số cao độ hợp lệ sau đưa về lưới chấm. Mục tiêu là **mỗi file ≤2%**. Nhãn LAB cung cấp thống kê cả file và loại đoạn, chưa có F0 chuẩn từng khung; contour mượt không chứng minh pitch đúng. Notebook AMDF gốc giữ nguyên; có thêm control H24 để đối chiếu theo cùng metric.''')
add('code',f'''from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
REPO=Path({str(REPO)!r})
HERE=REPO/'research_workbench_2026_10_07'
sys.path.insert(0,str(HERE))
import amdf_dual_window as dual
import swipe_reference as swipe
import swipe_praat_hybrid as hybrid
core,audit=dual.core,dual.audit
items=core.load_training()
by_name={{x['file']:x for x in items}}
config=json.loads((core.RESULTS/'frozen_config.json').read_text())['models']['AMDF_energy']['config']
families={{'H34':swipe,'H35':hybrid}}
receipts={{f:json.loads((HERE/f'results/{{f}}_experiment.json').read_text()) for f in families}}
for receipt in receipts.values():
    for relative,expected in receipt['code_sha256'].items():
        assert audit.digest(REPO/relative)==expected,relative
    for file,expected in receipt['data_sha256'].items():
        assert audit.digest(core.TRAIN/file)==expected,file
native_proof=swipe.native_api.metadata()
sptk_proof=swipe.sptk_api.metadata()
hybrid.SOURCE_CACHE.clear()
print('Local Python:',sys.executable,'; Praat',native_proof['version_stdout'],'; SPTK',sptk_proof['version'])
print('Chỉ train WAV, không đọc test. Ground truth là file-stat và nhãn đoạn.')
display(pd.DataFrame([{{'file':x['file'],'fs':x['fs'],**x['stats'],'segment_V_frames':int((x['labels']=='v').sum())}} for x in items]))''')
add('markdown','''## Tái lập fixed từ WAV

Fixed nghĩa là chấm một cấu hình đã chốt trên cả bốn file; không chọn cấu hình riêng theo chính file đang chấm. H24 fit cổng AMDF bằng ba file còn lại. Praat/SWIPE không fit bằng nhãn; các file khác chỉ được dùng khi chọn option ở nested.

SWIPE input float64 khôi phục scale PCM16 bằng ×32768, output Hz với UV=0, mốc thời gian 0. H35 ghép SWIPE vào lưới Praat trước, rồi ghép Praat vào lưới chấm 25/10 ms. Ghép tâm gần nhất trong nửa hop cộng một mẫu; nếu hòa chọn sớm. Không thêm padding, interpolation hay smoothing của agent. Internal padding của mã SWIPE vẫn giữ theo implementation.''')
add('code','''registries={f:json.loads((HERE/f'{f}_REGISTRY.json').read_text())['options'] for f in families}
features={}
native_calls={}
rows,contour_rows,fit_logs=[],[],[]
columns=['F0mean','F0std','F0num','F0mean_mape','F0std_mape','F0num_mape','average_mape',
         'macro_f1','recall_v','recall_uv','balanced_accuracy','TP','FN','FP','TN','false_voiced_sil']

def feature(module,option,item):
    key=(module.__name__,module.feature_key(option),item['file'])
    if key not in features:
        _,audio=core.load_audio(core.TRAIN/item['file'])
        features[key]=module.extract(item,audio,option)
        if 'native_call' in features[key]:
            native_calls['|'.join(key)]=features[key]['native_call']
    return features[key]

def measure(family,module,option,held,split):
    pool=[x for x in items if x['file']!=held['file']]
    native=feature(module,option,held)
    training=[feature(module,option,x) for x in pool]
    pred,f0,fit,_=module.infer(native,training,option,config)
    if module is dual:
        fit=dict(fit,requires_fit=True,actual_fit_files=sorted(x['file'] for x in pool))
    pred,f0,support=module.project(native,held,pred,f0,option['hop_ms'])
    measured=core.score_file(held,pred,f0)
    saved=pd.read_csv(HERE/f'results/{family}_fixed_lofo.csv') if split=='fixed' else pd.read_csv(HERE/f'results/{family}_metrics.csv')
    saved=saved[(saved.option_id==option['id'])&(saved.file==held['file'])]
    if split=='nested':
        saved=saved[(saved.split=='nested')&(saved.model=='candidate')]
    assert len(saved)==1
    assert np.allclose([measured[k] for k in columns],saved.iloc[0][columns].astype(float),atol=1e-8),(family,option['id'],held['file'])
    method=option['id'] if split=='fixed' else family+'_nested'
    rows.append({'evaluation':split,'method':method,'family':family,'option_id':option['id'],**measured})
    fit_logs.append({'evaluation':split,'method':method,'held_file':held['file'],'fit_files':sorted(x['file'] for x in pool),'fitted':fit})
    contour_rows.extend({'evaluation':split,'method':method,'family':family,'file':held['file'],
                        'time_s':float(t),'label':str(lab),'pred_voiced':bool(p),'f0_hz':float(f),'support':bool(s)}
                       for t,lab,p,f,s in zip(held['times'],held['labels'],pred,f0,support))

for held in items:
    measure('H24',dual,dual.registry('H24')[1],held,'fixed')
for family,module in families.items():
    for option in registries[family]:
        for held in items:
            measure(family,module,option,held,'fixed')
display(pd.DataFrame(rows)[['family','option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','false_voiced_sil']])
print('PASS36 fixed rows được tính từ WAV, khớp số liệu đã lưu 1e-8.')''')
add('markdown','''## Giữ riêng outer file và không chọn bằng kết quả held

Nested dùng ba file khác để chọn option rồi chấm file còn lại. Notebook tái lập lựa chọn đã lưu, không chạy lại search để đổi kết quả. Lịch sử đã xem bốn file nhiều lần khiến nested này vẫn là nghiên cứu thăm dò, chưa xác nhận trên dữ liệu mới.

Ở H35, ba file khác có thể thích SWIPE′, nhưng option ấy vẫn có thể xấu trên studio_M1. Đây là giới hạn khả năng khái quát hóa. Một bảng fixed có ba file dưới2% không đủ để đạt mục tiêu toàn bộ.''')
add('code','''for family,module in families.items():
    for selection in receipts[family]['selections']:
        held=selection['outer_held']
        if held=='final':
            continue
        assert held not in selection['selection_files'] and set(selection['selection_files'])==set(by_name)-{held}
        measure(family,module,selection['option'],by_name[held],'nested')
table=pd.DataFrame(rows)
contour_table=pd.DataFrame(contour_rows)
assert len(table)==44
table.to_csv(HERE/'results/swipe_notebook_per_file.csv',index=False)
contour_table.to_csv(HERE/'results/swipe_notebook_contours.csv',index=False)
status=table.query("evaluation=='nested'").groupby('family').average_mape.agg(mean='mean',worst='max',all_files_le_2=lambda x:bool((x<=2).all())).reset_index()
status.to_csv(HERE/'results/swipe_notebook_status.csv',index=False)
display(table.query("evaluation=='nested'")[['family','option_id','file','average_mape','F0std_mape','F0num_mape','macro_f1','false_voiced_sil']])
display(status)
print('Mục tiêu từng file đạt:',bool(status.all_files_le_2.any()))''')
add('markdown','''## Figures chứa mọi cấu hình, kể cả thất bại

Mỗi cột stacked cộng ba phần lỗi mean/std/count đã chia3, nên chiều cao chính là Average MAPE. Đường2% là mục tiêu từng file. H34 còn lỗi silence lớn ở ngưỡng thấp; tăng strength mất V. H35 giữ count và V/UV như Praat nhưng chưa sửa std studio_M1. Không đồng nhất SIL false voiced với số pitch sửa sai, vì chưa có F0 chuẩn từng khung.''')
add('code','''audit.HERE,audit.RESULTS,audit.FIGURES=HERE,HERE/'results',HERE/'figures'
audit.ARTIFACTS.clear()
plot_source=HERE/'results/swipe_notebook_per_file.csv'
for family in families:
    order=[x['id'] for x in registries[family]]
    labels=['Praat control']+([f'SWIPE {x["voicing_threshold"]:g}' for x in registries[family][1:]] if family=='H34' else [f'Praat + SWIPE {x["voicing_threshold"]:g}' for x in registries[family][1:]])
    fixed=table[(table.evaluation=='fixed')&(table.family==family)]
    fig,axes=audit.plt.subplots(2,2,figsize=(12,8))
    for ax,(file,part) in zip(axes.flat,fixed.groupby('file')):
        part=part.set_index('option_id').loc[order]
        bottom=np.zeros(len(order))
        for metric,label in [('F0mean_mape','mean'),('F0std_mape','std'),('F0num_mape','count')]:
            values=part[metric].to_numpy()/3
            ax.bar(labels,values,bottom=bottom,label=label)
            bottom+=values
        assert np.allclose(bottom,part.average_mape)
        ax.axhline(2,color='black',linestyle='--',label='target 2%')
        ax.set(title=file,ylabel='Average MAPE (%)')
        ax.tick_params(axis='x',rotation=20)
    axes[0,0].legend(fontsize=8)
    fig.suptitle(f'{family}: fixed results recomputed from WAV')
    audit.save_figure(f'swipe_notebook_{family}_components',fig,[plot_source],
                      'Các thành phần mean/std/count cộng thành Average MAPE; mọi cấu hình fixed.',
                      'Không chọn best theo held file; LAB chưa có F0 chuẩn từng khung.')
    display(fig)
    audit.plt.close(fig)
fig,axes=audit.plt.subplots(1,3,figsize=(14,4))
fixed=table.query("evaluation=='fixed' and family=='H34'")
for file,part in fixed.groupby('file'):
    part=part.set_index('option_id').loc[[x['id'] for x in registries['H34']]]
    for ax,metric in zip(axes,('macro_f1','recall_v','false_voiced_sil')):
        ax.plot(['Praat','.2','.3','.4','.5'],part[metric],'o-',label=file.removesuffix('.wav'))
        ax.set(title=metric,xlabel='SWIPE strength threshold')
axes[0].legend(fontsize=8)
audit.save_figure('swipe_notebook_H34_voicing',fig,[plot_source],
                  'V/UV F1, recall V và SIL của mọi fixed option H34.',
                  'Bốn file không đủ kết luận về giới hoặc speaker.')
display(fig)
audit.plt.close(fig)
for figure in audit.ARTIFACTS:
    figure.update(generator='build_swipe_notebook.py',generator_sha256=audit.digest(HERE/'build_swipe_notebook.py'),command='python research_workbench_2026_10_07/execute_swipe_notebook.py')
audit.json_write(HERE/'results/swipe_notebook_figure_manifest.json',{'figures':audit.ARTIFACTS})
print('Đã xuất ba PNG/SVG pairs, từ các số liệu vừa tính lại.')''')
add('code','''source_hashes={str(Path(m.__file__).relative_to(REPO)):audit.digest(m.__file__) for m in (dual,swipe,hybrid,core,audit)}
source_hashes.update({key:value for receipt in receipts.values() for key,value in receipt['code_sha256'].items()})
native_calls.update({'hybrid|'+identity+'|'+file:value[2] for (identity,file),value in hybrid.SOURCE_CACHE.items()})
audit.json_write(HERE/'results/swipe_notebook_provenance.json',{
    'source_sha256':source_hashes,'wav_sha256':{x['file']:audit.digest(core.TRAIN/x['file']) for x in items},
    'native_calls':native_calls,'fit_logs':fit_logs,'praat_native_sha256':native_proof['exe_sha256'],
    'sptk_native_sha256':sptk_proof['exe_sha256'],'test_read':False,'new_grid_or_selection':False})
assert len(native_calls)==32 and len(fit_logs)==44
print('PASS44 measured rows: H24control4 + H34fixed20 + H35fixed12 + nested8.')
print('Control/frozen/notebooks gốc giữ nguyên; H34 và H35 FAIL, mỗi file≤2% chưa đạt.')
print('Native calls/hash/fit exclusions/data/source/projection và contours được lưu để verify độc lập.')''')
add('markdown','''## Nguồn và cách học tiếp

Đọc `SPTK_NATIVE_SETUP.md`, `H34_REGISTRATION.md`, `H35_REGISTRATION.md`, hai report và `H35_swipe_usage.csv`. Setup đọc manual/code chính thức, không claim đã đọc full paper. Cấu hình thực nằm trong registry; raw native và hybrid source tags có thể dùng để truy lại fallback. Notebook này không tạo PDF, đọc test, dùng deep learning, truy cập Drive hoặc retry Jev.

Giới tính trong tên file chỉ là nhãn nhóm; mỗi tổ hợp device×F/M mới có một file. Không chọn algorithm theo tên file hoặc suy thành quy luật giọng nam/nữ. Notebook giải thích và tái lập phép đo, không đổi ground truth hoặc kéo số liệu về2%.''')
path=HERE/'SWIPE_PRAAT_LOCAL.ipynb'
assert not path.exists(),'Preserve existing notebook'
path.write_text(json.dumps({'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3 local','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.13.11'}},'nbformat':4,'nbformat_minor':5},ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print('Created',path,'with five code cells; source only, not executed.')
