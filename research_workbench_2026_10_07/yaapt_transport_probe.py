import json
from pathlib import Path

import numpy as np
import yaapt_adapter as api

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'results/yaapt_transport_probe.json'
    assert not path.exists(), 'Preserve probe'
    rows=[]
    for fs in (16000,44100):
        t=np.arange(fs)/fs
        for name,audio in [('sine173',.2*np.sin(2*np.pi*173*t)),
                           ('two173',.2*np.sin(2*np.pi*173*t)+.1*np.sin(2*np.pi*346*t+.2))]:
            times,frequency,call=api.pitch(audio,fs,35)
            center=(times>.15)&(times<.85)&(frequency>0)
            rows.append({'fs':fs,'signal':name,'reference_hz':173,'call':call,'frequency_hz':frequency.tolist(),
                         'center_voiced':int(center.sum()),'center_max_error_hz':float(abs(frequency[center]-173).max())})
    value={'rows':rows,'real_wav_read':False,'adapter_sha256':api.digest(api.__file__),
           'generator_sha256':api.digest(__file__),'rich_octave_failure_retained':'yaapt_synthetic_probe_v2.json'}
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{k:v for k,v in row.items() if k not in ('call','frequency_hz')} for row in rows],indent=2),flush=True)
    assert all(row['center_voiced']>=56 and row['center_max_error_hz']<3 for row in rows)


if __name__=='__main__':
    main()
