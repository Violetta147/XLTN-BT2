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
    verify_amdf_loop.verify('H39','praat7_filtered_v0.45')
    result=json.loads((HERE/'results/H39_experiment.json').read_text())
    options=json.loads((HERE/'H39_REGISTRY.json').read_text())['options']
    raw=pd.read_csv(HERE/'results/H39_raw_native_frames.csv')
    contours=pd.read_csv(HERE/'results/H39_nested_contours.csv')
    fixed=pd.read_csv(HERE/'results/H39_fixed_lofo.csv').set_index(['option_id','file'])
    proof=json.loads((HERE/'results/rapt_source_provenance.json').read_text())
    praat=json.loads((HERE/'results/praat_native_7002_provenance.json').read_text())
    assert digest(proof['exe'])==proof['exe_sha256']==result['environment']['sptk_exe_sha256']
    assert digest(praat['exe'])==praat['exe_sha256']==result['environment']['native_exe_sha256']
    assert result['environment']['sptk_key_source_sha256']==proof['source_sha256']
    for path,expected in proof['source_sha256'].items():
        assert digest(Path(proof['source_root'])/path)==expected
    assert len(result['native_calls'])==20 and len(raw.groupby(['option_id','file']))==20
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
            assert call['returncode']==0 and call['native_frames']==len(group)
            if option['method']=='rapt':
                hop=round(fs*.01)
                assert len(group)==int(np.ceil(len(pcm)/hop))
                assert np.allclose(nt,np.arange(len(group))*hop/fs,atol=1e-12)
                assert call['command']==[proof['exe'],'-a','0','-p',str(hop),'-s',str(fs/1000),'-L','70','-H','400','-t0',str(option['voicing_bias']),'-o','1']
                encoded=np.ascontiguousarray(pcm,dtype='<f8').tobytes()
                assert call['input_sha256']==hashlib.sha256(encoded).hexdigest() and call['input_samples']==len(pcm)
                native_float32=nf.astype(np.float32).astype('<f8')
                assert np.allclose(nf,native_float32,atol=1e-12)
                assert call['stdout_sha256']==hashlib.sha256(native_float32.tobytes()).hexdigest()
                assert call['native_called'] is True and call['adapter_sha256']==digest(HERE/'rapt_adapter.py')
                assert call['exe_sha256']==proof['exe_sha256'] and call['source_commit']==proof['sptk_commit']
                assert call['rapt_source_provenance_sha256']==digest(HERE/'results/rapt_source_provenance.json')
                assert call['native_internal_noise']=={'std_pcm_units':50.,'generator_seed':1,'agent_noise_added':False}
            else:
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
    fits=json.loads((HERE/'results/H39_fits.json').read_text())['fits']
    assert all(x['fitted']['actual_fit_files']==[] and not x['fitted']['requires_fit'] and x['classifier'] is None for x in fits)
    nested=pd.read_csv(HERE/'results/H39_metrics.csv').query("split=='nested' and model=='candidate'")
    assert result['goal_all_nested_files_le_2']==bool((nested.average_mape<=2).all())
    assert result['poisoned_gt_inference_invariant'] is True
    receipt={'family':'H39','native_calls_and_fixed_groups_replayed':checked,'fit_logs':len(fits),
             'raw_statistics_mape_voicing_support_recomputed':True,'PCM_source_binary_params_native_noise_checked':True,
             'H30_fixed_control_reproduced':True,'no_actual_training_fit':True,'verifier_sha256':digest(__file__),
             'input_sha256':{p.name:digest(p) for p in [HERE/'results/H39_experiment.json',HERE/'results/H39_fixed_lofo.csv',HERE/'results/H39_raw_native_frames.csv']}}
    (HERE/'results/H39_native_verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
