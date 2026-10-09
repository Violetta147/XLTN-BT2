"""H72: evaluate the one H71 full-train locked configuration on test."""
import argparse,json,platform,subprocess,time
from pathlib import Path
import numpy as np
import pandas as pd
import pyin_energy_fine_experiment as previous
from pyin25_adapter import pitch
from pyin_energy_experiment import energy,reject
from verify_srh import independent_item
HERE,OUT,REPO,core,audit=previous.HERE,previous.OUT,previous.REPO,previous.core,previous.audit
TEST=REPO/'TinHieuKiemThu'
CONFIG=dict(pipeline_id='pyin25_beta2_8_energy_0.07',beta_parameters=[2,8],energy_threshold=.07,frame_ms=25,hop_ms=10,center=False,padding=False,resampling=False,fmin=70,fmax=400,energy='centered_RMS/own_file_linear_p95_floor1e-12',selection='one configuration selected from four train files in H71; no test selection')

def check_registry():
    r=json.loads((HERE/'H72_REGISTRY.json').read_text());assert r['locked_config']==CONFIG
    for p,d in r['source_hashes'].items():assert audit.digest(REPO/p)==d,p
    for p,d in r['external_protected'].items():assert audit.digest(Path(p))==d,p
    return r

def prepare():
    assert not (HERE/'H72_REGISTRY.json').exists() and not (OUT/'H72_test_experiment.json').exists()
    r=previous.check_registry();sources=dict(r['source_hashes'])
    for n in ('H69_precheck.json','H70_precheck.json','H71_precheck.json','H71_verification.json'):
        assert json.loads((OUT/n).read_text())['status']=='PASS'
    selected=pd.read_csv(OUT/'H71_fixed.csv',float_precision='round_trip');selected=selected[selected.option_id=='pyin8_energy_0.07'];assert len(selected)==4 and (selected.average_mape<2).all()
    tests=sorted(TEST.glob('*.wav'));assert len(tests)==4
    paths=[HERE/p for p in ('H72_REGISTRATION.md','pyin_locked_test.py','verify_pyin_locked_test.py','H71_REGISTRY.json','H71_REPORT.md','results/H71_train_experiment.json','results/H71_verification.json')]
    paths += [REPO/'AGENTS.md'] + tests + [p.with_suffix('.lab') for p in tests] + [core.HERE/'test_3gt'/p.with_suffix('.lab').name for p in tests]
    receipt=json.loads((OUT/'H71_train_experiment.json').read_text());paths += [REPO/p for p in receipt['artifacts']]
    for p in paths:sources[str(p.relative_to(REPO))]=audit.digest(p)
    audit.json_write(HERE/'H72_REGISTRY.json',dict(family='H72',rollback=previous.old.common.matrix.commit_id(),locked_config=CONFIG,source_hashes=sources,external_protected=r['external_protected'],prechecks_reused_without_rerun=True,user_target='each of four train and four test files Average MAPE <2%; LOFO diagnostic not prerequisite',historical_test_exposure=True,old_H71_gate_decision_unchanged=True,parameter_search_on_test=False))
    print('PASS H72 integrity and reused prechecks; locked one train-selected config; no new inference')

def run():
    registry=check_registry();assert not (OUT/'H72_test_experiment.json').exists()
    git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip();branch=subprocess.check_output(git+['branch','--show-current'],cwd=REPO,text=True).strip();remote=subprocess.check_output(git+['ls-remote','origin','refs/heads/'+branch],cwd=REPO,text=True).split()[0]
    assert head==remote and not subprocess.check_output(git+['status','--porcelain'],cwd=REPO,text=True).strip()
    start=time.perf_counter();fixed=pd.read_csv(OUT/'H71_fixed.csv',float_precision='round_trip');train=fixed[fixed.option_id=='pyin8_energy_0.07'];rows=[dict(eval_split='train',pipeline_id=CONFIG['pipeline_id'],**r) for r in train.to_dict('records')];artifacts=[];logs=[]
    for path in sorted(TEST.glob('*.wav')):
        item,fs,audio=independent_item(path,'test');native,log=pitch(audio,fs,CONFIG['beta_parameters']);features=energy(audio,fs)
        assert np.array_equal(native['native_times'],features['times']) and np.array_equal(features['times'],item['times'])
        pred,f0=reject(native['voiced'],native['raw_f0'],features['relative_rms'],CONFIG['energy_threshold'])
        rows.append(dict(eval_split='test',pipeline_id=CONFIG['pipeline_id'],option_id='pyin8_energy_0.07',**core.score_file(item,pred,f0)));logs.append(dict(file=path.name,**log))
        p=OUT/f'H72_test_proof_{path.stem}.npz';np.savez_compressed(p,**native,**{k:v for k,v in features.items() if k not in native},pred=pred,f0=f0);artifacts.append(p)
        print('H72 test measured',path.name,flush=True)
    table=pd.DataFrame(rows);assert len(table)==8 and table.file.nunique()==8
    p=OUT/'H72_all_files.csv';table.to_csv(p,index=False);artifacts.append(p)
    p=OUT/'H72_runtime_logs.json';audit.json_write(p,logs);artifacts.append(p)
    finite=bool(np.isfinite(table.average_mape).all());all8=finite and bool((table.average_mape<2).all())
    audit.json_write(OUT/'H72_test_experiment.json',dict(family='H72',prereg_commit=head,registry_sha256=audit.digest(HERE/'H72_REGISTRY.json'),locked_config=CONFIG,actual_native_inferences=4,actual_supervised_fits=0,train_inference_repeated=False,parameter_search_on_test=False,train_groups_reused=4,test_groups_new=4,user_all8_target_pass=all8,train_below_2=int((table[table.eval_split=='train'].average_mape<2).sum()),test_below_2=int((table[table.eval_split=='test'].average_mape<2).sum()),champion_promoted=False,historical_H71_decision_modified=False,historical_test_exposure=True,protocol_change='User clarified goal: train and test each-file criterion; LOFO is retained diagnostic, not a prerequisite for frozen test evaluation.',runtime=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__),wall_time_s=time.perf_counter()-start,artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in artifacts}))
    print('H72 test finished; all8 target',all8)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
