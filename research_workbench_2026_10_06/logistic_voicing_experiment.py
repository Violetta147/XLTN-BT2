import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

import audit
import core
from estimator_experiment import eligibility

HERE = Path(__file__).resolve().parent


def features(item):
    return np.column_stack([item['ACF_score'], item['relative_rms']])


def fit_classifier(items):
    all_x, all_y, all_w = [], [], []
    total = sum(np.isin(x['labels'], ['v', 'uv']).sum() for x in items)
    for item in items:
        mask = np.isin(item['labels'], ['v', 'uv'])
        target = (item['labels'][mask] == 'v').astype(int)
        weights = np.array([total / (2 * len(items) * max((target == value).sum(), 1)) for value in target])
        all_x.append(features(item)[mask])
        all_y.append(target)
        all_w.append(weights)
    x, y, weights = np.vstack(all_x), np.concatenate(all_y), np.concatenate(all_w)
    scaler = StandardScaler().fit(x, sample_weight=weights)
    classifier = LogisticRegression(C=1., max_iter=500).fit(scaler.transform(x), y, sample_weight=weights)
    assert classifier.n_iter_[0] < 500 and np.isfinite(classifier.coef_).all()
    assert np.allclose(expit(scaler.transform(x) @ classifier.coef_[0] + classifier.intercept_[0]), classifier.predict_proba(scaler.transform(x))[:, 1], atol=1e-12)
    metadata = {'fit_files': [item['file'] for item in items], 'features': ['ACF_score', 'relative_rms'],
                'C': 1., 'score_threshold': .5, 'scaler_mean': scaler.mean_.tolist(), 'scaler_scale': scaler.scale_.tolist(),
                'coefficient': classifier.coef_[0].tolist(), 'intercept': float(classifier.intercept_[0]),
                'iterations': int(classifier.n_iter_[0]), 'sample_weights': 'equal total per-file/per-V-UV-class'}
    return metadata


def infer(item, config, fitted, classifier):
    x = (features(item) - np.array(classifier['scaler_mean'])) / np.array(classifier['scaler_scale'])
    score = expit(x @ np.array(classifier['coefficient']) + classifier['intercept'])
    mask = (score >= .5) & (item['relative_rms'] >= fitted['energy_threshold'])
    adapted = dict(item, ACF_score=np.where(mask, 1., -1.))
    pred, f0 = core.infer(adapted, config, dict(fitted, pitch_threshold=.5))
    assert np.array_equal(pred, mask)
    return pred, f0, score


def main():
    items = core.load_training()
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['ACF']['config']
    rows, predictions, fits = [], [], []
    for split in ('train', 'lofo'):
        for item in items:
            training = items if split == 'train' else [x for x in items if x is not item]
            fitted = core.fit(training, config)
            classifier = fit_classifier(training)
            assert split == 'train' or item['file'] not in classifier['fit_files']
            fits.append({'split': split, 'held_file': item['file'], **classifier, 'energy_threshold': fitted['energy_threshold']})
            baseline_pred, baseline_f0 = core.infer(item, config, fitted)
            pred, f0, score = infer(item, config, fitted, classifier)
            for model, mask, pitch in [('accepted', baseline_pred, baseline_f0), ('candidate', pred, f0)]:
                rows.append({'split': split, 'model': model, **core.score_file(item, mask, pitch)})
            for i in range(len(pred)):
                predictions.append({'split': split, 'file': item['file'], 'time_s': item['times'][i], 'label': item['labels'][i],
                                    'boundary': bool(item['boundary'][i]), 'acf_score': item['ACF_score'][i],
                                    'relative_rms': item['relative_rms'][i], 'logistic_score': score[i],
                                    'accepted_pred': bool(baseline_pred[i]), 'candidate_pred': bool(pred[i]),
                                    'accepted_f0_hz': baseline_f0[i], 'candidate_f0_hz': f0[i]})
    frame = pd.DataFrame(rows)
    p_metrics = audit.csv_write('logistic_voicing_metrics.csv', frame)
    p_predictions = audit.csv_write('logistic_voicing_predictions.csv', predictions)
    audit.json_write(HERE / 'results/logistic_voicing_fits.json', {'folds': fits})
    summaries = {model: {split: core.summarize(frame[(frame.model == model) & (frame.split == split)]) for split in ('train', 'lofo')} for model in ('accepted', 'candidate')}
    decision = eligibility(frame, summaries)
    classifier = fit_classifier(items)
    poison = dict(items[0], stats={'F0mean': -1,'F0std': -1,'F0num': -1}, labels=np.full(len(items[0]['labels']), 'unknown'))
    expected, actual = infer(items[0], config, core.fit(items,config),classifier), infer(poison,config,core.fit(items,config),classifier)
    assert np.array_equal(expected[0],actual[0]) and np.allclose(expected[1],actual[1],equal_nan=True) and np.allclose(expected[2],actual[2])
    audit.json_write(HERE / 'results/logistic_voicing_experiment.json', {'decision': decision, 'summaries': summaries,
                     'manual_sigmoid_verified': True, 'fit_held_files_excluded': True, 'poisoned_gt_inference_invariant': True,
                     'train_only': True, 'code_sha256': audit.digest(__file__)})
    data = pd.DataFrame(predictions)
    fig, axes = audit.plt.subplots(1, 2, figsize=(11,4))
    for ax, split in zip(axes,('train','lofo')):
        for label in ('v','uv','sil'):
            group = data[(data.split==split)&(data.label==label)]
            ax.scatter(group.acf_score,group.relative_rms,s=13,alpha=.45,label=label,color=audit.PALETTE[label])
        ax.set(xlabel='ACF score',ylabel='Relative RMS',title=split+' — existing features only',ylim=(0,1.5))
    mean,scale = np.array(classifier['scaler_mean']),np.array(classifier['scaler_scale'])
    coefficient = np.array(classifier['coefficient'])
    x = np.linspace(0,1,200)
    if abs(coefficient[1])>1e-10:
        y = mean[1]+scale[1]*(-classifier['intercept']-coefficient[0]*(x-mean[0])/scale[0])/coefficient[1]
        axes[0].plot(x,y,'k--',label='train logistic boundary (score=.5)')
    axes[0].legend(fontsize=7)
    audit.save_figure('logistic_voicing_boundary',fig,[p_predictions],'Đường biên logistic dùng hai đặc trưng đã có, fit trongfold.', 'Không thêmfeature hoặc chọnC/threshold bằngtest; score chưacalibrated vàscatterframechồngnhau.')
    fig, axes = audit.plt.subplots(1,3,figsize=(12,4))
    for ax, metric in zip(axes,('average_mape','macro_f1','recall_v')):
        for model in ('accepted','candidate'):
            group = frame[(frame.split=='lofo')&(frame.model==model)].set_index('file')
            ax.plot(group.index.str.replace('.wav','',regex=False),group[metric],'o-',label=model)
        ax.set(title=metric)
        ax.tick_params(axis='x',rotation=30)
    axes[0].legend(fontsize=8)
    audit.save_figure('logistic_voicing_lofo',fig,[p_metrics],'Held-file classification và file-statMAPE cùngđượcbáo.', 'Metric3GTkhôngxácminhpitchmỗiUV/Vframe; chỉ4file nênthăm dò.')
    for figure in audit.ARTIFACTS:
        figure.update(generator='logistic_voicing_experiment.py',generator_sha256=audit.digest(__file__),command='python research_workbench_2026_10_06/logistic_voicing_experiment.py')
    audit.json_write(HERE / 'results/logistic_voicing_figure_manifest.json',{'figures':audit.ARTIFACTS})
    table = pd.DataFrame([{'model':model,'split':split,**value} for model,parts in summaries.items() for split,value in parts.items()])
    report = ['# H16 — logistic voicing trên ACFscore/RMS', '',audit.markdown_table(table),'',
              '~~~json',json.dumps(decision,indent=2),'~~~','',
              'Standardization và class weights fit trainonly từngfold; heldfilekhông trongfit. C1/.5fixed. GiữRMS/path/median3 vàchampion; khôngtune từtest. Đây làclassifierthay vìchỉđổiF0distribution. Chưa cóframepitchtruth vàn=4.', '',
              '![Boundary](figures/logistic_voicing_boundary.png)','', '![LOFO](figures/logistic_voicing_lofo.png)','',
              '~~~powershell','python research_workbench_2026_10_06/logistic_voicing_experiment.py','~~~']
    (HERE / 'LOGISTIC_VOICING_REPORT.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(json.dumps(decision,indent=2),flush=True)
    print(table[['split','model','average_mape','macro_f1','recall_v','false_voiced_sil']].to_string(index=False),flush=True)


if __name__=='__main__':
    main()
