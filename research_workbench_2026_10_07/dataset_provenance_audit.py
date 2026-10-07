import concurrent.futures
import datetime
import hashlib
import json
import struct
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ROOT = REPO.parent
PUBLIC_REPO = 'dthle/TinHieuHuanLuyen'
PUBLIC_PIN = 'e38529d6485b59e49dddeccb44c129a6f93e48f3'
BASELINE = '874aca1a77a79b91c73be46ae3d1d91758baab4a'
OUTPUT = HERE / 'results' / 'dataset_provenance.json'
GIT = ['git', '-c', f'safe.directory={REPO.as_posix()}', '-C', str(REPO)]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'BT2-dataset-provenance'})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()


def stats(data):
    return {parts[0]: parts[1] for line in data.decode('utf-8-sig').splitlines()
            if (parts := line.split()) and parts[0] in {'F0mean', 'F0std', 'F0num'}}


def wav_metadata(data):
    chunks, metadata, pos = [], [], 12
    assert data[:4] == b'RIFF' and data[8:12] == b'WAVE'
    while pos + 8 <= len(data):
        tag = data[pos:pos + 4]
        size = struct.unpack_from('<I', data, pos + 4)[0]
        payload = data[pos + 8:pos + 8 + size]
        assert len(payload) == size
        chunks.append({'tag': tag.decode('ascii'), 'size': size})
        if tag == b'_PMX':
            tree = ET.fromstring(payload.decode('utf-8-sig').strip())
            metadata.extend({'tag': node.tag, 'text': node.text.strip()}
                            for node in tree.iter() if node.text and node.text.strip())
        pos += 8 + size + size % 2
    assert pos in {len(data), len(data) + 1}
    return {'chunks': chunks, 'xmp_fields': metadata}


def verify_public_file(path):
    local = path.read_bytes()
    url = f'https://raw.githubusercontent.com/{PUBLIC_REPO}/{PUBLIC_PIN}/{path.name}'
    row = {'local_path': path.relative_to(REPO).as_posix(), 'url': url,
           'local_sha256': sha256(local), 'local_bytes': len(local)}
    try:
        remote = fetch(url)
        row.update(remote_sha256=sha256(remote), remote_bytes=len(remote),
                   exact_bytes_equal=remote == local)
        if path.suffix == '.wav':
            row['verified'] = remote == local
            row['wav_metadata'] = wav_metadata(local)
        else:
            row['equal_after_line_ending_normalization'] = (
                remote.decode('utf-8-sig').splitlines() == local.decode('utf-8-sig').splitlines())
            row['verified'] = row['equal_after_line_ending_normalization']
        original = subprocess.check_output(GIT + ['show', f'{BASELINE}:{row["local_path"]}'])
        row['baseline_git_bytes_equal'] = original == local
        if path.suffix != '.wav':
            row['baseline_text_equal'] = original.decode('utf-8-sig').splitlines() == local.decode('utf-8-sig').splitlines()
        outer = ROOT / row['local_path']
        row['outer_local_path'] = str(outer)
        row['outer_bytes_equal'] = outer.read_bytes() == local
        if path.suffix != '.wav':
            row['outer_text_equal'] = outer.read_text(encoding='utf-8-sig').splitlines() == local.decode('utf-8-sig').splitlines()
        row['unchanged_baseline'] = row['baseline_git_bytes_equal'] if path.suffix == '.wav' else row['baseline_text_equal']
    except Exception as error:
        row.update(verified=False, error=str(error))
    return row


def run():
    before = {p.relative_to(REPO).as_posix(): sha256(p.read_bytes())
              for p in REPO.glob('TinHieu*/*') if p.is_file()}
    paths = sorted(p for p in REPO.glob('TinHieu*/*')
                   if p.suffix in {'.wav', '.lab'} or p.name == 'README')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(verify_public_file, paths))
    references = []
    for split, folder, cache in [('train', 'train_3gt', '.validation-3gt'),
                                 ('test', 'test_3gt', '.validation-test-3gt')]:
        for path in sorted((REPO / 'research_3gt_2026_10_05' / folder).glob('*.lab')):
            cache_path = ROOT / cache / path.name
            data = path.read_bytes()
            old_path = REPO / ('TinHieuHuanLuyen' if split == 'train' else 'TinHieuKiemThu') / path.name
            references.append({'split': split, 'path': path.relative_to(REPO).as_posix(),
                               'sha256': sha256(data), 'cached_source_path': str(cache_path),
                               'cached_source_sha256': sha256(cache_path.read_bytes()),
                               'cached_source_bytes_equal': data == cache_path.read_bytes(),
                               'old_stats': stats(old_path.read_bytes()), 'new_stats': stats(data)})
    public_history = {}
    for name in ['phone_F1.wav', 'phone_F1.lab', 'studio_M2.wav']:
        url = f'https://api.github.com/repos/{PUBLIC_REPO}/commits?' + urllib.parse.urlencode(
            {'sha': PUBLIC_PIN, 'path': name, 'per_page': 100})
        try:
            commits = json.loads(fetch(url))
            public_history[name] = {'url': url, 'commits': [
                {'sha': c['sha'], 'author_date': c['commit']['author']['date'],
                 'committer_date': c['commit']['committer']['date'], 'message': c['commit']['message']}
                for c in commits]}
        except Exception as error:
            public_history[name] = {'url': url, 'error': str(error)}
    after = {p.relative_to(REPO).as_posix(): sha256(p.read_bytes())
             for p in REPO.glob('TinHieu*/*') if p.is_file()}
    result = {'checked_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat(),
              'python': sys.version, 'auditor_sha256': sha256(Path(__file__).read_bytes()),
              'public_repo': PUBLIC_REPO, 'public_pin': PUBLIC_PIN, 'local_baseline': BASELINE,
              'policy': {'local_and_public_github_only': True, 'accessed_google_drive': False,
                         'ran_F0_inference': False, 'historical_logs_are_not_live_source_verification': True,
                         'public_copy_is_not_proof_of_original_authorship': True},
              'files': files, 'three_gt': references, 'public_history': public_history,
              'original_inputs_unchanged_during_audit': before == after,
              'summary': {'wav_exact_byte_matches': sum(x['verified'] for x in files if x['local_path'].endswith('.wav')),
                          'lab_text_matches': sum(x['verified'] for x in files if x['local_path'].endswith('.lab')),
                          'three_gt_cache_byte_matches': sum(x['cached_source_bytes_equal'] for x in references),
                          'baseline_matches': sum(x.get('unchanged_baseline', False) for x in files)}}
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['summary'], ensure_ascii=False))
    assert len(files) == 17 and all(x['verified'] and x['unchanged_baseline'] for x in files)
    assert len(references) == 8 and all(x['cached_source_bytes_equal'] for x in references)
    assert before == after


if __name__ == '__main__':
    run()
