import argparse
import json
import numpy as np
import pandas as pd


def independent_path(probability, frequencies):
    """Log-space dynamic programming, separate from author's products/means."""
    transition=-abs(np.log(frequencies[:,None]/frequencies[None,:]))
    scores=np.log(probability[0]);back=[]
    for row in probability[1:]:
        pairs=scores[:,None]+transition
        predecessor=np.argmax(pairs,axis=0);back.append(predecessor)
        scores=pairs[predecessor,np.arange(len(frequencies))]+np.log(row)
        scores-=np.max(scores)
    indices=[int(np.argmax(scores))]
    for predecessor in reversed(back): indices.append(int(predecessor[indices[-1]]))
    return frequencies[np.array(indices[::-1])]


def verify():
    import maps_experiment as api
    from verify_srh import independent_item,independent_score
    from voicing_recovery import gates
    api.check_registry()
    receipt=json.loads((api.OUT/'H60_train_experiment.json').read_text())
    for p,digest in receipt['artifacts'].items():assert api.audit.digest(api.REPO/p)==digest,p
    measured=pd.read_csv(api.OUT/'H60_fixed.csv',float_precision='round_trip')
    old=pd.read_csv(api.OUT/'H47_nested_contours.csv',float_precision='round_trip')
    checks=[]
    for path in sorted(api.core.TRAIN.glob('*.wav')):
        item,fs,audio=independent_item(path,'train')
        proof=dict(np.load(api.OUT/f'H60_native_{path.stem}.npz'))
        saved=dict(np.load(api.OUT/f'H60_predictions_{path.stem}.npz'))
        length,hop=2048,480;extra=int(48000//450)
        resampled_length=int(np.ceil(len(audio)*48000/fs))
        count=(resampled_length-length-extra)//hop+1
        assert np.array_equal(proof['times'],(np.arange(count)*hop+length/2)/48000)
        assert np.allclose(proof['frequencies'],np.geomspace(50,450,200),atol=1e-12)
        assert np.array_equal(independent_path(proof['probability'],proof['frequencies']),proof['f0'])
        assert np.array_equal(proof['probability'],np.clip(proof['raw_probability'],1e-12,1))
        assert np.array_equal(saved['times'],item['times'])
        baseline=old[(old.file==path.name)&(old.model=='candidate')]
        base_pred=baseline.pred_voiced.to_numpy(bool);base_f0=baseline.f0_hz.to_numpy()
        for k,option in enumerate(api.OPTIONS):
            pred=base_pred.copy();f0=base_f0.copy();fallback=0
            if option['mode']!='base':
                for i,t in enumerate(item['times']):
                    j=min(range(count),key=lambda j:(abs(float(proof['times'][j])-t),j))
                    covered=abs(float(proof['times'][j])-t)<=.005+1/48000 and 70<=proof['f0'][j]<=400
                    if option['mode']=='pitch':
                        if pred[i] and covered:f0[i]=proof['f0'][j]
                        elif pred[i]:fallback+=1
                    else:
                        pred[i]=covered and proof['confidence'][j]>=option['threshold']
                        f0[i]=proof['f0'][j] if pred[i] else np.nan
            assert np.array_equal(pred,saved['pred'][k]) and np.allclose(f0,saved['f0'][k],equal_nan=True,rtol=0,atol=0)
            metrics=independent_score(item,pred,f0)
            r=measured[(measured.file==path.name)&(measured.option_id==option['id'])].iloc[0]
            for key,value in metrics.items():assert np.isclose(value,r[key],atol=1e-9,rtol=1e-9,equal_nan=True),(path,key)
            checks.append(dict(file=path.name,option_id=option['id'],fallback_baseline_voiced=fallback,
                clipped_entries=int(np.sum(proof['raw_probability']!=proof['probability']))))
    selections=[];rows=measured.to_dict('records');names=sorted(measured.file.unique())
    from verify_yaapt_extension_v2 import independent_choose
    import yaapt_extension as alternate
    original=alternate.BY_ID
    try:
        alternate.BY_ID={o['id']:o for o in api.OPTIONS}
        for held in ['final']+names:
            pool=[n for n in names if n!=held]
            identity=independent_choose([r for r in rows if r['file'] in pool])
            selections.append(dict(outer_held=held,selection_files=pool,option_id=identity))
    finally:alternate.BY_ID=original
    assert selections==receipt['selections']
    summary,decision=gates(pd.read_csv(api.OUT/'H60_metrics.csv'))
    assert decision==receipt['decision']
    api.audit.json_write(api.OUT/'H60_verification.json',dict(status='PASS',groups=len(checks),checks=checks,
        independent_pcm_grid_projection_log_path_metrics_selection=True,
        shared_author_magnitude_phase=True,limitation='No independent implementation of magnitude/phase spline feature math.'))
    print('PASS H60 independent path/grid/projection/scoring/config selection',len(checks),'groups')


if __name__=='__main__':verify()
