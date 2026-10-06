import json
from pathlib import Path

import numpy as np
import pandas as pd

import audit
import core
import hysteresis_experiment as hysteresis
import logistic_voicing_experiment as logistic
from estimator_experiment import eligibility

HERE = Path(__file__).resolve().parent
OPTIONS = [{'id':'accepted_ACF','kind':'acf','margin':0.}] + [{'id':f'hysteresis_{margin:.2f}','kind':'hysteresis','margin':margin} for margin in (.02,.04,.06,.08,.12)] + [{'id':'logistic_2D_C1','kind':'logistic','margin':0.}]
CLASSIFIER_CACHE = {}


def fit_classifier(training):
    key = tuple(x['file'] for x in training)
    if key not in CLASSIFIER_CACHE:
        CLASSIFIER_CACHE[key] = logistic.fit_classifier(training)
    return CLASSIFIER_CACHE[key]


def predict(item,training,config,option):
    fitted = core.fit(training,config)
    if option['kind']=='acf':
        return core.infer(item,config,fitted)
    if option['kind']=='hysteresis':
        return hysteresis.infer(item,config,fitted,option['margin'])
    pred,f0,_ = logistic.infer(item,config,fitted,fit_classifier(training))
    return pred,f0


def select(training,config,context):
    tables = {}
    traces = []
    for option in OPTIONS:
        rows = []
        for held in training:
            other = [x for x in training if x is not held]
            result = core.score_file(held,*predict(held,other,config,option))
            rows.append(result)
            traces.append({'context':context,'option_id':option['id'],'held_file':held['file'],
                           'fit_files':'|'.join(x['file'] for x in other),**result})
        tables[option['id']] = pd.DataFrame(rows)
    baseline = tables['accepted_ACF']
    summaries = [{'context':context,'option_id':option['id'],'selection_files':'|'.join(x['file'] for x in training),
                  'guard_pass':hysteresis.acceptable(tables[option['id']],baseline),
                  **core.summarize(tables[option['id']])} for option in OPTIONS]
    eligible = [row for row in summaries if row['guard_pass']]
    chosen = min(eligible,key=lambda x:x['average_mape'])['option_id'] if eligible else 'accepted_ACF'
    return next(x for x in OPTIONS if x['id']==chosen),traces,summaries


def main():
    items = core.load_training()
    config = json.loads((core.RESULTS / 'frozen_config.json').read_text(encoding='utf-8'))['models']['ACF']['config']
    chosen,traces,summaries = select(items,config,'final')
    rows,choices = [],[]
    for split in ('train','lofo','nested'):
        for item in items:
            training = items if split=='train' else [x for x in items if x is not item]
            selected = chosen
            if split=='nested':
                selected,new_traces,new_summaries = select(training,config,'outer_'+item['file'])
                traces.extend(new_traces)
                summaries.extend(new_summaries)
                assert all(x['held_file'] != item['file'] and item['file'] not in x['fit_files'].split('|') for x in new_traces)
            choices.append({'split':split,'held_file':item['file'],'option_id':selected['id'],
                            'selection_files':'|'.join(x['file'] for x in training) if split=='nested' else '|'.join(x['file'] for x in items),
                            'fit_files':'|'.join(x['file'] for x in training)})
            for model,option in [('accepted',OPTIONS[0]),('candidate',selected)]:
                rows.append({'split':split,'model':model,'option_id':option['id'],**core.score_file(item,*predict(item,training,config,option))})
    for row in traces:
        assert row['held_file'] not in row['fit_files'].split('|')
    for row in choices:
        assert row['split']=='train' or row['held_file'] not in row['fit_files'].split('|')
    per_file = pd.DataFrame(rows)
    p_metrics = audit.csv_write('family_selection_metrics.csv',per_file)
    p_choices = audit.csv_write('family_selection_choices.csv',choices)
    p_inner = audit.csv_write('family_selection_inner_traces.csv',traces)
    p_summaries = audit.csv_write('family_selection_inner_summary.csv',summaries)
    decisions = {}
    for split in ('lofo','nested'):
        data = per_file[(per_file.split=='train')|(per_file.split==split)].copy()
        data.loc[data.split==split,'split']='lofo'
        summary = {model:{part:core.summarize(data[(data.model==model)&(data.split==part)]) for part in ('train','lofo')} for model in ('accepted','candidate')}
        decisions[split]=eligibility(data,summary)
        decisions[split]['nested_status']='Joint shortlist innerLOFO choice with outerheld excluded' if split=='nested' else 'Final option selected using these LOFO cases; optimistic selection score'
    metadata = {'registry':OPTIONS,'final_option':chosen,'decisions':decisions,
                'eligible':decisions['lofo']['eligible'] and decisions['nested']['eligible'],
                'promoted':False,'test_read':False,'outer_held_excluded':True,
                'exploration_history_not_erased':True,
                'classifiers_by_fit_files':list(CLASSIFIER_CACHE.values()),
                'code_sha256':{name:audit.digest(HERE/name) for name in ('family_selection.py','hysteresis_experiment.py','logistic_voicing_experiment.py')}}
    audit.json_write(HERE / 'results/family_selection_experiment.json',metadata)
    table = pd.DataFrame([{'split':split,'model':model,**core.summarize(per_file[(per_file.split==split)&(per_file.model==model)])} for split in ('train','lofo','nested') for model in ('accepted','candidate')])
    fig,axes = audit.plt.subplots(1,2,figsize=(12,4))
    context_table = pd.DataFrame(summaries).pivot(index='option_id',columns='context',values='average_mape')
    image = axes[0].imshow(context_table.to_numpy(),aspect='auto',cmap='viridis_r')
    axes[0].set_xticks(np.arange(len(context_table.columns)),context_table.columns.str.replace('outer_','',regex=False),rotation=30,ha='right')
    axes[0].set_yticks(np.arange(len(context_table)),context_table.index)
    axes[0].set_title('Inner selection: different training subsets')
    fig.colorbar(image,ax=axes[0],label='Inner file-stat AvgMAPE (%)')
    for j,model in enumerate(('accepted','candidate')):
        data = table[table.model==model].set_index('split').reindex(['train','lofo','nested'])
        axes[1].bar(np.arange(3)+(j-.5)*.35,data.average_mape,.35,label=model)
    axes[1].set_xticks(np.arange(3),['train','selected LOFO','nested joint choice'])
    axes[1].set(ylabel='Average MAPE (%)',title='Choice procedure versus chosen option')
    axes[1].legend(fontsize=8)
    audit.save_figure('family_selection_nested',fig,[p_metrics,p_summaries,p_choices],'Joint selection giữaACF/hysteresis/logistic vànestedheld-file evaluation.', 'Registryđềxuấtsaukhixemtraindata; nestedkhôngxóahistory, n=4, khôngphảichứngminhgeneralization.')
    for figure in audit.ARTIFACTS:
        figure.update(generator='family_selection.py',generator_sha256=audit.digest(__file__),command='python research_workbench_2026_10_06/family_selection.py')
    audit.json_write(HERE / 'results/family_selection_figure_manifest.json',{'figures':audit.ARTIFACTS})
    report = ['# H17 — lựa chọn family và margin trong nested train split','',audit.markdown_table(table),'',
              '## Chosen option từngfold','',audit.markdown_table(pd.DataFrame(choices)),'',
              '## Gates và final option','','~~~json',json.dumps({'final_option':chosen,'decisions':decisions,'eligible':metadata['eligible']},indent=2),'~~~','',
              'FinalselectedLOFO đã dùngchooptionchoice, không làheldscoređộc lập với bướcchọn. Nestedloạiouterheld khỏiinnerselection/fit; không xóa lịch sửđềxuấtregistry trêncùng4file. Testcũđãxemtrướcđây,chưađọclạitrongvòngnày. Khôngpromotemodel chỉbằngselectedscoređẹp.','',
              '![Nested choice](figures/family_selection_nested.png)','',
              '~~~powershell','python research_workbench_2026_10_06/family_selection.py','~~~']
    (HERE / 'FAMILY_SELECTION_REPORT.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(json.dumps({'final_option':chosen,'decisions':decisions,'eligible':metadata['eligible']},indent=2),flush=True)
    print(pd.DataFrame(choices).to_string(index=False),flush=True)
    print(table[['split','model','average_mape','macro_f1','recall_v','false_voiced_sil']].to_string(index=False),flush=True)


if __name__=='__main__':
    main()
