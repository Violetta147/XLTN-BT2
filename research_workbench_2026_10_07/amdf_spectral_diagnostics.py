import json
from pathlib import Path

import numpy as np
import pandas as pd
import amdf_spectral_controller as experiment

HERE=Path(__file__).resolve().parent
audit=experiment.audit


def main():
    result=json.loads((HERE/'results/H42_experiment.json').read_text())
    fixed=pd.read_csv(HERE/'results/H42_fixed_lofo.csv')
    usage=[]
    for identity,call in result['native_calls'].items():
        option,file=identity.split('|')
        windows=np.array(call['selected_windows'])
        usage.append({'option_id':option,'file':file,'native_voiced_frames':int((np.array(call['source'])!='unvoiced').sum()),
                      'routed_25ms':int((windows==25).sum()),'routed_40ms':int((windows==40).sum()),
                      'AMDF_candidates_used':call['source'].count('amdf_dip'),
                      'Praat_fallback':sum(tag.startswith('praat_') for tag in call['source'])})
    usage=pd.DataFrame(usage)
    path=audit.csv_write('H42_window_usage.csv',usage)
    fig,axes=audit.plt.subplots(2,2,figsize=(13,8))
    options=experiment.registry('H42')
    for ax,file in zip(axes.flat,sorted(fixed.file.unique())):
        subset=fixed[fixed.file==file].set_index('option_id').loc[[x['id'] for x in options]]
        bottom=np.zeros(len(subset))
        for key in ('F0mean_mape','F0std_mape','F0num_mape'):
            value=subset[key].to_numpy()/3
            ax.bar(np.arange(len(subset)),value,bottom=bottom,label=key)
            bottom+=value
        np.testing.assert_allclose(bottom,subset.average_mape,atol=1e-8)
        ax.axhline(2,color='black',ls='--',label='target2%')
        ax.set(title=file,ylabel='Average MAPE contribution (%)')
        ax.set_xticks(np.arange(len(subset)),['Praat.30','w25/b200','w40/b200','HF05','HF10','HF20','HF35'],rotation=25)
    axes[0,0].legend(fontsize=8)
    audit.ARTIFACTS.clear()
    audit.save_figure('H42_fixed_components',fig,[HERE/'results/H42_fixed_lofo.csv',path],
                     'Đủ7cấu hình×4file, mỗi thành phần MAPE chia3; không chọnbest riêngfile.',
                     'Descriptive fixed rows; nested chọn bằng file khác. Không F0 chuẩn từng khung.')
    for figure in audit.ARTIFACTS:
        figure.update(generator='amdf_spectral_diagnostics.py',generator_sha256=audit.digest(__file__),
                      command='python research_workbench_2026_10_07/amdf_spectral_diagnostics.py')
    audit.json_write(HERE/'results/H42_diagnostic_manifest.json',{'figures':audit.ARTIFACTS})
    nested=pd.read_csv(HERE/'results/H42_metrics.csv').query("split=='nested' and model=='candidate'")
    reference=pd.read_csv(HERE/'results/H41_metrics.csv').query("split=='nested' and model=='candidate'")
    by_index=fixed.set_index(['option_id','file'])
    def value(identity,file,metric):
        return f'{by_index.loc[(identity,file),metric]:.6f}'
    report=['# H42 — Đánh đổi và lựa chọn giữ riêng file','',
            'Giả thuyết phổ có ích ở cấu hình fixed5%, nhưng chưa giải quyết mục tiêu cả4file/nested vàphone_F1stdgate. Không promote hoặc đổi H41.', '',
            f"FixedHF05 phone_F1 AverageMAPE{value('amdf_spectral_hf05','phone_F1.wav','average_mape')}%/stdMAPE{value('amdf_spectral_hf05','phone_F1.wav','F0std_mape')}%, soH41fixed25/b200 {value('amdf_anchor_w25_b200','phone_F1.wav','average_mape')}%/{value('amdf_anchor_w25_b200','phone_F1.wav','F0std_mape')}%. Studio_F1stdMAPE{value('amdf_spectral_hf05','studio_F1.wav','F0std_mape')}% so{value('amdf_anchor_w25_b200','studio_F1.wav','F0std_mape')}%; studio_M1Average{value('amdf_spectral_hf05','studio_M1.wav','average_mape')}%/std{value('amdf_spectral_hf05','studio_M1.wav','F0std_mape')}% so{value('amdf_anchor_w25_b200','studio_M1.wav','average_mape')}%/{value('amdf_anchor_w25_b200','studio_M1.wav','F0std_mape')}%. Tốt lên ởfile này không đủ để chọn riêng theoGT lúcinfer.", '',
            f"Final vàouterphone_F1/phone_M1/studio_F1 chọnH41fixed25/b200. Outer studio_M1 chọnHF05 từ3file còn lại; heldfileAvg{nested.set_index('file').loc['studio_M1.wav','average_mape']:.6f}% làm targetFAIL. Nestedmean{nested.average_mape.mean():.6f}% soH41 {reference.average_mape.mean():.6f}%; worst{nested.average_mape.max():.6f}% so{reference.average_mape.max():.6f}%. Phone_F1nestedstd vẫn{nested.set_index('file').loc['phone_F1.wav','F0std_mape']:.6f}%,gateFAIL. Támgate giữ nguyên, bảyPASS mộtFAIL.",'',
            audit.markdown_table(nested[['file','option_id','F0mean','F0std','F0num','F0mean_mape','F0std_mape','F0num_mape','average_mape','macro_f1','recall_v','recall_uv','balanced_accuracy','false_voiced_sil']]),'',
            '## Route tại native frames','',audit.markdown_table(usage),'',
            'Route-count là native frame, không phải F0num của canonical grid; không coi mọi AMDFcandidate dùng là sửa pitch đúng. Curve/ratio đúng phép tính cũng không chứng nhận nội dung nhãn. Fourfile nested vẫnexploratory sau lịch sử đã xem nhiều vòng.','',
            'Độc lập fullFFT/Hann/PCM/NAMDF/parabola/band/tie/fallback/route kiểm tra588spectralframes và1176curveframes trên8curvegroups;28fixedgroups/112traces/120fits, labels/hash/gates/H41controls/PNGSVG đãcheck. H42 tái sử dụng4historicalPraatcalls,0newnativecalls; no test inference.','',
            'H42 không được promote. H41 vẫn là mốc per-fileAverage≤2%, nhưngphone_F1stdregression chưa giải quyết. Nếu thử feature/controller/band/selection mới, phải đăng ký vòng khác trước đo; không thaymetric/gate củaH42 hoặc lấybest mỗifile.']
    # All numeric statements below are also present in the fixed/nested tables.
    (HERE/'H42_ERROR_ANALYSIS.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(nested[['file','option_id','average_mape','F0std_mape']].to_string(index=False))


if __name__=='__main__':
    main()
