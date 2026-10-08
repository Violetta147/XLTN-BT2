import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import wavfile

import verify_amdf_loop
from verify_results import digest

HERE=Path(__file__).resolve().parent
REPO=HERE.parent


def main():
    verify_amdf_loop.verify('H40','praat7_filtered_v0.45')
    result=json.loads((HERE/'results/H40_experiment.json').read_text())
    options=json.loads((HERE/'H40_REGISTRY.json').read_text())['options']
    raw=pd.read_csv(HERE/'results/H40_raw_native_frames.csv',float_precision='round_trip')
    contours=pd.read_csv(HERE/'results/H40_nested_contours.csv')
    fixed=pd.read_csv(HERE/'results/H40_fixed_lofo.csv').set_index(['option_id','file'])
    proof=json.loads((HERE/'results/yaapt_source_discovery.json').read_text())
    praat=json.loads((HERE/'results/praat_native_7002_provenance.json').read_text())
    assert digest(praat['exe'])==praat['exe_sha256']==result['environment']['native_exe_sha256']
    environment=result['environment']['yaapt']
    assert environment['package_version']==proof['package_version']=='1.0.12.2'
    assert environment['python_port_commit']==proof['github_commit']
    assert len(environment['defaults'])==34
    for relative,source in proof['sources'].items():
        assert digest(HERE/'sources/yaapt'/relative)==source['sha256']
    for relative,expected in environment['source_sha256'].items():
        assert digest(REPO/relative)==expected
    assert len(result['native_calls'])==16 and len(raw.groupby(['option_id','file']))==16
    assert set(raw.option_id)=={x['id'] for x in options}
    checked=0
    for file in sorted(result['data_sha256']):
        fs,pcm=wavfile.read(REPO/'TinHieuHuanLuyen'/file)
        assert pcm.dtype==np.int16 and pcm.ndim==1
        canonical=contours[(contours.model=='accepted')&(contours.file==file)]
        times=canonical.time_s.to_numpy()
        labels=canonical.label.to_numpy()
        gt={}
        for line in (REPO/'research_3gt_2026_10_05/train_3gt'/file.replace('.wav','.lab')).read_text().splitlines():
            key,value=line.split()[:2]
            if key in ('F0mean','F0std','F0num'):
                gt[key]=float(value)
        for option in options:
            identity=option['id']
            group=raw[(raw.option_id==identity)&(raw.file==file)]
            nt,nf=group.time_s.to_numpy(),group.raw_f0_hz.to_numpy()
            assert np.isfinite(nf).all() and (nf>=0).all()
            assert np.array_equal(group.raw_voiced.to_numpy(),nf>0)
            call=result['native_calls'][identity+'|'+file]
            assert call['native_frames']==len(group)
            if option['method']=='yaapt':
                frame=int(np.fix(option['frame_ms']*fs/1000))
                hop=int(np.fix(fs*.01))
                positions=np.arange(frame//2,len(pcm)-frame//2,hop)
                assert np.array_equal(positions,call['frame_positions_samples'])
                assert len(group)==len(positions) and np.allclose(nt,positions/fs,atol=1e-12)
                assert call['frame_size_samples']==frame and call['hop_samples']==hop
                expected=dict(environment['defaults'],frame_length=float(option['frame_ms']),f0_min=70.,f0_max=400.,frame_space=10.)
                assert call['parameters']==expected and expected['tda_frame_length']==35
                encoded=np.ascontiguousarray(pcm.astype(np.float64)/32768,dtype=np.float64).tobytes()
                assert call['input_sha256']==hashlib.sha256(encoded).hexdigest() and call['input_samples']==len(pcm)
                assert call['input_unchanged'] is True and call['backend_called'] is True
                assert call['adapter_sha256']==digest(HERE/'yaapt_adapter.py')
                assert call['f0_sha256']==hashlib.sha256(np.ascontiguousarray(nf,dtype=np.float64).tobytes()).hexdigest()
                assert call['source_sha256']==environment['source_sha256']
                assert call['python_port_commit']==proof['github_commit'] and call['half_double_flags']==[0,0]
                assert call['output_attribute']=='samp_values (UV0), not samp_interp/upsampled values'
            else:
                assert call['returncode']==0
                assert call['command']==[praat['exe'],'--run',str(HERE/'praat_extract_native.praat'),str(REPO/'TinHieuHuanLuyen'/file),'filtered','0.45']
                assert call['script_sha256']==digest(HERE/'praat_extract_native.praat') and call['exe_sha256']==praat['exe_sha256']
                assert np.allclose(np.diff(nt),.01,atol=1e-12)
            indices=np.array([int(np.argmin(abs(nt-t))) for t in times])
            support=abs(nt[indices]-times)<=.005+1/fs
            pred=support&(nf[indices]>=70)&(nf[indices]<=400)
            valid=nf[indices][pred]
            saved=fixed.loc[(identity,file)]
            stats={'F0mean':valid.mean() if len(valid) else np.nan,'F0std':valid.std(ddof=0) if len(valid) else np.nan,'F0num':len(valid)}
            errors=[]
            for key,value in stats.items():
                assert np.isclose(saved[key],value,atol=1e-8,equal_nan=True)
                error=100*abs(value-gt[key])/gt[key]
                assert np.isclose(saved[key+'_mape'],error,atol=1e-8,equal_nan=True)
                errors.append(error)
            assert np.isclose(saved.average_mape,np.mean(errors),atol=1e-8,equal_nan=True)
            counts={'TP':int(((labels=='v')&pred).sum()),'FN':int(((labels=='v')&~pred).sum()),
                    'FP':int(((labels=='uv')&pred).sum()),'TN':int(((labels=='uv')&~pred).sum()),
                    'false_voiced_sil':int(((labels=='sil')&pred).sum())}
            assert all(saved[k]==v for k,v in counts.items())
            tp,tn,fp,fn=[counts[k] for k in ('TP','TN','FP','FN')]
            rv,ru=tp/max(tp+fn,1),tn/max(tn+fp,1)
            f1=(2*tp/max(2*tp+fp+fn,1)+2*tn/max(2*tn+fp+fn,1))/2
            assert np.allclose([saved.macro_f1,saved.recall_v,saved.recall_uv,saved.balanced_accuracy],[f1,rv,ru,(rv+ru)/2],atol=1e-10)
            assert np.isclose(saved.projection_coverage,support.mean()) and saved.native_frames==len(group)
            assert result['range_rejected_frames'][identity+'|'+file]==int(((nf>0)&~((nf>=70)&(nf<=400))).sum())
            checked+=1
    prior=pd.read_csv(HERE/'results/H30_fixed_lofo.csv').query("option_id=='praat7_filtered_v0.45'").set_index('file').sort_index()
    control=fixed.loc['praat7_filtered_v0.45'].sort_index()
    keys=['F0mean','F0std','F0num','average_mape','macro_f1','recall_v','false_voiced_sil']
    assert np.allclose(control[keys],prior[keys],atol=1e-8)
    fits=json.loads((HERE/'results/H40_fits.json').read_text())['fits']
    assert all(x['fitted']['actual_fit_files']==[] and not x['fitted']['requires_fit'] and x['classifier'] is None for x in fits)
    nested=pd.read_csv(HERE/'results/H40_metrics.csv').query("split=='nested' and model=='candidate'")
    assert result['goal_all_nested_files_le_2']==bool((nested.average_mape<=2).all())
    assert result['poisoned_gt_inference_invariant'] is True
    receipt={'family':'H40','native_calls_and_fixed_groups_replayed':checked,'fit_logs':len(fits),
             'raw_statistics_mape_voicing_support_recomputed':True,'normalized_PCM_raw_UV0_source_params_frame_centers_checked':True,'synthetic_octave_failures_retained':True,
             'H30_fixed_control_reproduced':True,'no_actual_training_fit':True,'verifier_sha256':digest(__file__),
             'input_sha256':{p.name:digest(p) for p in [HERE/'results/H40_experiment.json',HERE/'results/H40_fixed_lofo.csv',HERE/'results/H40_raw_native_frames.csv']}}
    (HERE/'results/H40_native_verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
