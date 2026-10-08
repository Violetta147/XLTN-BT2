"""Train-only native default Praat fingerprint; prior algorithms read from cache."""
import argparse, json, math, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import parselmouth
import recovery_pitch as api
HERE, OUT, REPO, core, audit = api.HERE, api.OUT, api.REPO, api.core, api.audit
OPTIONS=[dict(id=f'praat6_{method}_{step}',method=method,time_step=None if step=='auto' else .01)
         for method in ('ac','cc') for step in ('auto','10ms')]
def extract(audio,fs,option):
    sound=parselmouth.Sound(audio,sampling_frequency=fs)
    pitch=getattr(sound,'to_pitch_'+option['method'])(time_step=option['time_step'],pitch_floor=75,pitch_ceiling=600)
    return pitch.xs(),pitch.selected_array['frequency']
def guard():
    head=api.matrix.commit_id()
    branch=subprocess.check_output(['git','-c',f'safe.directory={REPO.as_posix()}','branch','--show-current'],cwd=REPO,text=True).strip()
    remote=subprocess.check_output(['git','-c',f'safe.directory={REPO.as_posix()}','ls-remote','origin',f'refs/heads/{branch}'],cwd=REPO,text=True).split()[0]
    assert head==remote
    assert not subprocess.check_output(['git','-c',f'safe.directory={REPO.as_posix()}','status','--porcelain'],cwd=REPO,text=True).strip()
    return head
def precheck():
    assert not (OUT/'R01_precheck.json').exists()
    t=np.arange(16000)/16000; audio=sum(np.cos(2*np.pi*200*h*t+.3*h)/h for h in range(1,7)); tests=[]
    for option in OPTIONS:
        times,f=extract(audio,16000,option); voiced=f[f>0]
        _,sil=extract(np.zeros(16000),16000,option)
        cents=float(abs(1200*np.log2(np.median(voiced)/200)))
        tests.append(dict(**option,voiced_count=len(voiced),median_cents=cents,silence_voiced=int((sil>0).sum()),passed=bool(len(voiced)>=20 and cents<100 and not np.any(sil>0))))
    passed=all(r['passed'] for r in tests)
    audit.json_write(OUT/'R01_precheck.json',dict(status='PASS' if passed else 'FAIL',BT2_used=False,tests=tests))
    assert passed
    old=json.loads((HERE/'H66_REGISTRY.json').read_text())
    sources=[REPO/p for p in old['source_hashes']]+[HERE/p for p in ('reference_reconstruction.py','REFERENCE_RECONSTRUCTION_REGISTRATION.md','results/R01_precheck.json','results/H28_fixed_lofo.csv','results/H30_fixed_lofo.csv','results/H30_raw_native_frames.csv','results/H33_fixed_lofo.csv','results/H33_raw_native_frames.csv','results/H47_nested_contours.csv','results/H48_test_contours.csv','results/dataset_provenance.json','results/public_repo_usage_review.json')]
    audit.json_write(HERE/'R01_REGISTRY.json',dict(options=OPTIONS,source_hashes={str(p.relative_to(REPO)):audit.digest(p) for p in sources},external_protected=old['external_protected'],runtime=dict(parselmouth=parselmouth.__version__,praat=parselmouth.PRAAT_VERSION)))
    print('R01 precheck PASS')
def stats_row(identity,name,values,target,kind):
    finite=[float(x) for x in values if np.isfinite(x) and x>0]
    mean=math.fsum(finite)/len(finite)
    ss=math.fsum((x-mean)**2 for x in finite)
    rows=[]
    for ddof in (0,1):
        std=math.sqrt(ss/(len(finite)-ddof))
        assert math.isclose(mean,np.mean(finite),rel_tol=1e-12)
        assert math.isclose(std,np.std(finite,ddof=ddof),rel_tol=1e-12)
        estimates=dict(F0mean=mean,F0std=std,F0num=len(finite))
        errors={k+'_mape':100*abs(v-target[k])/target[k] for k,v in estimates.items()}
        rows.append(dict(option_id=identity,file=name,origin=kind,std_ddof=ddof,**estimates,**errors,
            average_mape=sum(errors.values())/3,rounded_mean_match=round(mean,1)==target['F0mean'],rounded_std_match=round(std,1)==target['F0std'],count_match=len(finite)==target['F0num'],all_three_match=round(mean,1)==target['F0mean'] and round(std,1)==target['F0std'] and len(finite)==target['F0num']))
    return rows
def run():
    assert not (OUT/'R01_receipt.json').exists()
    reg=json.loads((HERE/'R01_REGISTRY.json').read_text())
    for p,d in reg['source_hashes'].items(): assert audit.digest(REPO/p)==d,p
    for p,d in reg['external_protected'].items(): assert audit.digest(Path(p))==d,p
    assert reg['runtime']==dict(parselmouth=parselmouth.__version__,praat=parselmouth.PRAAT_VERSION)
    head=guard(); rows=[]; native=[]; targets={}
    for path in sorted(core.TRAIN.glob('*.wav')):
        target=core.read_stats(core.TRAIN_GT/path.with_suffix('.lab').name); targets[path.name]=target
        fs,audio=core.load_audio(path)
        for option in OPTIONS:
            times,f=extract(audio,fs,option)
            rows+=stats_row(option['id'],path.name,f,target,'new_native_defaults_train_only')
            native += [dict(option_id=option['id'],file=path.name,time_s=float(t),f0_hz=float(v)) for t,v in zip(times,f)]
    # New analysis of saved native output; no algorithm run.
    for family in ('H30','H33'):
        cached=pd.read_csv(OUT/f'{family}_raw_native_frames.csv')
        for (identity,name),group in cached.groupby(['option_id','file']):
            rows+=stats_row(f'{family}:{identity}',name,group.raw_f0_hz,targets[name],'cached_native')
    # Harvest's cache contains only canonical projected statistics, clearly separated.
    cached_metrics=[]
    for family in ('H28','H30','H33'):
        table=pd.read_csv(OUT/f'{family}_fixed_lofo.csv')
        for record in table.to_dict('records'):
            record.update(family=family,origin='cached_canonical_projected_not_native');cached_metrics.append(record)
    counts=[]
    for family,filename,split in [('H47','H47_nested_contours.csv','train'),('H48','H48_test_contours.csv','test_cached_labels_only')]:
        table=pd.read_csv(OUT/filename);table=table[table.model=='candidate']
        for name,g in table.groupby('file'):
            gt=core.TRAIN_GT if split=='train' else core.HERE/'test_3gt'
            target=core.read_stats(gt/Path(name).with_suffix('.lab').name)
            counts.append(dict(file=name,split=split,LAB_V_centers=int((g.label=='v').sum()),teacher_F0num=target['F0num'],cached_baseline_count=int(g.pred_voiced.sum()),LAB_V_equals_teacher=int((g.label=='v').sum())==target['F0num']))
    table=pd.DataFrame(rows); table.to_csv(OUT/'R01_reference_matches.csv',index=False)
    pd.DataFrame(native).to_csv(OUT/'R01_new_native_frames.csv',index=False)
    pd.DataFrame(cached_metrics).to_csv(OUT/'R01_cached_pipeline_stats.csv',index=False)
    pd.DataFrame(counts).to_csv(OUT/'R01_label_count_audit.csv',index=False)
    matches=table.groupby(['option_id','std_ddof']).all_three_match.sum().to_dict()
    exact=[dict(option_id=k[0],std_ddof=int(k[1])) for k,n in matches.items() if n==4]
    outputs=[OUT/p for p in ('R01_reference_matches.csv','R01_new_native_frames.csv','R01_cached_pipeline_stats.csv','R01_label_count_audit.csv')]
    audit.json_write(OUT/'R01_receipt.json',dict(status='PASS',prereg_commit=head,new_BT2_inferences=16,new_inference_split='train_only',new_test_inference=False,teacher_procedure_identified=False,all_four_exact_matches=exact,match_counts=[dict(option_id=k[0],std_ddof=int(k[1]),matched_files=int(n)) for k,n in matches.items()],runtime=reg['runtime'],independent_scalar_numpy_stats=True,artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in outputs},limitations=['Matching outputs would not prove teacher software identity.','No native Harvest cache; projected statistics kept separate.','Sample versus population std cannot change mean or count.','Teacher algorithm and F0num definition remain unknown.']))
    print(table[table.origin=='new_native_defaults_train_only'][['option_id','file','std_ddof','average_mape','all_three_match']].to_string(index=False)); print('Exact all-four:',exact)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['precheck','run']);a=p.parse_args();precheck() if a.action=='precheck' else run()
