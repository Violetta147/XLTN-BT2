import json
import traceback
from pathlib import Path

import numpy as np

import yaapt_adapter as api

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'results/yaapt_raw_synthetic_probe.json'
    assert not path.exists(), 'Preserve completed probe'
    rows=[]
    for fs in (16000,44100):
        t=np.arange(fs)/fs
        for name,audio in [('rich173',sum(.2/k*np.sin(2*np.pi*173*k*t+.1*k) for k in range(1,12))),('zero',np.zeros(fs))]:
            for frame_ms in (25,35,45):
                row={'fs':fs,'signal':name,'frame_ms':frame_ms,'reference_hz':173 if name=='rich173' else None}
                try:
                    times,frequency,call=api.pitch(audio,fs,frame_ms)
                    valid=(times>.15)&(times<.85)&(frequency>0)
                    row.update(status='success',native_call=call,native_f0_hz=frequency.tolist(),voiced=int((frequency>0).sum()),
                               center_voiced=int(valid.sum()),center_max_error_hz=float(abs(frequency[valid]-173).max()) if valid.any() and name=='rich173' else None)
                except Exception as error:
                    row.update(status='failure',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
                rows.append(row)
    value={'rows':rows,'real_wav_read':False,'source_discovery_sha256':api.digest(HERE/'results/yaapt_source_discovery.json'),
           'adapter_sha256':api.digest(api.__file__),'generator_sha256':api.digest(__file__),'failures_retained':True}
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{k:v for k,v in x.items() if k not in ('native_call','native_f0_hz','traceback')} for x in rows],indent=2),flush=True)
    assert all(x['status']=='success' for x in rows), 'Raw probe failure retained; no BT2 benchmark'
    for row in rows:
        if row['signal']=='rich173':
            assert row['center_voiced']>=56 and row['center_max_error_hz']<3
        else:
            assert row['voiced']==0
    print('PASS 12 raw YAAPT rich tone/zero/fs/frame checks; no BT2 read')


if __name__=='__main__':
    main()
