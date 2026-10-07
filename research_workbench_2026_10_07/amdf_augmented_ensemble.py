import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import amdf_soft_spectral as soft

HERE = Path(__file__).resolve().parent
core, audit = soft.core, soft.audit
SOURCE_CACHE = {}
CACHE = {}
PROOF = json.loads((HERE / 'results/H44_experiment.json').read_text())
MEMBERS = [o['id'] for o in json.loads((HERE / 'H44_REGISTRY.json').read_text())['options']]
FIXED = None
BANK_PROOF = None
RAW = pd.read_csv(HERE / 'results/H44_raw_native_frames.csv', float_precision='round_trip')


def extract(item, audio, option):
    name = item['file']
    assert audit.digest(core.TRAIN / name) == PROOF['data_sha256'][name]
    if name not in CACHE:
        groups = {identity: RAW[(RAW.file == name) & (RAW.option_id == identity)] for identity in MEMBERS}
        reference = groups['praat7_filtered_v0.3']
        times = reference.time_s.to_numpy()
        matrix = np.stack([groups[identity].raw_f0_hz.to_numpy() for identity in MEMBERS])
        assert all(np.array_equal(groups[identity].time_s, times) for identity in MEMBERS)
        assert all(np.array_equal((row >= 70) & (row <= 400), (matrix[0] >= 70) & (matrix[0] <= 400)) for row in matrix)
        CACHE[name] = (times, matrix)
        original = PROOF['source_calls']['praat7_filtered_v0.3|' + name]
        SOURCE_CACHE[('praat7_filtered_v0.3', name)] = (times, matrix[0], original)
    times, matrix = CACHE[name]
    gate = matrix[0]
    return dict(item, times=times, member_frequencies=matrix, native_pred=(gate >= 70) & (gate <= 400),
                native_f0=np.where((gate >= 70) & (gate <= 400), gate, np.nan), range_rejected_frames=int(((gate > 0) & ((gate < 70) | (gate > 400))).sum()),
                native_call={'engine': 'H44 member evidence for fold-dependent H46 ensemble', 'member_ids': MEMBERS,
                             'member_source_sha256': audit.digest(HERE / 'results/H44_raw_native_frames.csv'),
                             'member_metrics_sha256': audit.digest(HERE / 'results/H44_fixed_lofo.csv')})


def ranking(names):
    ranks = []
    for identity in MEMBERS:
        rows = FIXED[(FIXED.option_id == identity) & FIXED.file.isin(names)].groupby('file').mean(numeric_only=True).reset_index()
        assert len(rows) == len(names) and set(rows.file) == set(names)
        reference = FIXED[(FIXED.option_id == MEMBERS[0]) & FIXED.file.isin(names)].groupby('file').mean(numeric_only=True).reset_index()
        valid = bool(np.isfinite(rows.average_mape).all() and rows.macro_f1.mean() >= reference.macro_f1.mean() - .01
                     and rows.recall_v.mean() >= reference.recall_v.mean() - .01
                     and rows.false_voiced_sil.sum() <= reference.false_voiced_sil.sum() + 1)
        ranks.append((not valid, float(rows.average_mape.max()) if valid else np.inf,
                      float(rows.average_mape.mean()) if valid else np.inf, identity))
    return sorted(ranks)


def infer(native, training, option, config):
    if option['method'] == 'control':
        selected = ['praat7_filtered_v0.3']
        ranks, names = [], []
    elif option['method'] == 'hard_control':
        selected = ['amdf_pitch_spectral_p170']
        ranks, names = [], []
    else:
        names = sorted(x['file'] for x in training)
        assert names and len(names) == len(set(names))
        ranks = ranking(names)
        valid = [entry[3] for entry in ranks if not entry[0]]
        assert len(valid) >= option['top_k']
        selected = valid[:option['top_k']]
    frequency = native['member_frequencies'][0].copy()
    indices = [MEMBERS.index(identity) for identity in selected]
    pred = native['native_pred'].copy()
    values = native['member_frequencies'][indices][:, pred]
    frequency[pred] = values[0] if len(indices) == 1 else np.exp2(np.mean(np.log2(values), axis=0))
    assert np.array_equal(pred, (frequency >= 70) & (frequency <= 400))
    fitted = {'requires_fit': bool(names), 'actual_fit_files': names, 'method': option['method'],
              'selected_members': selected, 'member_ranking': ranks,
              'output_f0_sha256': hashlib.sha256(np.ascontiguousarray(frequency).tobytes()).hexdigest()}
    return pred, np.where(pred, frequency, np.nan), fitted, None


def check():
    assert np.isclose(np.exp2(np.mean(np.log2([100., 200.]))), np.sqrt(20000))
    assert np.exp2(np.mean(np.log2([173.] * 9))) > 172.999999
    for k in (1, 3, 5, 9):
        synthetic = np.linspace(70, 400, k)
        value = np.exp2(np.mean(np.log2(synthetic)))
        assert 70 - 1e-10 <= value <= 400 + 1e-10
    audit.json_write(HERE / 'results/H46_precheck.json', {'synthetic_only': True, 'uses_BT2_WAV': False,
                     'top_k': [1, 3, 5, 9], 'aggregation': 'equal-weight log2 frequency mean',
                     'rule_sha256': audit.digest(__file__)})
    import build_h46_augmentation
    build_h46_augmentation.check()
    print('PASS synthetic ensemble and augmentation checks; no H46 BT2 inference')


def build_bank():
    global FIXED, BANK_PROOF
    import build_h46_augmentation
    BANK_PROOF = build_h46_augmentation.main()
    FIXED = pd.read_csv(HERE / 'results/H46_augmented_member_metrics.csv')
    assert len(FIXED) == 144 and set(FIXED.groupby('file').case_id.nunique()) == {4}
