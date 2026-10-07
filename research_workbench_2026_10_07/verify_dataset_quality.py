import hashlib
import itertools
import json
import wave
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
RESULTS = HERE / 'results'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    manifest = json.loads((RESULTS/'dataset_quality_manifest.json').read_text(encoding='utf-8'))
    assert manifest['generator_sha256'] == sha(HERE/'dataset_quality_audit.py')
    for source in manifest['inputs']:
        assert sha(REPO/source['path']) == source['sha256'], source
    for output in manifest['outputs']:
        assert sha(HERE/output['path']) == output['sha256'], output
    measured = pd.read_csv(RESULTS/'dataset_quality_per_file.csv')
    details = pd.read_csv(RESULTS/'dataset_quality_segments.csv')
    pairs = pd.read_csv(RESULTS/'dataset_quality_duplicate_pairs.csv')
    expected = {(split,p.name) for split,folder in [('train','TinHieuHuanLuyen'),('test','TinHieuKiemThu')]
                for p in (REPO/folder).glob('*.wav')}
    assert set(zip(measured.split,measured.file)) == expected
    assert len(measured) == len(expected) == 8
    pcm_hashes, file_hashes = {}, {}
    for row in measured.itertuples(index=False):
        folder = 'TinHieuHuanLuyen' if row.split == 'train' else 'TinHieuKiemThu'
        path = REPO/folder/row.file
        with wave.open(str(path),'rb') as reader:
            assert reader.getcomptype() == 'NONE'
            assert reader.getsampwidth() == 2 and reader.getnchannels() == 1
            fs, count = reader.getframerate(), reader.getnframes()
            values = np.frombuffer(reader.readframes(count),dtype='<i2')
        assert len(values) == row.samples == count and fs == row.fs
        assert abs(count/fs - row.duration_s) < 1e-12
        assert ((values == -32768) | (values == 32767)).sum() == row.rail_samples
        scaled = values.astype(np.float64)/32768
        assert np.isfinite(scaled).all() == row.finite_audio
        np.testing.assert_allclose([np.max(np.abs(scaled)), np.sqrt(np.mean(scaled**2)), scaled.mean()],
                                   [row.peak_abs,row.rms,row.dc_mean],rtol=1e-10,atol=1e-15)
        assert (np.abs(scaled)>=.99).sum() == row.near_rail_samples
        assert (values == 0).sum() == row.exact_zero_samples
        header = json.dumps({'fs': fs, 'dtype': 'int16', 'shape': [count]},sort_keys=True).encode()
        pcm_hashes[f'{row.split}/{row.file}'] = hashlib.sha256(header+values.tobytes()).hexdigest()
        file_hashes[f'{row.split}/{row.file}'] = sha(path)
        assert pcm_hashes[f'{row.split}/{row.file}'] == row.pcm_sha256
        segments, original = [], {}
        for line in path.with_suffix('.lab').read_text(encoding='utf-8').splitlines():
            tokens = line.split()
            if tokens[0].startswith('F0'):
                original[tokens[0]] = float(tokens[1])
            else:
                segments.append((float(tokens[0]),float(tokens[1]),tokens[2]))
        reference = {tokens[0]:float(tokens[1]) for tokens in
                     [line.split() for line in (REPO/'research_3gt_2026_10_05'/f'{row.split}_3gt'/path.with_suffix('.lab').name).read_text().splitlines()]}
        assert len(segments) == row.segment_count
        assert row.lab_issue_count == 0
        assert sum(max(0,c-b) for (_,b,_),(c,_,_) in zip(segments,segments[1:]))*1000 == row.internal_gap_ms
        assert sum(max(0,b-c) for (_,b,_),(c,_,_) in zip(segments,segments[1:]))*1000 == row.overlap_ms
        np.testing.assert_allclose(row.tail_unlabeled_ms,1000*max(0,count/fs-segments[-1][1]),atol=1e-12)
        labels, start, length, hop = [], 0, round(fs*.025), round(fs*.010)
        while start+length <= count:
            t = (start+length/2)/fs
            matches = [lab for a,b,lab in segments if a <= t < b]
            assert len(matches) <= 1
            labels.append(matches[0] if matches else 'unknown')
            start += hop
        assert len(labels) == row.frame_count and labels.count('unknown') == row.unknown_frames
        for lab in ('v','uv','sil'):
            assert labels.count(lab) == getattr(row,f'{lab}_frames')
            np.testing.assert_allclose(sum(b-a for a,b,label in segments if label == lab),getattr(row,f'{lab}_seconds'),atol=1e-12)
        assert reference['F0num']-labels.count('v') == row.reference_count_minus_v_grid
        for key in reference:
            assert reference[key] == getattr(row,f'reference_{key}')
        for key in original:
            assert original[key] == getattr(row,f'original_{key}')
        local_detail = details[(details.split==row.split)&(details.file==row.file)]
        assert len(local_detail) == len(segments)
        energies = {'v':[],'uv':[],'sil':[]}
        for (a,b,label), detail in zip(segments,local_detail.itertuples(index=False)):
            assert (a,b,label)==(detail.start_s,detail.end_s,detail.label)
            lo = (Fraction(str(a))+Fraction(1,50))*fs
            hi = (Fraction(str(b))-Fraction(1,50))*fs
            lo_ceil = -(-lo.numerator//lo.denominator)
            hi_ceil = -(-hi.numerator//hi.denominator)
            interior = scaled[max(0,lo_ceil):min(count,hi_ceil)] if hi_ceil>lo_ceil else np.array([])
            assert len(interior) == detail.interior_samples
            if len(interior):
                np.testing.assert_allclose(np.sqrt(np.mean(interior**2)),detail.interior_rms,rtol=1e-10,atol=1e-15)
            energies[label].append(interior)
        for label, pieces in energies.items():
            all_samples = np.concatenate(pieces)
            assert len(all_samples) == getattr(row,f'{label}_interior_samples')
            np.testing.assert_allclose(np.sqrt(np.mean(all_samples**2)),getattr(row,f'{label}_interior_rms'),rtol=1e-10,atol=1e-15)
        if row.v_interior_rms and row.sil_interior_rms:
            np.testing.assert_allclose(20*np.log10(row.v_interior_rms/row.sil_interior_rms),row.v_sil_energy_ratio_db,atol=1e-10)
    assert len(pairs) == 28 and pairs.cross_split.sum() == 16
    assert set(zip(pairs.left,pairs.right)) == set(itertools.combinations(pcm_hashes,2))
    for pair in pairs.itertuples(index=False):
        assert pair.identical_wav == (file_hashes[pair.left] == file_hashes[pair.right])
        assert pair.identical_native_pcm == (pcm_hashes[pair.left] == pcm_hashes[pair.right])
    old = pd.read_csv(REPO/'research_workbench_2026_10_06/results/training_data_profile.csv').set_index('file')
    for row in measured[measured.split=='train'].itertuples(index=False):
        for field in ('fs','samples','duration_s','rms','dc_mean','frame_count','v_frames','uv_frames','sil_frames'):
            np.testing.assert_allclose(getattr(row,field),old.loc[row.file,field],rtol=1e-10,atol=1e-14)
        assert row.rail_samples == old.loc[row.file,'native_clip_samples']
        for field in ('wav_sha256','segment_lab_sha256','stats_lab_sha256'):
            assert getattr(row,field)==old.loc[row.file,field]
    with Image.open(HERE/'figures/dataset_quality_waveforms.png') as image:
        image.verify()
    ElementTree.parse(HERE/'figures/dataset_quality_waveforms.svg')
    receipt = dict(files_verified=8, input_hashes_verified=24, pair_checks=28, cross_split_pairs=16,
                   independent_reader='stdlib wave with native int16 PCM; no scipy audio decoder or F0 inference',
                   original_lab_and_3gt_verified=True, segment_sample_energy_and_grid_counts_verified=True,
                   previous_train_profile_parity=True, immutable_inputs_verified=True,
                   verifier_sha256=sha(__file__),manifest_sha256=sha(RESULTS/'dataset_quality_manifest.json'))
    (RESULTS/'dataset_quality_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':
    main()
