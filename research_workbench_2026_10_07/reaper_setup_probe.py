import json
import subprocess
from datetime import datetime,timezone
from pathlib import Path

import numpy as np

import sptk_adapter as native

HERE=Path(__file__).resolve().parent
path=HERE/'results/reaper_synthetic_probe.json'
assert not path.exists(),'Preserve completed raw probe'
proof=native.metadata()
root=Path(proof['source_root'])
paths=subprocess.check_output(['git','-C',str(root),'ls-files','third_party/REAPER'],text=True).splitlines()
paths+=['src/analysis/pitch_extraction_by_reaper.cc','src/main/pitch.cc']
rows=[]
for fs in (16000,44100):
    t=np.arange(fs)/fs
    tone=np.sin(2*np.pi*173*t)+.4*np.sin(2*np.pi*346*t)
    glottal=sum(np.sin(2*np.pi*173*h*t)/h for h in range(1,13))
    for name,signal in [('two_harmonics',tone),('harmonic_rich',glottal),('silence',np.zeros(fs))]:
        audio=signal/max(np.max(abs(signal)),1e-12)*.75
        for threshold in (.3,1.2):
            record={'fs':fs,'signal':name,'threshold':threshold}
            try:
                times,f0,call=native.pitch(audio,fs,'reaper',threshold)
                valid=f0[f0>0]
                center=f0[(times>=.1)&(times<=.9)]
                center_valid=center[center>0]
                record.update(status='success',call=call,frames=len(f0),voiced_frames=len(valid),
                    center_voiced_frames=len(center_valid),center_frames=len(center),
                    center_median_error_hz=float(np.median(abs(center_valid-173))) if len(center_valid) else None,
                    center_max_error_hz=float(np.max(abs(center_valid-173))) if len(center_valid) else None,
                    all_max_error_hz=float(np.max(abs(valid-173))) if len(valid) else None)
            except Exception as error:
                record.update(status='failure',error_type=type(error).__name__,error=str(error))
            rows.append(record)
            print(f"REAPER synthetic {fs} {name} cost{threshold}: {record['status']}",flush=True)
            path.write_text(json.dumps({'rows':rows,'probe_complete':False,'real_wav_read':False},indent=2)+'\n')
result={'rows':rows,'probe_complete':True,'real_wav_read':False,'created_utc':datetime.now(timezone.utc).isoformat(),
        'source_url':proof['source_url'],'commit':proof['commit'],'exe_sha256':proof['exe_sha256'],
        'source_root':str(root),'source_sha256':{p:native.digest(root/p) for p in paths},
        'adapter_sha256':native.digest(HERE/'sptk_adapter.py'),'generator_sha256':native.digest(__file__),
        'raw_success_count':sum(r['status']=='success' for r in rows),
        'raw_failures_preserved':True,'synthetic_only_not_BT2_accuracy':True}
path.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k!='call'} for r in rows],indent=2))
