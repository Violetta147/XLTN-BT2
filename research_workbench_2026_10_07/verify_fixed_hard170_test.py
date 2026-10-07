import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import fixed_hard170_test as run
from verify_amdf_spectral import independent_pick

HERE = Path(__file__).resolve().parent


def main():
    result=json.loads((HERE/'results/H48_test_experiment.json').read_text())
    assert run.audit.digest(HERE/'H48_FIXED_CONFIG.json') == result['config_sha256']
    frozen=result['config']
    assert frozen['config']==run.CONFIG and frozen['test_parameter_grid'] is None
    for path,value in frozen['source_sha256'].items():
        assert run.audit.digest(run.core.REPO/path)==value
    assert not result['test_used_for_selection'] and result['new_native_calls']==4
    metrics=pd.read_csv(HERE/'results/H48_test_metrics.csv')
    contours=pd.read_csv(HERE/'results/H48_test_contours.csv')
    curve_rows,metric_rows=0,0
    for name,proof in result['native_calls'].items():
        path=run.core.REPO/'TinHieuKiemThu'/name
        assert run.audit.digest(path)==proof['wav_sha256']
        assert run.audit.digest(path.with_suffix('.lab'))==proof['labels_sha256']
        assert run.audit.digest(run.core.HERE/'test_3gt'/path.with_suffix('.lab').name)==proof['stats_sha256']
        assert run.audit.digest(HERE/proof['evidence_path'])==proof['evidence_sha256']
        call=proof['native_call']
        assert call['returncode']==0 and call['script_sha256']==run.audit.digest(HERE/'praat_extract_native.praat')
        assert call['exe_sha256']==run.praat.metadata()['exe_sha256']
        assert call['command']==[run.praat.metadata()['exe'],'--run',str(HERE/'praat_extract_native.praat'),str(path),'filtered','0.3']
        native=dict(np.load(HERE/proof['evidence_path']))
        fs,audio=run.core.load_audio(path)
        assert int(native['fs'])==fs
        bank={}
        for window in (25,40):
            curve_path=HERE/f'results/H48_curves_w{window}_{Path(name).stem}.npz'
            assert run.audit.digest(curve_path)==proof['curves'][str(window)]
            data=dict(np.load(curve_path))
            assert np.array_equal(data['times'],native['times']) and np.array_equal(data['gate_frequency'],native['gate'])
            assert str(data['audio_sha256'])==hashlib.sha256(np.ascontiguousarray(audio,dtype=np.float64).tobytes()).hexdigest()
            for i in range(len(data['times'])):
                start=int(data['starts'][i]); length=int(data['frame_samples'])
                valid=70<=native['gate'][i]<=400 and 0<=start and start+length<=len(audio)
                if not valid:
                    assert np.isnan(data['curve'][i]).all()
                    continue
                frame=audio[start:start+length]; centered=frame-frame.mean()
                fresh=np.ones(len(data['lags'])) if abs(centered).mean()<1e-8 else np.array([
                    abs(centered[:-lag]-centered[lag:]).mean()/(abs(centered[:-lag]).mean()+abs(centered[lag:]).mean()+1e-12) for lag in data['lags']])
                np.testing.assert_allclose(fresh,data['curve'][i],atol=1e-12,rtol=1e-12)
                curve_rows+=1
            bank[window]=data
        f0=native['gate'].copy()
        for i in np.flatnonzero((native['gate']>=70)&(native['gate']<=400)):
            start=int(bank[40]['starts'][i]); length=int(bank[40]['frame_samples'])
            ratio=np.nan
            if 0<=start and start+length<=len(audio):
                frame=audio[start:start+length]; centered=frame-frame.mean()
                if abs(centered).mean()>=1e-8:
                    power=abs(np.fft.fft(centered*np.hanning(length)))**2
                    hz=abs(np.fft.fftfreq(length,1/fs))
                    ratio=power[hz>=1000].sum()/power[hz>0].sum()
            np.testing.assert_allclose(native['ratio'][i],ratio,atol=1e-12,equal_nan=True)
            window=40 if np.isfinite(ratio) and ratio<=.05 and native['gate'][i]>=170 else 25
            f0[i]=independent_pick(bank[window]['curve'][i],bank[window]['lags'],fs,native['gate'][i])[0]
        np.testing.assert_allclose(f0,native['f0'],atol=1e-12)
        item=run.core.frame_features(path,split='test')
        for model,frequency in [('accepted',native['gate']),('candidate',f0)]:
            nt=native['times']; index=np.array([np.argmin(abs(nt-t)) for t in item['times']])
            support=abs(nt[index]-item['times'])<=.005+1/fs
            pred=support&(frequency[index]>=70)&(frequency[index]<=400)
            projected=np.where(pred,frequency[index],np.nan)
            fresh=run.core.score_file(item,pred,projected)
            saved=metrics[(metrics.file==name)&(metrics.model==model)].iloc[0]
            for key,value in fresh.items():
                if key!='file':
                    np.testing.assert_allclose(saved[key],value,atol=1e-8,rtol=1e-9)
            group=contours[(contours.file==name)&(contours.model==model)]
            assert np.array_equal(group.pred_voiced,pred) and np.array_equal(group.label,item['labels'])
            np.testing.assert_allclose(group.f0_hz,projected,atol=1e-12,equal_nan=True)
            metric_rows+=1
    all_files=pd.read_csv(HERE/'results/H48_all_files.csv')
    assert len(all_files)==8 and all_files.file.nunique()==8
    assert run.audit.digest(HERE/'results/H47_metrics.csv')==result['train_source_sha256']
    train=pd.read_csv(HERE/'results/H47_metrics.csv').query("split == 'nested' and model == 'candidate'")
    for name in train.file:
        expected=train[train.file==name].iloc[0]
        actual=all_files[all_files.file==name].iloc[0]
        for key in ('F0mean','F0std','F0num','average_mape'):
            np.testing.assert_allclose(actual[key],expected[key],atol=1e-12)
    assert result['goal_all_8_files_lt_2']==bool((all_files.average_mape<2).all())
    assert result['goal_all_test_files_lt_2']==bool((all_files.query("split == 'test'").average_mape<2).all())
    receipt=dict(independent_curve_rows=curve_rows,independent_test_metric_rows=metric_rows,source_config_wav_lab_hashes=True,
                 full_fft_and_candidate_pick_verified=True,new_native_calls_in_verifier=0,
                 all_8_files_lt_2=result['goal_all_8_files_lt_2'],experiment_sha256=run.audit.digest(HERE/'results/H48_test_experiment.json'),
                 verifier_sha256=run.audit.digest(__file__))
    run.audit.json_write(HERE/'results/H48_test_verification.json',receipt)
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
