from pathlib import Path

HERE = Path(__file__).resolve().parent
target = HERE / 'augmented_voicing_controller.py'
assert not target.exists()
source = (HERE / 'amdf_augmented_ensemble_controller.py').read_text().replace('H46', 'H47').replace('amdf_augmented_ensemble', 'augmented_voicing')
start = source.index('def registry(family):')
end = source.index('\n\ndef feature_key', start)
source = source[:start] + '''def registry(family):
    assert family == 'H47'
    base = {'frame_ms': 3000/70, 'hop_ms': 10, 'pitch_frame_ms': 40}
    return [dict(base, id='praat7_filtered_v0.3', method='control'),
            dict(base, id='amdf_pitch_spectral_p170', method='hard_control')] + [
        dict(base, id=f'voicing_{tag}_p{int(threshold*100):02d}', method='logistic', augmented=augmented, threshold=threshold)
        for tag, augmented in [('clean', False), ('aug', True)] for threshold in (.25, .5)]
''' + source[end:]
source = source.replace("HERE / 'build_h47_augmentation.py'", "HERE / 'augmented_voicing.py'").replace("HERE / 'results/H47_augmentation_manifest.json'", "HERE / 'results/H46_augmentation_manifest.json'").replace("HERE / 'results/H47_augmented_member_metrics.csv'", "HERE / 'results/H46_augmented_member_metrics.csv'")
source = source.replace("'new_native_calls':12, 'augmentation_proof':anchor_api.BANK_PROOF", "'new_native_calls':0, 'fit_augmentation_source':'H46 hash-verified waveform and gate bank'")
source = source.replace('goal_all_nested_files_le_2', 'goal_all_nested_files_lt_2').replace('.average_mape<=2', '.average_mape<2')
source = source.replace('Average MAPE≤2%', 'Average MAPE<2%')
source = source.replace("'rollback_repository_commit':'3d03ad098ba44c637880803085a99cb2fdc34f4b'", "'rollback_repository_commit':'ea21067f6589e19a5252eec6596e20acdbf400ce'")
source = source.replace("'algorithm':'Top-K H44 ensemble ranked using origin-grouped noise augmentation in fit pool'", "'algorithm':'Origin-balanced logistic rejection of Praat voiced frames; fixed hard170 pitch; clean versus H46 augmented fit; strict target <2%'")
source = source.replace('# H47 — Augmentation trong fit pool của ensemble', '# H47 — Học quyết định hữu thanh với augmentation')
old = 'Giữ toàn bộ9member H44, rank chỉ dùng fit_files, gộp clean và ba noise variants theo origin_file. TopK1/3/5/9 kết hợp F0 bằng trung bình log2, mask/count/range giữ Praat.30. Lựa chọn K vẫn dùng minimax inner và gate cũ, không dựa tên người/thiết bị hoặc GT held.'
new = 'Giữ pitch H43 hard170; logistic chỉ có thể loại khung Praat đã nhận hữu thanh. Học V so với UV/SIL trên fit origins, C=1, bốn đặc trưng âm học, threshold .25/.5. So clean với clean+3 noise variants kế thừa nhãn. Mỗi origin và variant có tổng trọng số bằng nhau; không cân bằng lớp. Không dùng F0num để cắt số khung. Inner minimax và gate cũ; yêu cầu mới strict <2%.'
source = source.replace(old, new)
source = source.replace('Không sửaGT, frozen/original, không dùngtest đểchọnK.', 'Không sửa GT, frozen/original, không dùng test để chọn cấu hình.')
source = source.replace('Đầu vào9member H44 đã kiểmtra PCM/FFT; H47 có12call Praat trên12WAV augmented train; clean held WAV không đổi. Nhãn/statistics của augmentation là latent targets kế thừa, không GT mới.', 'Tái sử dụng H44 pitch và H46 noise WAV/gate đã xác minh; 0 native call mới. Augmentation kế thừa nhãn, không tạo người nói mới. Chỉ 4 train; nested exploratory sau nhiều vòng đã xem. Candidate set đã thay đổi so với H45/H46; đạt target do fallback hard170 không tự chứng minh augmentation có ích.')
compile(source, str(target), 'exec')
target.write_text(source, encoding='utf-8')
verifier = HERE / 'verify_amdf_loop.py'
verifier.write_text(verifier.read_text().replace("'H45','H46')", "'H45','H46','H47')"), encoding='utf-8')
print('Generated H47 preregistered controller; previous measurements unchanged')
