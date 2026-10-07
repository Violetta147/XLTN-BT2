import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parent


def main():
    path=HERE/'YAAPT_AMDF_LOCAL.ipynb'
    assert not path.exists(),'Preserve notebook'
    template=json.loads((HERE/'BOUNDED_PITCH_LOCAL.ipynb').read_text(encoding='utf-8'))
    inherited=[cell['source'] for cell in template['cells'] if cell['cell_type']=='code']
    code1=f'''from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
REPO=Path({str(REPO)!r})
HERE=REPO/'research_workbench_2026_10_07'
sys.path.insert(0,str(HERE))
import amdf_dual_window as dual
import yaapt_reference as reference
core,audit=dual.core,dual.audit
items=core.load_training()
by_name={{x['file']:x for x in items}}
config=json.loads((core.RESULTS/'frozen_config.json').read_text())['models']['AMDF_energy']['config']
families={{'H40':reference}}
receipts={{f:json.loads((HERE/f'results/{{f}}_experiment.json').read_text()) for f in families}}
for receipt in receipts.values():
    for relative,expected in receipt['code_sha256'].items():
        assert audit.digest(REPO/relative)==expected,relative
    for file,expected in receipt['data_sha256'].items():
        assert audit.digest(core.TRAIN/file)==expected,file
native_proof=reference.native_api.metadata()
yaapt_proof=reference.yaapt_api.metadata()
print('Local Python:',sys.executable,'; Praat',native_proof['version_stdout'],'; YAAPT port',yaapt_proof['package_version'])
display(pd.DataFrame([{{'file':x['file'],'fs':x['fs'],**x['stats'],'segment_V_frames':int((x['labels']=='v').sum())}} for x in items]))
'''
    code2=inherited[1].replace('PASS28 fixed rows','PASS20 fixed rows')
    code3=inherited[2].replace('bounded_notebook','yaapt_notebook').replace('len(table)==32','len(table)==24')
    code4=inherited[3].replace('bounded_notebook','yaapt_notebook').replace('build_bounded_notebook','build_yaapt_notebook').replace('execute_bounded_notebook','execute_yaapt_notebook')
    start=code4.index("    labels=['Praat'")
    end=code4.index('\n    fixed=',start)
    code4=code4[:start]+"    labels=['Praat .45']+[f'YAAPT{x[\"frame_ms\"]}' for x in registries[family][1:]]"+code4[end:]
    code4=code4.replace('band/alpha ghi trên trục x.','spectral window ghi trên trục x; TDA35ms giữ.')
    code5='''source_hashes={str(Path(m.__file__).relative_to(REPO)):audit.digest(m.__file__) for m in (dual,reference,core,audit)}
source_hashes.update({key:value for receipt in receipts.values() for key,value in receipt['code_sha256'].items()})
audit.json_write(HERE/'results/yaapt_notebook_provenance.json',{
    'source_sha256':source_hashes,'wav_sha256':{x['file']:audit.digest(core.TRAIN/x['file']) for x in items},
    'native_calls':native_calls,'fit_logs':fit_logs,'praat_native_sha256':native_proof['exe_sha256'],
    'yaapt_port_commit':yaapt_proof['python_port_commit'],'test_read':False,'new_grid_or_selection':False})
assert len(native_calls)==16 and len(fit_logs)==24
print('PASS24 measured rows: H24 AMDF control4 + H40 fixed16 + nested4.')
print('Native/backend16 calls, source/WAV/fit exclusions/contours محفوظ provenance; original/frozen giữ.')
'''.replace('محفوظ','đã lưu trong')
    texts=[
        '# YAAPT và AMDF: tái lập từ WAV\n\nF0 là tần số cơ bản. V/UV/SIL là hữu thanh/vô thanh/khoảng lặng. YAAPT dùng ứng viên từ phổ và tương quan chuẩn hóa (tìm chu kỳ), rồi quy hoạch động chọn chuỗi qua thời gian. AMDF dùng chênh lệch biên độ trung bình theo độ trễ. Notebook đo lại H24 AMDF và toàn bộ H40 đã đăng ký; không mở grid mới. Average MAPE trung bình lỗi của mean/std(ddof0)/count; mục tiêu mỗi file≤2%. LAB không có F0 chuẩn từng khung.',
        '## Tính lại mọi cấu hình fixed\n\nH24 AMDF fit bằng ba file khác. YAAPT/Praat không fit theo nhãn. SourceYAAPT1.0.12.2/pin5c6c9bc, frame_length25/35/45 và tda35, hop10ms/range70–400. Spectral tracking dùng2×frame_size. Float64 normalized PCM giữ; lấy samp_values UV0, không nội suy lấpUV. Native centers ghép gần nhất vào lưới chấm25/10 trong5ms+mộtmẫu, hòa chọn sớm. Causal FIR/padding/vendorDP giữ. Không resample/clip/noise/offset theoLAB.',
        '## Chấm file được giữ riêng\n\nNested giữ một outer file ngoài mọi lựa chọn; ba file còn lại chọn option theo minimax lỗi từng file rồi mean/ID. Notebook dùng đúng choice đã lưu, không chọn best theo held file. Lịch sử đã xem bốn file khiến nested vẫn exploratory, chưa xác nhận trên corpus mới.',
        '## Các thành phần lỗi\n\nMỗi cột cộng lỗi mean/std/count chia3; chiều cao là Average MAPE. Đường2% áp dụng mỗi file. Fixed là đánh giá một cấu hình chung, khác nested. Giữ mọi cấu hình thất bại. Không ghép riêng bestphone và beststudio theo chính kết quả held.',
        '## Provenance\n\nLưu input/source/params/fit/calls/contours để đối chiếu độc lập. AMDF thực sự tính lại từ WAV, không sao chép bảng. Thống kê gầnGT không xác minh từng cao độ đúng.',
        '## Nguồn và giới hạn\n\nYAAPT_SOURCE_NOTE.md có paperabstract DOI10.1121/1.2916590, authorHTML/manual, pinnedMITsource và workflowcitation K-Dense. Không fullpaper/PDF extraction. Probe rich/sine subharmonic failures giữ; zero/two-harmonic thành công không bảo đảm tiếng nói. H40_REPORT.md/H40_ERROR_ANALYSIS.md tách fixed/nested. Notebook chạy năm cell nguyênsource bằngPythonexec/headlessdisplay, khôngJupyterkernel. Khôngtest/Drive/deep learning/Jev retry; originalnotebooks/frozen giữ. NhãnF/M/device chỉ bốn quan sát, chưa đủ suy rộng.'
    ]
    cells=[]
    for index,text in enumerate(texts):
        cells.append({'cell_type':'markdown','id':f'yaapt-text-{index}','metadata':{},'source':text+'\n'})
        if index<5:
            source=[code1,code2,code3,code4,code5][index]
            compile(source,f'YAAPT cell{index}','exec')
            cells.append({'cell_type':'code','id':f'yaapt-code-{index}','metadata':{},'source':source,'execution_count':None,'outputs':[]})
    metadata={'kernelspec':{'display_name':'Python 3 local','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.13.11'}}
    path.write_text(json.dumps({'cells':cells,'metadata':metadata,'nbformat':4,'nbformat_minor':5},ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    execute=(HERE/'execute_bounded_notebook.py').read_text().replace('BOUNDED_PITCH_LOCAL','YAAPT_AMDF_LOCAL').replace('H38 bounded notebook','H40 YAAPT notebook')
    (HERE/'execute_yaapt_notebook.py').write_text(execute,encoding='utf-8')
    verify=(HERE/'verify_bounded_notebook.py').read_text().replace('BOUNDED_PITCH_LOCAL','YAAPT_AMDF_LOCAL').replace('bounded_notebook','yaapt_notebook').replace('H38','H40').replace('==32','==24')
    start=verify.index("    sptk_proof=json.loads")
    end=verify.index("    assert provenance['test_read']",start)
    verify=verify[:start]+'''    assert digest(native_proof['exe'])==provenance['praat_native_sha256']
    proof=json.loads((HERE/'results/yaapt_source_discovery.json').read_text())
    experiment=json.loads((HERE/'results/H40_experiment.json').read_text())
    assert provenance['yaapt_port_commit']==proof['github_commit']
    assert len(provenance['native_calls'])==16
    for identity,call in provenance['native_calls'].items():
        file=identity.split('|')[-1]
        option=identity.split('|')[-2]
        expected=experiment['native_calls'][option+'|'+file]
        if option.startswith('praat'):
            assert call['returncode']==0 and call['exe_sha256']==provenance['praat_native_sha256']
            assert call['command']==expected['command'] and call['script_sha256']==digest(call['command'][2])
        else:
            from scipy.io import wavfile
            fs,pcm=wavfile.read(REPO/'TinHieuHuanLuyen'/file)
            assert pcm.dtype==np.int16 and pcm.ndim==1 and call['backend_called'] is True
            assert call['input_sha256']==hashlib.sha256(np.ascontiguousarray(pcm.astype(np.float64)/32768).tobytes()).hexdigest()
            for key in ('parameters','frame_positions_samples','frame_size_samples','hop_samples','f0_sha256','source_sha256','python_port_commit','output_attribute','half_double_flags'):
                assert call[key]==expected[key],key
            assert call['adapter_sha256']==digest(HERE/'yaapt_adapter.py') and call['input_unchanged'] is True
''' +verify[end:]
    compile(verify,'verify_yaapt_notebook.py','exec')
    (HERE/'verify_yaapt_notebook.py').write_text(verify,encoding='utf-8')
    print('Created source-only YAAPT notebook, five code cells, executor and verifier; no new measurement.')


if __name__=='__main__':
    main()
