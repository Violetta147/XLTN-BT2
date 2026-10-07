import concurrent.futures
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent


def normal(text):
    text = re.sub('<[^>]+>', '', text)
    return ''.join(x for x in unicodedata.normalize('NFKD',text).casefold() if x.isalnum())


def lookup(record):
    row = dict(id=record['id'], expected_title=record['title'], status='unresolved')
    try:
        if record.get('doi') and 'arxiv' not in record['doi'].lower():
            url = 'https://api.crossref.org/works/'+requests.utils.quote(record['doi'],safe='')
        elif record['id'] in ('harvest2017','kalman2014'):
            url = 'https://api.crossref.org/works'
        else:
            return dict(row,status='manual_primary_source',source=record['source'])
        params = {'query.title':record['title'],'rows':1} if record['id'] in ('harvest2017','kalman2014') else None
        response = requests.get(url,params=params,timeout=30)
        row['request_url'] = response.url
        response.raise_for_status()
        value = response.json()['message']
        if params:
            value = value['items'][0]
        row.update(raw_metadata=value,doi=value['DOI'],returned_title=value['title'][0],
                   identity_title_match=normal(value['title'][0])==normal(record['title']))
        row['status'] = 'metadata_identity_confirmed' if row['identity_title_match'] else 'manual_title_review'
    except Exception as error:
        row['error'] = str(error)
    return row


if __name__ == '__main__':
    records = json.loads((HERE/'literature_records.json').read_text())
    assert len({x['id'] for x in records}) == len(records)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        rows = list(executor.map(lookup,records))
    result = {'retrieved_utc':datetime.now(timezone.utc).isoformat(), 'requests_per_record':1,
              'pdf_requested':False, 'scope':'Metadata identity only; claim support assessed against primary content separately.',
              'records':rows}
    (HERE/'results/literature_citation_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('\n'.join(f"{x['id']}: {x['status']} {x.get('doi','')}" for x in rows))
