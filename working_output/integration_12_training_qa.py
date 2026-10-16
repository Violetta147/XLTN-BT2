from pathlib import Path
import argparse, hashlib, json, os, platform, sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import pandas as pd
import sklearn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / 'BT2_AMDF_implement_executed_original - Copy.ipynb'
parser = argparse.ArgumentParser()
parser.add_argument('--tag', choices=['before','after'], required=True)
args = parser.parse_args()
nb = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
ns = {'__name__':'__main__', 'display':lambda *a,**k: None}
for index in (1,3,5,7,9,10,14,19):
    source = ''.join(nb['cells'][index]['source'])
    exec(compile(source, f'{NOTEBOOK.name}:cell{index}', 'exec'), ns)
    if index == 1:
        # Restrict QA to the final required frame; do not enumerate TEST pairs.
        assert ns['TRAIN_DIR'].resolve() == (ROOT/'TinHieuHuanLuyen').resolve()
        ns['FRAME_MS_CANDIDATES'] = (25,)
        ns['TEST_DIR'] = ROOT / '_disabled_test_for_training_qa'
assert len(ns['train_pairs']) == 4
assert ns['FINAL_FRAME_MS'] == 25 and ns['HOP_MS'] == 10
assert ns['FINAL_THRESHOLD_METHOD'] == 'Gaussian'
assert np.isclose(ns['FINAL_THRESHOLD'], 0.41249330632749887, atol=1e-9)
assert np.isclose(ns['FINAL_ENERGY_THRESHOLD'], 0.061544615883604575, atol=1e-9)
rows=[]
for wav_path, lab_path in ns['train_pairs']:
    result=ns['process_file_amdf'](wav_path,lab_path)
    labels=np.asarray([ns['label_at_time'](t,result['segments']) for t in result['center_times']],dtype=object)
    pred=result['predicted_voiced']
    mask=np.isin(labels,('v','uv'))
    truth=labels[mask]=='v'; p=pred[mask]
    tp=int((truth&p).sum()); tn=int((~truth&~p).sum()); fp=int((~truth&p).sum()); fn=int((truth&~p).sum())
    f1v=2*tp/(2*tp+fp+fn) if (2*tp+fp+fn) else 0
    f1uv=2*tn/(2*tn+fp+fn) if (2*tn+fp+fn) else 0
    raw_contour=result.get('f0_raw_contour',result['f0_contour'])
    valid_raw=np.asarray(raw_contour)[np.isfinite(raw_contour)]
    valid_used=np.asarray(result['f0_contour'])[np.isfinite(result['f0_contour'])]
    gt_mean,gt_std=result['gt_f0_mean'],result['gt_f0_std']
    rows.append({'file':wav_path.name,'frames':len(labels),'TP':tp,'TN':tn,'FP':fp,'FN':fn,
      'macro_f1':(f1v+f1uv)/2,'recall_V':tp/(tp+fn),'recall_UV':tn/(tn+fp),
      'balanced_accuracy':(tp/(tp+fn)+tn/(tn+fp))/2,
      'NumF0':len(valid_used),'FP_SIL':int(((labels=='sil')&pred).sum()),
      'raw_F0mean_MAE_hz':abs(float(valid_raw.mean())-gt_mean),
      'used_F0mean_MAE_hz':abs(float(valid_used.mean())-gt_mean),
      'raw_F0std_MAE_hz':abs(float(valid_raw.std())-gt_std),
      'used_F0std_MAE_hz':abs(float(valid_used.std())-gt_std),
      'prediction_sha256':hashlib.sha256(pred.astype(np.uint8).tobytes()).hexdigest()})
frame=pd.DataFrame(rows)
frame.to_csv(ROOT/f'working_output/integration_12_training_{args.tag}.csv',index=False,float_format='%.10g')
summary={'tag':args.tag,'data':'TinHieuHuanLuyen only','files':len(rows),
 'frame_ms':ns['FINAL_FRAME_MS'],'hop_ms':ns['HOP_MS'],
 'T_pitch':float(ns['FINAL_THRESHOLD']),'T_energy':float(ns['FINAL_ENERGY_THRESHOLD']),
 'macro_f1_mean':float(frame.macro_f1.mean()),'BA_mean':float(frame.balanced_accuracy.mean()),
 'recall_V_mean':float(frame.recall_V.mean()),'recall_UV_mean':float(frame.recall_UV.mean()),
 'F0mean_MAE_raw':float(frame.raw_F0mean_MAE_hz.mean()),'F0mean_MAE_used':float(frame.used_F0mean_MAE_hz.mean()),
 'F0std_MAE_raw':float(frame.raw_F0std_MAE_hz.mean()),'F0std_MAE_used':float(frame.used_F0std_MAE_hz.mean()),
 'NumF0_total':int(frame.NumF0.sum()),'FP_SIL_total':int(frame.FP_SIL.sum()),
 'prediction_hashes':dict(zip(frame.file,frame.prediction_sha256)),
 'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scikit_learn':sklearn.__version__}
(ROOT/f'working_output/integration_12_training_{args.tag}.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
plt.close('all')
print(frame.to_string(index=False))
print(json.dumps(summary,indent=2))

