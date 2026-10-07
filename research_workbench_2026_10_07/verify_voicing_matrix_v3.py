import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
import voicing_matrix as api
from verify_voicing_features_v2 import independent_score, independent_features

HERE,OUT,REPO=api.HERE,api.OUT,api.REPO


def hashes(experiment):
    api.verify_registry()
    for path,digest in experiment['artifacts'].items():
        assert api.audit.digest(REPO/path)==digest,path


def check_row(item,features,model,row,override=None):
    pred,f0,prob,recover=api.infer(features,model,override)
    actual=independent_score(item,pred,f0)
    assert all(np.isclose(row[key],value,atol=1e-8) for key,value in actual.items()),row.get('recipe_id','selected')
    assert row['recovered']==sum(recover)
    for lab in ('v','uv','sil'):
        assert row['recovered_'+lab]==sum(recover&(item['labels']==lab))
    assert np.array_equal(f0[features['base_pred']],features['base_f0'][features['base_pred']])
    return pred,f0,prob,recover


def check_fits(path,bank):
    saved=json.loads(path.read_text())['fits']
    for i,row in enumerate(saved):
        seed=row['actual_seed'] or api.SEEDS[0]
        api.fit(bank,row['fit_files'],api.BY_ID[row['recipe_id']],seed)
        current=next(record for record in api.FIT_LOG if record['recipe_id']==row['recipe_id'] and record['fit_files']==row['fit_files'] and record['actual_seed']==row['actual_seed'])
        assert current==row,(row['recipe_id'],row['fit_files'],row['actual_seed'])
        if i%300==0: print('H51 verify fits',i,'/',len(saved),flush=True)
    return len(saved)


def train():
    experiment=json.loads((OUT/'H51_train_experiment.json').read_text());hashes(experiment)
    bank=api.load_bank();items={item['file']:item for item in api.core.load_training()};names=sorted(bank)
    refits=check_fits(OUT/'H51_train_fits.json',bank)
    fixed=pd.read_csv(OUT/'H51_fixed_lofo.csv');checked=0
    assert len(fixed)==len(api.RECIPES)*3*4
    predictions={name:dict(np.load(OUT/f'H51_predictions_{Path(name).stem}.npz',allow_pickle=False)) for name in names}
    for _,row in fixed.iterrows():
        held=row['file'];model=api.fit(bank,[n for n in names if n!=held],api.BY_ID[row.recipe_id],int(row.seed))
        pred,f0,prob,recover=check_row(items[held],bank[held],model,row)
        saved=predictions[held];idx=int(np.flatnonzero((saved['recipe_id']==row.recipe_id)&(saved['seed']==row.seed))[0])
        for key,value in [('pred',pred),('f0',f0),('prob',prob),('recover',recover)]:
            assert np.allclose(saved[key][idx],value,atol=1e-10,equal_nan=True),key
        checked+=1
    traces=pd.read_csv(OUT/'H51_inner_traces.csv')
    for selection in experiment['selections']:
        outer=selection['outer_held'];group=traces[traces.outer_held==outer];pool=selection['selection_files']
        assert outer=='final' or outer not in pool
        for _,row in group.iterrows():
            fits=row.fit_files.split('|');assert row.inner_held not in fits and (outer=='final' or outer not in fits)
            model=api.fit(bank,fits,api.BY_ID[row.recipe_id],int(row.seed))
            check_row(items[row.inner_held],bank[row.inner_held],model,row);checked+=1
        ranks=[]
        for identity,part in group.groupby('recipe_id'):
            valid=True
            for seed in api.SEEDS:
                g=part[part.seed==seed];c=group[(group.recipe_id=='hard170')&(group.seed==seed)]
                valid &= np.isfinite(g.average_mape).all() and g.macro_f1.mean()>=c.macro_f1.mean()-.01 and g.recall_v.mean()>=c.recall_v.mean()-.01 and g.false_voiced_sil.sum()<=c.false_voiced_sil.sum()+1
            ranks.append((not valid,part.average_mape.max() if valid else np.inf,part.average_mape.mean() if valid else np.inf,identity))
        assert min(ranks)[3]==selection['recipe_id']
    selected={r['outer_held']:r['recipe_id'] for r in experiment['selections']}
    metrics=pd.read_csv(OUT/'H51_metrics.csv')
    for _,row in metrics.iterrows():
        fits=names if row.split=='train' else [n for n in names if n!=row['file']]
        identity='hard170' if row.model=='accepted' else selected[row['file'] if row.split=='nested' else 'final']
        assert identity==row.option_id
        check_row(items[row['file']],bank[row['file']],api.fit(bank,fits,api.BY_ID[identity],int(row.seed)),row);checked+=1
    for seed in api.SEEDS:
        _,decision=api.base.gates(metrics[metrics.seed==seed]);assert decision==experiment['decisions'][str(seed)]
    manifest={case['case_id']:case for case in json.loads((OUT/'H46_augmentation_manifest.json').read_text())['cases']}
    noise=pd.read_csv(OUT/'H51_robustness.csv');designs={}
    pcm_frames=0
    for identity,case in manifest.items():
        fs,audio=api.core.load_audio(HERE/case['path']);x,pitch=independent_features(audio,fs)
        data=dict(np.load(OUT/f'H51_robust_design_{identity}.npz',allow_pickle=False));designs[identity]=data
        assert np.allclose(x,data['x'],atol=1e-8) and np.allclose(pitch,data['pitch'],atol=1e-8,equal_nan=True)
        pcm_frames+=len(x)
    for _,row in noise.iterrows():
        held=row['file'];check_row(items[held],designs[row.case_id],api.fit(bank,[n for n in names if n!=held],api.BY_ID[row.recipe_id],int(row.seed)),row);checked+=1
    permutation=pd.read_csv(OUT/'H51_permutation.csv')
    assert len(permutation)==900
    for _,row in permutation.iterrows():
        held=row['file'];digest=hashlib.sha256(f'{held}|{int(row.seed)}|{row.block}|{int(row['repeat'])}'.encode()).digest()
        rng=np.random.default_rng(int.from_bytes(digest[:8],'little'));x=bank[held]['x'].copy();order=rng.permutation(len(x));columns=api.BLOCKS[row.block];x[:,columns]=x[order][:,columns]
        model=api.fit(bank,[n for n in names if n!=held],api.BY_ID[row.recipe_id],int(row.seed))
        check_row(items[held],bank[held],model,row,x);checked+=1
        clean=independent_score(items[held],*api.infer(bank[held],model)[:2])
        assert np.isclose(row.delta_average_mape,row.average_mape-clean['average_mape'],atol=1e-8)
        assert np.isclose(row.delta_macro_f1,row.macro_f1-clean['macro_f1'],atol=1e-8)
    cross=pd.read_csv(OUT/'H51_cross_condition.csv')
    for _,row in cross.iterrows():
        fits=row.fit_files.split('|');assert row['file'] not in fits
        check_row(items[row['file']],bank[row['file']],api.fit(bank,fits,api.BY_ID[row.recipe_id],int(row.seed)),row);checked+=1
    api.audit.json_write(OUT/'H51_train_verification.json',dict(passed=True,model_refits=refits,verification_source_sha256=api.audit.digest(__file__),feature_verifier_sha256=api.audit.digest(HERE/'verify_voicing_features_v2.py'),independent_metric_groups=checked,
        robustness_pcm_fullfft_dct_acf_frames=pcm_frames,fit_selection_exclusion=True,seed_never_selected=True,permutation_groups=len(permutation),
        experiment_sha256=api.audit.digest(OUT/'H51_train_experiment.json'),freeze_sha256=api.audit.digest(OUT/'H51_FROZEN_SELECTION.json')))
    print('PASS H51 train',refits,checked,pcm_frames,flush=True)


def external():
    experiment=json.loads((OUT/'H51_external_experiment.json').read_text());hashes(experiment)
    bank=api.load_bank();names=sorted(bank);refits=check_fits(OUT/'H51_external_fits.json',bank)
    metrics=pd.read_csv(OUT/'H51_test_metrics.csv');checked=0;frames=0
    baseline=pd.read_csv(OUT/'H48_test_metrics.csv')
    for name,group in metrics.groupby('file'):
        path=REPO/'TinHieuKiemThu'/name;item=api.core.frame_features(path,split='test');fs,audio=api.core.load_audio(path)
        x,pitch=independent_features(audio,fs);data=dict(np.load(OUT/f'H51_test_{Path(name).stem}.npz',allow_pickle=False))
        assert np.allclose(x,data['x'],atol=1e-8) and np.allclose(pitch,data['pitch'],atol=1e-8,equal_nan=True);frames+=len(x)
        for _,row in group.iterrows():
            pred,f0,prob,recover=check_row(item,data,api.fit(bank,names,api.BY_ID[row.recipe_id],int(row.seed)),row)
            idx=int(np.flatnonzero((data['recipe_id']==row.recipe_id)&(data['seed']==row.seed))[0])
            for key,value in [('pred',pred),('f0',f0),('prob',prob),('recover',recover)]:assert np.allclose(data[key][idx],value,atol=1e-10,equal_nan=True)
            if row.recipe_id=='hard170':
                old=baseline[(baseline.model=='candidate')&(baseline.file==name)].iloc[0]
                assert np.isclose(old.average_mape,row.average_mape,atol=1e-8)
            checked+=1
    from benchmark_keele import score as benchmark_score
    keele=pd.read_csv(OUT/'H51_keele_metrics.csv');cases=json.loads((OUT/'H49_dataset_manifest.json').read_text())['cases']
    old_metrics=pd.read_csv(OUT/'H49_metrics.csv')
    for case in cases:
        directory=HERE/case['relative_dir'];fs,audio=api.core.load_audio(directory/'signal.wav');x,pitch=independent_features(audio,fs)
        length,hop=round(fs*.025),round(fs*.01);times=(np.arange(len(x))*hop+length/2)/fs
        data=dict(np.load(OUT/f'H51_keele_{case["id"]}.npz',allow_pickle=False));native=dict(np.load(OUT/f'H49_native_{case["id"]}.npz',allow_pickle=False))
        right=np.minimum(np.searchsorted(times,native['times']),len(times)-1);left=np.maximum(right-1,0)
        idx=np.where(abs(times[left]-native['times'])<=abs(times[right]-native['times']),left,right);support=abs(times[idx]-native['times'])<=.005+1/fs
        assert np.allclose(data['x'],x[idx],atol=1e-8) and np.allclose(data['pitch'],np.where(support,pitch[idx],np.nan),atol=1e-8,equal_nan=True);frames+=len(x)
        reference=np.load(directory/'pitch.npy',allow_pickle=False)
        for _,row in keele[keele.file==case['id']].iterrows():
            pred,f0,prob,recover=api.infer(data,api.fit(bank,names,api.BY_ID[row.recipe_id],int(row.seed)))
            idxout=int(np.flatnonzero((data['recipe_id']==row.recipe_id)&(data['seed']==row.seed))[0])
            assert np.allclose(data['f0'][idxout],f0,atol=1e-10,equal_nan=True)
            right=np.minimum(np.searchsorted(native['times'],reference['time']),len(native['times'])-1);left=np.maximum(right-1,0)
            idx=np.where(abs(native['times'][left]-reference['time'])<=abs(native['times'][right]-reference['time']),left,right)
            supported=abs(native['times'][idx]-reference['time'])<=.005+1/fs
            estimated=np.where(pred[idx]&supported,f0[idx],0.)
            assert np.array_equal(data['support'][idxout],supported) and np.allclose(data['estimate'][idxout],estimated,atol=1e-10)
            actual=benchmark_score(reference['pitch'],estimated,supported)
            assert all(np.isclose(row[key],value,atol=1e-8) for key,value in actual.items())
            # Independently check confusion counts and gross/cents denominators.
            valid=supported & (reference['pitch']>=0);r=reference['pitch'][valid];e=estimated[valid];both=(r>0)&(e>0)
            assert row.TP==sum(both) and row.FN==sum((r>0)&(e<=0)) and row.FP==sum((r==0)&(e>0))
            assert row.gross_error_frames==sum(abs(e[both]-r[both])/r[both]>.2)
            assert row.correct50_frames==sum(abs(1200*np.log2(e[both]/r[both]))<=50)
            if row.recipe_id=='hard170':
                old=old_metrics[(old_metrics.model=='candidate')&(old_metrics.file==case['id'])].iloc[0]
                assert np.isclose(old.average_mape,row.average_mape,atol=1e-8) and np.isclose(old.rpa50_pct,row.rpa50_pct,atol=1e-8)
            checked+=1
        print('H51 verify KEELE',case['id'],flush=True)
    assert api.audit.digest(OUT/'H51_FROZEN_SELECTION.json')==experiment['freeze_sha256']
    api.audit.json_write(OUT/'H51_external_verification.json',dict(passed=True,model_refits=refits,verification_source_sha256=api.audit.digest(__file__),feature_verifier_sha256=api.audit.digest(HERE/'verify_voicing_features_v2.py'),independent_metric_groups=checked,
        fullfft_dct_acf_pcm_frames=frames,native_calls=0,freeze_unchanged=True,reference_unknown_and_denominators_verified=True,
        experiment_sha256=api.audit.digest(OUT/'H51_external_experiment.json')))
    print('PASS H51 external',refits,checked,frames,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['train','external']);args=parser.parse_args()
    with threadpool_limits(limits=1):
        train() if args.phase=='train' else external()

