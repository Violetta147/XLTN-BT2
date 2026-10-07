from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'verify_amdf_anchor.py'
    assert not path.exists()
    text=(HERE/'verify_yaapt_reference.py').read_text().replace('H40','H41').replace('praat7_filtered_v0.45','praat7_filtered_v0.3').replace('H30','H31')
    start=text.index("    proof=json.loads((HERE/'results/yaapt_source_discovery.json')")
    end=text.index('    checked=0',start)
    text=text[:start]+'''    praat=json.loads((HERE/'results/praat_native_7002_provenance.json').read_text())
    assert digest(praat['exe'])==praat['exe_sha256']==result['environment']['native_exe_sha256']
    assert len(result['native_calls'])==40 and len(raw.groupby(['option_id','file']))==40
    assert len(result['source_calls'])==4
    assert set(raw.option_id)=={x['id'] for x in options}
    curve_cache={}
    curve_rows=0
''' +text[end:]
    start=text.index("            if option['method']=='yaapt':")
    end=text.index('            indices=np.array([int(np.argmin',start)
    text=text[:start]+'''            base=raw[(raw.option_id=='praat7_filtered_v0.3')&(raw.file==file)]
            bt,bf=base.time_s.to_numpy(),base.raw_f0_hz.to_numpy()
            assert np.allclose(nt,bt,atol=1e-12) and np.array_equal(nf>0,bf>0)
            assert call['returncode']==0 and call['command']==[praat['exe'],'--run',str(HERE/'praat_extract_native.praat'),str(REPO/'TinHieuHuanLuyen'/file),'filtered','0.3']
            assert call['script_sha256']==digest(HERE/'praat_extract_native.praat') and call['exe_sha256']==praat['exe_sha256']
            assert np.allclose(np.diff(nt),.01,atol=1e-12)
            assert call['rule_sha256']==digest(HERE/'amdf_anchor.py')
            assert call['output_f0_sha256']==hashlib.sha256(np.ascontiguousarray(nf,dtype=np.float64).tobytes()).hexdigest()
            sourcecall=result['source_calls']['praat7_filtered_v0.3|'+file]
            assert call['command']==sourcecall['command'] and call['stdout_sha256']==sourcecall['stdout_sha256']
            if option['method']=='control':
                assert call['AMDF_evidence'] is None
            else:
                evidence=call['AMDF_evidence']
                assert evidence['sha256']==digest(HERE/evidence['path'])
                assert evidence['source_sha256']==digest(HERE/'amdf_anchor.py')
                assert evidence['frozen_notebook_sha256']==digest(REPO/'research_3gt_2026_10_05/baselines/AMDF.ipynb')
                key=(option['amdf_window_ms'],file)
                if key not in curve_cache:
                    data=dict(np.load(HERE/evidence['path'],allow_pickle=False))
                    length=round(fs*option['amdf_window_ms']/1000)
                    assert int(data['frame_samples'])==length and int(data['fs'])==fs and int(data['input_samples'])==len(pcm)
                    audio=np.ascontiguousarray(pcm.astype(np.float64)/32768)
                    assert str(data['audio_sha256'])==hashlib.sha256(audio.tobytes()).hexdigest()
                    assert np.allclose(data['times'],bt,atol=1e-12) and np.array_equal(data['gate_frequency'],bf)
                    starts=np.array([round(t*fs-length/2) for t in bt])
                    assert np.array_equal(data['starts'],starts)
                    lag_grid=np.arange(max(1,int(np.floor(fs/400))),min(length-1,int(np.ceil(fs/70)))+1)
                    assert np.array_equal(data['lags'],lag_grid)
                    for i,(start,gate) in enumerate(zip(starts,bf)):
                        supported=70<=gate<=400 and start>=0 and start+length<=len(audio)
                        if not supported:
                            assert np.isnan(data['curve'][i]).all() and str(data['frame_sha256'][i])==''
                            continue
                        frame=audio[start:start+length]
                        assert str(data['frame_sha256'][i])==hashlib.sha256(frame.tobytes()).hexdigest()
                        centered=frame-frame.mean()
                        if abs(centered).mean()<1e-8:
                            fresh=np.ones(len(lag_grid))
                        else:
                            fresh=np.array([abs(centered[:-lag]-centered[lag:]).mean()/(abs(centered[:-lag]).mean()+abs(centered[lag:]).mean()+1e-12) for lag in lag_grid])
                        assert np.allclose(data['curve'][i],fresh,atol=1e-12,rtol=1e-12)
                        curve_rows+=1
                    curve_cache[key]=data
                    print('Verified independent NAMDF curves',key,flush=True)
                data=curve_cache[key]
                selected=np.full(len(bf),-1,dtype=int)
                fresh_f0=bf.copy()
                tags=np.where(bf>0,'praat_control','unvoiced').astype('<U32')
                for i in np.flatnonzero((bf>=70)&(bf<=400)):
                    curve=data['curve'][i]
                    if not np.isfinite(curve).all():
                        tags[i]='praat_window_unsupported'
                        continue
                    if np.ptp(curve)<=1e-12:
                        tags[i]='praat_no_candidate'
                        continue
                    dip_indices=np.array([j for j in range(1,len(curve)-1) if curve[j]<=curve[j-1] and curve[j]<=curve[j+1]],dtype=int)
                    if not len(dip_indices):
                        dip_indices=np.array([int(np.argmin(curve))])
                    allowed=[]
                    finite_candidates=0
                    for j in dip_indices:
                        lag=float(data['lags'][j])
                        if 0<j<len(curve)-1:
                            a,b,c=curve[j-1:j+2]
                            denominator=a-2*b+c
                            if abs(denominator)>1e-12:
                                delta=.5*(a-c)/denominator
                                if abs(delta)<=1:
                                    lag+=float(delta)
                        frequency=fs/lag
                        if not 70<=frequency<=400:
                            continue
                        finite_candidates+=1
                        deviation=abs(1200*np.log2(frequency/bf[i]))
                        if deviation<=option['agreement_cents']+1e-9:
                            allowed.append((float(curve[j]),float(deviation),float(frequency),int(j)))
                    if allowed:
                        _,_,fresh_f0[i],selected[i]=min(allowed)
                        tags[i]='amdf_dip'
                    else:
                        tags[i]='praat_disagreement' if finite_candidates else 'praat_no_candidate'
                assert np.allclose(nf,fresh_f0,atol=1e-10)
                assert call['selected_curve_indices']==selected.tolist() and call['source']==tags.tolist()
''' +text[end:]
    text=text.replace("'synthetic_octave_failures_retained':True", "'raw_NAMDF_formula_all_frame_input_hashes_and_band_dips_replayed':True,'actual_Praat_calls':4,'curve_feature_groups':len(curve_cache),'curve_rows_recomputed':curve_rows")
    text=text.replace("'normalized_PCM_raw_UV0_source_params_frame_centers_checked':True","'normalized_PCM_source_gate_time_and_count_preservation_checked':True")
    text=text.replace("float_precision='round_trip'","float_precision='round_trip'")
    compile(text,str(path),'exec')
    path.write_text(text,encoding='utf-8')


if __name__=='__main__':
    main()
