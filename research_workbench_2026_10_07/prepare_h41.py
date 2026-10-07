from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'amdf_praat_anchor.py'
    assert not path.exists()
    text=(HERE/'yaapt_reference.py').read_text().replace('H40','H41').replace('yaapt_reference.py','amdf_praat_anchor.py')
    text=text.replace('import yaapt_adapter as yaapt_api','import amdf_anchor as anchor_api').replace('import argparse','import argparse\nimport hashlib',1)
    start=text.index('def registry(')
    end=text.index('\n\ndef project(',start)
    text=text[:start]+'''def registry(family):
    assert family=='H41'
    return [{'id':'praat7_filtered_v0.3','frame_ms':3000/70,'hop_ms':10,'pitch_frame_ms':3000/70,
             'method':'control','voicing_threshold':.3}]+[
        {'id':f'amdf_anchor_w{window}_b{band}','frame_ms':3000/70,'hop_ms':10,'pitch_frame_ms':window,
         'method':'amdf_anchor','agreement_cents':band,'amdf_window_ms':window}
        for window in (25,40,55) for band in (50,100,200)]


def feature_key(option):
    return option['id']


def extract(item,audio,option):
    key=('praat7_filtered_v0.3',item['file'])
    if key not in anchor_api.SOURCE_CACHE:
        anchor_api.SOURCE_CACHE[key]=native_api.pitch(core.TRAIN/item['file'],'filtered',.3)
    times,gate,call=anchor_api.SOURCE_CACHE[key]
    frequency=gate.copy()
    source=np.where(gate>0,'praat_control','unvoiced').astype('<U32')
    selected=np.full(len(gate),-1,dtype=int)
    evidence=None
    if option['method']=='amdf_anchor':
        data=anchor_api.curves(item,audio,times,gate,option['amdf_window_ms'])
        evidence={k:v for k,v in data.items() if k not in ('times','lags','curves','starts')}
        for i in np.flatnonzero((gate>=70)&(gate<=400)):
            curve=data['curves'][i]
            if not np.isfinite(curve).all():
                source[i]='praat_window_unsupported'
                continue
            candidates,dips,indices=anchor_api.candidates(data['lags'],curve,item['fs'])
            frequency[i],source[i],chosen=anchor_api.choose(gate[i],candidates,dips,option['agreement_cents'])
            if chosen>=0:
                selected[i]=indices[chosen]
    pred=(frequency>=70)&(frequency<=400)
    assert np.array_equal(pred,(gate>=70)&(gate<=400))
    log=dict(call,engine='Praat .30 with local NAMDF candidate selection',AMDF_evidence=evidence,
             rule_sha256=audit.digest(anchor_api.__file__),gate_cached=True,source=source.tolist(),
             selected_curve_indices=selected.tolist(),output_f0_sha256=hashlib.sha256(frequency.tobytes()).hexdigest())
    return dict(item,times=times,preprocess=option['id'],native_pred=pred,native_f0=np.where(pred,frequency,np.nan),
                raw_native_frequency=frequency,raw_native_voiced=frequency>0,native_call=log,
                range_rejected_frames=int(((frequency>0)&~pred).sum()))
''' +text[end:]
    text=text.replace("'praat7_filtered_v0.45'","'praat7_filtered_v0.3'")
    text=text.replace("HERE/'results/H30_fixed_lofo.csv'","HERE/'results/H31_fixed_lofo.csv'")
    text=text.replace("HERE / 'yaapt_adapter.py', HERE / 'yaapt_setup_probe.py', HERE / 'yaapt_transport_probe.py', HERE / 'results/yaapt_raw_synthetic_probe.json', HERE / 'results/yaapt_synthetic_probe_v2.json', HERE / 'results/yaapt_transport_probe.json', HERE / 'results/yaapt_source_discovery.json', HERE / 'sources/yaapt/amfm_decompy/pYAAPT.py', HERE / 'sources/yaapt/amfm_decompy/basic_tools.py'",
                      "HERE / 'amdf_anchor.py', HERE / 'results/H41_precheck.json'")
    text=text.replace(",'yaapt':yaapt_api.metadata()",'')
    text=text.replace("'source_calls':", "'source_calls':")
    at=text.index("             'range_rejected_frames':")
    text=text[:at]+"             'source_calls':{key[0]+'|'+key[1]:v[2] for key,v in anchor_api.SOURCE_CACHE.items()},\n"+text[at:]
    start=text.index("    report=['# H41")
    end=text.index("    (HERE / f'{family}_REPORT.md')",start)
    text=text[:start]+'''    report=['# H41 — NAMDF candidates under fixed Praat voicing', '',audit.markdown_table(summary),'',
        'AMDF gate không thay: Praatfiltered.30 giữ V/UV/count. NAMDF raw40/55/25ms được tính tại tâm Praat, dùng localdip có F0 trongband50/100/200cents. Chọn dip thấp nhất, tie khoảng cáchcents rồiF0; khôngứngviên hoặc thiếuwindow giữPraat. Đây là engineeringhypothesis từkernelnotebook, không AAMDFpaperreplication.', '',
        '## Gate','','~~~json',json.dumps(decision,indent=2),'~~~','',
        '## Selection','',audit.markdown_table(pd.DataFrame([{"outer_held":x['outer_held'],"selected":x['option']['id']} for x in selections])),'',
        '## Mọi cấu hình fixed','',audit.markdown_table(fixed[['option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','macro_f1','recall_v','false_voiced_sil']]),'',
        f"Mỗi nested file Average MAPE≤2%: {value['goal_all_nested_files_le_2']}. Mean nhỏ không đủ. Bốn trainfiles/lịch sử đã xem làmnestedexploratory; LAB chỉfile-stat/nhãn đoạn, khôngF0chuẩntừngkhung.",'',
        'Nguồn/mapping ở AMDF_ANCHOR_SOURCE_NOTE.md. Curvesinput/start/time/hash vàrawfusion giữ đểverify độc lập. Khôngclip/resample/noise/GTmatching/file routing/promote/test/Drive/deep learning/PDF hoặcMCP retry.','',
        'Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/amdf_praat_anchor.py H41']
''' +text[end:]
    start=text.index('def check():')
    end=text.index("if __name__ == '__main__':",start)
    text=text[:start]+'''def check():
    import amdf_dual_window
    amdf_dual_window.check()
    native_api.metadata()
    core.init_functions()
    tests=[]
    for fs in (16000,44100):
        for window in (25,40,55):
            t=np.arange(round(fs*window/1000))/fs
            audio=.2*np.sin(2*np.pi*173*t)+.1*np.sin(2*np.pi*346*t+.2)
            lags,curve=core.AMDF['normalized_amdf'](audio,fs)
            frequencies,dips,indices=anchor_api.candidates(lags,curve,fs)
            estimated,tag,_=anchor_api.choose(173,frequencies,dips,100)
            assert tag=='amdf_dip' and abs(estimated-173)<2
            zl,zc=core.AMDF['normalized_amdf'](np.zeros(len(t)),fs)
            assert not len(anchor_api.candidates(zl,zc,fs)[0])
            tests.append({'fs':fs,'window_ms':window,'estimate_hz':estimated})
    assert anchor_api.choose(173,np.array([86.5]),np.array([.01]),200)[0]==173
    for band in (50,100,200):
        inside=173*2**(band/1200)
        outside=173*2**((band+.01)/1200)
        assert anchor_api.choose(173,np.array([inside]),np.array([.1]),band)[1]=='amdf_dip'
        assert anchor_api.choose(173,np.array([outside]),np.array([.1]),band)[0]==173
    assert anchor_api.choose(0,np.array([173.]),np.array([.1]),100)[0]==0
    dummy={'times':np.array([.01,.02]),'fs':16000}
    pp,ff,support=project(dummy,{'times':np.array([.015,.04])},np.array([True,True]),np.array([170.,190.]),10)
    assert pp[0] and ff[0]==170 and not pp[1] and np.isnan(ff[1])
    audit.json_write(HERE/'results/H41_precheck.json',{'family':'H41','runner_sha256':audit.digest(__file__),
        'rule_sha256':audit.digest(anchor_api.__file__),'known_tone_checks':tests,'zero_half_band_boundary_uv_and_time_checked':True,
        'historical_AMDF_parity_checked':True,'H41_real_WAV_measured':False})
    print('PASS AMDF known tone/zero/half/band/UV/time and frozen AMDF parity; no H41 measurement.')


''' +text[end:]
    text=text.replace("'baseline_commit':'c74467a'","'baseline_commit':'4526d57'").replace("'rollback_repository_commit':'c74467a'","'rollback_repository_commit':'4526d57'")
    text=text.replace("'algorithm':'YAAPT AMFM_decompy 1.0.12.2 pinned Python port'","'algorithm':'NAMDF local candidate selection under fixed Praat filtered .30 gate'")
    assert 'yaapt_api' not in text
    compile(text,str(path),'exec')
    path.write_text(text,encoding='utf-8')
    print('Built H41 source; no measurement.')


if __name__=='__main__':
    main()
