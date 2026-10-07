import hashlib
import json
from pathlib import Path

import numpy as np

import rapt_adapter as api

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'results/rapt_synthetic_probe.json'
    assert not path.exists(), 'Preserve completed probe'
    rows=[]
    for fs in (16000,44100):
        t=np.arange(fs)/fs
        signals={'two_harmonics':.5*np.sin(2*np.pi*173*t)+.25*np.sin(2*np.pi*346*t),
                 'harmonic_rich':sum(.2/k*np.sin(2*np.pi*173*k*t+.1*k) for k in range(1,12)),
                 'zero':np.zeros(fs)}
        for name,audio in signals.items():
            for threshold in (-.3,0.,.3):
                row={'fs':fs,'signal':name,'voicing_bias':threshold,'reference_hz':None if name=='zero' else 173.}
                try:
                    times,frequency,call=api.pitch(audio,fs,threshold)
                    assert len(frequency)==100 and np.allclose(np.diff(times),.01,atol=1e-12)
                    assert call['native_called'] is True
                    center=(times>=.1)&(times<.9)
                    valid=center&(frequency>0)
                    row.update(status='success',native_call=call,native_f0_hz=frequency.tolist(),
                               voiced=int((frequency>0).sum()),center_voiced=int(valid.sum()),
                               center_median_hz=float(np.median(frequency[valid])) if valid.any() else None,
                               center_max_error_hz=float(abs(frequency[valid]-173).max()) if valid.any() and name!='zero' else None)
                except Exception as error:
                    row.update(status='failure',error_type=type(error).__name__,error=str(error))
                rows.append(row)
    proof={'adapter_sha256':api.digest(api.__file__),'probe_generator_sha256':api.digest(__file__),
           'source_provenance_sha256':api.digest(HERE/'results/rapt_source_provenance.json'),
           'rows':rows,'real_wav_read':False,'failures_retained':True,'native_noise_and_padding_retained':True}
    path.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    assert all(x['status']=='success' for x in rows), 'Native probe failure retained; do not start BT2'
    for row in rows:
        if row['signal']=='harmonic_rich' and row['voicing_bias']==0:
            assert row['center_voiced']>=64 and row['center_max_error_hz']<3
    print(json.dumps([{k:v for k,v in x.items() if k not in ('native_call','native_f0_hz')} for x in rows],indent=2),flush=True)
    print('PASS RAPT transport18calls and rich-tone/default center checks; zeros/other thresholds retained, no BT2 read.')


if __name__=='__main__':
    main()
