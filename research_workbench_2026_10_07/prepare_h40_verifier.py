from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'verify_yaapt_reference.py'
    assert not path.exists()
    text=(HERE/'verify_rapt_reference.py').read_text().replace('H39','H40')
    text=text.replace("pd.read_csv(HERE/'results/H40_raw_native_frames.csv')","pd.read_csv(HERE/'results/H40_raw_native_frames.csv',float_precision='round_trip')")
    start=text.index("    proof=json.loads((HERE/'results/rapt_source_provenance.json')")
    end=text.index('    checked=0',start)
    text=text[:start]+'''    proof=json.loads((HERE/'results/yaapt_source_discovery.json').read_text())
    praat=json.loads((HERE/'results/praat_native_7002_provenance.json').read_text())
    assert digest(praat['exe'])==praat['exe_sha256']==result['environment']['native_exe_sha256']
    environment=result['environment']['yaapt']
    assert environment['package_version']==proof['package_version']=='1.0.12.2'
    assert environment['python_port_commit']==proof['github_commit']
    assert len(environment['defaults'])==34
    for relative,source in proof['sources'].items():
        assert digest(HERE/'sources/yaapt'/relative)==source['sha256']
    for relative,expected in environment['source_sha256'].items():
        assert digest(REPO/relative)==expected
    assert len(result['native_calls'])==16 and len(raw.groupby(['option_id','file']))==16
    assert set(raw.option_id)=={x['id'] for x in options}
''' +text[end:]
    start=text.index("            assert call['returncode']==0")
    end=text.index('            else:',start)
    text=text[:start]+'''            assert call['native_frames']==len(group)
            if option['method']=='yaapt':
                frame=int(np.fix(option['frame_ms']*fs/1000))
                hop=int(np.fix(fs*.01))
                positions=np.arange(frame//2,len(pcm)-frame//2,hop)
                assert np.array_equal(positions,call['frame_positions_samples'])
                assert len(group)==len(positions) and np.allclose(nt,positions/fs,atol=1e-12)
                assert call['frame_size_samples']==frame and call['hop_samples']==hop
                expected=dict(environment['defaults'],frame_length=float(option['frame_ms']),f0_min=70.,f0_max=400.,frame_space=10.)
                assert call['parameters']==expected and expected['tda_frame_length']==35
                encoded=np.ascontiguousarray(pcm.astype(np.float64)/32768,dtype=np.float64).tobytes()
                assert call['input_sha256']==hashlib.sha256(encoded).hexdigest() and call['input_samples']==len(pcm)
                assert call['input_unchanged'] is True and call['backend_called'] is True
                assert call['adapter_sha256']==digest(HERE/'yaapt_adapter.py')
                assert call['f0_sha256']==hashlib.sha256(np.ascontiguousarray(nf,dtype=np.float64).tobytes()).hexdigest()
                assert call['source_sha256']==environment['source_sha256']
                assert call['python_port_commit']==proof['github_commit'] and call['half_double_flags']==[0,0]
                assert call['output_attribute']=='samp_values (UV0), not samp_interp/upsampled values'
''' +text[end:]
    text=text.replace("            else:\n                assert call['command']","            else:\n                assert call['returncode']==0\n                assert call['command']")
    text=text.replace("'PCM_source_binary_params_native_noise_checked':True","'normalized_PCM_raw_UV0_source_params_frame_centers_checked':True,'synthetic_octave_failures_retained':True")
    assert 'rapt_' not in text and 'SPTK' not in text
    compile(text,str(path),'exec')
    path.write_text(text,encoding='utf-8')


if __name__=='__main__':
    main()
