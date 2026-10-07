from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    target=HERE/'amdf_spectral_controller.py'
    assert not target.exists()
    source=(HERE/'amdf_praat_anchor.py').read_text(encoding='utf-8')
    source=source.replace('H41','H42').replace('amdf_praat_anchor.py','amdf_spectral_controller.py')
    source=source.replace('import amdf_anchor as anchor_api','import amdf_spectral as anchor_api')
    start=source.index('def registry(')
    end=source.index('\n\ndef project(',start)
    source=source[:start]+'''def registry(family):
    assert family=='H42'
    return [{'id':'praat7_filtered_v0.3','frame_ms':3000/70,'hop_ms':10,'pitch_frame_ms':3000/70,
             'method':'control','voicing_threshold':.3}]+[
        {'id':f'amdf_anchor_w{window}_b200','frame_ms':3000/70,'hop_ms':10,'pitch_frame_ms':window,
         'method':'fixed_window','amdf_window_ms':window} for window in (25,40)]+[
        {'id':f'amdf_spectral_hf{int(threshold*100):02d}','frame_ms':3000/70,'hop_ms':10,
         'pitch_frame_ms':40,'method':'spectral_window','hf_threshold':threshold}
        for threshold in (.05,.10,.20,.35)]


def feature_key(option):
    return option['id']


def extract(item,audio,option):
    return anchor_api.extract(item,audio,option)
''' +source[end:]
    source=source.replace("HERE / 'amdf_anchor.py'", "HERE / 'amdf_spectral.py', HERE / 'amdf_anchor.py', HERE / 'results/H41_experiment.json', HERE / 'results/H41_native_verification.json'")
    start=source.index('    report=[')
    end=source.index("    (HERE / f'{family}_REPORT.md')",start)
    source=source[:start]+'''    report=['# H42 — Chọn cửa sổ NAMDF theo năng lượng phổ', '',audit.markdown_table(summary),'',
        'Tỷ lệ năng lượng trên1kHz từ raw40ms, bỏDC, Hann, FFT một phía có trọng số đối xứng. Tỷ lệ thấp dùng40ms, còn lại25ms; undefined dùng25ms. Band200cents/Praat.30/voicing/count và projection giữ H41. Không dựa tênfile/giới tính/device/LAB/GT lúc infer. Đây là engineering hypothesis, không paper replication.', '',
        '## Gate','','~~~json',json.dumps(decision,indent=2),'~~~','',
        '## Selection','',audit.markdown_table(pd.DataFrame([{"outer_held":x['outer_held'],"selected":x['option']['id']} for x in selections])),'',
        '## Mọi cấu hình fixed','',audit.markdown_table(fixed[['option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','macro_f1','recall_v','false_voiced_sil']]),'',
        f"Mỗi nested file Average MAPE≤2%: {value['goal_all_nested_files_le_2']}. MAPE là thống kê mean/std/count, không F0 từng khung. Nested exploratory trên4train đã xem nhiều lần.",'',
        'H41 curves/gate được tái sử dụng có hash; H42 có0nativecall mới,4historicalsourcegroups. Source note: AMDF_SPECTRAL_SOURCE_NOTE.md. Dữ liệu QA test đã đọc mô tả ở lượt trước, không dùng chọn feature/grid/ngưỡng. Không test inference/tuning hoặc sửa ground truth. Giữ failures/original/frozen, không promote tự động, khôngMCP retry/Drive/PDF/deep learning.', '',
        'Lệnh: C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/amdf_spectral_controller.py H42']
''' +source[end:]
    start=source.index('def check():')
    end=source.index("if __name__ == '__main__':",start)
    source=source[:start]+'''def check():
    anchor_api.check()


''' +source[end:]
    source=source.replace("'registered_utc':", "'registered_utc':")
    source=source.replace("'algorithm':'NAMDF local candidate selection under fixed Praat filtered .30 gate'", "'algorithm':'NAMDF spectral window controller under fixed Praat filtered .30 gate'")
    source=source.replace("'4526d57'","'18fe81a'")
    source=source.replace("'wall_time_s': time.perf_counter() - started", "'new_native_calls':0, 'historical_source_groups':4, 'wall_time_s': time.perf_counter() - started")
    target.write_text(source,encoding='utf-8')
    compile(source,str(target),'exec')
    print('Built H42 source; benchmark not run')


if __name__=='__main__':
    main()
