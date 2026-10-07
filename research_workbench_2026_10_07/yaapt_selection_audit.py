import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaapt_reference as run

HERE=Path(__file__).resolve().parent
audit=run.audit


def main():
    source=HERE/'results/H40_inner_traces.csv'
    traces=pd.read_csv(source)
    result=json.loads((HERE/'results/H40_experiment.json').read_text())
    rows=[]
    for selection in result['selections']:
        pool=traces[traces.outer_held==selection['outer_held']]
        base=pool[pool.option_id=='praat7_filtered_v0.45']
        ranking=[]
        for identity,part in pool.groupby('option_id'):
            finite=bool(np.isfinite(part.average_mape).all())
            f1=bool(part.macro_f1.mean()>=base.macro_f1.mean()-.01)
            recall=bool(part.recall_v.mean()>=base.recall_v.mean()-.01)
            silence=bool(part.false_voiced_sil.sum()<=base.false_voiced_sil.sum()+1)
            valid=finite and f1 and recall and silence
            worst=float(part.average_mape.max())
            mean=float(part.average_mape.mean())
            ranking.append((not valid,worst if valid else math.inf,mean if valid else math.inf,identity))
            rows.append({'outer_held':selection['outer_held'],'option_id':identity,'selection_files':'|'.join(sorted(part.inner_held)),
                'mean_mape':mean,'worst_mape':worst,'macro_f1':part.macro_f1.mean(),'recall_v':part.recall_v.mean(),
                'SIL':int(part.false_voiced_sil.sum()),'control_SIL':int(base.false_voiced_sil.sum()),
                'finite_ok':finite,'F1_ok':f1,'recall_ok':recall,'SIL_ok':silence,'eligible':valid,
                'chosen':identity==selection['option']['id']})
        assert min(ranking)[-1]==selection['option']['id']
    table=pd.DataFrame(rows)
    assert len(table)==20 and table.chosen.sum()==5
    studio=table[table.outer_held=='studio_M1.wav'].set_index('option_id')
    assert studio.loc['yaapt_f35','SIL']==2 and not studio.loc['yaapt_f35','SIL_ok']
    assert studio.loc['yaapt_f35','worst_mape']<studio.loc['praat7_filtered_v0.45','worst_mape']
    csv=HERE/'results/H40_selection_audit.csv'
    table.to_csv(csv,index=False)
    note=['# Vì sao H40 chọn control dù YAAPT cải thiện phone?','',
        'Minimax là giảm lỗi lớn nhất trong những file được phép chọn. Option phải qua điều kiện V/UV/SIL trước khi xếp hạng, theo đúng prereg. Đây là đọc lại trace đã lưu, không thay gate sau khi xem kết quả.','',
        '## Selection trên cả bốn file train','',audit.markdown_table(table[table.outer_held=='final']), '',
        'YAAPT25 giảm lỗi hai phonefiles nhưng worst6.334329% ởstudioM1 lớn hơn control2.769856%, nên không chọn. Không dùng best từng file rồi ghép thành một bảng như thể một pipeline chung.','',
        '## Khi giữ riêng studio_M1','',audit.markdown_table(studio.reset_index()), '',
        'Trong ba file còn lại, YAAPT35 cóworst2.049538% thấp hơn control2.769856%. Nhưng tổngfalse_voiced_sil=2 vượt control0+1; option bị loại trước xếp hạng. YAAPT45 cũng vượtSIL, YAAPT25worst3.150820% lớn hơncontrol. Vì vậy fold này vẫnchọncontrol, không dùng heldstudioM1 để quyết định.','',
        'Đây là đánh đổi thật của gate đăng ký, không dấu hiệu code bỏ qua YAAPT. Điều chỉnh điều kiện hoặc thêm cổng silence từ signal cần giả thuyết/grid/gate mới trước đo; không sửaH40 để choPASS. Unknown groundtruth từngkhung vẫngiữ.']
    report=HERE/'H40_SELECTION_AUDIT.md'
    report.write_text('\n'.join(note)+'\n',encoding='utf-8')
    audit.json_write(HERE/'results/H40_selection_audit_verification.json',{'candidate_pools_replayed':20,'selections_matched':5,
        'source_sha256':audit.digest(source),'experiment_sha256':audit.digest(HERE/'results/H40_experiment.json'),
        'csv_sha256':audit.digest(csv),'report_sha256':audit.digest(report),'generator_sha256':audit.digest(__file__),
        'no_new_WAV_backend_or_selection':True})
    print(table[['outer_held','option_id','worst_mape','SIL','eligible','chosen']].to_string(index=False))


if __name__=='__main__':
    main()
