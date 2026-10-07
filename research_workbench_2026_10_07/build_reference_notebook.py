import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
cells = []


def add(kind, source):
    cell = {'cell_type': kind, 'metadata': {}, 'source': source.strip() + '\n'}
    if kind == 'code':
        cell.update(execution_count=None, outputs=[])
    cells.append(cell)


add('markdown', '''# AMDF → Harvest → Praat: kiểm chứng từ WAV và hiểu giới hạn

F0 là tần số cơ bản. AMDF so hiệu biên độ giữa tín hiệu và bản dịch theo độ trễ; ACF đo mức tương quan. V/UV/SIL là hữu thanh/vô thanh/khoảng lặng. Harvest tạo và nối các ứng viên F0; Praat filtered lọc thông thấp Gaussian rồi phân tích tự tương quan và chọn đường qua các ứng viên.

Notebook này chạy lại các pipeline đã đăng ký từ WAV train local, giữ notebook gốc. Không tạo giả thuyết/grid mới. H24 tách cửa sổ gate25ms và pitch40ms; H29 dùng pitch Harvest với cổng AMDF; H30 dùng pipeline Praat7 filtered; H31 chỉ đổi voicing threshold; H32 chỉ đổi silence threshold. Không dùng deep learning.

Average MAPE từng file = (lỗi phần trăm F0mean + F0std + F0num)/3. F0std dùng độ lệch chuẩn quần thể, ddof=0; F0num là số F0 hữu hạn sau projection về lưới chấm. Mục tiêu **mỗi file ≤2%**. Một mean bốn file dưới2% chưa đủ.

LAB có ground truth thống kê cả file và nhãn loại đoạn, không có F0 chuẩn từng khung. Mã chạy/đồ thị không chứng minh mọi cao độ đúng. Nguồn paper không PDF và mức bằng chứng xem PAPER_KNOWLEDGE_WITHOUT_PDF.md và LITERATURE_REVIEW.md.''')
add('code', f'''from pathlib import Path
import sys, json, hashlib
import numpy as np
import pandas as pd
REPO = Path({str(REPO)!r})
HERE = REPO / 'research_workbench_2026_10_07'
sys.path.insert(0,str(HERE))
import amdf_dual_window as dual
import harvest_voicing as harvest
import praat_filtered_reference as filtered
import praat_voicing_threshold as voicing
import praat_silence_threshold as silence
core, audit = dual.core, dual.audit
items = core.load_training()
by_name = {{x['file']:x for x in items}}
config = json.loads((core.RESULTS/'frozen_config.json').read_text())['models']['AMDF_energy']['config']
families = {{'H29':harvest,'H30':filtered,'H31':voicing,'H32':silence}}
receipts = {{family:json.loads((HERE/f'results/{{family}}_experiment.json').read_text()) for family in families}}
for receipt in receipts.values():
    for relative, expected in receipt['code_sha256'].items():
        assert audit.digest(REPO/relative)==expected,relative
    for file, expected in receipt['data_sha256'].items():
        assert audit.digest(core.TRAIN/file)==expected,file
proof = filtered.native_api.metadata()
world_proof = json.loads((HERE/'results/pyworld_035_compatibility.json').read_text())
assert audit.digest(world_proof['native_module'])==world_proof['native_module_sha256']
print('Môi trường:',sys.executable,'; native Praat',proof['version_stdout'],'; PyWORLD',harvest.pyworld.__version__)
print('Chỉ đọc train WAV local. Notebook dùng .venv-bt2-world để import PyWORLD.')
display(pd.DataFrame([{{'file':x['file'],'fs':x['fs'],**x['stats']}} for x in items]))''')
add('markdown', '''## Cấu hình cố định và nested là hai phép chấm khác nhau

LOFO (leave one file out) fit cổng AMDF bằng ba file và chấm file còn lại. Praat không fit bằng nhãn; threshold cố định vẫn phải được chọn bằng các file khác nếu báo nested. Native pitch dùng cửa sổ của thuật toán; canonical25/10 chỉ là lưới chấm chung. Ghép tâm gần nhất, nửa hop + một mẫu, không padding; F0 native ngoài70–400Hz nhận UV/NaN theo policy đã đăng ký.

Bảng fixed sau tính lại mọi cấu hình đại diện từ WAV; không lấy cấu hình tốt nhất theo GT của file đang chấm. Bảng nested tính lại lựa chọn đã lưu của từng outer fold và kiểm tra outer file vắng khỏi pool chọn. Giữ nguyên lịch sử lựa chọn; không mở lại search để đổi kết quả. Với bốn file đã xem nhiều lần, nested vẫn là exploratory, không phải xác nhận trên dữ liệu mới.''')
add('code', '''registries = {family:json.loads((HERE/f'{family}_REGISTRY.json').read_text())['options'] for family in families}
cases = [('AMDF25','H24','amdf_f25_h10',None,None),
         ('AMDF_gate25_pitch40','H24','amdf_gate25_pitch40',dual,dual.registry('H24')[1])]
cases += [(identity,'H29',identity,harvest,next(x for x in registries['H29'] if x['id']==identity))
          for identity in ('harvest_raw','harvest_amdf')]
cases += [(x['id'],'H30',x['id'],filtered,x) for x in registries['H30'] if x['method']!='control']
cases += [(x['id'],'H31',x['id'],voicing,x) for x in registries['H31'] if x['voicing_threshold'] in (.25,.30,.40)]
cases += [(x['id'],'H32',x['id'],silence,x) for x in registries['H32']]
features = {}
native_calls, fit_logs, contour_rows, rows = {}, [], [], []
columns = ['F0mean','F0std','F0num','F0mean_mape','F0std_mape','F0num_mape','average_mape',
           'macro_f1','recall_v','recall_uv','balanced_accuracy','TP','FN','FP','TN','false_voiced_sil']

def feature(module, option, item):
    key = (module.__name__,module.feature_key(option),item['file'])
    if key not in features:
        _, audio = core.load_audio(core.TRAIN/item['file'])
        features[key] = module.extract(item,audio,option)
        if 'native_call' in features[key]:
            native_calls['|'.join(key)] = features[key]['native_call']
    return features[key]

def measure(method, family, identity, module, option, held, split):
    pool = [x for x in items if x['file']!=held['file']]
    if module is None:
        fitted = core.fit(pool,config)
        pred,f0 = core.infer(held,config,fitted)
        fit = {'requires_fit':True,'actual_fit_files':sorted(x['file'] for x in pool),**fitted}
        support = np.ones(len(pred),dtype=bool)
    else:
        native = feature(module,option,held)
        training = [feature(module,option,x) for x in pool]
        pred,f0,fit,_ = module.infer(native,training,option,config)
        pred,f0,support = module.project(native,held,pred,f0,option['hop_ms'])
        if module is dual:
            fit = {'requires_fit':True,'actual_fit_files':sorted(x['file'] for x in pool),**fit}
    measured = core.score_file(held,pred,f0)
    path = HERE/f'results/{family}_fixed_lofo.csv' if split=='fixed' else HERE/f'results/{family}_metrics.csv'
    saved = pd.read_csv(path)
    saved = saved[(saved.option_id==identity)&(saved.file==held['file'])]
    if split=='nested':
        saved = saved[(saved.split=='nested')&(saved.model=='candidate')]
    assert len(saved)==1,(family,identity,held['file'],split)
    assert np.allclose([measured[k] for k in columns],saved.iloc[0][columns].astype(float),atol=1e-8)
    rows.append({'evaluation':split,'method':method,'family':family,'option_id':identity,**measured})
    fit_logs.append({'evaluation':split,'method':method,'held_file':held['file'],
                     'fit_files':sorted(x['file'] for x in pool),'fitted':fit})
    contour_rows.extend({'evaluation':split,'method':method,'family':family,'file':held['file'],
                         'time_s':float(t),'label':str(lab),'pred_voiced':bool(p),'f0_hz':float(f),
                         'support':bool(s)} for t,lab,p,f,s in zip(held['times'],held['labels'],pred,f0,support))

for method,family,identity,module,option in cases:
    for held in items:
        measure(method,family,identity,module,option,held,'fixed')
for family,module in families.items():
    for selection in receipts[family]['selections']:
        held = selection['outer_held']
        if held=='final':
            continue
        assert held not in selection['selection_files']
        assert set(selection['selection_files'])==set(by_name)-{held}
        option = selection['option']
        measure(family+'_nested',family,option['id'],module,option,by_name[held],'nested')
table = pd.DataFrame(rows)
table.to_csv(HERE/'results/reference_notebook_per_file.csv',index=False)
pd.DataFrame(contour_rows).to_csv(HERE/'results/reference_notebook_contours.csv',index=False)
source_hashes = {str(Path(module.__file__).relative_to(REPO)):audit.digest(module.__file__)
                 for module in (dual,harvest,filtered,voicing,silence,core,audit)}
source_hashes.update({key:value for receipt in receipts.values() for key,value in receipt['code_sha256'].items()})
audit.json_write(HERE/'results/reference_notebook_provenance.json',
    {'source_sha256':source_hashes,'wav_sha256':{x['file']:audit.digest(core.TRAIN/x['file']) for x in items},
     'native_calls':native_calls,'fit_logs':fit_logs,'world_native_sha256':world_proof['native_module_sha256'],
     'praat_native_sha256':proof['exe_sha256'],'test_wav_read':False,'frozen_config_sha256':audit.digest(core.RESULTS/'frozen_config.json')})
display(table[['evaluation','method','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','recall_v','false_voiced_sil']])
print('Tính lại:',len(cases)*4,'fixed rows và16 nested rows; khớp kết quả đã lưu với tolerance1e-8.')''')
add('markdown', '''## Lỗi mean, std hay count?

Mỗi thanh tách ba đóng góp MAPE/3; đường2% là mục tiêu cho từng file. Std nhỏ hơn không tự chứng minh contour tốt hơn: bỏ khung hợp lệ cũng có thể làm std giảm. Count sai cũng có thể xảy ra dù phát hiện V tốt, vì số GT của file không nhất thiết trùng số tâm khung nhãn V trên lưới chấm. Không ép phân phối hay cắt F0 để khớp GT.''')
add('code', '''audit.ARTIFACTS.clear()
plot_methods = ['AMDF25','AMDF_gate25_pitch40','harvest_amdf','praat7_raw_v0.45',
                'praat7_filtered_v0.45','praat7_filtered_v0.3','praat7_filtered_s0.11']
labels = ['AMDF25','AMDF40','Harvest+gate','Praat raw','Filtered .45','Filtered .30','Silence .11']
fig,axes = audit.plt.subplots(2,2,figsize=(13,8),sharey=True)
for ax,(file,part) in zip(axes.flat,table[table.evaluation=='fixed'].groupby('file')):
    part = part.set_index('method').loc[plot_methods]
    bottom = np.zeros(len(part))
    for metric,label in [('F0mean_mape','mean'),('F0std_mape','std'),('F0num_mape','count')]:
        values = part[metric].to_numpy()/3
        ax.bar(labels,values,bottom=bottom,label=label)
        bottom += values
    assert np.allclose(bottom,part.average_mape)
    ax.axhline(2,color='black',linestyle='--',label='target2%')
    ax.set(title=file,ylabel='Average MAPE (%)')
    ax.tick_params(axis='x',rotation=30)
axes[0,0].legend(fontsize=8)
fig.suptitle('Measured fixed configurations; no selection using held-file GT')
audit.save_figure('reference_notebook_components',fig,[HERE/'results/reference_notebook_per_file.csv'],
    'Tính lại từ WAV; mỗi đóng góp MAPE chia3.', 'File-stat và bốn file đã nghiên cứu, không GT F0 từng khung.')
display(fig)
audit.plt.close(fig)''')
add('markdown', '''## Quy trình chọn cấu hình có đạt từng file không?

Bảng dưới dùng kết quả nested vừa tính lại từ WAV với lựa chọn outer đã đăng ký, không ghép best threshold của chính mỗi file. Cổng kiểm tra cải thiện và mục tiêu≤2% là hai điều khác nhau: H30 qua gates tương đối với AMDF nhưng chưa đạt mục tiêu; H32 mean dưới2% vẫn còn file trên2%.

F1 là trung bình F1 của hai lớp V/UV; recall V là tỷ lệ khung nhãn V được nhận lại. SIL báo riêng, không đưa vào F1 V/UV. F/M trong tên file chỉ là nhóm của bộ dữ liệu này, chưa đủ để khẳng định kết luận về giới hoặc speaker mới.''')
add('code', '''nested = table[table.evaluation=='nested']
status = nested.groupby('family').average_mape.agg(mean='mean',worst='max',all_files_le_2=lambda x:bool((x<=2).all())).reset_index()
status.to_csv(HERE/'results/reference_notebook_status.csv',index=False)
display(status)
fig,axes = audit.plt.subplots(1,3,figsize=(14,4))
for family,part in nested.groupby('family'):
    part = part.sort_values('file')
    for ax,metric in zip(axes,('average_mape','macro_f1','recall_v')):
        ax.plot(part.file.str.replace('.wav','',regex=False),part[metric],'o-',label=family)
        ax.set(title=metric)
        ax.tick_params(axis='x',rotation=25)
axes[0].axhline(2,color='black',linestyle='--',label='target2%')
axes[0].legend(fontsize=8)
audit.save_figure('reference_notebook_nested',fig,[HERE/'results/reference_notebook_per_file.csv'],
    'Nested tái tính với outer choices đã lưu.', 'Exploratory sau lịch sử nhiều vòng trên bốn file; không đánh giá độc lập mới.')
for artifact in audit.ARTIFACTS:
    artifact.update(generator='build_reference_notebook.py',generator_sha256=audit.digest(HERE/'build_reference_notebook.py'),
                    command='python research_workbench_2026_10_07/execute_reference_notebook.py')
audit.json_write(HERE/'results/reference_notebook_figure_manifest.json',{'figures':audit.ARTIFACTS})
display(fig)
audit.plt.close(fig)
print('Trạng thái thật:', 'đạt' if status.all_files_le_2.any() else 'chưa đạt mỗi file≤2%')''')
add('code', '''diagnostics = pd.DataFrame([{'file':x['file'],'GT_count':x['stats']['F0num'],
    'canonical_frames':len(x['times']),'segment_V_frames':int((x['labels']=='v').sum()),
    'segment_UV_frames':int((x['labels']=='uv').sum()),'segment_SIL_frames':int((x['labels']=='sil').sum())} for x in items])
display(diagnostics)
diagnostics.to_csv(HERE/'results/reference_notebook_label_counts.csv',index=False)
print('F0num GT và số tâm khung đoạn V là hai đại lượng cần phân biệt; không ép dự đoán theo các count này.')
print('Notebook chạy đúng source qua Python/display adapter; không phải Jupyter kernel. Không mở test, Drive hoặc PDF.')''')
path = HERE / 'REFERENCE_PIPELINES_LOCAL.ipynb'
assert not path.exists(), 'Preserve existing notebook and user edits'
book = {'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'BT2 WORLD local','language':'python','name':'python3'},'language_info':{'name':'python'}},'cells':cells}
path.write_text(json.dumps(book,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
for cell in cells:
    if cell['cell_type']=='code':
        compile(cell['source'],str(path),'exec')
print('Built and compiled five exact notebook code cells:',path)
