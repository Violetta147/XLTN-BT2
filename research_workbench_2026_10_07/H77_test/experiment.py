"""One frozen full-train H76 candidate evaluated on test; no fitting/search."""
import argparse,importlib.util,json,subprocess,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent;WORK=HERE.parent
spec=importlib.util.spec_from_file_location('h76_cached',WORK/'H76_decode/experiment.py');previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
REPO=previous.REPO;core=previous.core;audit=previous.audit
CONFIG=dict(family='H77',model='H75 recover5_C1 fit all four train files',decoder='bridge10_edge25',frame_ms=25,hop_ms=10,energy=.07,periodicity=.6,probability=.5,context=previous.CONTEXT,edge_hops=25,fit_on_test=False,source_selection='one candidate locked from H76 full-train all-file results; H76 held selection remains energy07')

def check_registry():
    r=json.loads((HERE/'REGISTRY.json').read_text());assert r['locked_config']==CONFIG
    for p,d in r['source_hashes'].items():assert audit.digest(REPO/p)==d,p
    for p,d in r['external_protected'].items():assert audit.digest(Path(p))==d,p
    return r

def prepare(out):
    assert not (HERE/'REGISTRY.json').exists() and not out.exists();out.mkdir();old=previous.check_registry();names=sorted(p.name for p in core.TRAIN.glob('*.wav'));models=json.loads((WORK/'H75_ml/run_train/models.json').read_text());model=next(m for m in models if m['option_id']=='recover5_C1' and m['fit_files']==names);audit.json_write(HERE/'locked_model.json',model)
    table=pd.read_csv(WORK/'H76_decode/run_train/all_train_metrics.csv',float_precision='round_trip');train=table[(table.option_id=='bridge10_edge25')&(table.fit_pool=='|'.join(names))];assert len(train)==4 and (train.average_mape<2).all();assert json.loads((WORK/'H76_decode/run_train/verification.json').read_text())['status']=='PASS'
    audit.json_write(out/'final_info.json',dict(status='PASS',BT2_test_used=False,supervised_fits=0,train_groups_reused=4,locked_config=CONFIG,model_sha256=audit.digest(HERE/'locked_model.json'),H76_historical_selection_unchanged=True,prechecks_reused_without_rerun=True))
    sources=dict(old['source_hashes']);paths=[HERE/p for p in ('experiment.py','verify.py','plot.py','notes.txt','REGISTRATION.md','locked_model.json')]+[out/'final_info.json',WORK/'H76_decode/REGISTRY.json',WORK/'H76_decode/experiment.py',WORK/'H76_decode/verify.py',WORK/'H76_decode/run_train/final_info.json',WORK/'H76_decode/run_train/verification.json'];receipt=json.loads((WORK/'H76_decode/run_train/final_info.json').read_text());paths += [REPO/p for p in receipt['artifacts']]
    for p in paths:sources[str(p.relative_to(REPO))]=audit.digest(p)
    audit.json_write(HERE/'REGISTRY.json',dict(family='H77',rollback=previous.previous.base.previous.old.common.matrix.commit_id(),locked_config=CONFIG,source_hashes=sources,external_protected=old['external_protected'],test_search=False,historical_test_exposure=True,LOFO_diagnostic_not_test_prerequisite=True))
    print('PASS H77 frozen model/config and four cached train groups; no test feature extraction or inference',flush=True)

def test(out):
    check_registry();assert not out.exists();git=['git','-c',f'safe.directory={REPO.as_posix()}'];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=REPO,text=True).strip();branch=subprocess.check_output(git+['branch','--show-current'],cwd=REPO,text=True).strip();assert subprocess.check_output(git+['ls-remote','origin','refs/heads/'+branch],cwd=REPO,text=True).split()[0]==head and not subprocess.check_output(git+['status','--porcelain'],cwd=REPO,text=True).strip();out.mkdir();start=time.perf_counter()
    from verify_srh import independent_item
    import voicing_recovery as features
    model=json.loads((HERE/'locked_model.json').read_text());names=model['fit_files'];prior=pd.read_csv(WORK/'H76_decode/run_train/all_train_metrics.csv',float_precision='round_trip');train=prior[(prior.option_id=='bridge10_edge25')&(prior.fit_pool=='|'.join(names))];rows=[dict(eval_split='train',pipeline_id='H77_bridge10_edge25',**r) for r in train.to_dict('records')];logs=[]
    print('H77: evaluate one full-train frozen classifier/decoder on test; native H72 cached; no test fitting or selection',flush=True)
    for path in sorted((REPO/'TinHieuKiemThu').glob('*.wav')):
        item,fs,audio=independent_item(path,'test');native=dict(np.load(WORK/f'results/H72_test_proof_{path.stem}.npz'));f=features.design(audio,fs);assert np.array_equal(f['times'],native['native_times']) and np.array_equal(f['times'],item['times']);bank=dict(x=np.column_stack((f['x'][:,:4],native['probability'])),acf_pitch=f['pitch'],times=f['times'],labels=item['labels'],native_voiced=native['voiced'],native_f0=native['raw_f0'],control_pred=native['pred']);raw_pred,raw_f0=previous.previous.infer(bank,dict(id='recover5_C1'),model);pred,f0,mode=previous.decode(bank,raw_pred,raw_f0,dict(id='bridge10_edge25',edge_hops=25));rows.append(dict(eval_split='test',pipeline_id='H77_bridge10_edge25',option_id='bridge10_edge25',fit_pool='|'.join(names),eval_file_in_fit=False,**core.score_file(item,pred,f0)));np.savez_compressed(out/f'proof_{path.stem}.npz',**bank,raw_pred=raw_pred,raw_f0=raw_f0,pred=pred,f0=f0,mode=mode);logs.append(dict(file=path.name,fs=int(fs),frame_samples=round(fs*.025),hop_samples=round(fs*.01),native_inference_repeated=False,model_refit=False,test_feature_extraction_new=True,frames=len(pred)));print('H77 test measured',path.name,flush=True)
    table=pd.DataFrame(rows);assert len(table)==8;table.to_csv(out/'all_files.csv',index=False);audit.json_write(out/'runtime_logs.json',logs);artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in out.iterdir()};audit.json_write(out/'final_info.json',dict(status='MEASURED',family='H77',prereg_commit=head,locked_config=CONFIG,registry_sha256=audit.digest(HERE/'REGISTRY.json'),actual_native_inferences=0,supervised_fits=0,new_test_feature_files=4,cached_train_groups=4,new_test_groups=4,train_below_two=int((table[table.eval_split=='train'].average_mape<2).sum()),test_below_two=int((table[table.eval_split=='test'].average_mape<2).sum()),target_achieved=bool(np.isfinite(table.average_mape).all() and (table.average_mape<2).all()),champion_promoted=False,test_parameter_search=False,historical_test_exposure=True,H76_historical_selection_unchanged=True,wall_time_s=time.perf_counter()-start,artifacts=artifacts))
    print('H77 completed; each-file target',bool((table.average_mape<2).all()),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--action',choices=['prepare','test'],required=True);p.add_argument('--out_dir',required=True);a=p.parse_args();prepare(Path(a.out_dir).resolve()) if a.action=='prepare' else test(Path(a.out_dir).resolve())
