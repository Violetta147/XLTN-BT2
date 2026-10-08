import argparse
import json
import numpy as np
import pandas as pd
import bounded_srh as api
from verify_srh import independent_item,independent_score


def scalar_infer(proof,times,base,width):
    output=np.array(base['f0']);pred=np.array(base['pred'])
    if width==0:return pred,output
    lower,upper=map(int,proof['passes'][-1])
    for i,(time,voiced) in enumerate(zip(times,pred)):
        if not voiced:continue
        k=min(range(len(proof['native_times'])),key=lambda k:(abs(time-proof['native_times'][k]),k))
        if abs(time-proof['native_times'][k])>.005+1/int(proof['native_fs']):continue
        candidates=[f for f in range(max(70,lower),min(400,upper)+1) if abs(1200*np.log2(f/base['f0'][i]))<=width]
        if not candidates:continue
        best=min(candidates,key=lambda f:(-proof['curves'][k,f-1],f))
        if proof['curves'][k,best-1]>0:output[i]=best
    return pred,output


def choose(rows):
    base=[r for r in rows if r['option_id']=='hard170'];rank=[]
    for identity in api.BY_ID:
        values=[r for r in rows if r['option_id']==identity];valid=all(np.isfinite(r['average_mape']) for r in values)
        for key in ('macro_f1','recall_v'):valid &= sum(r[key] for r in values)/len(values)>=sum(r[key] for r in base)/len(base)-.01
        valid &= sum(r['false_voiced_sil'] for r in values)<=sum(r['false_voiced_sil'] for r in base)+1
        rank.append((not valid,max(r['average_mape'] for r in values) if valid else np.inf,
                     sum(r['average_mape'] for r in values)/len(values) if valid else np.inf,identity))
    return sorted(rank)[0][-1]


def verify(stage):
    api.check_registry();receipt=json.loads((api.OUT/f'H55_{stage}_experiment.json').read_text())
    for path,digest in receipt['artifacts'].items():assert api.audit.digest(api.REPO/path)==digest
    assert receipt['new_native_calls']==0 and receipt['actual_fit_files']==[] and receipt['seed'] is None
    assert json.loads((api.OUT/f'H54_{stage}_verification.json').read_text())['passed']
    stored=pd.read_csv(api.OUT/f'H55_{stage}_fixed.csv',float_precision='round_trip')
    old=pd.read_csv(api.OUT/('H47_nested_contours.csv' if stage=='train' else 'H48_test_contours.csv'),float_precision='round_trip')
    rows=[];frames=0
    for name in sorted(stored.file.unique()):
        path=(api.core.TRAIN if stage=='train' else api.REPO/'TinHieuKiemThu')/name
        item,_,_=independent_item(path,stage);base=old[(old.file==name)&(old.model=='candidate')]
        base=dict(pred=base.pred_voiced.to_numpy(bool),f0=base.f0_hz.to_numpy())
        native=dict(np.load(api.OUT/f'H54_{stage}_native_{path.stem}_w100.npz',allow_pickle=False))
        output=dict(np.load(api.OUT/f'H55_{stage}_predictions_{path.stem}.npz',allow_pickle=False))
        assert np.allclose(output['times'],item['times'],atol=1e-12)
        for k,identity in enumerate(output['option_id']):
            pred,f0=scalar_infer(native,item['times'],base,api.BY_ID[str(identity)]['width_cents'])
            assert np.array_equal(pred,base['pred']) and np.array_equal(pred,output['pred'][k])
            assert np.allclose(f0,output['f0'][k],atol=1e-12,equal_nan=True)
            if identity!='hard170':
                distance=abs(1200*np.log2(f0[pred]/base['f0'][pred]));assert max(distance)<=api.BY_ID[str(identity)]['width_cents']+1e-9
                frames+=sum(pred)
            metrics=independent_score(item,pred,f0);row=stored[(stored.file==name)&(stored.option_id==identity)].iloc[0]
            assert all(np.isclose(row[key],value,rtol=1e-10,atol=1e-8,equal_nan=True) for key,value in metrics.items())
            rows.append(dict(file=name,option_id=identity,**metrics))
    if stage=='train':
        assert len(rows)==16
        for selection in receipt['selections']:
            pool=selection['selection_files'];outer=selection['outer_held']
            assert set(pool)==set(stored.file.unique())-({outer} if outer!='final' else set())
            assert choose([r for r in rows if r['file'] in pool])==selection['option_id']
        traces=pd.read_csv(api.OUT/'H55_inner_traces.csv',keep_default_na=False);assert len(traces)==64 and (traces.actual_fit_files=='').all()
        for _,trace in traces.iterrows():
            assert trace.inner_held!=trace.outer_held
            original=next(r for r in rows if r['file']==trace['file'] and r['option_id']==trace.option_id)
            assert all(np.isclose(trace[key],value,atol=1e-8,equal_nan=True) for key,value in original.items() if key not in ('file','option_id'))
        table=pd.read_csv(api.OUT/'H55_metrics.csv',float_precision='round_trip')
        for _,row in table.iterrows():
            original=next(r for r in rows if r['file']==row['file'] and r['option_id']==row.option_id)
            assert all(np.isclose(row[key],value,atol=1e-8,equal_nan=True) for key,value in original.items() if key not in ('file','option_id'))
        _,gates=api.common.gates(table);assert gates==receipt['decision']
    else:
        freeze=json.loads((api.OUT/'H55_FROZEN_SELECTION.json').read_text())
        assert set(stored.option_id)==set(freeze['external_options']) and not receipt['test_tuning']
        assert receipt['freeze_sha256']==api.audit.digest(api.OUT/'H55_FROZEN_SELECTION.json')
    api.audit.json_write(api.OUT/f'H55_{stage}_verification.json',dict(passed=True,metric_groups=len(rows),scalar_bounded_frames=int(frames),
        independent_scalar_selector_projection_metrics=True,new_native_calls=0,source_proof='H54 cached verified LPC/FFT/SRH, hashes protected',
        verifier_sha256=api.audit.digest(__file__)))
    print(f'PASS H55 {stage}: {frames} scalar bounded selections, {len(rows)} metric groups')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['train','test']);verify(parser.parse_args().stage)
