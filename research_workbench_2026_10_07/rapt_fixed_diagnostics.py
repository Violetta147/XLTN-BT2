import json
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'research_workbench_2026_10_06'))
import audit

audit.HERE,audit.RESULTS,audit.FIGURES=HERE,HERE/'results',HERE/'figures'


def main():
    receipt=HERE/'results/H39_fixed_diagnostics_verification.json'
    assert not receipt.exists(), 'Preserve completed diagnostics'
    source=HERE/'results/H39_fixed_lofo.csv'
    table=pd.read_csv(source)
    order=[x['id'] for x in json.loads((HERE/'H39_REGISTRY.json').read_text())['options']]
    labels=['Praat','RAPT -.3','RAPT 0','RAPT .3','RAPT .6']
    assert len(table)==20
    audit.ARTIFACTS.clear()
    fig,axes=audit.plt.subplots(2,2,figsize=(13,9))
    for ax,(file,group) in zip(axes.flat,table.groupby('file')):
        group=group.set_index('option_id').loc[order]
        bottom=np.zeros(5)
        for metric,label in [('F0mean_mape','mean'),('F0std_mape','std'),('F0num_mape','count')]:
            part=group[metric].to_numpy()/3
            ax.bar(labels,part,bottom=bottom,label=label)
            bottom+=part
        assert np.allclose(bottom,group.average_mape)
        ax.axhline(2,color='black',ls='--',label='target 2%')
        ax.set(title=file,ylabel='Average MAPE (%)')
        ax.tick_params(axis='x',rotation=20)
    axes[0,0].legend(fontsize=8)
    audit.save_figure('H39_fixed_components',fig,[source],'Ba thành phần lỗi/3 cộng thành Average MAPE; đủ mọi cấu hình fixed.',
                      'Fixed khác nested; không chọn best theo held file hoặc xem LAB là F0 chuẩn từng khung.')
    fig,axes=audit.plt.subplots(1,3,figsize=(14,4))
    for file,group in table.groupby('file'):
        group=group.set_index('option_id').loc[order]
        for ax,metric in zip(axes,['macro_f1','recall_v','false_voiced_sil']):
            ax.plot(labels,group[metric],'o-',label=file.removesuffix('.wav'))
            ax.set(title=metric)
            ax.tick_params(axis='x',rotation=25)
    axes[0].legend(fontsize=8)
    audit.save_figure('H39_fixed_voicing',fig,[source],'Voicing F1/recallV và SIL cho đủ mọi fixed bias.',
                      'SIL falsevoiced là số khung lặng dự đoánV; không phải số cao độ sai đã được chứng minh.')
    for figure in audit.ARTIFACTS:
        figure.update(generator=Path(__file__).name,generator_sha256=audit.digest(__file__),command='python research_workbench_2026_10_07/rapt_fixed_diagnostics.py')
        png=(HERE/figure['png']).read_bytes()
        assert png[:8]==b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II',png[16:24]))>200
        ET.parse(HERE/figure['svg'])
    audit.json_write(HERE/'results/H39_fixed_diagnostics_manifest.json',{'figures':audit.ARTIFACTS})
    totals=table.groupby('option_id').agg(average_mape=('average_mape','mean'),false_voiced_sil=('false_voiced_sil','sum'),macro_f1=('macro_f1','mean'),recall_v=('recall_v','mean')).reset_index()
    report=['# H39 — RAPT fixed error analysis','',
            'Đọc số đo đã lưu; không native/WAV/test read, không đổi rule, GT, grid hoặc selection. Default RAPT tăng recall phone_F1 nhưng count162 so GT148 và stdMAPE11.877707%; meanMAPE.507664% thấp chưa đủ. Bias−.3 thiếu F0 trên cả4file (140/216/116/78 versus148/232/127/82). Bias.6 có97SILfalsevoiced tổngbốnfile. Những kết quả này không chứng minh cơ chế noise/NCCF riêng là nguyên nhân: đã so toànpipeline.','',
            audit.markdown_table(totals),'',audit.markdown_table(table[['option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','F0num','macro_f1','recall_v','false_voiced_sil']]),'',
            'LAB không có F0 chuẩn từngkhung; không gọi một candidate octaveerror chỉ vì lệch ứng viên khác. Mục tiêu mỗi file≤2% chưa đạt; final/allouter chọn Praatcontrol. Chỉ4file/nestedexploratory.','',
            '![Components](figures/H39_fixed_components.png)','', '![Voicing](figures/H39_fixed_voicing.png)']
    path=HERE/'H39_ERROR_ANALYSIS.md'
    path.write_text('\n'.join(report)+'\n',encoding='utf-8')
    audit.json_write(receipt,{'source_sha256':audit.digest(source),'generator_sha256':audit.digest(__file__),
                            'report_sha256':audit.digest(path),'all_fixed_rows':20,'stacked_components_match_average_mape':True,
                            'png_headers_svg_xml_checked':True,'new_native_wav_or_test_read':False,'new_selection':False})
    print(totals.to_string(index=False))
    print('PASS H39 fixed figures: all20 rows, exact component totals, hashes/PNG/SVG; no remeasurement.')


if __name__=='__main__':
    main()
