from pathlib import Path

HERE = Path(__file__).resolve().parent
target = HERE / 'amdf_selection_ensemble_controller.py'
assert not target.exists()
source = (HERE / 'amdf_soft_spectral_controller.py').read_text(encoding='utf-8').replace('H44', 'H45').replace('amdf_soft_spectral', 'amdf_selection_ensemble')
start, end = source.index('def registry(family):'), source.index('\n\ndef feature_key')
source = source[:start] + '''def registry(family):
    assert family == 'H45'
    base = {'frame_ms': 3000/70, 'hop_ms': 10, 'pitch_frame_ms': 40}
    return [dict(base, id='praat7_filtered_v0.3', method='control'),
            dict(base, id='amdf_pitch_spectral_p170', method='hard_control')] + [
        dict(base, id=f'amdf_ensemble_k{k:02d}', method='ensemble', top_k=k) for k in (1, 3, 5, 9)]
''' + source[end:]
start, end = source.index('def infer(native, training, option, config):'), source.index('\n\ndef run(')
source = source[:start] + '''def infer(native, training, option, config):
    return anchor_api.infer(native, training, option, config)
''' + source[end:]
start, end = source.index('    native_rows=[]'), source.index('    prediction_cache = {}')
source = source[:start] + source[end:]
source = source.replace("HERE / 'results/H41_experiment.json', HERE / 'results/H41_native_verification.json'", "HERE / 'results/H44_experiment.json', HERE / 'results/H44_spectral_verification.json', HERE / 'results/H44_raw_native_frames.csv', HERE / 'results/H44_fixed_lofo.csv', HERE / 'H44_REGISTRY.json'")
start, end = source.index('    report=['), source.index("    (HERE / f'{family}_REPORT.md')")
source = source[:start] + '''    report=['# H45 — Kết hợp các cấu hình được chọn từ train', '', audit.markdown_table(summary), '',
        'Giữ toàn bộ9member H44, rank chỉ dùng fit_files. TopK1/3/5/9 kết hợp F0 bằng trung bình log2, mask/count/range giữ Praat.30. Lựa chọn K vẫn dùng minimax inner và gate cũ, không dựa tên người/thiết bị hoặc GT held.', '',
        '## Gate', '', '~~~json', json.dumps(decision, indent=2), '~~~', '',
        '## Selection', '', audit.markdown_table(pd.DataFrame([{'outer_held': x['outer_held'], 'selected': x['option']['id']} for x in selections])), '',
        '## Mọi cấu hình fixed', '', audit.markdown_table(fixed[['option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','macro_f1','recall_v','false_voiced_sil']]), '',
        f"Mỗi nested file Average MAPE≤2%: {value['goal_all_nested_files_le_2']}. Nested exploratory trên4train đã xem nhiều lần. Không sửaGT, frozen/original, không dùngtest đểchọnK. Khôngpromote tựđộng.", '',
        'Đầu vào9member H44 đã kiểmtra PCM/FFT; H45 không có nativecall mới. Đọc H45_REGISTRATION.md; membership/ranking từngfit trong H45_fits.json.']
''' + source[end:]
source = source.replace("'algorithm':'Soft NAMDF frequency interpolation with spectral and pitch evidence'", "'algorithm':'Top-K training-ranked H44 member geometric-frequency ensemble'")
source = source.replace("'rollback_repository_commit':'a68f0e529bda5a5ae8dbb8251fb8ed932f7b5254'", "'rollback_repository_commit':'35cb166ccd7968100642765fa42aeacf7fc52323'")
compile(source, str(target), 'exec')
target.write_text(source, encoding='utf-8')
print('Generated H45 runner without changing H44 source')
