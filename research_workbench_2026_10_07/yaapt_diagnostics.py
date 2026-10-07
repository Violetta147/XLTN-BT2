import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
import yaapt_reference as run

HERE=Path(__file__).resolve().parent
audit=run.audit


def main():
    source=HERE/'results/H40_fixed_lofo.csv'
    table=pd.read_csv(source)
    assert len(table)==16
    keys=['F0mean_mape','F0std_mape','F0num_mape']
    assert np.allclose(table[keys].sum(axis=1)/3,table.average_mape)
    order=['praat7_filtered_v0.45','yaapt_f25','yaapt_f35','yaapt_f45']
    labels=['Praat .45','YAAPT25','YAAPT35','YAAPT45']
    audit.ARTIFACTS.clear()
    for name,metrics in [('components',keys),('voicing',['recall_v','macro_f1','false_voiced_sil'])]:
        fig,axes=audit.plt.subplots(2,2,figsize=(12,8))
        for ax,(file,part) in zip(axes.flat,table.groupby('file')):
            part=part.set_index('option_id').loc[order]
            if name=='components':
                bottom=np.zeros(4)
                for metric,label in zip(metrics,['mean','std','count']):
                    values=part[metric].to_numpy()/3
                    ax.bar(labels,values,bottom=bottom,label=label)
                    bottom+=values
                assert np.allclose(bottom,part.average_mape)
                ax.axhline(2,color='black',linestyle='--',label='target 2%')
                ax.set(ylabel='Average MAPE (%)')
            else:
                x=np.arange(4)
                ax.plot(x,part.recall_v,'o-',label='recall V')
                ax.plot(x,part.macro_f1,'s-',label='macro F1')
                ax.set(ylim=(0,1.05),ylabel='rate',xticks=x,xticklabels=labels)
                for i,row in enumerate(part.itertuples()):
                    ax.annotate(f'count {row.F0num:g}; SIL {row.false_voiced_sil:g}',(i,.15),fontsize=7,rotation=15)
            ax.set(title=file)
            ax.tick_params(axis='x',rotation=20)
        axes[0,0].legend(fontsize=8)
        fig.suptitle(f'H40 fixed {name}: all registered options')
        audit.save_figure(f'H40_fixed_{name}',fig,[source],
            'Tất cả cấu hình fixed, không chọn riêng từng file.',
            'GT file-stat/nhãn đoạn; không có F0 chuẩn từng khung, nested là exploratory.')
    for figure in audit.ARTIFACTS:
        figure.update(generator=Path(__file__).name,generator_sha256=audit.digest(__file__),command='python research_workbench_2026_10_07/yaapt_diagnostics.py')
        for item in figure['sources']:
            assert audit.digest(HERE/item['path'])==item['sha256']
        png=(HERE/figure['png']).read_bytes()
        assert png[:8]==b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II',png[16:24]))>200
        ET.parse(HERE/figure['svg'])
    audit.json_write(HERE/'results/H40_fixed_diagnostics_manifest.json',{'figures':audit.ARTIFACTS})
    summary=table.groupby('option_id').agg(mean=('average_mape','mean'),worst=('average_mape','max'),SIL=('false_voiced_sil','sum'))
    studio=table[table.file=='studio_M1.wav']
    note=['# H40 — Phân tích lỗi YAAPT','',audit.markdown_table(summary.reset_index()),'',
        'YAAPT25 đạt phone_F1 1.043199% và phone_M1 1.160040%, nhưng studio_F1 3.150820%/studio_M1 6.334329%. Không được chọn YAAPT riêng cho phone dựa kết quả chính file đó. Final và cả outer folds chọn controlH30. Nestedmean2.156992%, worst2.769856%, targetfalse/gateFAIL.','',
        '## Studio nam: cửa sổ lớn chưa giúp','',audit.markdown_table(studio[['option_id','F0mean_mape','F0std_mape','F0num_mape','average_mape','F0num','macro_f1','recall_v','projection_coverage','false_voiced_sil']]),'',
        'YAAPT studio_M1 có count89/93/96 ở25/35/45ms soGT82: số khung dự đoán dư tăng, và std cũng xaGT hơn. Đây là lỗi thống kê cả file, không xác minh khung nào sai nếu thiếu F0 chuẩn từng khung. Missing support ở đầu/cuối khác với quyết định UV; raw frames/support giữ để tách cơ chế. Không bù count/std bằng GT.','',
        '## Tất cả thành phần và đánh đổi','',audit.markdown_table(table[['option_id','file',*keys,'average_mape','F0num','macro_f1','recall_v','false_voiced_sil','projection_coverage']]),'',
        'SIL thấp không đủ: count lệch và phân bố F0 lệch vẫn làm MAPE lớn. Hai file điện thoại/studio và nhãn F/M chỉ là bốn quan sát, không đủ suy rộng về giới tính hoặc thiết bị.','',
        'Nguồn: YAAPT_SOURCE_NOTE.md (abstract/manual/code, không fullpaper/PDF). Synthetic rich/sine octave failures giữ. H40 verifier:64traces/68fits/24metrics/16fixedsourcegroups; input normalizedPCM,UV0,timing/params/hash/source/control verified. Không mới WAV/test/backend/MCP call trong diagnostic.']
    path=HERE/'H40_ERROR_ANALYSIS.md'
    path.write_text('\n'.join(note)+'\n',encoding='utf-8')
    audit.json_write(HERE/'results/H40_fixed_diagnostics_verification.json',{'fixed_rows':16,'component_sums_verified':True,
        'new_audio_or_backend_call':False,'PNG_SVG_checked':True,'report_sha256':audit.digest(path),'source_sha256':audit.digest(source),'generator_sha256':audit.digest(__file__)})
    print(summary.to_string())


if __name__=='__main__':
    main()
