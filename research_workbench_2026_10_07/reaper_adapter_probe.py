import json
from pathlib import Path

import numpy as np

import reaper_adapter as adapter
import sptk_adapter as native

HERE=Path(__file__).resolve().parent
path=HERE/'results/reaper_adapter_probe.json'
assert not path.exists(),'Preserve completed adapter probes'
rows=[]
for fs in (16000,44100):
    t=np.arange(fs)/fs
    signal=sum(np.sin(2*np.pi*173*h*t)/h for h in range(1,13))
    signal=signal/np.max(abs(signal))*.75
    for name,audio in [('harmonic_rich',signal),('silence',np.zeros(fs))]:
        for cost in (.9,1.5):
            times,f0,call=adapter.pitch(audio,fs,cost)
            center=f0[(times>=.1)&(times<=.9)]
            valid=center[center>0]
            record={'fs':fs,'signal':name,'cost':cost,'voiced_frames':int((f0>0).sum()),
                    'center_frames':len(center),'center_voiced_frames':len(valid),
                    'median_error_hz':float(np.median(abs(valid-173))) if len(valid) else None,
                    'max_error_hz':float(np.max(abs(valid-173))) if len(valid) else None,'call':call}
            rows.append(record)
            path.write_text(json.dumps({'rows':rows,'probe_complete':False,'real_wav_read':False},indent=2)+'\n')
            if name=='silence':
                assert not len(valid) and not call['native_called'] and call['status']=='exact_whole_input_zero'
            elif cost==1.5:
                assert len(valid)>=.8*len(center) and np.max(abs(valid-173))<3
            print(f'REAPER adapter {fs} {name} cost{cost}: V={record["voiced_frames"]}',flush=True)
proof={'rows':rows,'probe_complete':True,'real_wav_read':False,'adapter_sha256':native.digest(HERE/'reaper_adapter.py'),
       'generator_sha256':native.digest(__file__),'sptk_adapter_sha256':native.digest(HERE/'sptk_adapter.py'),
       'raw_probe_sha256':native.digest(HERE/'results/reaper_synthetic_probe.json'),
       'native_provenance_sha256':native.digest(HERE/'results/sptk_native_provenance.json'),
       'failure_conversion':False,'raw_failure_and_octave_case_retained':True}
path.write_text(json.dumps(proof,indent=2)+'\n')
print('PASS REAPER adapter eight checks; raw failures preserved, no BT2 WAV read.')
