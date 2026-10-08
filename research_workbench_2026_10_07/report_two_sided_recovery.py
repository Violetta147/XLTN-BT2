import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import two_sided_recovery as api
from verify_srh import independent_item


def build():
    inputs=[];tables={};removed=[]
    models=json.loads((api.OUT/'H56_models.json').read_text());bank=api.source.bank_train();names=sorted(bank)
    for stage in ('train','test'):
        path=api.OUT/f'H57_{stage}_verification.json';assert json.loads(path.read_text())['passed'];inputs.append(path)
        path=api.OUT/f'H57_{stage}_fixed.csv';tables[stage]=pd.read_csv(path,float_precision='round_trip');inputs.append(path)
        path=api.OUT/f'H57_{stage}_proofs.json';proofs=json.loads(path.read_text());inputs.append(path)
        for name in sorted(tables[stage].file.unique()):
            fit=[n for n in names if n!=name] if stage=='train' else names
            item,_,_=independent_item((api.core.TRAIN if stage=='train' else api.REPO/'TinHieuKiemThu')/name,stage)
            for seed in api.SEEDS:
                mid=next(i for i,m in enumerate(models) if m['fit_files']==fit and m['seed']==seed)
                base=next(p for p in proofs if p['file']==name and p['model_id']==mid and p['option_id']=='hard170')
                for p in proofs:
                    if p['file']!=name or p['model_id']!=mid or not p['option_id'].startswith('two_sided'):continue
                    mask=np.array(base['pred'])&~np.array(p['pred'])
                    removed.append(dict(stage=stage,file=name,seed=seed,option_id=p['option_id'],removed=int(sum(mask)),
                        removed_v=int(sum(mask&(item['labels']=='v'))),removed_uv=int(sum(mask&(item['labels']=='uv'))),removed_sil=int(sum(mask&(item['labels']=='sil')))))
    removed=pd.DataFrame(removed);removed.to_csv(api.OUT/'H57_removed_label_audit.csv',index=False)
    # Post-hoc training-only interpretation of three components, not a new mapping rule.
    model=next(m for m in models if m['fit_files']==names and m['seed']==11)
    n=min(len(bank[name]['x']) for name in names);x=[];labels=[]
    for name in names:
        ix=np.round(np.linspace(0,len(bank[name]['x'])-1,n)).astype(int);x.append(bank[name]['x'][ix]);labels.append(bank[name]['labels'][ix])
    raw=np.vstack(x);labels=np.concatenate(labels);z=(raw[:,api.source.RECIPE['columns']]-np.array(model['mean']))/np.array(model['scale'])
    logs=[]
    for k in range(3):
        variance=np.array(model['variance'][k]);logs.append(np.log(model['weights'][k])-.5*np.sum(np.log(2*np.pi*variance)+(z-np.array(model['centers'][k]))**2/variance,axis=1))
    logs=np.array(logs).T;resp=np.exp(logs-logs.max(axis=1,keepdims=True));resp/=resp.sum(axis=1,keepdims=True)
    components=[]
    for k in range(3):
        weight=resp[:,k];components.append(dict(component=k,chosen_as_voiced=k==model['component'],responsibility_mass=float(sum(weight)),
            weighted_periodicity=float(weight@raw[:,0]/sum(weight)),weighted_fraction_lab_v=float(weight@(labels=='v')/sum(weight))))
    components=pd.DataFrame(components);components.to_csv(api.OUT/'H57_component_semantics_audit.csv',index=False)
    train=tables['train'];fixed=train[train.fit_pool.str.count('\\|')==2]
    matrix=fixed.groupby(['option_id','file']).average_mape.mean().unstack().loc[list(api.BY_ID)]
    seeds=fixed.groupby(['option_id','seed']).agg(mean_mape=('average_mape','mean'),worst_mape=('average_mape','max'),removed=('removed','sum'),mean_recall_v=('recall_v','mean')).reset_index()
    seeds.to_csv(api.OUT/'H57_seed_summary.csv',index=False)
    test=tables['test'][tables['test'].seed==11]
    figures=api.HERE/'figures';figures.mkdir(exist_ok=True)
    figure,axis=plt.subplots(figsize=(8,4.5));axis.imshow(matrix.to_numpy(),aspect='auto',cmap='Blues',vmin=0,vmax=18)
    axis.set_xticks(range(4),[s.replace('.wav','') for s in matrix.columns]);axis.set_yticks(range(5),matrix.index)
    for i in range(5):
        for j in range(4):axis.text(j,i,f'{matrix.iloc[i,j]:.2f}',ha='center',va='center',color='white' if matrix.iloc[i,j]>7 else 'black')
    axis.set_title('H57 fixed LOFO Average MAPE (%) — mean of 3 seeds');figure.tight_layout()
    for suffix in ('png','svg'):figure.savefig(figures/f'H57_two_sided_matrix.{suffix}',dpi=160)
    plt.close(figure)
    text='''# H57 — loại khung bằng GMM: không cải thiện

**Cả ba ngưỡng loại khung đều làm train xấu hơn.** Final giữhard170; outerphone_M1 chọnrecovery_only đã sửa estimator, baouter kháccontrol. Nested mỗifiletrain<2 qua3seeds, nhưng ba điều kiện giảmMAPEFAIL, khôngpromote. Selectedbaseline vẫn4/4train,0/4test<2; mục tiêu8file chưađạt. H56/H57 cùng nhau đã tách được sai số estimator recovery và hạn chế quyết định loại khung bằng một cụmGMM.

Reuse33GMMmodels vàposterior/anchoredpitch H56, khôngfitmới. Ba ngưỡng.1/.25/.5 loại originalbaselineV khi posterior của cụm được chọn<threshold. Giữ mọi khung recovery vàpitch giữlại; đây là thay mask nên cùng lúc thay count/mean/std vàclassification, không có nghĩa chỉ sửa count.

## Ma trận train và seed

'''+api.audit.markdown_table(matrix.reset_index())+'''

![Ma trận](figures/H57_two_sided_matrix.png)

'''+api.audit.markdown_table(seeds)+'''

Không chọnseed hoặcthreshold từtest. Rejection loại nhiềuLABV; recall giảm, không phải chỉ bỏ false positives. Tất cả variantsrejection vượt2% trênmọitrain fixedLOFO, không được chọn. Seedsummary lưu đủ3seeds; matrix làmean qua seeds, không giả mọi kết quảrejection giống nhau.

## Phân tích khung bị loại

'''+api.audit.markdown_table(removed[removed.seed==11])+'''

## Vì sao posterior không đủ cho quyết định loại khung

'''+api.audit.markdown_table(components)+'''

Bảng trên là audittraining-only fulltrainmodel seed11: membership mềm của3cụm được đối chiếu vớiLAB sau đo, không dùng sửa mappingtrongH57. H51/H56 chọn **một cụm có meanperiodicity cao nhất** làm voiced. Posterior là xác suất thuộc cụm đó theoGMM, không được hiệu chỉnh/kiểm chứng như xác suất hữu thanh theoLAB. Có thể có nhiều cụm chứaV nhưng khác đặc trưng/độ mạnh; đối xử tất cả cụm còn lại làUV/SIL không được bảo đảm. Bảng fractionLABV cùng sốremovedV là bằng chứng định lượng cho giới hạn mapping này. Không coi nhãnV theoLAB tự động tương đươngvalidF0referencecount.

Để thử sửa mapping cần một vòng riêng: mapping đa cụm theo trainingperiodicity hoặc nhãntraining vớiheld-filevalidation, giữtestngoài lựachọn; không thay mapping H57 sau khi xem kết quả. Không dùng thresholdposterior tùy ý để cốkhớpcount thầy. Đây là vấnđề cơ chế đã quan sát, không kết luậnML/GMM vô dụng hoặc data/testlỗi.

## Test diagnostics khóa trước

'''+api.audit.markdown_table(test[['file','option_id','average_mape','F0mean_mape','F0std_mape','F0num_mape','F0mean_abs_error','F0std_abs_error','macro_f1','recall_v','recall_uv','balanced_accuracy','false_voiced_sil','removed']])+'''

Diagnostictwo_sided025 không được train chọn. Mặc dùphone_M2 cóMAPE5.613773 thấp hơnbaseline6.833750, recallV giảm0.970149→0.783582 vàcountMAPE tăng5.691057→13.821138%; mean/std phần khác bù vàoaverage. Không gọi đây là cải thiện được chấp nhận. Ba test khácxấuhơn,0/4<2. Historicalexposure giữ, không tune/route theofiletest. Không nhìnq010/050testvìkhôngselected.

## Kiểm tra và thời điểm prereg

Prereg9fdecdd đãcommit vàpushsuccess trướctrain, nhưng explicitls-remotereadback trảlỗi `Empty reply from server`; runner vẫn được gọi. SHAremote chỉ xácminh hoàn tất sautrain. **Không đạt đầy đủ thứtự remoteverify-before-train**, hồsơ H57_prereg_remote_verification_note.md giữ nguyên. Không đổi source/config/output sau đo, khôngrerun đểxóa lịch sử. Freeze3891d32 đãpush vàremote-SHAverified trướctest, bằngchứng lỗi timing khôngche. Tấtcảkếtquả vốn exploratory sauhistoryexposure.

VerifierPASS300train/36testgroups,240innerrecords/72summaryrows,scalarrejectstrictthreshold/retainedpitch/metrics/pools/seed/selection/gates/hash; sourceGMM/estimator cachedverified H56. Nooptimizer/nativecalls mới; syntheticfixtureties/mask/retainedpitchPASS. Originalnotebookfrozen/WAV/LAB/teacher3GTunchanged. Lệnh two_sided_recovery.py train/test;verify_two_sided_recovery.py train/test;report_two_sided_recovery.py. NoDrive/DL/PDF/Jev/proseskill; khôngrerun H56/H57/oldmatrix. BT1bổsung vẫn sauBT2.
'''
    # Use the measured diagnostic value, not a hand-written estimate.
    value=test[(test.file=='phone_M2.wav')&(test.option_id=='two_sided_025')].average_mape.iloc[0]
    text=text.replace('5.613773',f'{value:.6f}');(api.HERE/'H57_REPORT.md').write_text(text,encoding='utf-8')
    selected=json.loads((api.OUT/'H57_FROZEN_SELECTION.json').read_text())['option']['id'];status=[]
    full='|'.join(names)
    for stage,table in tables.items():
        for _,r in table[(table.fit_pool==full)&(table.option_id==selected)].iterrows():status.append(dict(stage=stage,file=r['file'],seed=int(r.seed),average_mape=r.average_mape,strict_below_2=bool(r.average_mape<2)))
    pd.DataFrame(status).to_csv(api.OUT/'H57_selected_all_files.csv',index=False)
    outputs=[api.HERE/'H57_REPORT.md',api.OUT/'H57_removed_label_audit.csv',api.OUT/'H57_component_semantics_audit.csv',api.OUT/'H57_seed_summary.csv',api.OUT/'H57_selected_all_files.csv']+list(figures.glob('H57_two_sided_matrix.*'))
    inputs += [api.OUT/'H56_models.json']+list(api.OUT.glob('H50_design_*.npz'))
    api.audit.json_write(api.OUT/'H57_reporting.json',dict(passed=True,selected=selected,all_eight_target_met=all(r['strict_below_2'] for r in status),new_measurements=0,
        protocol_deviation='Explicit prereg remote readback completed after train; push succeeded before train. Freeze readback completed before test.',
        input_hashes={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in inputs},outputs={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in outputs},source_sha256=api.audit.digest(__file__)))
    print('H57 reporting complete; all8 target FAIL; cluster semantics audit saved')


if __name__=='__main__':build()
