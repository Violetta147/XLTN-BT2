import argparse
import json
import platform
import time
import numpy as np
import pandas as pd
import scipy
from threadpoolctl import threadpool_limits
import recovery_pitch as common
from maps_adapter import native, project
from verify_srh import independent_item, independent_score
from voicing_recovery import gates

HERE, OUT, REPO, core, audit = common.HERE, common.OUT, common.REPO, common.core, common.audit
OPTIONS = [dict(id='hard170', mode='base'), dict(id='maps_pitch', mode='pitch')] + [
    dict(id=f'maps_whole_{int(q*100):02d}', mode='whole', threshold=q) for q in (.2, .5, .8)]


def choose(rows):
    base = [r for r in rows if r['option_id']=='hard170']
    ranking = []
    for option in OPTIONS:
        group = [r for r in rows if r['option_id']==option['id']]
        good = all(np.isfinite(r['average_mape']) for r in group)
        for key in ('macro_f1', 'recall_v'):
            good &= np.mean([r[key] for r in group]) >= np.mean([r[key] for r in base])-.01
        good &= sum(r['false_voiced_sil'] for r in group) <= sum(r['false_voiced_sil'] for r in base)+1
        ranking.append((not good, max(r['average_mape'] for r in group) if good else np.inf,
                        np.mean([r['average_mape'] for r in group]) if good else np.inf, option['id']))
    return sorted(ranking)[0][-1]


def check_registry():
    registry = json.loads((HERE/'H60_REGISTRY.json').read_text())
    assert registry['options']==OPTIONS
    for name, digest in registry['source_hashes'].items():
        assert audit.digest(REPO/name)==digest, name
    return registry


def precheck():
    from verify_maps import independent_path
    rows=[]
    for fs in (16000, 44100):
        t=np.arange(round(.3*fs))/fs
        for pitch in (90, 200, 320):
            audio=sum(np.sin(2*np.pi*pitch*h*t)/h for h in range(1,6))*.1
            proof=native(audio,fs)
            assert np.array_equal(independent_path(proof['probability'],proof['frequencies']),proof['f0'])
            error=float(np.median(abs(1200*np.log2(proof['f0']/pitch))))
            assert error<100, (fs,pitch,error)
            rows.append(dict(fs=fs,pitch=pitch,median_cents_error=error))
        for audio in (np.zeros(len(t)),np.random.default_rng(11).normal(0,.01,len(t))):
            proof=native(audio,fs)
            assert np.isfinite(proof['probability']).all() and np.isfinite(proof['f0']).all()
    audit.json_write(OUT/'H60_precheck.json',dict(synthetic_only=True, BT2_used=False,
        tone_tests=rows, silence_noise_finite=True, independent_log_path_parity=True,
        note='Silence finiteness is not a silence rejection accuracy claim. Deterministic algorithm, no fitted seeds.'))
    protected=[HERE/'maps_adapter.py',HERE/'maps_experiment.py',HERE/'verify_maps.py',
        HERE/'H60_REGISTRATION.md',HERE/'MAPS_SOURCE_REVIEW.md',OUT/'MAPS_source_download.json',
        OUT/'H60_precheck.json',OUT/'H60_initial_synthetic_failure.json',OUT/'H47_nested_contours.csv',
        HERE/'verify_srh.py',HERE/'verify_yaapt_extension_v2.py',HERE/'yaapt_extension.py',
        HERE/'voicing_recovery.py',HERE/'recovery_pitch.py',HERE/'voicing_matrix.py',
        REPO/'research_3gt_2026_10_05/core.py',REPO/'research_workbench_2026_10_06/audit.py',
        core.RESULTS/'frozen_config.json',REPO/'.gitattributes']
    protected+=list((HERE/'vendor/maps').iterdir())
    protected+=list(core.TRAIN.glob('*.wav'))+list(core.TRAIN.glob('*.lab'))+list(core.TRAIN_GT.glob('*.lab'))
    audit.json_write(HERE/'H60_REGISTRY.json',dict(family='H60', options=OPTIONS,
        rollback=common.matrix.commit_id(), source_hashes={str(p.relative_to(REPO)):audit.digest(p) for p in protected},
        random_training=False, test_enabled_only_if_eligible=True))
    print('PASS H60 synthetic precheck; registry written; no BT2 measurements')


def train():
    check_registry()
    assert not (OUT/'H60_train_experiment.json').exists(), 'Preserve prior measurements'
    started=time.perf_counter()
    old=pd.read_csv(OUT/'H47_nested_contours.csv',float_precision='round_trip')
    rows=[];artifacts=[]
    with threadpool_limits(limits=1):
        for path in sorted(core.TRAIN.glob('*.wav')):
            item,fs,audio=independent_item(path,'train')
            baseline=old[(old.file==path.name)&(old.model=='candidate')]
            assert np.allclose(baseline.time_s,item['times'],atol=1e-12)
            base=dict(pred=baseline.pred_voiced.to_numpy(bool), f0=baseline.f0_hz.to_numpy())
            proof=native(audio,fs)
            proof_path=OUT/f'H60_native_{path.stem}.npz'
            np.savez_compressed(proof_path,**proof);artifacts.append(proof_path)
            predictions=[];pitches=[]
            for option in OPTIONS:
                if option['mode']=='base': pred,f0=base['pred'],base['f0']
                else: pred,f0,_=project(proof,item['times'],base,option['mode'],option.get('threshold',.5))
                metrics=core.score_file(item,pred,f0)
                rows.append(dict(option_id=option['id'],**metrics))
                predictions.append(pred);pitches.append(f0)
            saved=OUT/f'H60_predictions_{path.stem}.npz'
            np.savez_compressed(saved,times=item['times'],pred=predictions,f0=pitches);artifacts.append(saved)
            print('H60 measured train',path.name,flush=True)
    names=sorted({r['file'] for r in rows});inner=[];selections=[]
    for held in ['final']+names:
        pool=[n for n in names if n!=held]
        records=[r for r in rows if r['file'] in pool]
        selected=choose(records)
        selections.append(dict(outer_held=held,selection_files=pool,option_id=selected))
        for r in records:inner.append(dict(outer_held=held,inner_held=r['file'],
            selection_files='|'.join(pool),actual_fit_files='',**r))
    selected={r['outer_held']:r['option_id'] for r in selections};summaries=[]
    for split in ('train','lofo','nested'):
        for name in names:
            for model,identity in [('accepted','hard170'),('candidate',selected[name] if split=='nested' else selected['final'])]:
                score=next(r for r in rows if r['file']==name and r['option_id']==identity)
                summaries.append(dict(split=split,model=model,**score))
    summary,decision=gates(pd.DataFrame(summaries))
    for filename,data in [('H60_fixed.csv',rows),('H60_inner_traces.csv',inner),('H60_metrics.csv',summaries)]:
        p=OUT/filename;pd.DataFrame(data).to_csv(p,index=False);artifacts.append(p)
    audit.json_write(OUT/'H60_train_experiment.json',dict(family='H60',prereg_commit=common.matrix.commit_id(),
        registry_sha256=audit.digest(HERE/'H60_REGISTRY.json'),selections=selections,summaries=summary,decision=decision,
        actual_fits=0,native_calls=4,unique_measured_groups=len(rows),test_used=False,
        cv_note='Deterministic pretrained author likelihood table. Fold-local config selection; no fold-specific model fits.',
        runtime=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
        wall_time_s=time.perf_counter()-started,artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in artifacts}))
    print(json.dumps(dict(selections=selections,decision=decision),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['precheck','train'])
    args=parser.parse_args();precheck() if args.action=='precheck' else train()
