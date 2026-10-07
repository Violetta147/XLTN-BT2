import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import verify_results
from verify_selection import summary

HERE = Path(__file__).resolve().parent


def verify(family, baseline):
    verify_results.verify(family)
    result = json.loads((HERE / f'results/{family}_experiment.json').read_text())
    trace = pd.read_csv(HERE / f'results/{family}_inner_traces.csv')
    for selection in result['selections']:
        pool = trace[trace.outer_held == selection['outer_held']]
        base = summary(pool[pool.option_id == baseline])
        ranking = []
        for identity, table in pool.groupby('option_id'):
            new = summary(table)
            valid = (np.isfinite(table.average_mape).all()
                     and new['macro_f1'] >= base['macro_f1'] - .01
                     and new['recall_v'] >= base['recall_v'] - .01
                     and new['false_voiced_sil'] <= base['false_voiced_sil'] + 1)
            if family in ('H25','H26','H27','H28','H29','H30','H31','H32','H33','H34','H35','H36','H37','H38','H39','H40','H41','H42','H43','H44','H45'):
                ranking.append((not valid, float(table.average_mape.max()) if valid else float('inf'), new['average_mape'] if valid else float('inf'), identity))
            else:
                ranking.append((not valid, new['average_mape'] if valid else float('inf'), identity))
        assert min(ranking)[-1] == selection['option']['id']
    metrics = pd.read_csv(HERE / f'results/{family}_metrics.csv')
    s = {(model, split): summary(table) for (model, split), table in metrics.groupby(['model', 'split'])}
    before = metrics[(metrics.split == 'nested') & (metrics.model == 'accepted')].set_index('file')
    after = metrics[(metrics.split == 'nested') & (metrics.model == 'candidate')].set_index('file')
    base, new = s['accepted', 'nested'], s['candidate', 'nested']
    checks = {
        'train_mape_relative_10_percent': s['candidate', 'train']['average_mape'] <= .9*s['accepted', 'train']['average_mape'],
        'lofo_mape_relative_5_percent': new['average_mape'] <= .95*base['average_mape'],
        'lofo_f1_drop_at_most_01': new['macro_f1'] >= base['macro_f1']-.01,
        'lofo_recall_v_drop_at_most_01': new['recall_v'] >= base['recall_v']-.01,
        'lofo_sil_increase_at_most_1': new['false_voiced_sil'] <= base['false_voiced_sil']+1,
        'lofo_no_file_mape_worse_by_over_2pp': ((after.average_mape-before.average_mape)<=2).all(),
        'lofo_phone_f1_std_not_worse': after.loc['phone_F1.wav','F0std_mape']<=before.loc['phone_F1.wav','F0std_mape'],
        'selected_lofo_mape_relative_5_percent': s['candidate','lofo']['average_mape']<=.95*s['accepted','lofo']['average_mape']}
    checks = {k: bool(v) for k,v in checks.items()}
    assert checks == result['decision']['checks']
    assert all(checks.values()) == result['decision']['eligible']
    fits = json.loads((HERE / f'results/{family}_fits.json').read_text())['fits']
    for fit in fits:
        classifier = fit['classifier']
        if classifier is not None:
            assert classifier['fit_files'] == fit['fit_files']
            assert min(classifier['scale']) > 0
            assert all(np.isfinite(classifier[key]).all() for key in ('mean','scale','coefficient'))
            assert len(classifier['feature_names']) == len(classifier['coefficient'])
    extra = {}
    if family == 'H27':
        praat_fits = [fit for fit in fits if fit['option_id'].startswith('praat_')]
        assert praat_fits
        for fit in praat_fits:
            assert fit['fitted']['requires_fit'] is False
            assert fit['fitted']['actual_fit_files'] == []
            assert fit['classifier'] is None
        nested = metrics[(metrics.split == 'nested') & (metrics.model == 'candidate')]
        assert result['goal_all_nested_files_le_2'] == bool((nested.average_mape <= 2).all())
        assert metrics.projection_coverage.between(0, 1).all()
        assert any(path.endswith('amdf_dual_window.py') for path in result['code_sha256'])
        extra['praat_no_training_fit_verified'] = True
    if family == 'H28':
        native_fits = [fit for fit in fits if fit['option_id'].startswith('harvest_')]
        assert native_fits
        for fit in native_fits:
            assert fit['fitted']['requires_fit'] is False
            assert fit['fitted']['actual_fit_files'] == []
            assert fit['classifier'] is None
        provenance = json.loads((HERE / 'results/pyworld_035_compatibility.json').read_text())
        assert verify_results.digest(provenance['native_module']) == provenance['native_module_sha256']
        assert result['environment']['native_module_sha256'] == provenance['native_module_sha256']
        nested = metrics[(metrics.split == 'nested') & (metrics.model == 'candidate')]
        assert result['goal_all_nested_files_le_2'] == bool((nested.average_mape <= 2).all())
        assert metrics.projection_coverage.between(0, 1).all()
        extra['harvest_no_training_fit_and_native_hash_verified'] = True
    if family == 'H29':
        for fit in fits:
            expected = fit['fit_files'] if fit['fitted']['requires_fit'] else []
            assert fit['fitted']['actual_fit_files'] == expected
            assert fit['classifier'] is None
        fixed = pd.read_csv(HERE / 'results/H29_fixed_lofo.csv')
        prior = pd.read_csv(HERE / 'results/H28_fixed_lofo.csv')
        raw = fixed[fixed.option_id == 'harvest_raw'].set_index('file').sort_index()
        original = prior[prior.option_id == 'harvest_h10'].set_index('file').sort_index()
        columns = ['F0mean','F0std','F0num','average_mape','macro_f1','recall_v','false_voiced_sil']
        assert np.allclose(raw[columns], original[columns], atol=1e-8)
        nested = metrics[(metrics.split == 'nested') & (metrics.model == 'candidate')]
        assert result['goal_all_nested_files_le_2'] == bool((nested.average_mape <= 2).all())
        extra['raw_harvest_reproduced_and_gate_fit_pool_verified'] = True
    if family in ('H30','H31','H32','H33','H34','H36'):
        proof = json.loads((HERE / 'results/praat_native_7002_provenance.json').read_text())
        assert verify_results.digest(proof['exe']) == proof['exe_sha256'] == result['environment']['native_exe_sha256']
        for fit in fits:
            if fit['option_id'].startswith(('praat7_','pyin_','swipe_','reaper_')):
                assert fit['fitted']['requires_fit'] is False
                assert fit['fitted']['actual_fit_files'] == [] and fit['classifier'] is None
        fixed = pd.read_csv(HERE / f'results/{family}_fixed_lofo.csv').set_index(['option_id','file'])
        native = pd.read_csv(HERE / f'results/{family}_raw_native_frames.csv')
        contours = pd.read_csv(HERE / f'results/{family}_nested_contours.csv')
        options = json.loads((HERE / f'{family}_REGISTRY.json').read_text())['options']
        identities = {option['id'] for option in options if option['method'] != 'control' or family in ('H33','H34','H36')}
        assert set(native.option_id) == identities
        assert len(result['native_calls']) == len(identities)*4
        for (identity, file), group in native.groupby(['option_id', 'file']):
            canonical = contours[(contours.model == 'accepted') & (contours.file == file)]
            times, target = group.time_s.to_numpy(), canonical.time_s.to_numpy()
            raw = group.raw_f0_hz.to_numpy()
            assert np.isfinite(raw).all() and (raw >= 0).all()
            right = np.minimum(np.searchsorted(times, target), len(times)-1)
            left = np.maximum(right-1, 0)
            indices = np.where(abs(times[left]-target) <= abs(times[right]-target), left, right)
            fs = int(pd.read_csv(verify_results.REPO / 'research_workbench_2026_10_06/results/training_data_profile.csv').set_index('file').loc[file,'fs'])
            support = abs(times[indices]-target) <= .005+1/fs
            pred = support & (raw[indices] >= 70) & (raw[indices] <= 400)
            valid = raw[indices][pred]
            saved = fixed.loc[(identity,file)]
            statistics = {'F0mean': valid.mean(), 'F0std': valid.std(), 'F0num': len(valid)}
            assert all(np.isclose(saved[key], value, atol=1e-8, equal_nan=family=='H36') for key,value in statistics.items())
            if family in ('H32','H33','H34','H36'):
                gt = {}
                for line in (verify_results.REPO / 'research_3gt_2026_10_05/train_3gt' / file.replace('.wav','.lab')).read_text().splitlines():
                    parts = line.split()
                    if parts[0] in statistics:
                        gt[parts[0]] = float(parts[1])
                errors = {key: 100*abs(value-gt[key])/gt[key] for key,value in statistics.items()}
                assert all(np.isclose(saved[key+'_mape'], value, atol=1e-8, equal_nan=family=='H36') for key,value in errors.items())
                assert np.isclose(saved.average_mape, np.mean(list(errors.values())), atol=1e-8, equal_nan=family=='H36')
            labels = canonical.label.to_numpy()
            counts = {'TP': int(((labels=='v') & pred).sum()), 'FN': int(((labels=='v') & ~pred).sum()),
                      'FP': int(((labels=='uv') & pred).sum()), 'TN': int(((labels=='uv') & ~pred).sum()),
                      'false_voiced_sil': int(((labels=='sil') & pred).sum())}
            assert all(saved[key] == value for key,value in counts.items())
            assert np.isclose(saved.projection_coverage, support.mean())
            assert saved.native_frames == len(group)
            assert result['range_rejected_frames'][identity+'|'+file] == int(((raw>0)&((raw<70)|(raw>400))).sum())
            call = result['native_calls'][identity+'|'+file]
            if family == 'H33' and identity.startswith('pyin_'):
                option = next(x for x in options if x['id']==identity)
                parameters = call['parameters']
                frame, hop = round(fs*option['frame_ms']/1000),round(fs*.01)
                assert parameters['frame_length']==frame and parameters['hop_length']==hop and parameters['sr']==fs
                assert parameters['center'] is False and parameters['fill_na']=='NaN'
                assert parameters['fmin']==70 and parameters['fmax']==400
                assert parameters['n_thresholds']==100 and parameters['beta_parameters']==[2,18]
                assert parameters['boltzmann_parameter']==2 and parameters['resolution']==.1
                assert parameters['max_transition_rate']==35.92 and parameters['switch_prob']==.01 and parameters['no_trough_prob']==.01
                assert np.allclose(times,(np.arange(len(group))*hop+frame/2)/fs,atol=1e-12)
                assert len(group)==1+(call['input_samples']-frame)//hop
                assert np.array_equal(group.raw_voiced.to_numpy(),raw>0)
                assert group.voiced_probability.between(0,1).all()
                assert call['adapter_sha256']==verify_results.digest(HERE/'pyin_adapter.py')
            elif (family == 'H34' and identity.startswith('swipe_')) or (family=='H36' and identity.startswith('reaper_')):
                import hashlib
                from scipy.io import wavfile
                native_proof = json.loads((HERE/'results/sptk_native_provenance.json').read_text())
                assert call['returncode']==0
                assert call['exe_sha256']==native_proof['exe_sha256']==verify_results.digest(native_proof['exe'])
                assert call['source_commit']=='0ebff5a9b1fb5851709130efa1d3efb186ef702a'
                option = next(x for x in options if x['id']==identity)
                hop = round(fs*.01)
                code='2' if family=='H36' else '1'
                threshold=option['unvoiced_cost'] if family=='H36' else option['voicing_threshold']
                expected_command = [native_proof['exe'],'-a',code,'-p',str(hop),'-s',str(fs/1000),'-L','70','-H','400','-t'+code,str(threshold),'-o','1']
                assert call['command']==expected_command
                actual_fs, pcm = wavfile.read(verify_results.REPO/'TinHieuHuanLuyen'/file)
                assert actual_fs==fs and pcm.dtype==np.int16 and pcm.ndim==1
                assert call['input_sha256']==hashlib.sha256(np.ascontiguousarray(pcm,dtype='<f8').tobytes()).hexdigest()
                assert call['input_samples']==len(pcm) and len(group)==int(np.ceil(len(pcm)/hop))
                assert np.allclose(times,np.arange(len(group))*hop/fs,atol=1e-12)
                assert np.array_equal(group.raw_voiced,raw>0)
                assert call['adapter_sha256']==verify_results.digest(HERE/'sptk_adapter.py')
                if family=='H36':
                    assert pcm.any() and call['native_called'] is True and call['status']=='native_success'
                    assert call['reaper_adapter_sha256']==verify_results.digest(HERE/'reaper_adapter.py')
            else:
                assert call['returncode'] == 0 and call['exe_sha256'] == proof['exe_sha256']
                script = 'praat_extract_silence.praat' if family == 'H32' else 'praat_extract_native.praat'
                assert call['script_sha256'] == verify_results.digest(HERE / script)
                assert Path(call['command'][3]).resolve() == (verify_results.REPO / 'TinHieuHuanLuyen' / file).resolve()
        extra['native_all_fixed_f0_stats_voicing_range_projection_and_calls_replayed'] = True
        nested = metrics[(metrics.split=='nested') & (metrics.model=='candidate')]
        assert result['goal_all_nested_files_le_2'] == bool((nested.average_mape<=2).all())
        if family in ('H32','H33','H34','H36'):
            extra['all_fixed_mape_components_independently_recomputed'] = True
        if family == 'H33':
            for path,expected in result['environment']['pyin_runtime_source_sha256'].items():
                assert verify_results.digest(path)==expected,path
            prior = pd.read_csv(HERE/'results/H30_fixed_lofo.csv').query("option_id=='praat7_filtered_v0.45'").set_index('file').sort_index()
            control = fixed.loc['praat7_filtered_v0.45'].sort_index()
            keys = ['F0mean','F0std','F0num','average_mape','macro_f1','recall_v','false_voiced_sil']
            assert np.allclose(control[keys],prior[keys],atol=1e-8)
            extra['pyin_runtime_parameters_time_alignment_and_control_parity_checked'] = True
        if family in ('H34','H36'):
            root = Path(result['environment']['sptk_source_root'])
            for path,expected in result['environment']['sptk_key_source_sha256'].items():
                assert verify_results.digest(root/path)==expected,path
            prior = pd.read_csv(HERE/'results/H30_fixed_lofo.csv').query("option_id=='praat7_filtered_v0.45'").set_index('file').sort_index()
            control = fixed.loc['praat7_filtered_v0.45'].sort_index()
            keys = ['F0mean','F0std','F0num','average_mape','macro_f1','recall_v','false_voiced_sil']
            assert np.allclose(control[keys],prior[keys],atol=1e-8)
            extra[('reaper' if family=='H36' else 'swipe')+'_native_parameters_time_alignment_pcm_input_and_control_checked'] = True
    if family == 'H24':
        contours = pd.read_csv(HERE / 'results/H24_nested_contours.csv')
        for file, group in contours.groupby('file'):
            a = group[group.model=='accepted'].reset_index(drop=True)
            b = group[group.model=='candidate'].reset_index(drop=True)
            assert np.array_equal(a.pred_voiced,b.pred_voiced)
            assert np.array_equal(a.f0_hz.notna(),b.f0_hz.notna())
        extra['voicing_and_valid_f0_count_unchanged'] = True
        fixed = pd.read_csv(HERE / 'results/H24_fixed_lofo.csv')
        for file, group in fixed.groupby('file'):
            for metric in ('TP','FN','FP','TN','false_voiced_sil','F0num','projection_coverage'):
                assert group[metric].nunique()==1
        assert (fixed.projection_coverage==1).all()
        extra['exact_canonical_support_all_frames'] = True
    receipt = {'family': family, 'selection_replayed': True, 'fits_checked':len(fits),
               'gates_recomputed': checks, **extra, 'verifier_sha256':verify_results.digest(__file__)}
    (HERE / f'results/{family}_selection_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('family')
    parser.add_argument('baseline')
    args = parser.parse_args()
    verify(args.family,args.baseline)
