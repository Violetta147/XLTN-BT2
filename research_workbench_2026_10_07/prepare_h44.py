from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    targets=[HERE/name for name in ('amdf_soft_spectral.py','amdf_soft_spectral_controller.py','verify_amdf_soft_spectral.py')]
    assert not any(p.exists() for p in targets)
    rule=(HERE/'amdf_pitch_spectral.py').read_text().replace('H43','H44')
    start=rule.index('def route(')
    end=rule.index('\n\ndef load_evidence',start)
    rule=rule[:start]+'''def weight(ratio, option, gate):
    if option['method'] in ('control','fixed_window'):
        return 0.
    if not np.isfinite(ratio) or ratio > .05:
        return 0.
    if option['method']=='spectral_window':
        return float(gate>=option['minimum_gate_hz'])
    assert option['method']=='soft_spectral'
    return float(np.clip((gate-option['center_hz'])/option['width_hz']+.5,0,1))


def blend(short,long,alpha):
    if alpha==0:
        return short
    if alpha==1:
        return long
    return float(short*2**(alpha*np.log2(long/short)))
''' +rule[end:]
    start=rule.index('def extract(')
    rule=rule[:start]+'''def extract(item, audio, option):
    evidence=load_evidence(item,audio)
    times,gate=evidence['times'],evidence['gate']
    frequency=gate.copy()
    values={w:gate.copy() for w in (25,40)}
    indices={w:np.full(len(gate),-1,dtype=int) for w in (25,40)}
    tags={w:np.where(gate>0,'praat_control','unvoiced').astype('<U40') for w in (25,40)}
    alpha=np.zeros(len(gate))
    for i in np.flatnonzero((gate>=70)&(gate<=400)):
        for w in (25,40):
            data=evidence['data'][w]
            curve=data['curve'][i]
            if not np.isfinite(curve).all():
                tags[w][i]='praat_window_unsupported'
                continue
            candidates,dips,lag_indices=anchor.candidates(data['lags'],curve,item['fs'])
            values[w][i],tags[w][i],chosen=anchor.choose(gate[i],candidates,dips,200)
            if chosen>=0:
                indices[w][i]=lag_indices[chosen]
        if option['method']=='control':
            continue
        alpha[i]=weight(evidence['ratio'][i],option,gate[i])
        frequency[i]=blend(values[25][i],values[40][i],alpha[i])
    pred=(frequency>=70)&(frequency<=400)
    assert np.array_equal(pred,(gate>=70)&(gate<=400))
    original=SOURCE_CACHE[('praat7_filtered_v0.3',item['file'])][2]
    log=dict(original,engine='H44 soft spectral NAMDF blend',historical_native_call=True,new_native_call=False,
             spectral_evidence=evidence['proof'],weights40=alpha.tolist(),
             candidate_f0={str(w):values[w].tolist() for w in (25,40)},
             candidate_indices={str(w):indices[w].tolist() for w in (25,40)},
             candidate_tags={str(w):tags[w].tolist() for w in (25,40)},
             rule_sha256=audit.digest(__file__),output_f0_sha256=hashlib.sha256(frequency.tobytes()).hexdigest())
    return dict(item,times=times,preprocess=option['id'],native_pred=pred,native_f0=np.where(pred,frequency,np.nan),
                raw_native_frequency=frequency,raw_native_voiced=frequency>0,native_call=log,
                range_rejected_frames=int(((frequency>0)&~pred).sum()))


def check():
    cases=[]
    for center in (140,170,200):
        for width in (20,40):
            option={'method':'soft_spectral','center_hz':center,'width_hz':width}
            for gate,expected in ((center-width/2-1,0),(center-width/2,0),(center,.5),(center+width/2,1),(center+width/2+1,1)):
                assert weight(.05,option,gate)==expected
                assert weight(.05+1e-9,option,gate)==0
                assert weight(np.nan,option,gate)==0
            assert blend(100.,200.,0)==100 and blend(100.,200.,1)==200
            assert np.isclose(blend(100.,200.,.5),np.sqrt(20000),atol=1e-12)
            assert all(100<=blend(100.,200.,a)<=200 for a in np.linspace(0,1,11))
            cases.append(dict(center_hz=center,width_hz=width))
    assert weight(.01,{'method':'spectral_window','minimum_gate_hz':170},170)==1
    assert weight(.01,{'method':'spectral_window','minimum_gate_hz':170},169.999)==0
    for fs in (16000,44100):
        t=np.arange(round(fs*.04))/fs
        low=.2*np.sin(2*np.pi*200*t)
        assert high_frequency_ratio(low,fs)<1e-5
        assert high_frequency_ratio(.2*np.sin(2*np.pi*2000*t),fs)>.999
        assert np.isnan(high_frequency_ratio(np.zeros(len(t)),fs))
        assert np.isclose(high_frequency_ratio(low*3+.037,fs),high_frequency_ratio(low,fs),atol=1e-14)
    audit.json_write(HERE/'results/H44_precheck.json',{'synthetic_cases':cases,'rule_sha256':audit.digest(__file__),
                     'uses_BT2_WAV':False,'new_native_calls':0,'blend':'log2 frequency interpolation; exact endpoints',
                     'ratio_threshold':.05,'band_cents':200})
    print('PASS soft weights/boundaries/NaN/log-blend/endpoints/range and synthetic FFT checks')
'''
    targets[0].write_text(rule,encoding='utf-8')
    runner=(HERE/'amdf_pitch_spectral_controller.py').read_text().replace('H43','H44').replace('amdf_pitch_spectral_controller.py','amdf_soft_spectral_controller.py')
    runner=runner.replace('import amdf_pitch_spectral as anchor_api','import amdf_soft_spectral as anchor_api').replace("HERE / 'amdf_pitch_spectral.py'","HERE / 'amdf_soft_spectral.py'")
    start=runner.index('def registry(')
    end=runner.index('\n\ndef feature_key',start)
    runner=runner[:start]+'''def registry(family):
    assert family=='H44'
    base={'frame_ms':3000/70,'hop_ms':10,'pitch_frame_ms':40}
    return [dict(base,id='praat7_filtered_v0.3',method='control',voicing_threshold=.3),
            dict(base,id='amdf_anchor_w25_b200',method='fixed_window',amdf_window_ms=25),
            dict(base,id='amdf_pitch_spectral_p170',method='spectral_window',minimum_gate_hz=170,hf_threshold=.05)]+[
        dict(base,id=f'amdf_soft_c{center}_w{width}',method='soft_spectral',center_hz=center,width_hz=width,hf_threshold=.05)
        for center in (140,170,200) for width in (20,40)]
''' +runner[end:]
    runner=runner.replace('40916e3','29f712a')
    runner=runner.replace('NAMDF pitch-conditioned spectral window controller under fixed Praat filtered .30 gate','Soft NAMDF frequency interpolation with spectral and pitch evidence')
    runner=runner.replace('Chọn cửa sổ NAMDF theo phổ và cao độ','Trộn mềm NAMDF25/40ms theo phổ và cao độ')
    runner=runner.replace('Dùng40ms khi tỷ lệ≤.05 vàgateF0≥ngưỡng0/140/170/200Hz; còn lại25ms, undefined dùng25ms.',
        'Nếuratio≤.05, alpha40=clip((gateF0−center)/width+.5,0,1), cònlại0; F0=f25*2**(alpha*log2(f40/f25)), exactendpoints. Center140/170/200Hz,width20/40Hz. H43hard170ablation giữ.')
    runner=runner.replace('H44_SOURCE_NOTE.md','H44_REGISTRATION.md')
    targets[1].write_text(runner,encoding='utf-8')
    verifier=(HERE/'verify_amdf_pitch_spectral.py').read_text().replace('H43','H44').replace('amdf_pitch_spectral.py','amdf_soft_spectral.py')
    verifier=verifier.replace("len(result['native_calls'])==28","len(result['native_calls'])==36")
    start=verifier.index('            output=gate.copy()')
    end=verifier.index('            actual=group.raw_f0_hz.to_numpy()',start)
    verifier=verifier[:start]+'''            output=gate.copy()
            candidates={w:gate.copy() for w in (25,40)}
            selected={w:np.full(len(gate),-1,dtype=int) for w in (25,40)}
            tags={w:np.where(gate>0,'praat_control','unvoiced').astype('<U40') for w in (25,40)}
            alpha=np.zeros(len(gate))
            for i in np.flatnonzero((gate>=70)&(gate<=400)):
                for w in (25,40):
                    data=curves[w]
                    candidates[w][i],tags[w][i],selected[w][i]=independent_pick(data['curve'][i],data['lags'],fs,gate[i])
                if option['method']=='control':
                    continue
                if option['method']=='fixed_window' or not np.isfinite(ratio[i]) or ratio[i]>.05:
                    a=0.
                elif option['method']=='spectral_window':
                    a=float(gate[i]>=170)
                else:
                    lower=option['center_hz']-option['width_hz']/2
                    upper=option['center_hz']+option['width_hz']/2
                    a=0. if gate[i]<=lower else 1. if gate[i]>=upper else (gate[i]-lower)/(upper-lower)
                alpha[i]=a
                s,l=candidates[25][i],candidates[40][i]
                output[i]=s if a==0 else l if a==1 else 2**((1-a)*np.log2(s)+a*np.log2(l))
''' +verifier[end:]
    start=verifier.index("            assert call['source']==tags.tolist()")
    end=verifier.index("            assert call['output_f0_sha256']",start)
    verifier=verifier[:start]+'''            np.testing.assert_allclose(call['weights40'],alpha,atol=1e-12)
            for w in (25,40):
                np.testing.assert_allclose(call['candidate_f0'][str(w)],candidates[w],atol=1e-10)
                assert call['candidate_tags'][str(w)]==tags[w].tolist()
                assert call['candidate_indices'][str(w)]==selected[w].tolist()
''' +verifier[end:]
    verifier=verifier.replace("('praat7_filtered_v0.3','amdf_anchor_w25_b200','amdf_anchor_w40_b200')","('praat7_filtered_v0.3','amdf_anchor_w25_b200')")
    start=verifier.index('    old_h42=')
    end=verifier.index('    fits=',start)
    verifier=verifier[:start]+'''    old_h43=pd.read_csv(HERE/'results/H43_fixed_lofo.csv').query("option_id=='amdf_pitch_spectral_p170'").set_index('file').sort_index()
    np.testing.assert_allclose(fixed.loc['amdf_pitch_spectral_p170'].sort_index()[keys],old_h43[keys],atol=1e-8)
''' +verifier[end:]
    verifier=verifier.replace("'H42_zero_pitch_floor_parity':True","'H43_hard_pitch_condition_parity':True")
    targets[2].write_text(verifier,encoding='utf-8')
    for p in targets:
        compile(p.read_text(encoding='utf-8'),str(p),'exec')
    print('Built H44 source and independent verifier; no BT2 measurement')


if __name__=='__main__':
    main()
