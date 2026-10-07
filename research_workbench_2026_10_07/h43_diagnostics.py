import json
from pathlib import Path

import numpy as np
import pandas as pd
import amdf_pitch_spectral_controller as experiment

HERE=Path(__file__).resolve().parent
audit=experiment.audit


def main():
    result=json.loads((HERE/'results/H43_experiment.json').read_text())
    fixed=pd.read_csv(HERE/'results/H43_fixed_lofo.csv')
    nested=pd.read_csv(HERE/'results/H43_metrics.csv').query("split=='nested' and model=='candidate'")
    selected=[]
    for entry in result['selections']:
        outer=entry['outer_held']
        trace=pd.read_csv(HERE/'results/H43_inner_traces.csv')
        pool=trace[trace.outer_held==outer]
        candidates=[]
        for identity,group in pool.groupby('option_id'):
            candidates.append({'outer_held':outer,'option_id':identity,'selection_files':'|'.join(sorted(group.inner_held)),
                               'worst_average_mape':group.average_mape.max(),'mean_average_mape':group.average_mape.mean(),
                               'selected':identity==entry['option']['id']})
        selected.extend(candidates)
    selection=audit.csv_write('H43_selection_pools.csv',selected)
    usage=[]
    for identity,call in result['native_calls'].items():
        option,file=identity.split('|')
        windows=np.array(call['selected_windows'])
        positive=sum(tag!='unvoiced' for tag in call['source'])
        outside=result['range_rejected_frames'][identity]
        usage.append(dict(option_id=option,file=file,raw_native_voiced=positive,range_excluded=outside,
                          in_range_native_voiced=positive-outside,route25=int((windows==25).sum()),
                          route40=int((windows==40).sum()),AMDF_used=call['source'].count('amdf_dip'),
                          Praat_fallback=sum(tag.startswith('praat_') for tag in call['source'])))
    usage=pd.DataFrame(usage)
    assert len(usage)==28
    assert (usage.AMDF_used+usage.Praat_fallback==usage.raw_native_voiced).all()
    routed=usage[usage.option_id!='praat7_filtered_v0.3']
    assert (routed.route25+routed.route40==routed.in_range_native_voiced).all()
    audit.csv_write('H43_window_usage.csv',usage)
    fig,axes=audit.plt.subplots(2,2,figsize=(12,8))
    options=experiment.registry('H43')
    for ax,file in zip(axes.flat,sorted(fixed.file.unique())):
        table=fixed[fixed.file==file].set_index('option_id').loc[[x['id'] for x in options]]
        bottom=np.zeros(len(table))
        for metric in ('F0mean_mape','F0std_mape','F0num_mape'):
            values=table[metric].to_numpy()/3
            ax.bar(np.arange(len(table)),values,bottom=bottom,label=metric)
            bottom+=values
        np.testing.assert_allclose(bottom,table.average_mape,atol=1e-8)
        ax.axhline(2,color='black',ls='--',label='target2%')
        ax.set(title=file,ylabel='Average MAPE contribution (%)')
        ax.set_xticks(np.arange(len(table)),['Praat.30','25ms','40ms','HF05/p0','HF05/p140','HF05/p170','HF05/p200'],rotation=30)
    axes[0,0].legend(fontsize=8)
    audit.ARTIFACTS.clear()
    audit.save_figure('H43_fixed_components',fig,[HERE/'results/H43_fixed_lofo.csv',selection],
                     'Đủ7options, giữ cảfailedfixedrows. Ngưỡng0 làH42HF05control.',
                     'Fixedfile-stat dùngcùngcấuhình, khôngnested hoặc F0groundtruth từngkhung.')
    for figure in audit.ARTIFACTS:
        figure.update(generator='h43_diagnostics.py',generator_sha256=audit.digest(__file__),
                      command='python research_workbench_2026_10_07/h43_diagnostics.py')
    audit.json_write(HERE/'results/H43_diagnostic_manifest.json',{'figures':audit.ARTIFACTS})
    pool=pd.DataFrame(selected)
    final_fixed=fixed[fixed.option_id==result['selections'][0]['option']['id']].set_index('file').loc[sorted(fixed.file.unique())]
    fixed_values='/'.join(f'{x:.6f}' for x in final_fixed.average_mape)
    held_studio=nested.set_index('file').loc['studio_M1.wav','average_mape']
    report=['# H43 — Qua gate control nhưng nested target chưa đạt','',
            f'Finalngưỡng170Hz cố định trên4file đạtAverage≤2%: {fixed_values}%. Nhưngouterstudio_M1 chọn140Hz từ3filekhác vàheldAverage{held_studio:.6f}%; nestedtargetFAIL. Không coi fixedtarget lànestedtarget, khôngpromote tự động.','',
            f'Phone_F1nestedstdMAPE.089632% soH31.851866% vàH41 2.332506%; tất cả8gate soH31PASS. Nestedmean{nested.average_mape.mean():.6f}% nhưngworst{nested.average_mape.max():.6f}%; mean nhỏ không đủ. VUV/count/SIL giữcontrol, count147/233/123/85. Khôngkhẳngđịnh F0 từngkhung đúng vìGT chỉfile-stat/segment.','',
            audit.markdown_table(nested[['file','option_id','F0mean','F0std','F0num','F0mean_mape','F0std_mape','F0num_mape','average_mape','macro_f1','recall_v','recall_uv','balanced_accuracy','false_voiced_sil']]),'',
            '## Vì sao studio_M1 chọn140?','',
            audit.markdown_table(pool[pool.outer_held=='studio_M1.wav'].sort_values(['worst_average_mape','mean_average_mape','option_id'])),'',
            'So sánh chỉ trong3filecòn lại:140Hz cóworst/mean nhỏ hơn170Hz; quy tắcminimax làm đúngregistry nhưngheldstudio_M1 xấu. Đây là bằng chứng limitedselectionstability trênn4, khôngcode bỏqua cấuhình170 hoặc leakheldfile. Khôngsửaselection/gateH43 sauđo.','',
            '## Routecounts','',audit.markdown_table(usage),'',
            'Route chỉnativeF0∈70–400; phone_M1 có2rawPraatframes khoảng473Hz bị rangeexclude, canonicalcount233 khôngđổi. Không tínhhai frame này làAMDFroute hoặcnhãnsai đãxácnhận.','',
            'H43 verifier independentlyreplayed fullFFT/Hann/PCM/NAMDF/band/refine/tie/routepitchcondition/sourcenativehash/labels/std/MAPE/count/VUV/support và112traces/120fits/28fixedgroups. H42p0parity/H41controls kiểm tra. 0newnativecalls,4historicalPraatgroups; no testinference/tuning. Giữfailures, original/frozen/notebooks cũ.','',
            'Tiếp theo notebook riêng replayregisteredH42/H43 từWAV đểcósource/figures/receipts thực; hypothesis mới cầnprereg trước đo. H41 targetnested vẫn làmốc, H43 cònselectiontarget chưađạt; không đổi mục tiêu thành mean≤2%.']
    # Numbers in prose are checked against the source tables before delivery.
    (HERE/'H43_ERROR_ANALYSIS.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(nested[['file','average_mape','F0std_mape']].to_string(index=False,float_format=lambda x:f'{x:.9f}'))
    print(fixed.query("option_id=='amdf_pitch_spectral_p170'")[['file','average_mape']].to_string(index=False,float_format=lambda x:f'{x:.9f}'))


if __name__=='__main__':
    main()
