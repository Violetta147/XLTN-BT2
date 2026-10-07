from pathlib import Path

HERE=Path(__file__).resolve().parent


def build():
    path=HERE/'yaapt_reference.py'
    assert not path.exists()
    text=(HERE/'rapt_reference.py').read_text(encoding='utf-8').replace('H39','H40').replace('rapt_reference.py','yaapt_reference.py')
    text=text.replace('import sptk_adapter as sptk_api\nimport rapt_adapter as rapt_api','import yaapt_adapter as yaapt_api')
    text=text.replace("{'id':f'rapt_b{threshold:g}','frame_ms':None,'hop_ms':10,'pitch_frame_ms':None,\n         'method':'rapt','voicing_bias':threshold} for threshold in (-.3,0.,.3,.6)",
        "{'id':f'yaapt_f{window}','frame_ms':window,'hop_ms':10,'pitch_frame_ms':35,\n         'method':'yaapt','spectral_frame_ms':window} for window in (25,35,45)")
    text=text.replace("rapt_api.pitch(audio,item['fs'],option['voicing_bias'])","yaapt_api.pitch(audio,item['fs'],option['spectral_frame_ms'])")
    text=text.replace("engine='SPTK4.4 RAPT'","engine='AMFM_decompy pinned YAAPT port'")
    text=text.replace("HERE / 'sptk_adapter.py', HERE / 'rapt_adapter.py', HERE / 'rapt_setup_probe.py', HERE / 'results/rapt_synthetic_probe.json', HERE / 'results/rapt_source_provenance.json'",
        "HERE / 'yaapt_adapter.py', HERE / 'yaapt_setup_probe.py', HERE / 'yaapt_transport_probe.py', HERE / 'results/yaapt_raw_synthetic_probe.json', HERE / 'results/yaapt_synthetic_probe_v2.json', HERE / 'results/yaapt_transport_probe.json', HERE / 'results/yaapt_source_discovery.json', HERE / 'sources/yaapt/amfm_decompy/pYAAPT.py', HERE / 'sources/yaapt/amfm_decompy/basic_tools.py'")
    start=text.index(",'sptk':sptk_api.metadata()")
    end=text.index('}}',start)
    text=text[:start]+",'yaapt':yaapt_api.metadata()"+text[end:]
    start=text.index("    report=['# H40")
    end=text.index("    (HERE / f'{family}_REPORT.md')",start)
    text=text[:start]+'''    report=['# H40 — YAAPT reference port', '',audit.markdown_table(summary),'',
        'Thuật toán kết hợp ứng viên từ phổ và tương quan chuẩn hóa, rồi chọn chuỗi bằng dynamic programming. Đây là whole-pipeline comparison; chỉ grid frame_length 25/35/45 ms thay đổi trong YAAPT, tda_frame_length giữ 35 ms. Đọc YAAPT_SOURCE_NOTE.md và H40_REGISTRATION.md.', '',
        'Raw samp_values giữ UV0; không dùng contour nội suy. Native frames_pos/fs, nearest canonical25/10 trong5ms+mộtmẫu, tie sớm; causal FIR giữ nguyên, không sửa offset bằng LAB. Không fit hoặc matching mean/std/count của held file.', '',
        '## Gate', '', '~~~json',json.dumps(decision,indent=2),'~~~','',
        '## Selections','',audit.markdown_table(pd.DataFrame([{"outer_held":x['outer_held'],"selected":x['option']['id']} for x in selections])),'',
        '## Tất cả cấu hình fixed','',audit.markdown_table(fixed[['option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','macro_f1','recall_v','false_voiced_sil']]),'',
        f"Mỗi nested file Average MAPE≤2%: {value['goal_all_nested_files_le_2']}. Mean≤2% không thay thế điều kiện từng file. Bốn file và lịch sử đã xem khiến nested exploratory; không test tuning hoặc xác minh F0 từng khung.",'',
        'Giữ probe sine/rich octave failures. Transport two-harmonic và zero kiểm tra dữ liệu/UV, không bảo đảm đúng trên tiếng nói. Không promote hoặc thay original baseline. Jev không tham gia vòng này; nhánh MCP vẫn dừng sau lỗi trước đó.','',
        'Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/yaapt_reference.py H40']
''' +text[end:]
    start=text.index('    proof=rapt_api.metadata()')
    end=text.index('    native_api.metadata()',start)
    text=text[:start]+'''    proof=yaapt_api.metadata()
    failed=json.loads((HERE/'results/yaapt_raw_synthetic_probe.json').read_text())
    assert failed['adapter_sha256']==audit.digest(HERE/'sources/yaapt_adapter_v1/yaapt_adapter.py')
    assert failed['generator_sha256']==audit.digest(HERE/'sources/yaapt_adapter_v1/yaapt_setup_probe.py')
    assert all(x['status']=='failure' and x['error_type']=='AssertionError' for x in failed['rows'])
    probe=json.loads((HERE/'results/yaapt_synthetic_probe_v2.json').read_text())
    transport=json.loads((HERE/'results/yaapt_transport_probe.json').read_text())
    assert probe['adapter_sha256']==transport['adapter_sha256']==audit.digest(HERE/'yaapt_adapter.py')
    assert probe['generator_sha256']==audit.digest(HERE/'yaapt_setup_probe.py')
    assert transport['generator_sha256']==audit.digest(HERE/'yaapt_transport_probe.py')
    assert len(probe['rows'])==12 and len(transport['rows'])==4
    assert not probe['real_wav_read'] and not transport['real_wav_read']
    assert all(x['status']=='success' for x in probe['rows'])
    assert all(x['voiced']==0 for x in probe['rows'] if x['signal']=='zero')
    assert all(x['center_voiced']>=56 and x['center_max_error_hz']<3 for x in transport['rows'] if x['signal']=='two173')
    assert all(x['center_max_error_hz']>50 for x in transport['rows'] if x['signal']=='sine173')
    assert all(x['center_max_error_hz']>80 for x in probe['rows'] if x['signal']=='rich173')
    assert len(proof['defaults'])==34
''' +text[end:]
    text=text.replace("'18_synthetic_native_calls_checked':True","'16_actual_backend_probes_checked':True,'octave_failures_retained':True,'metadata_failure_before_backend_retained':True")
    text=text.replace('PASS nativeRAPTidentity/18syntheticprobes/AMDFparity/nearesttime; no H40 BT2 measured.',
        'PASS YAAPT source/transport/timing/zero and retained octave failures; no H40 BT2 measured.')
    text=text.replace("'baseline_commit':'ac20514'","'baseline_commit':'c74467a'").replace("'rollback_repository_commit':'ac20514'","'rollback_repository_commit':'c74467a'")
    text=text.replace("'algorithm':'SPTK4.4 native RAPT NCCF and dynamic programming'","'algorithm':'YAAPT AMFM_decompy 1.0.12.2 pinned Python port'")
    assert 'rapt_api' not in text and 'sptk_api' not in text
    compile(text,str(path),'exec')
    path.write_text(text,encoding='utf-8')


if __name__=='__main__':
    build()
