import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import amdf_anchor as anchor
import amdf_soft_spectral as spectral
import praat_native_adapter as praat
from augmented_voicing_controller import project

HERE = Path(__file__).resolve().parent
core, audit = anchor.core, anchor.audit
CONFIG = dict(option_id='amdf_pitch_spectral_p170', gate_method='filtered', voicing_threshold=.3,
              range_hz=[70,400], short_window_ms=25, long_window_ms=40, hop_ms=10,
              minimum_gate_hz=170, hf_threshold=.05, hf_cutoff_hz=1000, agreement_cents=200,
              canonical_frame_ms=25, target='every file average_mape < 2 percent')


def estimate(path):
    fs, audio = core.load_audio(path)
    times, gate, call = praat.pitch(path, CONFIG['gate_method'], CONFIG['voicing_threshold'])
    item = dict(file=Path(path).name,fs=fs)
    bank = {}
    for window in (25,40):
        proof = anchor.curves(item,audio,times,gate,window)
        bank[window] = dict(np.load(HERE / proof['path']))
    ratio = np.full(len(times),np.nan)
    f0 = gate.copy()
    for i in np.flatnonzero((gate>=70)&(gate<=400)):
        long_start = bank[40]['starts'][i]
        length = int(bank[40]['frame_samples'])
        if 0 <= long_start and long_start+length <= len(audio):
            ratio[i] = spectral.high_frequency_ratio(audio[long_start:long_start+length],fs)
        window = 40 if np.isfinite(ratio[i]) and ratio[i]<=.05 and gate[i]>=170 else 25
        curve = bank[window]['curve'][i]
        if np.isfinite(curve).all():
            candidates,dips,_ = anchor.candidates(bank[window]['lags'],curve,fs)
            f0[i],_,_ = anchor.choose(gate[i],candidates,dips,200)
    valid = (gate>=70)&(gate<=400)
    assert np.array_equal(valid,(f0>=70)&(f0<=400))
    evidence_path = HERE / f'results/H48_native_{Path(path).stem}.npz'
    assert not evidence_path.exists()
    np.savez_compressed(evidence_path,times=times,gate=gate,ratio=ratio,f0=f0,fs=fs)
    return fs,times,gate,f0,dict(native_call=call,evidence_path=str(evidence_path.relative_to(HERE)),
                             evidence_sha256=audit.digest(evidence_path),wav_sha256=audit.digest(path),
                             curves={str(w):audit.digest(HERE / f'results/H48_curves_w{w}_{Path(path).stem}.npz') for w in (25,40)})


def run():
    assert not (HERE / 'results/H48_test_experiment.json').exists()
    frozen = json.loads((HERE / 'H48_FIXED_CONFIG.json').read_text())
    assert frozen['config'] == CONFIG
    for path,digest in frozen['source_sha256'].items():
        assert audit.digest(core.REPO / path) == digest
    started = time.perf_counter()
    anchor.OUTPUT_PREFIX = 'H48'
    rows,frames,calls = [],[],{}
    paths = sorted((core.REPO / 'TinHieuKiemThu').glob('*.wav'))
    assert len(paths)==4
    for path in paths:
        fs,times,gate,f0,proof = estimate(path)
        # Scoring labels/statistics load only after waveform inference.
        item = core.frame_features(path,split='test')
        native = dict(times=times,fs=fs)
        for model,values in [('accepted',gate),('candidate',f0)]:
            pred = (values>=70)&(values<=400)
            pp,ff,support = project(native,item,pred,np.where(pred,values,np.nan),10)
            metrics = core.score_file(item,pp,ff)
            rows.append(dict(split='test',model=model,**metrics))
            for i,t in enumerate(item['times']):
                frames.append(dict(model=model,file=path.name,time_s=t,label=item['labels'][i],
                                   pred_voiced=bool(pp[i]),f0_hz=ff[i],support=bool(support[i])))
        proof['labels_sha256']=audit.digest(path.with_suffix('.lab'))
        proof['stats_sha256']=audit.digest(core.HERE/'test_3gt'/path.with_suffix('.lab').name)
        calls[path.name]=proof
        print(f'H48 fixed test scored {path.name}',flush=True)
    table=pd.DataFrame(rows)
    audit.csv_write('H48_test_metrics.csv',table)
    audit.csv_write('H48_test_contours.csv',frames)
    train=pd.read_csv(HERE/'results/H47_metrics.csv').query("model == 'candidate' and split == 'nested'")
    test=table.query("model == 'candidate'")
    all_files=pd.concat([train.assign(split='train'),test],ignore_index=True)
    audit.csv_write('H48_all_files.csv',all_files)
    value=dict(family='H48',config=frozen,config_sha256=audit.digest(HERE/'H48_FIXED_CONFIG.json'),
               train_source_sha256=audit.digest(HERE/'results/H47_metrics.csv'),native_calls=calls,
               new_native_calls=4,test_used_for_selection=False,test_history='Test seen in earlier notebook and QA history; fixed before this measurement, not a pristine held-out set.',
               goal_all_8_files_lt_2=bool((all_files.average_mape<2).all()),
               goal_all_test_files_lt_2=bool((test.average_mape<2).all()),
               train_only_source='H47 hard170 replay verified; reused train metrics, no train rerun',
               completed_utc=datetime.now(timezone.utc).isoformat(),wall_time_s=time.perf_counter()-started,
               environment=dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,praat=praat.metadata()['version_stdout']))
    audit.json_write(HERE/'results/H48_test_experiment.json',value)
    report=['# Cấu hình hard170 cố định — kiểm tra toàn bộ 8 file','',
            'Cấu hình chốt từ train trước phép đo test, chỉ một cấu hình; không chọn best trên test. Bốn train tái sử dụng kết quả H47 đã replay, bốn test tính mới từ WAV. Test đã được xem trong lịch sử nên không gọi đây là held-out độc lập hoàn toàn.','',
            audit.markdown_table(all_files[['split','file','F0mean_mape','F0std_mape','F0num_mape','average_mape','F0mean_abs_error','F0std_abs_error','F0num','macro_f1','recall_v','recall_uv','balanced_accuracy','false_voiced_sil']]),'',
            f"Mỗi file <2%: **{value['goal_all_8_files_lt_2']}**. Mỗi test <2%: **{value['goal_all_test_files_lt_2']}**.",'',
            '## Test so với Praat control','',audit.markdown_table(table),'',
            'Average MAPE là trung bình lỗi tương đối của thống kê mean/std/count cả file, không phải F0 từng khung. Không có per-frame pitch GT. Augmentation H47 không được chọn; hard170 đã biết từ H43. Không chỉnh GT, không sửa notebook đã nộp hoặc frozen_config gốc. Nếu test chưa đạt, giữ failure và không dò tham số trên chính test để gọi cải tiến độc lập.']
    (HERE/'ALL_FILES_STATUS.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(all_files[['split','file','average_mape','F0mean_mape','F0std_mape','F0num_mape']].to_string(index=False))
    print('All 8 files strict <2:',value['goal_all_8_files_lt_2'])


def register():
    path=HERE/'H48_FIXED_CONFIG.json'
    assert not path.exists()
    source_paths=[Path(__file__),Path(anchor.__file__),Path(spectral.__file__),Path(praat.__file__),HERE/'praat_extract_native.praat',Path(core.__file__),core.BASELINES/'AMDF.ipynb',HERE/'augmented_voicing_controller.py']
    audit.json_write(path,dict(registered_utc=datetime.now(timezone.utc).isoformat(),config=CONFIG,
                     rollback_repository_commit='77cae08e14fa6e29ff33c1d1f6ef40472b8816cb',
                     chosen_using='H47 train inner minimax; hard170 final and all outer selections',
                     source_sha256={str(p.relative_to(core.REPO)):audit.digest(p) for p in source_paths},
                     goal_strict_lt_2=True,test_parameter_grid=None))


if __name__=='__main__':
    assert sys.argv[1] in ('register','run')
    register() if sys.argv[1]=='register' else run()
