import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
import amdf_praat_anchor as run

HERE=Path(__file__).resolve().parent
audit=run.audit


def main():
    source=HERE/'results/H41_fixed_lofo.csv'
    table=pd.read_csv(source)
    nested=pd.read_csv(HERE/'results/H41_metrics.csv').query("split=='nested' and model=='candidate'")
    result=json.loads((HERE/'results/H41_experiment.json').read_text())
    assert len(table)==40 and len(nested)==4
    components=['F0mean_mape','F0std_mape','F0num_mape']
    assert np.allclose(table[components].sum(axis=1)/3,table.average_mape)
    assert (nested.average_mape<=2).all() and result['goal_all_nested_files_le_2'] is True
    assert not result['decision']['eligible'] and not result['decision']['champion_promoted']
    for file,part in table.groupby('file'):
        for key in ['F0num','TP','FP','TN','FN','macro_f1','recall_v','recall_uv','balanced_accuracy','false_voiced_sil','projection_coverage']:
            assert np.allclose(part[key],part[key].iloc[0]),(file,key)
    options=json.loads((HERE/'H41_REGISTRY.json').read_text())['options']
    order=[x['id'] for x in options]
    labels=['Praat']+[f'w{x["amdf_window_ms"]}/b{x["agreement_cents"]}' for x in options[1:]]
    fig,axes=audit.plt.subplots(2,2,figsize=(13,8))
    for ax,(file,part) in zip(axes.flat,table.groupby('file')):
        part=part.set_index('option_id').loc[order]
        bottom=np.zeros(len(order))
        for metric,label in zip(components,['mean','std','count']):
            values=part[metric].to_numpy()/3
            ax.bar(labels,values,bottom=bottom,label=label)
            bottom+=values
        assert np.allclose(bottom,part.average_mape)
        ax.axhline(2,color='black',linestyle='--',label='target 2%')
        ax.set(title=file,ylabel='Average MAPE (%)')
        ax.tick_params(axis='x',rotation=45,labelsize=8)
    axes[0,0].legend(fontsize=8)
    fig.suptitle('H41: all registered NAMDF windows/bands; fixed Praat gate')
    audit.ARTIFACTS.clear()
    audit.save_figure('H41_fixed_components',fig,[source],'Ba thành phần lỗi chia3 cộng thành AverageMAPE; đủ40rows.',
        'Fixed không nested; H41 đạtfileAverageMAPE nhưngphoneF1stdgateFAIL, khôngpromote.')
    for figure in audit.ARTIFACTS:
        figure.update(generator=Path(__file__).name,generator_sha256=audit.digest(__file__),command='python research_workbench_2026_10_07/amdf_anchor_diagnostics.py')
        for item in figure['sources']:
            assert audit.digest(HERE/item['path'])==item['sha256']
        png=(HERE/figure['png']).read_bytes()
        assert png[:8]==b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II',png[16:24]))>200
        ET.parse(HERE/figure['svg'])
    audit.json_write(HERE/'results/H41_diagnostics_manifest.json',{'figures':audit.ARTIFACTS})
    usage=[]
    for identity,call in result['native_calls'].items():
        option,file=identity.split('|')
        counts=pd.Series(call['source']).value_counts().to_dict()
        usage.append({'option_id':option,'file':file,**{tag:int(counts.get(tag,0)) for tag in ['amdf_dip','praat_disagreement','praat_no_candidate','praat_window_unsupported','praat_control','unvoiced']}})
    usages=pd.DataFrame(usage)
    usages.to_csv(HERE/'results/H41_source_usage.csv',index=False)
    assert (usages.drop(columns=['option_id','file']).sum(axis=1).to_numpy()==[x['native_frames'] for x in result['native_calls'].values()]).all()
    note=['# H41 — Đạt Average MAPE từng file, còn std regression','',
        'Cảfinal/outerfolds chọn cùngamdf_anchor_w25_b200 bằngfile khác. Nestedmean1.332617%,worst1.940495%; cả4AverageMAPE≤2%. Đây là mốc số đo file-stat trêntrain, khôngF0frameaccuracy/generalization trêncorpusmới.','',
        audit.markdown_table(nested[['file','option_id','F0mean','F0std','F0num',*components,'average_mape','macro_f1','recall_v','recall_uv','balanced_accuracy','false_voiced_sil']]),'',
        '## Vì sao chưa promote?','',
        'Phone_F1stdMAPE2.332506% soPraatcontrol.851866%;AverageMAPEphone1.080551% so.595007%. GatephoneF1stdnotworseFAIL, bảygatekhácPASS. Không đổi gate sauđo, không gọiallgatesPASS hoặcpromotefrozen. StudioM1AverageMAPE3.175722→1.940495%/std5.456594→2.158397%; studioF1std1.291866→.554161%; phoneM1std1.605526→.908681%.','',
        '## Voicing/count giữ nguyên','',
        'Dựđoáncount147/233/123/85 soGT148/232/127/82. CountMAPE.675676/.431034/3.149606/3.658537%; macroF1.893977/recallV.929270/SIL0 aggregate. Khôngxóa/thêmframe hoặcfitheldstats đểđạt2%. Count khôngbằngGTnhưngtrungbìnhbaerrors≤2%; Avg≤2 khôngbảođảmmỗicomponent≤2.','',
        '## Tất cả cấu hình và nguồn','',audit.markdown_table(table[['option_id','file',*components,'average_mape']]),'',
        audit.markdown_table(usages),'',
        'Verifier độc lập:160innertraces/168fits/24metrics/40fixedgroups;4actualPraatcalls/12featuregroups/1764fullcurves đều tái tính bằng côngthứcNAMDF độc lập từnormalizedPCM, start/inputSHA/dipparabola/tie/band/fallback/tags/source/timeprojection/MAPE/VUV. KhôngWAV/backend/testcallmới trongdiagnostic.','',
        'AAMDFpaperexactmapping vẫnthiếucôngthức quaHTML/code; AMDF_ANCHOR_SOURCE_NOTE.md ghiabstract-only vàworkflowcitation. H41 engineeringrule khônggáncho tácgiảpaper. Hướngquality/dualwindowcontroller cóthểkhảo sát riêng, phảiprereg trướcmeasure; không chọnwindowtheofile/giới/device hoặcGTstd.']
    report=HERE/'H41_ERROR_ANALYSIS.md'
    report.write_text('\n'.join(note)+'\n',encoding='utf-8')
    audit.json_write(HERE/'results/H41_diagnostics_verification.json',{'component_rows':40,'source_usage_rows':40,
        'all_VUV_count_support_invariant_checked':True,'file_average_target_true_but_gate_false_checked':True,
        'new_audio_or_backend_call':False,'source_sha256':audit.digest(source),'report_sha256':audit.digest(report),
        'generator_sha256':audit.digest(__file__),'PNG_SVG_checked':True})
    print(nested[['file','average_mape','F0std_mape','F0num_mape']].to_string(index=False))


if __name__=='__main__':
    main()
