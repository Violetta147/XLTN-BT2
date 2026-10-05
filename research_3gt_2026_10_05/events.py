import datetime
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
EVENTS = HERE / 'results' / 'events.jsonl'
REPORT = ROOT / 'BAO_CAO_SU_KIEN_BT2_2026-10-05.md'


def record(action, result, decision='Đang kiểm tra'):
    timestamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat(timespec='seconds')
    event = {'time_vietnam': timestamp, 'action': action, 'result': result, 'decision': decision}
    with EVENTS.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + '\n')
    events = [json.loads(line) for line in EVENTS.read_text(encoding='utf-8').splitlines()]
    lines = ['# Báo cáo sự kiện BT2 – điều tra và cải tiến F0', '',
             'Mốc giờ Việt Nam (UTC+7). Mỗi dòng được ghi khi bước tương ứng hoàn thành.', '',
             '| Thời gian | Việc đã làm / giả thuyết | Kết quả / bằng chứng | Quyết định / bước ngoặt |',
             '|---|---|---|---|']
    for item in events:
        values = [item['time_vietnam'].replace('T', ' ').replace('+07:00', ''), item['action'], item['result'], item['decision']]
        lines.append('| ' + ' | '.join(str(value).replace('|', '/').replace('\n', ' ') for value in values) + ' |')
    lines.extend(['', 'Dữ liệu thí nghiệm và mã tái lập: `XLTN-BT2/research_3gt_2026_10_05/`.',
                  'Test chỉ được chạy sau khi lưu cấu hình đã chốt. Baseline test đã được xem trong phiên trước; test mới ở đây độc lập với việc chọn cải tiến, nhưng không phải bộ dữ liệu chưa từng xem.'])
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'[{timestamp}] {action}: {result}', flush=True)

