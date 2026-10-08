import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import recovery_pitch as api
from verify_srh import independent_item


def build():
    inputs=[];tables={};diagnosis=[];boundaries=[];cases=[];comparison=[]
    for stage in ('train','test'):
        for kind in ('experiment','verification'):
            path=api.OUT/f'H56_{stage}_{kind}.json';inputs.append(path)
            if kind=='verification':assert json.loads(path.read_text())['passed']
        path=api.OUT/f'H56_{stage}_fixed.csv';inputs.append(path);tables[stage]=pd.read_csv(path,float_precision='round_trip')
        path=api.OUT/f'H56_{stage}_proofs.json';inputs.append(path);proofs=json.loads(path.read_text())
        for name in sorted(tables[stage].file.unique()):
            pool='|'.join(n for n in sorted(api.bank_train()) if n!=name) if stage=='train' else '|'.join(sorted(api.bank_train()))
            pair={identity:next(p for p in proofs if p['file']==name and p['option_id']==identity and
                api_model(p)['seed']==11 and '|'.join(api_model(p)['fit_files'])==pool)
                for identity in ('hard170','recovery_acf','recovery_bound_200')}
            path=(api.core.TRAIN if stage=='train' else api.REPO/'TinHieuKiemThu')/name
            item,fs,audio=independent_item(path,stage);segments=api.core.read_segments(path.with_suffix('.lab'))
            pred=np.array(pair['hard170']['pred']);labels=item['labels'];count=int(sum(pred));center=int(sum(labels=='v'));reference=item['stats']['F0num']
            tp=int(sum(pred&(labels=='v')));fn=int(sum((~pred)&(labels=='v')));fp=int(sum(pred&(labels=='uv')));sil=int(sum(pred&(labels=='sil')));unknown=int(sum(pred&~np.isin(labels,['v','uv','sil'])))
            assert count==tp+fp+sil+unknown and center==tp+fn
            assert count-reference==(center-reference)+fp+sil+unknown-fn
            diagnosis.append(dict(stage=stage,file=name,fs=fs,duration_s=len(audio)/fs,signal_peak=float(max(abs(audio))),
                center_v_frames=center,reference_F0num=reference,baseline_F0num=count,TP=tp,FN=fn,FP_uv=fp,FP_sil=sil,FP_unknown=unknown,
                center_minus_reference=center-reference,pred_minus_reference=count-reference,count_mape=100*abs(count-reference)/reference,
                count_average_mape_contribution=100*abs(count-reference)/reference/3,
                exact_v_mask_conditional_contribution=100*abs(center-reference)/reference/3,not_a_bound_on_all_models=True))
            edges=np.array([t for a,b,label in segments for t in (a,b)]);distance=np.min(abs(item['times'][:,None]-edges[None,:]),axis=1);near=distance<=.0125
            for label in ('v','uv','sil'):
                for boundary in (False,True):
                    mask=(labels==label)&(near==boundary)
                    boundaries.append(dict(stage=stage,file=name,label=label,within_12_5ms_boundary=boundary,frames=int(sum(mask)),
                        baseline_voiced=int(sum(pred&mask)),baseline_nonvoiced=int(sum((~pred)&mask))))
            for seed in api.SEEDS:
                for identity in pair:
                    r=tables[stage][(tables[stage].file==name)&(tables[stage].fit_pool==pool)&(tables[stage].seed==seed)&(tables[stage].option_id==identity)].iloc[0]
                    comparison.append(dict(stage=stage,file=name,seed=seed,option_id=identity,**{field:r[field] for field in ('average_mape','F0mean','F0std','F0num','F0mean_mape','F0std_mape','F0num_mape','F0mean_abs_error','F0std_abs_error','macro_f1','recall_v','recall_uv','balanced_accuracy','false_voiced_sil','recovered')}))
            old=np.array(pair['recovery_acf']['f0'],float);new=np.array(pair['recovery_bound_200']['f0'],float)
            recovered=np.array(pair['recovery_acf']['pred'])&~pred
            assert pair['recovery_acf']['pred']==pair['recovery_bound_200']['pred']
            for i in np.flatnonzero(recovered):
                voiced=np.flatnonzero(pred);nearest=voiced[np.argmin(abs(item['times'][voiced]-item['times'][i]))]
                cases.append(dict(stage=stage,file=name,seed=11,time_s=item['times'][i],label=labels[i],within_12_5ms_boundary=bool(near[i]),
                    old_recovered_estimated_f0_hz=old[i],anchored_recovered_estimated_f0_hz=new[i],
                    nearest_baseline_estimated_f0_hz=pair['hard170']['f0'][nearest],anchor_distance_ms=1000*abs(item['times'][nearest]-item['times'][i]),
                    pitch_changed=bool(old[i]!=new[i]),same_recovery_decision=True,frame_f0_truth_available=False))
    diagnosis=pd.DataFrame(diagnosis);boundary=pd.DataFrame(boundaries);cases=pd.DataFrame(cases);comparison=pd.DataFrame(comparison)
    for filename,table in [('H56_count_decomposition.csv',diagnosis),('H56_boundary_audit.csv',boundary),('H56_recovery_cases.csv',cases),('H56_paired_comparison.csv',comparison)]:table.to_csv(api.OUT/filename,index=False)
    train=tables['train'];fixed=train[train.fit_pool.str.count('\\|')==2]
    for table in (fixed,tables['test']):
        for _,group in table.groupby(['option_id','file']):
            for field in ('average_mape','F0mean','F0std','F0num','macro_f1','recall_v','recall_uv'):
                assert group[field].max()-group[field].min()<1e-8
    matrix=fixed.groupby(['option_id','file']).average_mape.mean().unstack().loc[list(api.BY_ID)]
    seeds=fixed.groupby(['option_id','seed']).average_mape.agg(['mean','max']).reset_index()
    figures=api.HERE/'figures';figures.mkdir(exist_ok=True)
    figure,axis=plt.subplots(figsize=(8,4.5));axis.imshow(matrix.to_numpy(),cmap='Blues',vmin=0,vmax=4.2,aspect='auto')
    axis.set_xticks(range(4),[s.replace('.wav','') for s in matrix.columns]);axis.set_yticks(range(5),matrix.index)
    for i in range(5):
        for j in range(4):axis.text(j,i,f'{matrix.iloc[i,j]:.3f}',ha='center',va='center',color='white' if matrix.iloc[i,j]>2.2 else 'black')
    axis.set_title('H56 fixed LOFO Average MAPE (%) — mean of 3 seeds');figure.tight_layout()
    for suffix in ('png','svg'):figure.savefig(figures/f'H56_recovery_matrix.{suffix}',dpi=160)
    plt.close(figure)
    # Plot the measured counterfactual on one train file, never as frame truth.
    chosen=cases[(cases.stage=='train')&(cases.file=='phone_M1.wav')].iloc[0]
    figure,axis=plt.subplots(figsize=(7,3.5));values=[chosen.nearest_baseline_estimated_f0_hz,chosen.old_recovered_estimated_f0_hz,chosen.anchored_recovered_estimated_f0_hz]
    axis.bar(['Nearby baseline','Original recovered ACF','Anchored recovered ACF'],values,color=['gray','tab:orange','tab:blue'])
    for i,v in enumerate(values):axis.text(i,v+3,f'{v:.2f}',ha='center')
    axis.set_ylim(0,max(values)*1.2);axis.set_ylabel('Estimated F0 (Hz)');axis.set_title(f'phone_M1 train, {chosen.time_s:.4f}s: same recovery mask, no frame F0 truth')
    figure.tight_layout()
    for suffix in ('png','svg'):figure.savefig(figures/f'H56_estimator_ablation.{suffix}',dpi=160)
    plt.close(figure)
    trainreceipt=json.loads((api.OUT/'H56_train_experiment.json').read_text());selected=json.loads((api.OUT/'H56_FROZEN_SELECTION.json').read_text())['option']['id']
    columns=['stage','file','center_v_frames','reference_F0num','baseline_F0num','FP_uv','FP_sil','FN','center_minus_reference','pred_minus_reference','count_average_mape_contribution']
    text='''# H56 — nguyên nhân ở pitch recovery và phần đếm

**Đã cô lập được một nguồn làm sai F0std trên train, nhưng chưa có cải tiến chung đạt mục tiêu.** Thay cách lấy F0 của cùng các khung được khôi phục giảm mạnh sai số ở phone_M1 và studio_F1. Final chọn hard170; outer phone_M1 chọn original recovery_acf, ba outer khác hard170, cho thấy selection không ổn định. Gate và mục tiêu từng8file<2% vẫn FAIL. Không sửa pipeline giữ lại, notebook đã nộp, LAB hoặc3GT.

GMM gmm_PEZS giữ nguyên feature/learner/threshold nhưH51,fit theo đúng pool, ba seed11/29/47. Bốn recovery nhánh có **cùng mask/count/VUV/SIL**; chỉ pitch của khung mới khác. Peak tương quan tìm trong100/200/400cents quanh F0 baseline gần nhất<=50ms, không phù hợp thìfallback pitchACF cũ. BaselineVpitch giữ nguyên. Đây là can thiệp có kiểm soát vào output estimator; không chứng minh F0 từng khung đúng vì BT2 thiếu reference theo thời gian.

## Kiểm tra train và ba seed

'''+api.audit.markdown_table(matrix.reset_index())+'''

![Ma trận](figures/H56_recovery_matrix.png)

'''+api.audit.markdown_table(seeds)+'''

Các fixed LOFO kết quả giống nhau qua ba seed; không chọn seed đẹp. Với bound200, phone_M1 recovery4.007407→1.048232%, studio_F1 recovery3.135052→0.899591%, mask/count/F1 hoàn toàn giống nhánhACF. So baseline, studio_F1 tốt hơn1.473576→0.899591%, nhưng phone_M1 vẫn kém0.776151% và studio_M1 vẫn2.399893%>2. Width100 chưa sửa được điểm studio_F1; width200/400 cùng kết quảfixedLOFO, không đồng nghĩa mọi outputs ởmọipool giống nhau.

![Tách estimator](figures/H56_estimator_ablation.png)

Khung phone_M1 1.9925s có LABV: F0 cũ240.172Hz, baseline gần nhất98.111Hz, bản anchored{new_pitch:.3f}Hz. Khung được giữ trong cả hai nhánh nên count không đổi. Sự giảm stdMAPE khi thay riêng estimator chứng minh lựa chọn pitch tác động đến lỗi thống kê, không chứng minh reference thật của khung là98Hz. Các trường hợp từng khung trongH56_recovery_cases.csv dùng seed11 vì cácfixedLOFO outputs đều bằng nhau qua ba seed.

## Phần đếm và nhãn đoạn

'''+api.audit.markdown_table(diagnosis[columns])+'''

Phân rã chính xác: `predicted_count − reference = (center_V_count − reference) + FP_UV + FP_SIL + FP_unknown − FN_V`. Đã kiểm từngfile. F0num chuẩn không phải số tâm khungLABV: studio_M1 94tâmV/82reference, phone_M2 134tâmV/123reference. Vì vậy chỉ tăng recallV chưa chắc giảm countMAPE. Baseline studio_M1 có85pitch, do94V +4UVFP −13VFN; sai số quyết định bù nhau vềcount. Không dùng sự bù này để gọi classification đúng.

Với exactLABVmask vàfinitepitchởmọikhungV, studio_M1 count đóng góp4.878049điểm vàoAverageMAPE dù mean/std bằngreference. Đây là **counterfactual có điều kiện**, không cận dưới mọi pipeline: khungV ngữ âm có thể không cóF0ước lượng hợp lệ theo engine của thầy. Chưa biết engine, frame/hop/timestamp, ngưỡngvalidF0, range vàddof tạo3GT nên không quy choGTsai. H56_boundary_audit.csv phân lỗi tại tâm gầnbiên<=12.5ms vàngoài biên; phân tích hậu nghiệm không đổi nhãn hoặc threshold.

## Test: paired diagnostics đã khóa

'''+api.audit.markdown_table(comparison.loc[(comparison.seed==11)&(comparison.stage=='test'),['file','option_id','average_mape','F0mean_mape','F0std_mape','F0num_mape','F0mean_abs_error','F0std_abs_error','macro_f1','recall_v','recall_uv','balanced_accuracy','false_voiced_sil','recovered']])+'''

Test cũng giống nhau qua ba seed. Bound200 cải thiện studio_F2 từ5.063462baseline xuống3.437002%; so cùng recoverymask,ACF4.179890→3.437002. Ba test khác bản recovery tệ hơn baseline, cảbốn vẫn>2. Bound200 không được train chọn. Không route theo file, chỉnh theo test hoặc báo fresh independent confirmation; test đã định hướng nghiên cứu trong lịch sử. Serialized fulltrain models dùngtest, khôngfit hay chuẩn hóa học lại trêntest.

## Kết luận nguyên nhân và việc tiếp theo

Có bằng chứng **một phần lỗi kỹ thuật nằm ở estimator khi recovery**, và **quyết định V theo LAB với điều kiện validF0 tạo3GT là hai mục tiêu khác nhau**. Chưa có bằng chứng đủ để kết luận test bị lỗi, dữ liệu ít là nguyên nhân duy nhất, hoặc mọiF0 gầnanchor đều đúng. Việc có thể tiếp tục: kiểm tra mô hình cho cả phép thêm và loại khung với estimator recovery đã cải thiện, chọn/kiểm tra theo filetrain; cần đăng ký vòng riêng, không tinh chỉnh trực tiếp theo test. Kiểm chứng khả năng tổng quát sau nhiều lần xem test cần corpus/người nói chưa dùng định hướng, cùng referenceprotocol. Không tự tái gán nhãn thầy để đạt2%.

Những thông tin còn thiếu để audit reference chính xác: frame length/hop vàtimestamp; engine+phiênbản/range/ngưỡnghữu thanh; quy tắc giữbỏF0ởkhungV/biên; stdpopulation hay sample; output F0 chuẩn từng khung hoặc cách tạo ba thống kê. Không gửi tin thầy hoặc suy đoán có công cụ/ghi nhầm thay bằng chứng.

## Kiểm tra và tái lập

Prereg0b64071/freeze530841f push/remoteverify trướctrain/test.33GMMfits,300train metricgroups/240innerrecords/72summaryrows; test36groups/0fits. Verifier PASS scalarGMMweights/scalertrain/componentmapping/peakselector/nearestfallback/masks/metrics/foldexclusion/selection/gates/hashes.12oldACFfixedLOFO groups exactparityH51. H50/H51 feature cache previouslyverified/hashprotected; verifier không rerunoptimizer33fits hayclaim mớiPCMverification.18synthetic precheckPASS, khôngframeGTBT2. Python3.13.11/numpy2.4.3/scipy1.17.1/sklearn1.8.0.

Lệnh recovery_pitch.py train/test;verify_recovery_pitch.py train/test;report_recovery_pitch.py. Khôngrerunmeasurements đã lưu. Registration/registry/model/prob/pred/pitchproofs cùngworkbench/results. NoDrive/DL/PDF/Jev/proseskill; BT2 vẫn trước bàiBT1bổsung.
'''
    new_pitch=chosen.anchored_recovered_estimated_f0_hz;text=text.replace('{new_pitch:.3f}',f'{new_pitch:.3f}')
    (api.HERE/'H56_REPORT.md').write_text(text,encoding='utf-8')
    selected_status=[]
    for stage,table in tables.items():
        for name in sorted(table.file.unique()):
            pool='|'.join(sorted(api.bank_train()))
            for _,r in table[(table.file==name)&(table.fit_pool==pool)&(table.option_id==selected)].iterrows():selected_status.append(dict(stage=stage,file=name,seed=int(r.seed),average_mape=r.average_mape,strict_below_2=bool(r.average_mape<2)))
    pd.DataFrame(selected_status).to_csv(api.OUT/'H56_selected_all_files.csv',index=False)
    outputs=[api.HERE/'H56_REPORT.md']+list(api.OUT.glob('H56_*decomposition.csv'))+[api.OUT/'H56_boundary_audit.csv',api.OUT/'H56_recovery_cases.csv',api.OUT/'H56_paired_comparison.csv',api.OUT/'H56_selected_all_files.csv']+list(figures.glob('H56_*'))
    original=api.REPO.parent/'turn-in-assignment - Copy/BT2_ACF_best_no_energy_set.ipynb'
    assert api.audit.digest(original)=='b643a1cdf6ac67d3e1dcacf9ce45ea4c49625da114e8c07f402c3fca5d13f85c'
    api.audit.json_write(api.OUT/'H56_reporting.json',dict(passed=True,selected=selected,all_eight_target_met=all(r['strict_below_2'] for r in selected_status),
        original_notebook_unchanged=True,new_measurements=0,diagnosis_decomposition_checked=True,
        input_hashes={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in inputs},outputs={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in outputs},source_sha256=api.audit.digest(__file__)))
    print('H56 report complete: estimator mechanism isolated; all8 target FAIL')


MODELS=None
def api_model(proof):
    global MODELS
    if MODELS is None:MODELS=json.loads((api.OUT/'H56_models.json').read_text())
    return MODELS[proof['model_id']]


if __name__=='__main__':build()
