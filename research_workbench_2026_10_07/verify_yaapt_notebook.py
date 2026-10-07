import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    path = HERE/'YAAPT_AMDF_LOCAL.ipynb'
    book = json.loads(path.read_text(encoding='utf-8'))
    meta = book['metadata']['bt2_local_execution']
    source = json.dumps([cell['source'] for cell in book['cells']],ensure_ascii=False).encode('utf-8')
    assert meta['source_cells_sha256']==hashlib.sha256(source).hexdigest()
    assert meta['all_code_cells_executed'] and not meta['source_rewritten'] and not meta['test_wav_read']
    code = [cell for cell in book['cells'] if cell['cell_type']=='code']
    assert len(code)==5 and [cell['execution_count'] for cell in code]==list(range(1,6))
    assert all(cell['outputs'] and not any(x['output_type']=='error' for x in cell['outputs']) for cell in code)
    assert any('image/png' in x.get('data',{}) for cell in code for x in cell['outputs'])
    table = pd.read_csv(HERE/'results/yaapt_notebook_per_file.csv')
    contours = pd.read_csv(HERE/'results/yaapt_notebook_contours.csv')
    assert len(table)==24 and not table.duplicated(['evaluation','method','file']).any()
    provenance = json.loads((HERE/'results/yaapt_notebook_provenance.json').read_text())
    for relative, expected in provenance['source_sha256'].items():
        assert digest(REPO/relative)==expected,relative
    names = set(provenance['wav_sha256'])
    profile = pd.read_csv(REPO/'research_workbench_2026_10_06/results/training_data_profile.csv').set_index('file')
    for file, expected in provenance['wav_sha256'].items():
        assert digest(REPO/'TinHieuHuanLuyen'/file)==expected
        assert digest(REPO/'TinHieuHuanLuyen'/file.replace('.wav','.lab'))==profile.loc[file,'segment_lab_sha256']
        assert digest(REPO/'research_3gt_2026_10_05/train_3gt'/file.replace('.wav','.lab'))==profile.loc[file,'stats_lab_sha256']
    for fit in provenance['fit_logs']:
        assert set(fit['fit_files'])==names-{fit['held_file']}
        expected = fit['fit_files'] if fit['fitted']['requires_fit'] else []
        assert fit['fitted']['actual_fit_files']==expected
    assert len(provenance['fit_logs'])==24
    native_proof = json.loads((HERE/'results/praat_native_7002_provenance.json').read_text())
    assert digest(native_proof['exe'])==provenance['praat_native_sha256']
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
    assert provenance['test_read'] is False and provenance['new_grid_or_selection'] is False
    checked = 0
    keys = ['F0mean','F0std','F0num','F0mean_mape','F0std_mape','F0num_mape','average_mape',
            'macro_f1','recall_v','recall_uv','balanced_accuracy','TP','FN','FP','TN','false_voiced_sil']
    for (evaluation,method,file),group in contours.groupby(['evaluation','method','file']):
        measured = table[(table.evaluation==evaluation)&(table.method==method)&(table.file==file)].iloc[0]
        stats = {'F0mean':group.f0_hz.dropna().mean(),'F0std':group.f0_hz.dropna().std(ddof=0),'F0num':group.f0_hz.notna().sum()}
        gt = {}
        for line in (REPO/'research_3gt_2026_10_05/train_3gt'/file.replace('.wav','.lab')).read_text().splitlines():
            parts = line.split()
            if parts[0] in stats:
                gt[parts[0]]=float(parts[1])
        for key,value in stats.items():
            assert np.isclose(measured[key],value,atol=1e-8)
            assert np.isclose(measured[key+'_mape'],100*abs(value-gt[key])/gt[key],atol=1e-8)
        assert np.isclose(measured.average_mape,np.mean([measured[k+'_mape'] for k in stats]),atol=1e-8)
        segments = []
        for line in (REPO/'TinHieuHuanLuyen'/file.replace('.wav','.lab')).read_text().splitlines():
            parts = line.split()
            if len(parts)==3 and parts[0] not in stats:
                segments.append((float(parts[0]),float(parts[1]),parts[2].lower()))
        labels = np.array([next((lab for a,b,lab in segments if a<=t<b),'unknown') for t in group.time_s])
        assert np.array_equal(labels,group.label)
        pred = group.pred_voiced.to_numpy()
        counts = {'TP':int(((labels=='v')&pred).sum()),'FN':int(((labels=='v')&~pred).sum()),
                  'FP':int(((labels=='uv')&pred).sum()),'TN':int(((labels=='uv')&~pred).sum()),
                  'false_voiced_sil':int(((labels=='sil')&pred).sum())}
        assert all(measured[k]==v for k,v in counts.items())
        tp,tn,fp,fn = [counts[k] for k in ('TP','TN','FP','FN')]
        rv,ru = tp/max(tp+fn,1),tn/max(tn+fp,1)
        f1 = (2*tp/max(2*tp+fp+fn,1)+2*tn/max(2*tn+fp+fn,1))/2
        assert np.allclose([measured.recall_v,measured.recall_uv,measured.balanced_accuracy,measured.macro_f1],
                           [rv,ru,(rv+ru)/2,f1],atol=1e-10)
        family = measured.family
        saved = pd.read_csv(HERE/f'results/{family}_fixed_lofo.csv') if evaluation=='fixed' else pd.read_csv(HERE/f'results/{family}_metrics.csv')
        saved = saved[(saved.option_id==measured.option_id)&(saved.file==file)]
        if evaluation=='nested':
            saved = saved[(saved.split=='nested')&(saved.model=='candidate')]
            choices = json.loads((HERE/f'results/{family}_experiment.json').read_text())['selections']
            choice = next(x for x in choices if x['outer_held']==file)
            assert file not in choice['selection_files'] and choice['option']['id']==measured.option_id
        assert len(saved)==1 and np.allclose(measured[keys].astype(float),saved.iloc[0][keys].astype(float),atol=1e-8)
        checked += 1
    assert checked==24
    status = pd.read_csv(HERE/'results/yaapt_notebook_status.csv').set_index('family')
    for family in ('H40',):
        values = table[(table.evaluation=='nested')&(table.family==family)].average_mape
        assert len(values)==4
        assert np.isclose(status.loc[family,'mean'],values.mean()) and np.isclose(status.loc[family,'worst'],values.max())
        assert status.loc[family,'all_files_le_2']==bool((values<=2).all())
    manifest = json.loads((HERE/'results/yaapt_notebook_figure_manifest.json').read_text())
    assert len(manifest['figures'])==1
    for figure in manifest['figures']:
        assert digest(HERE/figure['generator'])==figure['generator_sha256']
        for source in figure['sources']:
            assert digest(HERE/source['path'])==source['sha256']
        png = (HERE/figure['png']).read_bytes()
        assert png[:8]==b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II',png[16:24]))>200
        ET.parse(HERE/figure['svg'])
    receipt = {'notebook_sha256':digest(path),'exact_source_cells_executed':5,'source_cells_sha256':meta['source_cells_sha256'],
               'measured_rows_recomputed_from_wav_and_contours_checked':checked,'actual_fit_exclusions_checked':True,
               'native_binary_call_provenance_checked':True,'status_and_figures_verified':True,
               'all_files_target_met':bool(status.all_files_le_2.any()),'execution_method':meta['execution_method'],
               'verifier_sha256':digest(__file__)}
    (HERE/'results/yaapt_notebook_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
