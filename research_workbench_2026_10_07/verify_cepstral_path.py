import argparse
import json
import numpy as np
import pandas as pd
import cepstral_path as api
from verify_yaapt_extension_v2 import independent_item, independent_score


def independent_features(audio,fs,proof):
    length=int(proof['frame_samples']);nfft=int(proof['nfft']);lags=proof['lags']
    for i in np.flatnonzero(proof['base_pred']):
        start=round(float(proof['times'][i])*fs-length/2)
        x=np.array([audio[s] if 0<=s<len(audio) else 0. for s in range(start,start+length)])
        x-=sum(x)/len(x)
        magnitude=abs(np.fft.fft(x*np.hanning(length),nfft))
        floor=max(max(magnitude)*1e-8,1e-20)
        cep=np.fft.ifft(np.log(np.maximum(magnitude,floor))).real[lags]
        acf=[]
        for lag in lags:
            a,b=x[:-lag],x[lag:]
            acf.append(np.dot(a,b)/max(np.sqrt(np.dot(a,a))*np.sqrt(np.dot(b,b)),1e-20))
        acf=np.array(acf)
        assert np.allclose(cep,proof['cep_curves'][i],atol=1e-8,rtol=1e-8)
        assert np.allclose(acf,proof['acf_curves'][i],atol=1e-10,rtol=1e-10)
        assert proof['starts'][i]==start
        expected=[float(proof['base_f0'][i])]
        for curve in (acf,cep):
            peaks=[]
            for k in range(1,len(curve)-1):
                if curve[k]>0 and curve[k]>=curve[k-1] and curve[k]>=curve[k+1]:peaks.append(k)
            peaks.sort(key=lambda k:(-curve[k],k));accepted=[]
            for k in peaks:
                a,b,c=curve[k-1:k+2]
                delta=(a-c)/(2*(a-2*b+c)) if abs(a-2*b+c)>1e-12 else 0.
                lag=lags[k]+max(-.5,min(.5,delta));pitch=fs/lag
                if 70<=pitch<=400 and abs(1200*np.log2(pitch/proof['base_f0'][i]))<=200:accepted.append(pitch)
                if len(accepted)==4:break
            expected+=accepted
        finite=proof['candidates'][i,np.isfinite(proof['candidates'][i])]
        assert len(expected)==len(finite) and np.allclose(expected,finite,atol=1e-8,rtol=1e-10)
        for j,pitch in enumerate(finite):
            q=fs/pitch
            index=np.searchsorted(lags,q)-1;index=max(0,min(len(lags)-2,index))
            weight=np.clip((q-lags[index])/(lags[index+1]-lags[index]),0,1)
            value=acf[index]*(1-weight)+acf[index+1]*weight
            strength=cep[index]*(1-weight)+cep[index+1]*weight
            assert np.isclose(np.clip(value,0,1),proof['acf_score'][i,j],atol=1e-10)
            assert np.isclose(np.clip(strength/max(max(cep[1:-1]),1e-20),0,1),proof['cep_score'][i,j],atol=1e-8)


def independent_path(proof,option):
    if option['alpha'] is None:return proof['base_f0'].copy()
    output=proof['base_f0'].copy();alpha=option['alpha'];strength=option['transition']
    voiced=np.flatnonzero(proof['base_pred'])
    for run in np.split(voiced,np.flatnonzero(np.diff(voiced)>1)+1):
        if not len(run):continue
        back=[];costs=None
        for i in run:
            candidates=proof['candidates'][i];valid=np.flatnonzero(np.isfinite(candidates))
            next_cost=np.full(9,np.inf);predecessors=np.zeros(9,int)
            for j in valid:
                cents=abs(1200*np.log2(candidates[j]/proof['base_f0'][i]))
                local=1-((1-alpha)*proof['acf_score'][i,j]+alpha*proof['cep_score'][i,j])+.15*cents/200
                if costs is None:next_cost[j]=local;continue
                values=[]
                for k in range(9):
                    previous=proof['candidates'][i-1,k]
                    if np.isfinite(previous):
                        distance=min(abs(1200*np.log2(candidates[j]/previous))/200,3)
                        values.append(costs[k]+strength*distance)
                    else:values.append(np.inf)
                best=int(np.argmin(values));predecessors[j]=best;next_cost[j]=values[best]+local
            costs=next_cost;back.append(predecessors)
        state=int(np.argmin(costs))
        for t in range(len(run)-1,-1,-1):
            output[run[t]]=proof['candidates'][run[t],state];state=int(back[t][state])
    return output


def choose(rows):
    rank=[]
    for identity in api.BY_ID:
        scores=[r['average_mape'] for r in rows if r['option_id']==identity]
        rank.append((max(scores),sum(scores)/len(scores),identity))
    return min(rank)[-1]


def verify(stage):
    api.check_registry()
    receipt=json.loads((api.OUT/f'H53_{stage}_experiment.json').read_text())
    for path,digest in receipt['artifacts'].items():assert api.audit.digest(api.REPO/path)==digest,path
    metrics=pd.read_csv(api.OUT/f'H53_{stage}_fixed.csv',float_precision='round_trip')
    old=pd.read_csv(api.OUT/('H47_nested_contours.csv' if stage=='train' else 'H48_test_contours.csv'),float_precision='round_trip')
    rows=[];frames=0
    for name in sorted(metrics.file.unique()):
        path=(api.core.TRAIN if stage=='train' else api.REPO/'TinHieuKiemThu')/name
        item,fs,audio=independent_item(path,stage)
        proof=dict(np.load(api.OUT/f'H53_{stage}_design_{path.stem}.npz',allow_pickle=False))
        saved=dict(np.load(api.OUT/f'H53_{stage}_predictions_{path.stem}.npz',allow_pickle=False))
        group=old[(old.file==name)&(old.model=='candidate')]
        assert np.array_equal(group.pred_voiced.to_numpy(bool),proof['base_pred'])
        assert np.allclose(group.f0_hz,proof['base_f0'],atol=1e-12,equal_nan=True)
        assert np.allclose(proof['times'],item['times'],atol=1e-12)
        independent_features(audio,fs,proof);frames+=int(proof['base_pred'].sum())
        for k,identity in enumerate(saved['option_id']):
            expected=independent_path(proof,api.BY_ID[str(identity)])
            assert np.allclose(expected,saved['f0'][k],rtol=0,atol=1e-10,equal_nan=True)
            assert np.array_equal(np.isfinite(expected),saved['pred'])
            value=independent_score(item,saved['pred'],expected)
            stored=metrics[(metrics.file==name)&(metrics.option_id==identity)].iloc[0]
            assert all(np.isclose(stored[key],v,atol=1e-9,rtol=1e-10) for key,v in value.items())
            rows.append(dict(file=name,option_id=identity,**value))
    if stage=='train':
        assert len(rows)==40
        for selection in receipt['selections']:
            outer=selection['outer_held'];pool=selection['selection_files']
            assert outer not in pool and set(pool)==set(metrics.file.unique())-({outer} if outer!='final' else set())
            assert choose([r for r in rows if r['file'] in pool])==selection['option_id']
        traces=pd.read_csv(api.OUT/'H53_inner_traces.csv',keep_default_na=False)
        assert len(traces)==160 and (traces.actual_fit_files=='').all()
        table=pd.read_csv(api.OUT/'H53_metrics.csv',float_precision='round_trip')
        for _,row in table.iterrows():
            group=next(r for r in rows if r['file']==row['file'] and r['option_id']==row['option_id'])
            assert all(np.isclose(row[key],v,atol=1e-9) for key,v in group.items() if key not in ('file','option_id'))
        _,gates=api.common.gates(table);assert gates==receipt['decision']
    else:
        freeze=json.loads((api.OUT/'H53_FROZEN_SELECTION.json').read_text())
        assert set(metrics.option_id)==set(freeze['external_options'])
        assert receipt['freeze_sha256']==api.audit.digest(api.OUT/'H53_FROZEN_SELECTION.json') and not receipt['test_tuning']
    api.audit.json_write(api.OUT/f'H53_{stage}_verification.json',dict(passed=True,
        independent_full_fft_cepstrum_direct_correlation_candidate_frames=frames,metric_groups=len(rows),
        independent_scalar_path=True,mask_count_vuv_sil_unchanged=True,new_native_calls=0,
        verifier_sha256=api.audit.digest(__file__)))
    print(f'PASS H53 {stage}: {frames} independent cepstral/correlation frames, {len(rows)} metric groups, scalar paths and unchanged masks')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['train','test'])
    verify(parser.parse_args().stage)
