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
verify_amdf_loop.verify('H35','praat7_filtered_v0.3')
result=json.loads((HERE/'results/H35_experiment.json').read_text())
registry=json.loads((HERE/'H35_REGISTRY.json').read_text())['options']
source=pd.read_csv(HERE/'results/H35_source_native_frames.csv')
raw=pd.read_csv(HERE/'results/H35_raw_native_frames.csv')
contours=pd.read_csv(HERE/'results/H35_nested_contours.csv')
fixed=pd.read_csv(HERE/'results/H35_fixed_lofo.csv').set_index(['option_id','file'])
prior=pd.read_csv(HERE/'results/H31_fixed_lofo.csv').query("option_id=='praat7_filtered_v0.3'").set_index('file').sort_index()
control=fixed.loc['praat7_filtered_v0.3'].sort_index()
keys=['F0mean','F0std','F0num','average_mape','macro_f1','recall_v','false_voiced_sil']
assert np.allclose(control[keys],prior[keys],atol=1e-8)
praat=json.loads((HERE/'results/praat_native_7002_provenance.json').read_text())
sptk=json.loads((HERE/'results/sptk_native_provenance.json').read_text())
assert digest(sptk['exe'])==sptk['exe_sha256']==result['environment']['sptk_exe_sha256']
assert digest(praat['exe'])==praat['exe_sha256']==result['environment']['native_exe_sha256']
for path,expected in sptk['key_source_sha256'].items():
    assert digest(Path(sptk['source_root'])/path)==expected
assert len(result['source_calls'])==12
files=sorted(result['data_sha256'])
assert set(source.source_id)=={'praat7_filtered_v0.3','swipe_t0.2','swipe_t0.3'}
assert len(source.groupby(['source_id','file']))==12 and len(raw.groupby(['option_id','file']))==12
usage=[]
for file in files:
    fs,pcm=wavfile.read(REPO/'TinHieuHuanLuyen'/file)
    assert pcm.ndim==1 and pcm.dtype==np.int16
    gate=source[(source.source_id=='praat7_filtered_v0.3')&(source.file==file)]
    gt,gf=gate.time_s.to_numpy(),gate.raw_f0_hz.to_numpy()
    assert np.allclose(np.diff(gt),.01,atol=1e-12)
    for identity in sorted(source.source_id.unique()):
        native=source[(source.source_id==identity)&(source.file==file)]
        call=result['source_calls'][identity+'|'+file]
        assert call['returncode']==0 and call['native_frames']==len(native)
        if identity.startswith('swipe_'):
            threshold=float(identity.removeprefix('swipe_t'))
            hop=round(fs*.01)
            assert call['command']==[sptk['exe'],'-a','1','-p',str(hop),'-s',str(fs/1000),'-L','70','-H','400','-t1',str(threshold),'-o','1']
            assert call['input_sha256']==hashlib.sha256(np.ascontiguousarray(pcm,dtype='<f8').tobytes()).hexdigest()
            assert call['input_samples']==len(pcm) and len(native)==int(np.ceil(len(pcm)/hop))
            assert np.allclose(native.time_s,np.arange(len(native))*hop/fs,atol=1e-12)
            assert call['exe_sha256']==sptk['exe_sha256'] and call['adapter_sha256']==digest(HERE/'sptk_adapter.py')
            assert call['source_commit']==sptk['commit']
        else:
            assert call['command']==[praat['exe'],'--run',str(HERE/'praat_extract_native.praat'),str(REPO/'TinHieuHuanLuyen'/file),'filtered','0.3']
            assert call['script_sha256']==digest(HERE/'praat_extract_native.praat') and call['exe_sha256']==praat['exe_sha256']
    canonical=contours[(contours.model=='accepted')&(contours.file==file)]
    target=canonical.time_s.to_numpy()
    for option in registry:
        group=raw[(raw.option_id==option['id'])&(raw.file==file)]
        assert np.allclose(group.time_s,gt,atol=1e-12)
        gate_v=(gf>=70)&(gf<=400)
        if option['method']=='control':
            frequency=gf
            tags=np.full(len(gt),'praat_control')
        else:
            swipe=source[(source.source_id==f"swipe_t{option['voicing_threshold']:g}")&(source.file==file)]
            st,sf=swipe.time_s.to_numpy(),swipe.raw_f0_hz.to_numpy()
            right=np.minimum(np.searchsorted(st,gt),len(st)-1)
            left=np.maximum(right-1,0)
            idx=np.where(abs(st[left]-gt)<=abs(st[right]-gt),left,right)
            support=abs(st[idx]-gt)<=.005+1/fs
            available=support&(sf[idx]>=70)&(sf[idx]<=400)
            use=gate_v&available
            frequency=np.where(gate_v,np.where(use,sf[idx],gf),0.)
            tags=np.where(~gate_v,'unvoiced',np.where(use,'swipe','praat_fallback'))
            usage.append({'option_id':option['id'],'file':file,'native_voiced':int(gate_v.sum()),
                          'swipe_used':int(use.sum()),'praat_fallback':int((gate_v&~use).sum()),
                          'swipe_unsupported':int((gate_v&~support).sum())})
        assert np.allclose(group.raw_f0_hz,frequency,atol=1e-10)
        assert np.array_equal(group.hybrid_source.to_numpy(),tags)
        assert np.array_equal(group.raw_voiced.to_numpy(),frequency>0)
        right=np.minimum(np.searchsorted(gt,target),len(gt)-1)
        left=np.maximum(right-1,0)
        idx=np.where(abs(gt[left]-target)<=abs(gt[right]-target),left,right)
        support=abs(gt[idx]-target)<=.005+1/fs
        prediction=support&(frequency[idx]>=70)&(frequency[idx]<=400)
        assert np.array_equal(prediction,canonical.pred_voiced.to_numpy())
        valid=frequency[idx][prediction]
        saved=fixed.loc[(option['id'],file)]
        assert np.allclose([valid.mean(),valid.std(),len(valid)],[saved.F0mean,saved.F0std,saved.F0num],atol=1e-8)
        gt_stats={}
        for line in (REPO/'research_3gt_2026_10_05/train_3gt'/file.replace('.wav','.lab')).read_text().splitlines():
            key,value=line.split()[:2]
            if key in ('F0mean','F0std','F0num'):
                gt_stats[key]=float(value)
        errors=[100*abs(value-gt_stats[key])/gt_stats[key] for key,value in [('F0mean',valid.mean()),('F0std',valid.std()),('F0num',len(valid))]]
        assert np.allclose(errors,[saved.F0mean_mape,saved.F0std_mape,saved.F0num_mape],atol=1e-8)
        assert np.isclose(saved.average_mape,np.mean(errors),atol=1e-8)
        labels=canonical.label.to_numpy()
        counts={'TP':int(((labels=='v')&prediction).sum()),'FN':int(((labels=='v')&~prediction).sum()),
                'FP':int(((labels=='uv')&prediction).sum()),'TN':int(((labels=='uv')&~prediction).sum()),
                'false_voiced_sil':int(((labels=='sil')&prediction).sum())}
        assert all(saved[k]==v for k,v in counts.items())
        assert np.isclose(saved.projection_coverage,support.mean())
        assert saved.native_frames==len(group) and saved.effective_median_span_ms==0
        assert result['range_rejected_frames'][option['id']+'|'+file]==int(((frequency>0)&~((frequency>=70)&(frequency<=400))).sum())
        for key in ('F0num','TP','FN','FP','TN','macro_f1','recall_v','recall_uv','balanced_accuracy','false_voiced_sil'):
            assert np.isclose(saved[key],control.loc[file,key],atol=1e-10)
fits=json.loads((HERE/'results/H35_fits.json').read_text())['fits']
for fit in fits:
    assert fit['fitted']['requires_fit'] is False and fit['fitted']['actual_fit_files']==[] and fit['classifier'] is None
nested=pd.read_csv(HERE/'results/H35_metrics.csv').query("split=='nested' and model=='candidate'")
assert result['goal_all_nested_files_le_2']==bool((nested.average_mape<=2).all())
assert result['poisoned_gt_inference_invariant'] is True
usage_path=HERE/'results/H35_swipe_usage.csv'
pd.DataFrame(usage).to_csv(usage_path,index=False)
proof={'family':'H35','source_calls':12,'fixed_groups_replayed':12,'fit_logs':len(fits),
       'independent_fusion_two_stage_alignment_and_fallback_replayed':True,'voicing_and_count_match_control_every_fixed_file':True,
       'control_H31_fixed_03_parity':True,'fixed_mape_components_recomputed':True,'native_input_and_source_binary_parameters_checked':True,
       'generator_sha256':digest(__file__),'input_sha256':{p.name:digest(p) for p in [HERE/'results/H35_experiment.json',HERE/'results/H35_source_native_frames.csv',HERE/'results/H35_raw_native_frames.csv',HERE/'results/H35_fixed_lofo.csv',usage_path]}}
(HERE/'results/H35_hybrid_verification.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
