import json
from pathlib import Path

import numpy as np
import pandas as pd
import amdf_dual_window as experiment

HERE = Path(__file__).resolve().parent
core = experiment.core
items = core.load_training()
config = json.loads((core.RESULTS/'frozen_config.json').read_text())['models']['AMDF_energy']['config']
rows = []
for item in items:
    fit = core.fit([x for x in items if x['file'] != item['file']], config)
    pitch = item['AMDF_score'] < fit['pitch_threshold']
    energy = item['relative_rms'] >= fit['energy_threshold']
    voiced = item['labels'] == 'v'
    pred, f0 = core.infer(item, config, fit)
    assert np.array_equal(pred, pitch & energy)
    row = {'file':item['file'], **fit, 'V':int(voiced.sum()),
           'V_rejected_pitch_only':int((voiced & ~pitch & energy).sum()),
           'V_rejected_energy_only':int((voiced & pitch & ~energy).sum()),
           'V_rejected_both':int((voiced & ~pitch & ~energy).sum()),
           'V_pass':int((voiced & pitch & energy).sum()),
           'canonical_V_minus_GTcount':int(voiced.sum()-item['stats']['F0num'])}
    assert row['V'] == sum(row[k] for k in ('V_pass','V_rejected_pitch_only','V_rejected_energy_only','V_rejected_both'))
    rows.append(row)
table = pd.DataFrame(rows)
reference = pd.read_csv(HERE/'results/H24_fixed_lofo.csv').query("option_id == 'amdf_f25_h10'").set_index('file')
assert all(reference.loc[row['file'],'TP'] == row['V_pass'] for row in rows)
table.to_csv(HERE/'results/H24_voicing_bottleneck.csv',index=False)
(HERE/'results/H24_voicing_bottleneck_verification.json').write_text(json.dumps({
    'source_sha256':experiment.audit.digest(__file__), 'train_only':True,
    'voicing_partition_and_saved_TP_verified':True,
    'baseline_config_sha256':experiment.audit.digest(core.RESULTS/'frozen_config.json'),
    'data_sha256':{item['file']:experiment.audit.digest(core.TRAIN/item['file']) for item in items},
    'interpretation':'Algorithm gate attribution only; not a cause of teacher F0num versus segment label mismatch.'},indent=2)+'\n')
print(table.to_string(index=False))
