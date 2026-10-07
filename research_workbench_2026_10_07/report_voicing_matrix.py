import itertools
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import spectrogram
import voicing_matrix as api

HERE,OUT=api.HERE,api.OUT


def table(frame):
    return api.audit.markdown_table(frame)


def main():
    train=json.loads((OUT/'H51_train_experiment.json').read_text())
    external=json.loads((OUT/'H51_external_experiment.json').read_text())
    for phase,value in [('train',train),('external',external)]:
        receipt=json.loads((OUT/f'H51_{phase}_verification.json').read_text())
        assert receipt['passed'] and receipt['experiment_sha256']==api.audit.digest(OUT/f'H51_{phase}_experiment.json')
        for path,digest in value['artifacts'].items():assert api.audit.digest(api.REPO/path)==digest
    fixed=pd.read_csv(OUT/'H51_fixed_lofo.csv');metrics=pd.read_csv(OUT/'H51_metrics.csv')
    freeze=json.loads((OUT/'H51_FROZEN_SELECTION.json').read_text())
    measured=['average_mape','macro_f1','recall_v','recall_uv','F0mean_mape','F0std_mape','F0num_mape','false_voiced_sil','recovered_v','recovered_uv','recovered_sil']
    by_seed=fixed.groupby(['recipe_id','method','blocks','seed'],dropna=False)[measured].mean().reset_index()
    worst=fixed.groupby(['recipe_id','seed']).average_mape.max()
    by_seed['worst_file_mape']=[worst.loc[(row.recipe_id,row.seed)] for row in by_seed.itertuples()]
    summary=by_seed.groupby(['recipe_id','method','blocks'],dropna=False).agg(mean_mape=('average_mape','mean'),std_seed_mape=('average_mape','std'),
        min_seed_mape=('average_mape','min'),max_seed_mape=('average_mape','max'),worst_file_any_seed=('worst_file_mape','max'),
        mean_f1=('macro_f1','mean'),mean_recall_v=('recall_v','mean')).reset_index()
    api.write_csv('H51_seed_summary.csv',summary.to_dict('records'))
    interactions=[];ablations=[]
    values={(row.recipe_id,int(row.seed)):row for row in by_seed.itertuples()}
    for method in api.METHODS:
        for seed in api.SEEDS:
            full=values[(method+'_PEZSM',seed)];control=values[('hard170',seed)]
            for block in api.BLOCKS:
                identity=method+'_'+''.join(b for b in api.BLOCKS if b!=block);reduced=values[(identity,seed)]
                ablations.append(dict(method=method,seed=seed,removed_block=block,delta_mape=reduced.average_mape-full.average_mape,delta_f1=reduced.macro_f1-full.macro_f1))
            for a,b in itertools.combinations(api.BLOCKS,2):
                pair=''.join(block for block in api.BLOCKS if block in (a,b))
                va,vb,vab=values[(method+'_'+a,seed)],values[(method+'_'+b,seed)],values[(method+'_'+pair,seed)]
                interactions.append(dict(method=method,seed=seed,pair=pair,interaction_mape=vab.average_mape-va.average_mape-vb.average_mape+control.average_mape,
                                         interaction_f1=vab.macro_f1-va.macro_f1-vb.macro_f1+control.macro_f1))
    api.write_csv('H51_pair_interactions.csv',interactions);api.write_csv('H51_leave_one_block_out.csv',ablations)
    permutation=pd.read_csv(OUT/'H51_permutation.csv')
    importance=permutation.groupby(['recipe_id','block'])[['delta_average_mape','delta_macro_f1']].mean().reset_index()
    noise=pd.read_csv(OUT/'H51_robustness.csv');cross=pd.read_csv(OUT/'H51_cross_condition.csv')
    test=pd.read_csv(OUT/'H51_test_metrics.csv');keele=pd.read_csv(OUT/'H51_keele_metrics.csv')
    test_summary=test.groupby(['recipe_id','seed']).agg(mean_mape=('average_mape','mean'),worst_file=('average_mape','max'),F1=('macro_f1','mean'),recall_v=('recall_v','mean'),SIL=('false_voiced_sil','sum')).reset_index()
    from benchmark_keele import pooled
    transfer=pd.DataFrame([dict(recipe_id=identity,seed=seed,**pooled(group)) for (identity,seed),group in keele.groupby(['recipe_id','seed'])])
    api.write_csv('H51_keele_pooled.csv',transfer.to_dict('records'))
    figures=HERE/'figures';figures.mkdir(exist_ok=True)
    noncontrol=summary[summary.recipe_id!='hard170'].copy()
    order=sorted(noncontrol.blocks.unique(),key=lambda text:(len(text),text))
    fig,axes=plt.subplots(1,2,figsize=(12,12))
    for ax,column,title in zip(axes,['mean_mape','mean_f1'],['Average MAPE (%) — lower is better','Macro F1 — higher is better']):
        matrix=noncontrol.pivot(index='blocks',columns='method',values=column).reindex(index=order,columns=api.METHODS)
        im=ax.imshow(matrix.to_numpy(),aspect='auto',cmap='viridis_r' if column=='mean_mape' else 'viridis')
        ax.set_yticks(range(len(order)),order);ax.set_xticks(range(len(api.METHODS)),api.METHODS,rotation=35,ha='right');ax.set_title(title)
        fig.colorbar(im,ax=ax,shrink=.6)
    fig.suptitle('H51 full factorial: 31 feature subsets × 5 learners; mean of file scores and seeds')
    fig.tight_layout();fig.savefig(figures/'H51_matrix.png',dpi=160);fig.savefig(figures/'H51_matrix.svg');plt.close(fig)
    items={item['file']:item for item in api.core.load_training()};error_rows=[];examples=[]
    for name,item in sorted(items.items()):
        data=dict(np.load(OUT/f'H51_predictions_{Path(name).stem}.npz',allow_pickle=False))
        bank=dict(np.load(OUT/f'H50_design_{Path(name).stem}.npz',allow_pickle=False))
        for identity in api.FULL:
            for seed in api.SEEDS:
                idx=int(np.flatnonzero((data['recipe_id']==identity)&(data['seed']==seed))[0]);recovered=data['recover'][idx];labels=item['labels'];boundary=item['boundary']
                for lab in ('v','uv','sil'):
                    for boundary_value in (False,True):
                        mask=(labels==lab)&(boundary==boundary_value)
                        error_rows.append(dict(recipe_id=identity,seed=seed,file=name,label=lab,boundary=boundary_value,frames=int(mask.sum()),recovered=int((recovered&mask).sum())))
        idx=int(np.flatnonzero((data['recipe_id']=='logistic_PEZSM')&(data['seed']==11))[0]);recovered=data['recover'][idx]
        for i in np.flatnonzero(recovered)[:8]:
            examples.append(dict(file=name,time_s=item['times'][i],center_label=item['labels'][i],boundary=bool(item['boundary'][i]),
                                 probability_v=data['prob'][idx,i],estimated_f0_hz=data['f0'][idx,i],kind='correct_V_recovery' if item['labels'][i]=='v' else 'new_false_voiced',pitch_truth_available=False))
        fs,audio=api.core.load_audio(api.core.TRAIN/name)
        fig,axes=plt.subplots(3,1,figsize=(11,7),sharex=True,gridspec_kw={'height_ratios':[1,1.6,1]})
        axes[0].plot(np.arange(len(audio))/fs,audio,lw=.5,color='#555555');axes[0].set_ylabel('PCM amplitude')
        length=round(fs*.025);nfft=1<<(length-1).bit_length()
        frequencies,times,power=spectrogram(audio,fs,window='hann',nperseg=length,noverlap=length-round(fs*.01),nfft=nfft)
        selected=frequencies<=2000
        axes[1].pcolormesh(times,frequencies[selected],10*np.log10(np.maximum(power[selected],1e-12)),shading='auto',cmap='magma');axes[1].set_ylabel('Frequency (Hz)')
        axes[2].plot(item['times'],bank['base_f0'],'.',ms=3,label='hard170 estimate',color='#1f77b4')
        axes[2].plot(item['times'][recovered],data['f0'][idx,recovered],'x',ms=5,label='LR full-feature additions, seed11',color='#d62728')
        colors=dict(v='#8bd49c',uv='#f8cb78',sil='#b9c9e0')
        for a,b,lab in item['segments']:
            for ax in (axes[0],axes[2]):ax.axvspan(a,b,color=colors[lab],alpha=.22)
        axes[2].set_ylim(60,410);axes[2].set_ylabel('Estimated F0 (Hz)');axes[2].set_xlabel('Time (s)');axes[2].legend(loc='upper right',fontsize=8)
        fig.suptitle(name+' — LAB: green V / orange UV / blue SIL; no per-frame F0 ground truth')
        fig.tight_layout();fig.savefig(figures/f'H51_qualitative_{Path(name).stem}.png',dpi=150);fig.savefig(figures/f'H51_qualitative_{Path(name).stem}.svg');plt.close(fig)
    api.write_csv('H51_error_by_boundary.csv',error_rows);api.write_csv('H51_qualitative_cases.csv',examples)
    nested=metrics[(metrics.split=='nested')&(metrics.model=='candidate')][['seed','file','option_id','average_mape','macro_f1','recall_v','false_voiced_sil']]
    target=[]
    for seed in api.SEEDS:
        train_fixed=metrics[(metrics.split=='train')&(metrics.model=='candidate')&(metrics.seed==seed)]
        test_fixed=test[(test.recipe_id==freeze['recipe']['id'])&(test.seed==seed)]
        target.append(dict(seed=seed,train_files_below2=int((train_fixed.average_mape<2).sum()),test_files_below2=int((test_fixed.average_mape<2).sum()),
                           all8_below2=bool((train_fixed.average_mape<2).all() and (test_fixed.average_mape<2).all())))
    api.write_csv('H51_all8_target.csv',target)
    compact=summary[(summary.recipe_id=='hard170')|summary.recipe_id.isin(api.FULL)]
    single=noncontrol[noncontrol.blocks.str.len()==1]
    interaction_summary=pd.DataFrame(interactions).groupby(['method','pair'])[['interaction_mape','interaction_f1']].mean().reset_index()
    ablation_summary=pd.DataFrame(ablations).groupby(['method','removed_block'])[['delta_mape','delta_f1']].mean().reset_index()
    lines=['# H51 — ma trận thí nghiệm và phân tích lỗi','',
        f"Cấu hình final chọn bằng clean train: **{freeze['recipe']['id']}**. Tám gate đạt ở mọi seed: **{train['all_seed_gates_pass']}**; từng nested train file<2 ở mọi seed: **{train['each_nested_file_all_seeds_below2']}**. Không promote hoặc sửa notebook đã nộp/frozen.",'',
        'Ma trận gồm 155 cấu hình: 31 tổ hợp đặc trưng × 5 mô hình, mỗi cấu hình được đánh giá với seed 11, 29, 47, kèm control hard170. Seed là giá trị khởi tạo bộ sinh số ngẫu nhiên. Logistic, SVM và kNN cho kết quả xác định; RF và GMM được học riêng ở ba seed. Chỉ có bốn file train; ba seed không tạo thêm người nói.','',
        'Năm nhóm đặc trưng: P là độ tuần hoàn; E là năng lượng tương đối; Z là tốc độ đổi dấu ZCR; S là tỷ lệ năng lượng tần số cao; M là 13 hệ số MFCC mô tả phân bố phổ. Các cửa sổ dài 25 ms, dịch 10 ms. Điều kiện cho phép khôi phục và cách lấy F0 giữ chung. Việc bỏ một nhóm chỉ áp dụng vào đầu vào mô hình; GMM vẫn dùng độ tuần hoàn để gán nghĩa cho cụm.','',
        f"Prereg commit `{train['prereg_commit']}`; commit khóa external `{external['frozen_commit']}`. Các commit đã được push/remoteverify trước từng phase. Runtime/fit/artifact hashes ở JSON; train actual fits={train['actual_model_fits']}, native calls mới=0. Reuse H50/H46/H48/H49 hash-verified evidence; không rerun các experiment cũ.",'',
        '## Kết quả chính và grouped cross-validation','',
        'Kiểm định chéo giữ từng file làm một nhóm: bốn lượt kiểm tra ngoài, mỗi lượt dùng ba file còn lại để chọn cấu hình qua ba lượt bên trong. Với bốn file, cách này tương đương GroupKFold bốn nhóm và leave-one-file-out. Cấu hình được chọn để giảm lỗi của file xấu nhất trên mọi seed; các giới hạn F1, recall và lỗi SIL phải đạt ở từng seed. Kết quả trên tập đã học, kiểm định chéo với cấu hình final và kiểm định chéo lồng nhau được lưu riêng. Vì train đã được xem qua nhiều vòng, đây vẫn là thăm dò. Chưa xác minh danh tính người nói nên không gọi là giữ người nói độc lập.','',table(nested),'',
        'Mục tiêu cho một cấu hình trên tám file: bốn train đã tham gia học và bốn test được đánh giá mô tả. Không coi cả tám là dữ liệu chưa từng được dùng.','',table(pd.DataFrame(target)),'',
        '## Ma trận, ablation và multiple seeds','',
        'Bảng dùng toàn bộ đặc trưng và control dưới đây tính trung bình bốn file ở từng seed, rồi tính trung bình và độ lệch chuẩn giữa các seed. Worst là lỗi của file xấu nhất trong mọi seed. Độ lệch chuẩn giữa seed chỉ đo biến động thuật toán, không đo mức bất định của quần thể người nói. Toàn bộ ma trận nằm ở H51_seed_summary.csv; H51_fixed_lofo.csv chứa đủ 1.872 dòng file × cấu hình × seed, gồm control.','',table(compact),'',
        'Đơn từng block (giữ common recovery guards):','',table(single),'',
        '![Full matrix](figures/H51_matrix.png)','',
        'Leave-one-block-out: delta=removed−full; MAPE dương/F1 âm là bỏ block làm xấu đi.','',table(ablation_summary),'',
        '## Synergy/complementary và permutation','',
        'Độ tương tác được tính bằng f(A+B)−f(A)−f(B)+f(control). Với MAPE, giá trị âm là thuận lợi so với hiệu ứng cộng; với F1, giá trị dương là thuận lợi. Đây là phép đối chiếu trên nhánh khôi phục, không chứng minh quan hệ nhân quả. MFCC là nhóm 13 chiều, các nhóm còn lại một chiều; điều kiện khôi phục vẫn dùng chung.','',table(interaction_summary),'',
        'Permutation gồm 900 phép đảo: mỗi nhóm đặc trưng đầu vào mô hình được xáo trộn ba lần trên file giữ ngoài tập học. Điều kiện khôi phục và pitch vẫn dùng tín hiệu gốc. MAPE tăng hoặc F1 giảm sau khi đảo thường cho thấy mô hình đang dùng thông tin hữu ích của nhóm đó; tương quan giữa đặc trưng có thể làm dấu đổi chiều. Không diễn giải đây là mức quan trọng có tính nhân quả.','',table(importance),'',
        '## Robustness và cross-condition','',
        'Dùng 12 bản nhiễu H46 từ bốn file: nhiễu trắng 30/20 dB và nhiễu hồng 20 dB. Mô hình chỉ học từ âm thanh sạch, loại file gốc đang đánh giá khỏi tập học. Baseline được lấy từ hard170 đã chạy trên chính âm thanh nhiễu. Nhãn đoạn và ba thống kê kế thừa từ âm thanh sạch là mục tiêu tiềm ẩn; không có phép đo F0 chuẩn mới sau thêm nhiễu. Ba biến thể không phải người nói mới hay nhiều seed tạo nhiễu. Kiểm tra gain/DC của H50 chỉ xác minh tính bất biến số học, chưa chứng nhận mọi điều kiện thu.','',table(noise.groupby(['condition','recipe_id'])[measured[:7]].mean().reset_index()),'',
        'Phone → studio và studio → phone: học trên hai file thuộc một điều kiện, đánh giá hai file thuộc điều kiện còn lại trong train. Không chọn tham số theo điều kiện đích. Khác biệt người nói và kênh thu bị trộn với nhau nên chưa thể kết luận môi trường thu gây ra thay đổi nào.','',table(cross.groupby(['direction','recipe_id'])[['average_mape','macro_f1','recall_v','false_voiced_sil']].mean().reset_index()),'',
        '## Generalization','',
        'BT2 test chỉ được chấm với cấu hình đã chọn bằng train, control và năm cấu hình dùng toàn bộ đặc trưng đã đăng ký trước, ở ba seed. Không chọn hoặc tinh chỉnh bằng test. Vì test đã được xem trong lịch sử, kết quả là đánh giá mô tả.','',table(test_summary),'',
        'KEELE gồm mười người nói, năm nam và năm nữ; các mô hình học trên BT2 train. Không học lại trên corpus, đổi reference hoặc dò độ dịch thời gian. Đây là kiểm tra chuyển dữ liệu để chẩn đoán: corpus đã được xem ở H49, cửa sổ reference khác pipeline, và độ trễ giữa tín hiệu thanh quản với microphone chỉ được sửa một phần. GPE bỏ qua khung V bị bỏ sót nên cần xem cùng VDE, FFE và RPA. Corpus không có nhãn SIL riêng. MAPE cả file dùng reference đã ghép thời gian của corpus, khác ba thống kê thầy cung cấp.','',table(transfer[['recipe_id','seed','gpe20_pct','vde_pct','ffe20_pct','rpa50_pct','file_mean_average_mape','files_average_mape_lt2']]),'',
        '## Qualitative/error analysis và cơ chế','',
        'Cả bốn file train được minh họa với logistic dùng toàn bộ đặc trưng, seed 11, đã định trước. Waveform, phổ theo thời gian, vùng LAB và F0 ước lượng cho thấy nơi thêm khung. Không có F0 chuẩn từng khung để xác nhận cao độ thêm vào là đúng. H51_qualitative_cases.csv ghi tám khung khôi phục đầu tiên mỗi file; H51_error_by_boundary.csv ghi đầy đủ theo V/UV/SIL và biên nhãn. Chưa nghe hoặc xác minh nên không đoán âm vị, tác giả hay người nói từ đồ thị.','',
        'P cung cấp bằng chứng chu kỳ; E nhận biết năng lượng thấp; Z biểu thị tốc độ đổi dấu; S/M mô tả phân bố phổ. RF/SVM có thể học biên phi tuyến, kNN dựa trên láng giềng, logistic dùng biên tuyến tính, GMM phân cụm theo mật độ. Đây là lý do để thử, cần đối chiếu ablation và permutation để xem cơ chế có ích trong dữ liệu này không. GMM học và gán nghĩa cụm không dùng LAB, nhưng chọn pipeline qua validation vẫn dùng nhãn.','',
        'Khôi phục đúng khung có tâm V có thể làm count/std xa ba thống kê chuẩn hơn. Vì chưa biết quy trình tạo ba thống kê và LAB không có F0 chuẩn từng khung, tăng recall không đồng nghĩa giảm MAPE hoặc sửa đúng cao độ. Không đổi nhãn tâm thành nhãn theo phần lớn cửa sổ để giảm điểm; H50_label_overlap.csv chỉ dùng chẩn đoán.','',
        'Đã chạy mọi ô trong registry này; chưa thử mọi thuật toán, tham số hoặc corpus có thể có. Các nhánh cepstrum, HPS, LPC, HMM, biến đổi pitch/thời gian hoặc corpus chưa từng dùng cần giả thuyết và đăng ký riêng. Giữ đầy đủ kết quả thất bại. Bài BT1 bổ sung vẫn theo thứ tự sau cải thiện BT2.','',
        'NguồnprimaryAPI: [GMM](https://scikit-learn.org/stable/modules/generated/sklearn.mixture.GaussianMixture.html), [RF](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html), [SVC](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html), [kNN](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html); docsHTML đọc07/10/2026, parameterexplicit, runtime local ghiJSON. [KEELE](https://zenodo.org/records/3921794) vàREADMEcaveat ởBENCHMARK_KEELE_REPORT.md. KhôngPDF/proseskill/Jev/Drive/DL.']
    for name in sorted(items):lines.extend(['',f'![{name} qualitative](figures/H51_qualitative_{Path(name).stem}.png)'])
    report=HERE/'H51_REPORT.md';report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paths=[report]+list(OUT.glob('H51_seed_summary.csv'))+list(OUT.glob('H51_pair_interactions.csv'))+list(OUT.glob('H51_leave_one_block_out.csv'))+list(OUT.glob('H51_keele_pooled.csv'))+list(OUT.glob('H51_error_by_boundary.csv'))+list(OUT.glob('H51_qualitative_cases.csv'))+[OUT/'H51_all8_target.csv']+list(figures.glob('H51_*.png'))+list(figures.glob('H51_*.svg'))
    api.audit.json_write(OUT/'H51_reporting_receipt.json',dict(verified_input_only=True,artifacts={str(path.relative_to(api.REPO)):api.audit.digest(path) for path in paths},
        fixed_rows=len(fixed),recipes=len(api.RECIPES),seeds=api.SEEDS,each_cell_present=True))
    print('Wrote H51 report and factorial/qualitative figures from verified measurements',flush=True)


if __name__=='__main__':main()
