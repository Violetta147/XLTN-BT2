import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cepstral_path as api
from verify_yaapt_extension_v2 import independent_item


def build():
    for family,stages in [('H52',('train','test')),('H53',('train','test'))]:
        for stage in stages:
            assert json.loads((api.OUT/f'{family}_{stage}_verification.json').read_text())['passed']
    train=pd.read_csv(api.OUT/'H53_train_fixed.csv',float_precision='round_trip')
    test=pd.read_csv(api.OUT/'H53_test_fixed.csv',float_precision='round_trip')
    comparison=pd.read_csv(api.OUT/'H52_test_metrics.csv',float_precision='round_trip')
    columns=['option_id','file','average_mape','F0mean_mape','F0std_mape','F0num_mape','macro_f1','recall_v','false_voiced_sil']
    summary=train.pivot(index='option_id',columns='file',values='average_mape')
    summary=summary.loc[[r['id'] for r in api.OPTIONS]]
    figure,axis=plt.subplots(figsize=(8,5.5))
    plotted=axis.imshow(summary.to_numpy(),aspect='auto',cmap='viridis_r',vmin=0,vmax=3)
    axis.set_xticks(range(4),[name.replace('.wav','') for name in summary.columns])
    axis.set_yticks(range(len(summary)),summary.index)
    for i in range(len(summary)):
        for j in range(4):axis.text(j,i,f'{summary.iloc[i,j]:.3f}',ha='center',va='center',color='white' if summary.iloc[i,j]>1.5 else 'black')
    axis.set_title('H53: train Average MAPE (%) — all configurations')
    figure.colorbar(plotted,ax=axis,label='Average MAPE (%)');figure.tight_layout()
    figures=api.HERE/'figures';figures.mkdir(exist_ok=True)
    for extension in ('png','svg'):figure.savefig(figures/f'H53_pitch_matrix.{extension}',dpi=160)
    plt.close(figure)
    cases=[]
    for stage in ('train','test'):
        for path in sorted(api.OUT.glob(f'H53_{stage}_predictions_*.npz')):
            stem=path.stem.replace(f'H53_{stage}_predictions_','')
            proof=dict(np.load(api.OUT/f'H53_{stage}_design_{stem}.npz',allow_pickle=False))
            output=dict(np.load(path,allow_pickle=False))
            k=int(np.flatnonzero(output['option_id']=='cep_a050_t015')[0])
            indices=np.flatnonzero(proof['base_pred'])
            distances=abs(1200*np.log2(output['f0'][k,indices]/proof['base_f0'][indices]))
            largest=indices[np.argsort(-distances,kind='stable')[:3]]
            directory=api.core.TRAIN if stage=='train' else api.REPO/'TinHieuKiemThu'
            item,fs,audio=independent_item(directory/(stem+'.wav'),stage)
            segments=api.core.read_segments(directory/(stem+'.lab'))
            boundaries=[time for a,b,label in segments for time in (a,b)]
            for i in largest:
                cases.append(dict(stage=stage,file=stem+'.wav',time_s=proof['times'][i],label=item['labels'][i],
                    estimated_baseline_f0_hz=proof['base_f0'][i],estimated_cep_path_f0_hz=output['f0'][k,i],
                    delta_cents=1200*np.log2(output['f0'][k,i]/proof['base_f0'][i]),
                    distance_to_lab_boundary_ms=1000*min(abs(proof['times'][i]-b) for b in boundaries),
                    frame_f0_truth_available=False))
    pd.DataFrame(cases).to_csv(api.OUT/'H53_largest_pitch_changes.csv',index=False)
    text='''# H53 — kết quả chọn ứng viên cepstrum và đường đi cao độ

**Chưa tìm được cấu hình chung tốt hơn hard170.** Cả lựa chọn cuối trên bốn train và bốn outer folds đều giữ hard170. Không thay notebook đã nộp hoặc baseline. Mục tiêu mỗi một trong tám file Average MAPE <2% vẫn chưa đạt.

Vòng này đo cao độ thật từ tín hiệu: cepstrum tìm chu kỳ từ phổ; tương quan chuẩn hóa cung cấp ứng viên thời gian. Có chín cấu hình từ trọng số CEP 0/.5/1 và trọng số chuyển giữa các khung 0/.15/.5. Không fit mô hình, không có seed ngẫu nhiên. Mặt nạ hữu thanh giữ nguyên nên count, F1, recall V/UV và SIL giữ nguyên. Dự đoán fixed không thay đổi giữa các pool; các folds đánh giá lựa chọn tham số, không phải nhiều lượt học khác nhau.

## Ma trận train

'''+api.audit.markdown_table(summary.reset_index())+'''

![Ma trận](figures/H53_pitch_matrix.png)

Mọi biến thể mới đều có studio_M1 >2%; riêng một cấu hình CEP làm phone_F1 giảm rất nhỏ, 0.34008→0.33689%, nhưng xấu hơn ở những file khác. Không chọn tham số riêng cho file hoặc ghép các kết quả tốt nhất. Với hybrid alpha.5, temporal penalty.15 giảm mean file MAPE từ1.41782 (lambda0) xuống1.30097%; vẫn cao hơn control1.12493%. Đây là tác động mô tả giữa hai cấu hình đã đăng ký, chưa phải cải thiện toàn pipeline.

## Test đã chốt trước

'''+api.audit.markdown_table(test[columns])+'''

Cấu hình được chọn từ train vẫn là hard170, có0/4test <2%. Hybrid cep_a050_t015 là cấu hình chẩn đoán đã đăng ký trước đo, không phải cấu hình được chọn: phone_M2 giảm6.83375→5.31124%, studio_M2 giảm2.11479→1.96592%, nhưng phone_F2 và studio_F2 xấu hơn. Không dùng hai kết quả tốt này để promote, chọn lại trên test hoặc tuyên bố đạt mục tiêu8file. Test đã được xem trong lịch sử nên cũng không phải tập xác nhận hoàn toàn mới.

## Kiểm tra và giới hạn

Verifier PASS trên588khung train và603khung test: cepstrum bằng full FFT/real IFFT độc lập, tương quan trực tiếp, peak/refinement, nội suy score, scalar dynamic programming, MAPE và mặt nạ bất biến. Có40nhóm metric train và8nhóm test,160inner records; registry/source/input/output hash đã kiểm. Không có lỗi verifier trong H53. Probe synthetic là8tín hiệu×9cấu hình, median error<5Hz và bất biến gain/DC, không thay validation trên tiếng nói.

Các ứng viên bị giới hạn±200cents quanh baseline; do đó vòng này chỉ sửa cao độ gần baseline, chưa thử sửa sai nguyên một octave. Alpha0/1 loại một nguồn khỏi local score nhưng vẫn giữ candidate bank chung có vị trí peak từ cả hai nguồn; không gọi đây là ablation loại toàn bộ CEP/NCCF. Lambda0 bỏ temporal penalty, vẫn giữ prior gần baseline. Không dùng HMM học trên PTDB, SRH hoặc PEFAC và không tuyên bố tái hiện pipeline MathWorks.

H53_largest_pitch_changes.csv lưu ba thay đổi lớn nhất mỗi file của hybrid cố định, chọn sau đo cho phân tích mô tả. Nhãn LAB chỉ cho biết V/UV/SIL và biên đoạn; hai giá trị F0 đều là ước lượng. Không có F0 chuẩn từng khung trên BT2 để kết luận giá trị nào đúng. MAPE theo thống kê cả file và đường mượt không đủ chứng minh contour đúng. Kết quả này cũng không chứng minh thất bại do dữ liệu ít.

Prereg b2e2bd5 và freeze1458206 đều push/remoteverify trước train/test. Lệnh: cepstral_path.py train/test; verify_cepstral_path.py train/test. Không rerun phép đo đã lưu. Nguồn HTML và thiết kế chính xác ở H53_REGISTRATION.md; giới hạn prior/filter/window/scoring giữ nguyên.
'''
    text=text.replace('1.41782',f"{train.loc[train.option_id=='cep_a050_t000','average_mape'].mean():.5f}")
    text=text.replace('1.30097',f"{train.loc[train.option_id=='cep_a050_t015','average_mape'].mean():.5f}")
    (api.HERE/'H53_REPORT.md').write_text(text,encoding='utf-8')
    report='''# H52 — kết quả mở rộng YAAPT

**Không có cải thiện đủ để thay baseline.** Final và cả bốn outer folds chọn hard170. YAAPT đã được thử ở H40; H52 mở rộng ngưỡng hữu thanh, dùng riêng cao độ dưới mask hiện tại và bỏ transition cost ở bước DP cuối.

Default35ms được replay để lưu candidate/merit/NLFER evidence; raw/native/canonical parity với H40_f35 đã kiểm. Đây không phải bằng chứng độc lập mới. Hồ sơ H40 và các probe sine/rich173 lỗi octave giữ nguyên; bộ probe mới không phủ định lỗi cũ.

## Train

'''+api.audit.markdown_table(pd.read_csv(api.OUT/'H52_fixed.csv')[columns])+'''

## Test đã chốt trước

'''+api.audit.markdown_table(comparison[columns])+'''

Selected hard170 giữ0/4test <2%,4/4train <2%; mục tiêu8file FAIL. YAAPTdefault chẩn đoán có studio_F2=1.85319%, nhưng ba test khác >2% và không được chọn trên train. Không dùng kết quả test để ghép pipeline theo file.

v2 verifier PASS5148train và1301test frames,32metric groups tổng cộng, final DP scalar và PCM NLFER fullFFT độc lập; không reimplement toàn bộ spectral candidate generation. V1 sai thứ tự phép tính float khi các chi phí gần hòa; chỉ checker v2 sửa, source đo/outputs giữ nguyên. Xem H52_VERIFICATION_NOTE.md.

Prereg đầu51f05a9 dùng trùng tên source H40. Đã phục hồi ba file H40 từ56ee7d8, đổi tên source H52 và đăng ký amendedc09574e **trước bất kỳ đo BT2 H52**; testfreeze390a533. H40 source diff so56ee7d8 hiện bằng0. Không sửa notebook đã nộp, WAV/LAB hoặc frozen baseline.

Nguồn/phiên bản, mức đọc HTML/abstract/code và lỗi discovery ở H52_YAAPT_SOURCE_NOTE.md. Không đọc PDF. Lệnh: yaapt_extension.py train/external; verify_yaapt_extension_v2.py train/test. Không có stochastic fit/seed; không rerun kết quả đã lưu. Không đủ bằng chứng quy nguyên nhân cho dữ liệu ít hoặc GT sai.
'''
    (api.HERE/'H52_REPORT.md').write_text(report,encoding='utf-8')
    selected=json.loads((api.OUT/'H53_FROZEN_SELECTION.json').read_text())['option']['id']
    status=pd.concat([train.loc[train.option_id==selected].assign(split='train'),test.loc[test.option_id==selected].assign(split='test')])
    assert len(status)==8
    status['strict_average_mape_below_2']=status.average_mape<2
    status.to_csv(api.OUT/'H53_all8_status.csv',index=False)
    outputs=[api.HERE/'H52_REPORT.md',api.HERE/'H53_REPORT.md',api.OUT/'H53_largest_pitch_changes.csv',api.OUT/'H53_all8_status.csv',
             figures/'H53_pitch_matrix.png',figures/'H53_pitch_matrix.svg']
    sources=[api.OUT/'H53_train_fixed.csv',api.OUT/'H53_test_fixed.csv',api.OUT/'H52_fixed.csv',api.OUT/'H52_test_metrics.csv']
    api.audit.json_write(api.OUT/'H52_H53_reporting.json',dict(passed=True,
        sources={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in sources},
        outputs={str(p.relative_to(api.REPO)):api.audit.digest(p) for p in outputs},
        script_sha256=api.audit.digest(__file__),frame_pitch_truth_claim=False))
    print('PASS H52/H53 reports, matrix and 24 descriptive largest-change cases generated from verified results')


if __name__=='__main__':build()
