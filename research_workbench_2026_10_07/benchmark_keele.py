import hashlib
import io
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import fixed_hard170_test as fixed

HERE = Path(__file__).resolve().parent
DATA = HERE / 'benchmark_data'
core, audit = fixed.core, fixed.audit
ARCHIVE = DATA / 'KEELE.zip'


def acquire():
    import requests
    DATA.mkdir(exist_ok=True)
    if not ARCHIVE.exists():
        response = requests.get('https://zenodo.org/api/records/3921794/files/KEELE.zip/content', timeout=60)
        response.raise_for_status()
        ARCHIVE.write_bytes(response.content)
    assert hashlib.md5(ARCHIVE.read_bytes()).hexdigest() == 'f5a87014bad14744660b90187de7d43f'
    root = DATA / 'KEELE'
    assert not root.exists()
    rows = []
    with zipfile.ZipFile(ARCHIVE) as archive:
        ids = sorted({Path(n).parts[1] for n in archive.namelist() if n.endswith('/signal.wav')})
        assert len(ids) == 10
        metadata = json.loads(archive.read('KEELE/_metadata.json'))
        (HERE / 'sources').mkdir(exist_ok=True)
        (HERE / 'sources/H49_KEELE_README.txt').write_text(BeautifulSoup(metadata['README'],'html.parser').get_text('\n'),encoding='utf-8')
        for identity in ids:
            target = root / identity
            target.mkdir(parents=True)
            files = ['signal.wav','pitch.npy','pitch.json','_metadata.json','signal.json']
            hashes = {}
            for filename in files:
                data = archive.read(f'KEELE/{identity}/{filename}')
                (target / filename).write_bytes(data)
                hashes[filename] = hashlib.sha256(data).hexdigest()
            fs,audio = core.load_audio(target/'signal.wav')
            pitch = np.load(target/'pitch.npy',allow_pickle=False)
            assert fs == 20000 and pitch.dtype.names == ('time','pitch') and np.isfinite(pitch['time']).all()
            assert np.allclose(np.diff(pitch['time']),.01,atol=1e-12)
            rows.append(dict(id=identity,relative_dir=str(target.relative_to(HERE)),fs=fs,samples=len(audio),duration_s=len(audio)/fs,reference_rows=len(pitch),hashes=hashes))
    audit.json_write(HERE/'results/H49_dataset_manifest.json',dict(dataset='KEELE corpus reference via Bechtold Zenodo3921794',
                     url='https://zenodo.org/records/3921794',archive_sha256=audit.digest(ARCHIVE),archive_md5='f5a87014bad14744660b90187de7d43f',
                     acquired_utc=datetime.now(timezone.utc).isoformat(),cases=rows,license='noncommercial use according to curator',
                     extraction='Only WAV/JSON/NPY parsed; archive Python and pyc not loaded or executed.',
                     original_readme_sha256=audit.digest(HERE/'sources/H49_KEELE_README.txt'),
                     reference_warning='README discourages treating .pev as exact GT for different analysis windows; negative references unknown or lx without speech. Diagnostic benchmark only.'))
    print('PASS acquired 10 recordings, archive checksum and safe numeric reference parsing; no pitch estimation')


def estimate(path):
    fs,audio = core.load_audio(path)
    times,gate,call = fixed.praat.pitch(path,'filtered',.3)
    item = dict(file=path.parent.name+'.wav',fs=fs)
    bank,proofs = {},{}
    for window in (25,40):
        proof = fixed.anchor.curves(item,audio,times,gate,window)
        bank[window] = dict(np.load(HERE/proof['path']))
        proofs[str(window)] = dict(path=proof['path'],sha256=proof['sha256'])
    ratio = np.full(len(times),np.nan)
    f0 = gate.copy()
    for i in np.flatnonzero((gate>=70)&(gate<=400)):
        start = int(bank[40]['starts'][i]); length = int(bank[40]['frame_samples'])
        if 0<=start and start+length<=len(audio):
            ratio[i] = fixed.spectral.high_frequency_ratio(audio[start:start+length],fs)
        window = 40 if np.isfinite(ratio[i]) and ratio[i]<=.05 and gate[i]>=170 else 25
        curve = bank[window]['curve'][i]
        if np.isfinite(curve).all():
            candidates,dips,_ = fixed.anchor.candidates(bank[window]['lags'],curve,fs)
            f0[i],_,_ = fixed.anchor.choose(gate[i],candidates,dips,200)
    path_out = HERE / f'results/H49_native_{path.parent.name}.npz'
    assert not path_out.exists()
    np.savez_compressed(path_out,times=times,gate=gate,ratio=ratio,f0=f0,fs=fs)
    return times,gate,f0,dict(native_call=call,curves=proofs,path=str(path_out.relative_to(HERE)),sha256=audit.digest(path_out))


def align(times, values, ref_times, fs):
    right=np.minimum(np.searchsorted(times,ref_times),len(times)-1)
    left=np.maximum(right-1,0)
    index=np.where(abs(times[left]-ref_times)<=abs(times[right]-ref_times),left,right)
    support=abs(times[index]-ref_times)<=.005+1/fs
    pitch=values[index].copy()
    pitch[~support]=0.
    pitch[(pitch<70)|(pitch>400)]=0.
    return pitch,support


def score(reference,estimate,support):
    valid = support & np.isfinite(reference) & (reference>=0)
    r,e = reference[valid],estimate[valid]
    rv,ev = r>0,e>0
    both=rv&ev
    tp,tn,fp,fn = int(both.sum()),int((~rv&~ev).sum()),int((~rv&ev).sum()),int((rv&~ev).sum())
    rel = abs(e[both]-r[both])/r[both]
    cents = abs(1200*np.log2(e[both]/r[both]))
    gross = int((rel>.2).sum())
    correct50 = int((cents<=50).sum())
    pred,truth = e[ev],r[rv]
    mean,std,count = pred.mean(),pred.std(ddof=0),len(pred)
    gt_mean,gt_std,gt_count = truth.mean(),truth.std(ddof=0),len(truth)
    component = np.array([100*abs(a-b)/b if b>0 else np.nan for a,b in [(mean,gt_mean),(std,gt_std),(count,gt_count)]])
    return dict(scored_frames=len(r),support_coverage=float(support.mean()),unknown_reference_frames=int((reference<0).sum()),
                voiced_reference_frames=int(rv.sum()),reference_voiced_outside_70_400=int(((r>0)&((r<70)|(r>400))).sum()),
                both_voiced_frames=tp,TP=tp,TN=tn,FP=fp,FN=fn,gross_error_frames=gross,correct50_frames=correct50,
                gpe20_pct=100*gross/max(tp,1),vde_pct=100*(fp+fn)/max(len(r),1),ffe20_pct=100*(fp+fn+gross)/max(len(r),1),
                rpa50_pct=100*correct50/max(int(rv.sum()),1),voiced_recall=tp/max(tp+fn,1),unvoiced_recall=tn/max(tn+fp,1),
                macro_f1=(2*tp/max(2*tp+fp+fn,1)+2*tn/max(2*tn+fp+fn,1))/2,
                mae_hz_both_voiced=float(abs(e[both]-r[both]).mean()),median_abs_cents_both_voiced=float(np.median(cents)),
                F0mean=mean,F0std=std,F0num=count,reference_F0mean=gt_mean,reference_F0std=gt_std,reference_F0num=gt_count,
                F0mean_abs_error=abs(mean-gt_mean),F0std_abs_error=abs(std-gt_std),
                F0mean_mape=component[0],F0std_mape=component[1],F0num_mape=component[2],average_mape=component.mean())


def pooled(table):
    n,b,v = table.scored_frames.sum(),table.both_voiced_frames.sum(),table.voiced_reference_frames.sum()
    return dict(files=len(table),frames=int(n),gpe20_pct=100*table.gross_error_frames.sum()/b,
                vde_pct=100*(table.FP.sum()+table.FN.sum())/n,
                ffe20_pct=100*(table.FP.sum()+table.FN.sum()+table.gross_error_frames.sum())/n,
                rpa50_pct=100*table.correct50_frames.sum()/v,
                file_mean_average_mape=float(table.average_mape.mean()),worst_file_average_mape=float(table.average_mape.max()),
                files_average_mape_lt2=int((table.average_mape<2).sum()))


def check():
    r=np.array([100.,100.,100.,0.,0.])
    e=np.array([100.,150.,0.,100.,0.])
    s=score(r,e,np.ones(5,dtype=bool))
    assert s['gpe20_pct']==50 and s['vde_pct']==40 and s['ffe20_pct']==60 and np.isclose(s['rpa50_pct'],100/3)
    a,b=align(np.array([.01,.02]),np.array([100.,200.]),np.array([.0,.01,.015,.02,.03]),20000)
    assert np.array_equal(b,[False,True,True,True,False]) and a[2]==100
    s=score(np.array([-20000.,-100.,0.,100.]),np.array([200.,200.,0.,100.]),np.ones(4,dtype=bool))
    assert s['scored_frames']==2 and s['unknown_reference_frames']==2
    audit.json_write(HERE/'results/H49_precheck.json',dict(synthetic_only=True,no_benchmark_inference=True,
                     alignment_earlier_ties=True,unknown_negatives_excluded=True,metric_denominators_verified=True,source_sha256=audit.digest(__file__)))
    print('PASS synthetic alignment/negative-reference/GPE/VDE/FFE/RPA formulas')


def register():
    path=HERE/'H49_REGISTRY.json'
    assert not path.exists()
    audit.json_write(path,dict(registered_utc=datetime.now(timezone.utc).isoformat(),family='H49',config=fixed.CONFIG,
                     dataset_manifest_sha256=audit.digest(HERE/'results/H49_dataset_manifest.json'),
                     rollback_repository_commit='e78cdd64b5932b7e33d5a0044bdb7208d7dba565',
                     cases='all10 KEELE original corpus recordings; no KEELE_mod or consensus reference',
                     variants=['Praat filtered .30 control','BT2 hard170 fixed'],benchmark_training=False,benchmark_tuning=False,
                     scoring='Reference native 100Hz timestamps, nearest estimate <=5ms+sample, earlier ties, reference<0 excluded, all positive reference pitches retained including outside70-400',
                     primary_metrics=['gpe20_pct','vde_pct','ffe20_pct','rpa50_pct'],statistics_goal='every file average_mape <2%; diagnostic, not same GT protocol as BT2',
                     engineering_good_gate='pooled rpa50 >=90%, vde<=10%, ffe20<=10%; selected before measurement, not an official benchmark criterion',
                     source_sha256={str(p.relative_to(core.REPO)):audit.digest(p) for p in [Path(__file__),Path(fixed.__file__),Path(fixed.anchor.__file__),Path(fixed.spectral.__file__),Path(fixed.praat.__file__),HERE/'praat_extract_native.praat',Path(core.__file__),core.BASELINES/'AMDF.ipynb']}))


def run():
    assert not (HERE/'results/H49_experiment.json').exists()
    started=time.perf_counter()
    registry=json.loads((HERE/'H49_REGISTRY.json').read_text())
    assert registry['config']==fixed.CONFIG
    for path,value in registry['source_sha256'].items():
        assert audit.digest(core.REPO/path)==value
    manifest=json.loads((HERE/'results/H49_dataset_manifest.json').read_text())
    assert registry['dataset_manifest_sha256']==audit.digest(HERE/'results/H49_dataset_manifest.json')
    fixed.anchor.OUTPUT_PREFIX='H49'
    rows,frames,proofs=[],[],{}
    for case in manifest['cases']:
        directory=HERE/case['relative_dir']
        for filename,value in case['hashes'].items():
            assert audit.digest(directory/filename)==value
        times,gate,f0,proof=estimate(directory/'signal.wav')
        # Read reference only after estimating from the microphone waveform.
        reference=np.load(directory/'pitch.npy',allow_pickle=False)
        for model,frequency in [('control',gate),('candidate',f0)]:
            aligned,support=align(times,frequency,reference['time'],case['fs'])
            rows.append(dict(model=model,file=case['id'],**score(reference['pitch'],aligned,support)))
            for i,t in enumerate(reference['time']):
                frames.append(dict(model=model,file=case['id'],time_s=t,reference_f0_hz=reference['pitch'][i],
                                   predicted_f0_hz=aligned[i],support=bool(support[i])))
        proofs[case['id']]=proof
        print('H49 finished',case['id'],flush=True)
    table=pd.DataFrame(rows)
    audit.csv_write('H49_metrics.csv',table)
    audit.csv_write('H49_frames.csv',frames)
    summary={model:pooled(part) for model,part in table.groupby('model')}
    candidate=summary['candidate']
    good=bool(candidate['rpa50_pct']>=90 and candidate['vde_pct']<=10 and candidate['ffe20_pct']<=10)
    value=dict(family='H49',summaries=summary,predeclared_engineering_good_gate=good,registry_sha256=audit.digest(HERE/'H49_REGISTRY.json'),
               dataset_manifest_sha256=audit.digest(HERE/'results/H49_dataset_manifest.json'),source_calls=proofs,new_native_calls=10,
               completed_utc=datetime.now(timezone.utc).isoformat(),wall_time_s=time.perf_counter()-started,
               fit_files=[],tuned_on_benchmark=False,reference_limitations=manifest['reference_warning'],
               output_hashes={f'H49_{s}.csv':audit.digest(HERE/f'results/H49_{s}.csv') for s in ('metrics','frames')})
    audit.json_write(HERE/'results/H49_experiment.json',value)
    report=['# Benchmark KEELE — cấu hình BT2 cố định','',
            'Tất cả10 người nói (5nam/5nữ), cùng câu chuyện North Wind. Không fit hoặc tune trên KEELE. Pipeline là Praat7.0.02 filtered.30 + NAMDF hard170 đã chốt từ BT2, không phải notebook ACF đã nộp. Control dùng cùng callPraat, không tinh chỉnhNAMDF. Giữ fs20k/range70–400/hop10ms.','',
            '## Tổng hợp','',audit.markdown_table(pd.DataFrame([dict(model=k,**v) for k,v in summary.items()])),'',
            'GPE20: lỗi tương đối>20% trên khung cảreference vàprediction hữu thanh. VDE: sai quyết định hữu thanh trên mọi khung chấm. FFE20: VDE hoặcGPE, mẫu sốmọi khung chấm. RPA50: F0 trong50cents trên mọi khungreference hữu thanh, bỏ sót tínhsai. Không dùngGPE một mình vì nóbỏ qua khungbị bỏ sót.','',
            '## Từng file','',audit.markdown_table(table[['model','file','gpe20_pct','vde_pct','ffe20_pct','rpa50_pct','mae_hz_both_voiced','macro_f1','voiced_recall','unvoiced_recall','F0mean_mape','F0std_mape','F0num_mape','average_mape','reference_voiced_outside_70_400']]),'',
            f'Gate kỹ thuật đăng ký trước (RPA≥90%, VDE≤10%, FFE≤10%, pooled): **{good}**. Đây là tiêu chí chẩn đoán của phép thử, không tiêu chuẩn chính thức.','',
            '## Giới hạn kết luận','',
            'Nguồn KEELE cópitchtrack kiểmtra tay từlaryngograph, nhưng README cảnhbáo cửa sổthamchiếu25.6ms (mộtđoạnghi26.5ms) khácpipeline thì khôngcoilàGT khớp chínhxác. DelayLX/microphone chỉhiệuchỉnh mộtphần. Negativepitch đại diệnđoạn hỏng/khôngthể phản ánhspeech; loại khỏi scoring, khôngđổi chúng thànhUV. Các positiveF0 ngoài70–400 vẫnđược chấm để lộrange limitation. Không dịchreference để tối ưu kết quả. Chỉ nearesttime tolerance≤5ms+sample, báo coverage.','',
            'Benchmark tốt chỉcho thấypipeline hoạtđộng trêncorpus này; khôngchứngminh BT2 sai/ítdata lànguyênnhân duy nhất. Benchmarkxấu gợiý cầnxem thuậttoán, range, VUV, alignment vàreference protocol, khôngquy lỗi riêngdata. Thốngkêmean/std/count tựtính từreference đãcăn thời gian, khôngphảibaGT do thầy cungcấp vàkhông dùng đểtrain. Mộtcorpus,10speakers,cùngtext khôngđủ chochứngnhận generalization mọiđiềukiện.','',
            'Nguồn và protocol chi tiết: H49_REGISTRATION.md, BENCHMARK_SOURCES.md; dự liệu tải local, originalBT2/frozen giữ nguyên.']
    (HERE/'BENCHMARK_KEELE_REPORT.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    action=sys.argv[1]
    assert action in ('acquire','check','register','run')
    globals()[action]()
