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
    path = HERE/'AMDF_ANCHOR_LOCAL.ipynb'
    book = json.loads(path.read_text(encoding='utf-8'))
    meta = book['metadata']['bt2_local_execution']
    source = json.dumps([cell['source'] for cell in book['cells']],ensure_ascii=False).encode('utf-8')
    assert meta['source_cells_sha256']==hashlib.sha256(source).hexdigest()
    assert meta['all_code_cells_executed'] and not meta['source_rewritten'] and not meta['test_wav_read']
    code = [cell for cell in book['cells'] if cell['cell_type']=='code']
    assert len(code)==5 and [cell['execution_count'] for cell in code]==list(range(1,6))
    assert all(cell['outputs'] and not any(x['output_type']=='error' for x in cell['outputs']) for cell in code)
    assert any('image/png' in x.get('data',{}) for cell in code for x in cell['outputs'])
    table = pd.read_csv(HERE/'results/amdf_anchor_notebook_per_file.csv')
    contours = pd.read_csv(HERE/'results/amdf_anchor_notebook_contours.csv')
    assert len(table)==48 and not table.duplicated(['evaluation','method','file']).any()
    provenance = json.loads((HERE/'results/amdf_anchor_notebook_provenance.json').read_text())
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
    assert len(provenance['fit_logs'])==48
    native_proof = json.loads((HERE/'results/praat_native_7002_provenance.json').read_text())
    assert digest(native_proof['exe'])==provenance['praat_native_sha256']
    experiment=json.loads((HERE/'results/H41_experiment.json').read_text())
    assert len(provenance['native_calls'])==40 and len(provenance['source_calls'])==4
    checked_curves=set()
    for identity,call in provenance['native_calls'].items():
        file=identity.split('|')[-1]
        option=identity.split('|')[-2]
        expected=experiment['native_calls'][option+'|'+file]
        assert call['returncode']==0 and call['exe_sha256']==provenance['praat_native_sha256']
        assert call['command']==expected['command'] and call['script_sha256']==digest(call['command'][2])
        for key in ('output_f0_sha256','rule_sha256','source','selected_curve_indices'):
            assert call[key]==expected[key],key
        if call['AMDF_evidence']:
            proof=call['AMDF_evidence']
            assert digest(HERE/proof['path'])==proof['sha256'] and proof['source_sha256']==digest(HERE/'amdf_anchor.py')
            if proof['path'] not in checked_curves:
                fresh=dict(np.load(HERE/proof['path'],allow_pickle=False))
                prior=dict(np.load(HERE/expected['AMDF_evidence']['path'],allow_pickle=False))
                assert set(fresh)==set(prior)
                for key in fresh:
                    if fresh[key].dtype.kind in 'f':
                        assert np.allclose(fresh[key],prior[key],atol=1e-12,equal_nan=True),key
                    else:
                        assert np.array_equal(fresh[key],prior[key]),key
                checked_curves.add(proof['path'])
    assert len(checked_curves)==12
    for identity,call in provenance['source_calls'].items():
        assert call['command']==experiment['source_calls'][identity]['command']
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
    assert checked==48
    status = pd.read_csv(HERE/'results/amdf_anchor_notebook_status.csv').set_index('family')
    for family in ('H41',):
        values = table[(table.evaluation=='nested')&(table.family==family)].average_mape
        assert len(values)==4
        assert np.isclose(status.loc[family,'mean'],values.mean()) and np.isclose(status.loc[family,'worst'],values.max())
        assert status.loc[family,'all_files_le_2']==bool((values<=2).all())
    manifest = json.loads((HERE/'results/amdf_anchor_notebook_figure_manifest.json').read_text())
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
    (HERE/'results/amdf_anchor_notebook_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
