from pathlib import Path

HERE = Path(__file__).resolve().parent
module_path = HERE / 'amdf_augmented_ensemble.py'
controller_path = HERE / 'amdf_augmented_ensemble_controller.py'
assert not module_path.exists() and not controller_path.exists()
module = (HERE / 'amdf_selection_ensemble.py').read_text().replace("FIXED = pd.read_csv(HERE / 'results/H44_fixed_lofo.csv')", 'FIXED = None\nBANK_PROOF = None')
module = module.replace("rows = FIXED[(FIXED.option_id == identity) & FIXED.file.isin(names)]", "rows = FIXED[(FIXED.option_id == identity) & FIXED.file.isin(names)].groupby('file').mean(numeric_only=True).reset_index()")
module = module.replace("reference = FIXED[(FIXED.option_id == MEMBERS[0]) & FIXED.file.isin(names)]", "reference = FIXED[(FIXED.option_id == MEMBERS[0]) & FIXED.file.isin(names)].groupby('file').mean(numeric_only=True).reset_index()")
module = module.replace('H45', 'H46')
module += '''

def build_bank():
    global FIXED, BANK_PROOF
    import build_h46_augmentation
    BANK_PROOF = build_h46_augmentation.main()
    FIXED = pd.read_csv(HERE / 'results/H46_augmented_member_metrics.csv')
    assert len(FIXED) == 144 and set(FIXED.groupby('file').case_id.nunique()) == {4}
'''
module = module.replace('    cases=[]', '    cases=[]')
module = module.replace("    print('PASS synthetic geometric aggregation/range checks; no H46 BT2 inference')", "    import build_h46_augmentation\n    build_h46_augmentation.check()\n    print('PASS synthetic ensemble and augmentation checks; no H46 BT2 inference')")
source = (HERE / 'amdf_selection_ensemble_controller.py').read_text().replace('H45', 'H46').replace('amdf_selection_ensemble', 'amdf_augmented_ensemble')
source = source.replace('    started = time.perf_counter()', '    started = time.perf_counter()\n    anchor_api.build_bank()')
source = source.replace("'new_native_calls':0, 'historical_source_groups':4", "'new_native_calls':12, 'augmentation_proof':anchor_api.BANK_PROOF, 'historical_source_groups':4")
source = source.replace("Path(__file__), HERE / 'amdf_dual_window.py'", "Path(__file__), HERE / 'build_h46_augmentation.py', HERE / 'results/H46_augmentation_manifest.json', HERE / 'results/H46_augmented_member_metrics.csv', HERE / 'amdf_dual_window.py'")
source = source.replace("'rollback_repository_commit':'35cb166ccd7968100642765fa42aeacf7fc52323'", "'rollback_repository_commit':'3d03ad098ba44c637880803085a99cb2fdc34f4b'")
source = source.replace('# H46 — Kết hợp các cấu hình được chọn từ train', '# H46 — Augmentation trong fit pool của ensemble')
source = source.replace('rank chỉ dùng fit_files.', 'rank chỉ dùng fit_files, gộp clean và ba noise variants theo origin_file.')
source = source.replace('H46 không có nativecall mới.', 'H46 có12call Praat trên12WAV augmented train; clean held WAV không đổi. Nhãn/statistics của augmentation là latent targets kế thừa, không GT mới.')
source = source.replace("'algorithm':'Top-K training-ranked H44 member geometric-frequency ensemble'", "'algorithm':'Top-K H44 ensemble ranked using origin-grouped noise augmentation in fit pool'")
verifier = (HERE / 'verify_amdf_selection_ensemble.py').read_text().replace('H45', 'H46')
verifier = verifier.replace("member_metrics = pd.read_csv(HERE / 'results/H44_fixed_lofo.csv')", "member_metrics = pd.read_csv(HERE / 'results/H46_augmented_member_metrics.csv')")
verifier = verifier.replace("data = member_metrics[(member_metrics.option_id == member) & member_metrics.file.isin(pool)]", "data = member_metrics[(member_metrics.option_id == member) & member_metrics.file.isin(pool)].groupby('file').mean(numeric_only=True).reset_index()")
verifier = verifier.replace("ref = member_metrics[(member_metrics.option_id == 'praat7_filtered_v0.3') & member_metrics.file.isin(pool)]", "ref = member_metrics[(member_metrics.option_id == 'praat7_filtered_v0.3') & member_metrics.file.isin(pool)].groupby('file').mean(numeric_only=True).reset_index()")
verifier = verifier.replace("membership_fit_pool_only=True, new_native_calls=0", "membership_fit_pool_only=True, new_native_calls=12")
for path, text in ((module_path, module), (controller_path, source), (HERE / 'verify_amdf_augmented_ensemble.py', verifier)):
    compile(text, str(path), 'exec')
    path.write_text(text, encoding='utf-8')
print('Generated H46 augmented-fit runner/verifier; H45 unchanged')
