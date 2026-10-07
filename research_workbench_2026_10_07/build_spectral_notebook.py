import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'AMDF_SPECTRAL_LOCAL.ipynb'
    assert not path.exists()
    book=json.loads((HERE/'AMDF_ANCHOR_LOCAL.ipynb').read_text(encoding='utf-8'))
    code=[cell for cell in book['cells'] if cell['cell_type']=='code']
    for cell in code:
        cell['source']=cell['source'].replace('amdf_anchor_notebook','spectral_notebook').replace('build_amdf_anchor_notebook','build_spectral_notebook').replace('execute_amdf_anchor_notebook','execute_spectral_notebook')
        cell['execution_count']=None
        cell['outputs']=[]
    code[0]['source']=code[0]['source'].replace('import amdf_praat_anchor as reference',
        'import amdf_pitch_spectral_controller as reference\nimport amdf_spectral_controller as spectral\nimport amdf_anchor as anchor')
    code[0]['source']=code[0]['source'].replace("families={'H41':reference}","families={'H42':spectral,'H43':reference}")
    code[0]['source']=code[0]['source'].replace("reference.anchor_api.OUTPUT_PREFIX='spectral_notebook'\nreference.anchor_api.SOURCE_CACHE.clear()\nreference.anchor_api.CURVE_CACHE.clear()",
        "anchor.OUTPUT_PREFIX='spectral_notebook'\nanchor.CURVE_CACHE.clear()\nfor module in families.values():\n    module.anchor_api.SOURCE_CACHE.clear()\n    module.anchor_api.FEATURE_CACHE.clear()")
    code[1]['source']='''fresh_source_calls={}
for item in items:
    fs,audio=core.load_audio(core.TRAIN/item['file'])
    times,gate,call=reference.native_api.pitch(core.TRAIN/item['file'],'filtered',.3)
    fresh_source_calls['praat7_filtered_v0.3|'+item['file']]=call
    data,curve_proofs={},{}
    for window in (25,40):
        evidence=anchor.curves(item,audio,times,gate,window)
        data[window]=dict(np.load(HERE/evidence['path'],allow_pickle=False))
        curve_proofs[str(window)]={'path':evidence['path'],'sha256':evidence['sha256']}
    ratios=np.full(len(times),np.nan)
    frame_hashes=np.full(len(times),'',dtype='<U64')
    length=int(data[40]['frame_samples'])
    import hashlib
    for i in np.flatnonzero((gate>=70)&(gate<=400)):
        start=int(data[40]['starts'][i])
        if 0<=start and start+length<=len(audio):
            frame=np.ascontiguousarray(audio[start:start+length],dtype=np.float64)
            frame_hashes[i]=hashlib.sha256(frame.tobytes()).hexdigest()
            ratios[i]=reference.anchor_api.high_frequency_ratio(frame,fs)
    spectral_path=HERE/f'results/spectral_notebook_spectral_{Path(item["file"]).stem}.npz'
    assert not spectral_path.exists(),'Preserve completed replay features'
    np.savez_compressed(spectral_path,times=times,gate_frequency=gate,ratio=ratios,
                        starts=data[40]['starts'],frame_samples=length,frame_sha256=frame_hashes,fs=fs)
    for module in families.values():
        rule=module.anchor_api
        rule.SOURCE_CACHE[('praat7_filtered_v0.3',item['file'])]=(times,gate,call)
        rule.FEATURE_CACHE[item['file']]={'data':data,'times':times,'gate':gate,'ratio':ratios,
            'proof':{'path':str(spectral_path.relative_to(HERE)),'sha256':audit.digest(spectral_path),
                     'curve_paths':curve_proofs,'H41_experiment_sha256':audit.digest(HERE/'results/H41_experiment.json'),
                     'rule_sha256':audit.digest(rule.__file__)}}
print('Recomputed 4 fresh Praat source groups, 8 raw NAMDF curve groups and 4 spectral feature groups.')
''' +code[1]['source']
    code[1]['source']=code[1]['source'].replace("native_calls['|'.join(key)]=features[key]['native_call']",
        "native_calls['|'.join(key)]=dict(features[key]['native_call'],historical_native_call=False,new_native_call=False,gate_source='fresh notebook Praat call shared among options')")
    code[1]['source']=code[1]['source'].replace('PASS44 fixed rows','PASS60 fixed rows')
    code[2]['source']=code[2]['source'].replace('len(table)==48','len(table)==68')
    code[3]['source']=code[3]['source'].replace("labels=['Praat .30']+[f'w{x[\"amdf_window_ms\"]}/b{x[\"agreement_cents\"]}' for x in registries[family][1:]]",
        "labels=['Praat .30','25ms','40ms']+[f'HF{int(x[\"hf_threshold\"]*100):02d}/p{x.get(\"minimum_gate_hz\",0)}' for x in registries[family][3:]]")
    code[4]['source']=code[4]['source'].replace("'source_calls':{key[0]+'|'+key[1]:value[2] for key,value in reference.anchor_api.SOURCE_CACHE.items()}",
        "'source_calls':fresh_source_calls,'new_actual_Praat_calls':4,'new_curve_groups':8,'new_spectral_groups':4")
    code[4]['source']=code[4]['source'].replace('len(native_calls)==40 and len(fit_logs)==48','len(native_calls)==56 and len(fit_logs)==68')
    code[4]['source']=code[4]['source'].replace('PASS48 measured rows: H24 AMDF control4 + H41 fixed40 + nested4.',
        'PASS68 measured rows: H24 AMDF control4 + H42/H43 fixed56 + nested8.')
    code[4]['source']=code[4]['source'].replace('4 actual Praat calls/40 derived option groups/12 NAMDF feature groups',
        '4 actual fresh Praat calls/56 derived option groups/8 NAMDF feature groups/4 spectral groups')
    markdown=[
        '# AMDF theo phổ và cao độ — chạy local từ WAV\n\nNAMDF là sai khác biên độ trung bình đã chuẩn hóa trên phần chồng lấp. Praat quyết định hữu thanh và làm mốc cao độ; AMDF chỉ tinh chỉnh cao độ. H42 chọn25/40ms theo tỷ lệ phổ, H43 thêm điều kiện cao độ từng khung. LAB có thống kê cả file và nhãn đoạn, chưa có F0 chuẩn từng thời điểm. Average MAPE là trung bình lỗi phần trăm mean/std/count, không phải lỗi cao độ từng khung. Không đọc test trong notebook.',
        '## Tính lại từ WAV\n\nBốn call Praat mới, NAMDF raw25/40ms và tỷ lệ phổ40ms được tính lại. H24control AMDF được fit chỉ bằng3file khác. Các cấu hình H42/H43 đã đăng ký, không thêm grid. Source cells được commit/push trước replay; output sẽ được verifier đối chiếu sau chạy.',
        '## Dùng lựa chọn giữ riêng file đã lưu\n\nFixed dùng cùng cấu hình cho4file; nested dùng lựa chọn từ3file khác. Notebook replay các lựa chọn đã chốt, không chọn best trên chính file đang chấm. H43fixed170Hz đạt từngfile≤2%, nhưng outerstudio_M1 chọn140Hz vànestedtargetFAIL; không đánh đồng hai kết quả.',
        '## Figures từ phép tính vừa chạy\n\nMỗi thành phần MAPE chia3, tổng làAverage. Giữ đủ các cấu hình và kết quả không đạt. Ngưỡng phổ/cao độ hiển thị theo registry; chúng không phân loại nam/nữ hoặc thiết bị.',
        '## Provenance và giới hạn\n\nPython exec nguyên code cell với headlessdisplay, không phải Jupyterkernel. Bốn train đã được dùng nhiều vòng: nested vẫnexploratory. Không sửa nhãn, original/frozen, không tune test, khôngPDF/Drive/deeplearning/MCP retry. ĐọcH42/H43_REPORT.md vàH43_ERROR_ANALYSIS.md để thấy đánh đổi vàselection failure.'
    ]
    for cell,text in zip([c for c in book['cells'] if c['cell_type']=='markdown'],markdown):
        cell['source']=text
    book['metadata'].pop('bt2_local_execution',None)
    for i,cell in enumerate(code):
        compile(cell['source'],f'AMDF_SPECTRAL_LOCAL:cell{i}','exec')
    path.write_text(json.dumps(book,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    executor=(HERE/'execute_amdf_anchor_notebook.py').read_text().replace('AMDF_ANCHOR_LOCAL','AMDF_SPECTRAL_LOCAL').replace('H41 AMDF anchor notebook','H42/H43 spectral AMDF notebook')
    (HERE/'execute_spectral_notebook.py').write_text(executor,encoding='utf-8')
    verifier=(HERE/'verify_amdf_anchor_notebook.py').read_text().replace('AMDF_ANCHOR_LOCAL','AMDF_SPECTRAL_LOCAL').replace('amdf_anchor_notebook','spectral_notebook')
    verifier=verifier.replace('==48','==68').replace("for family in ('H41',):","for family in ('H42','H43'):").replace("len(manifest['figures'])==1","len(manifest['figures'])==2")
    start=verifier.index("    experiment=json.loads((HERE/'results/H41_experiment.json')")
    end=verifier.index("    assert provenance['test_read']",start)
    verifier=verifier[:start]+'''    assert provenance['new_actual_Praat_calls']==4 and provenance['new_curve_groups']==8 and provenance['new_spectral_groups']==4
    assert len(provenance['native_calls'])==56 and len(provenance['source_calls'])==4
    checked_curves,checked_spectral=set(),set()
    for identity,call in provenance['native_calls'].items():
        module,option,file=identity.split('|')
        family='H43' if module=='amdf_pitch_spectral_controller' else 'H42'
        experiment=json.loads((HERE/f'results/{family}_experiment.json').read_text())
        expected=experiment['native_calls'][option+'|'+file]
        assert call['returncode']==0 and call['exe_sha256']==provenance['praat_native_sha256']
        assert call['command']==expected['command'] and call['script_sha256']==digest(call['command'][2])
        assert call['historical_native_call'] is False and call['new_native_call'] is False
        for key in ('output_f0_sha256','rule_sha256','source','selected_windows','selected_curve_indices'):
            assert call[key]==expected[key],key
        evidence=call['spectral_evidence']
        assert digest(HERE/evidence['path'])==evidence['sha256']
        for window,proof in evidence['curve_paths'].items():
            assert digest(HERE/proof['path'])==proof['sha256']
            if proof['path'] not in checked_curves:
                fresh=dict(np.load(HERE/proof['path'],allow_pickle=False))
                prior=dict(np.load(HERE/expected['spectral_evidence']['curve_paths'][window]['path'],allow_pickle=False))
                assert set(fresh)==set(prior)
                for key in fresh:
                    if fresh[key].dtype.kind=='f':
                        assert np.allclose(fresh[key],prior[key],atol=1e-12,equal_nan=True),key
                    else:
                        assert np.array_equal(fresh[key],prior[key]),key
                checked_curves.add(proof['path'])
        if evidence['path'] not in checked_spectral:
            fresh=dict(np.load(HERE/evidence['path'],allow_pickle=False))
            prior=dict(np.load(HERE/expected['spectral_evidence']['path'],allow_pickle=False))
            assert set(fresh)==set(prior)
            for key in fresh:
                if fresh[key].dtype.kind=='f':
                    assert np.allclose(fresh[key],prior[key],atol=1e-12,equal_nan=True),key
                else:
                    assert np.array_equal(fresh[key],prior[key]),key
            checked_spectral.add(evidence['path'])
    assert len(checked_curves)==8 and len(checked_spectral)==4
    prior=json.loads((HERE/'results/H43_experiment.json').read_text())
    for identity,call in provenance['source_calls'].items():
        assert call['command']==prior['source_calls'][identity]['command']
        assert call['stdout_sha256']==prior['source_calls'][identity]['stdout_sha256']
''' +verifier[end:]
    compile(verifier,'verify_spectral_notebook.py','exec')
    (HERE/'verify_spectral_notebook.py').write_text(verifier,encoding='utf-8')
    print('Built five source-only cells and executor; notebook not run')


if __name__=='__main__':
    main()
