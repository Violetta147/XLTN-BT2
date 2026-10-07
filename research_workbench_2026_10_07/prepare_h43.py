from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    rule=HERE/'amdf_pitch_spectral.py'
    runner=HERE/'amdf_pitch_spectral_controller.py'
    verifier=HERE/'verify_amdf_pitch_spectral.py'
    assert not any(p.exists() for p in (rule,runner,verifier))
    text=(HERE/'amdf_spectral.py').read_text().replace('H42','H43')
    text=text.replace('def route(ratio, option):','def route(ratio, option, gate):')
    text=text.replace("return 40 if np.isfinite(ratio) and ratio <= option['hf_threshold'] else 25",
                      "return 40 if np.isfinite(ratio) and ratio <= option['hf_threshold'] and gate >= option['minimum_gate_hz'] else 25")
    text=text.replace("route(evidence['ratio'][i],option)","route(evidence['ratio'][i],option,gate[i])")
    start=text.index('def check():')
    text=text[:start]+'''def check():
    tests=[]
    for fs in (16000,44100):
        t=np.arange(round(fs*.040))/fs
        low=.2*np.sin(2*np.pi*200*t)
        high=.2*np.sin(2*np.pi*2000*t)
        lr,hr=high_frequency_ratio(low,fs),high_frequency_ratio(high,fs)
        assert lr<1e-5 and hr>.999
        assert np.isnan(high_frequency_ratio(np.zeros(len(t)),fs))
        assert np.isclose(high_frequency_ratio(low+.037,fs),lr,atol=1e-14)
        assert np.isclose(high_frequency_ratio(low*3,fs),lr,atol=1e-14)
        for floor in (0,140,170,200):
            option={'method':'spectral_window','hf_threshold':.05,'minimum_gate_hz':floor}
            assert route(lr,option,floor)==40
            assert route(lr,option,floor-1e-9)==25
            assert route(hr,option,300)==25 and route(np.nan,option,300)==25
            assert route(.05,option,300)==40 and route(.05+1e-9,option,300)==25
        tests.append({'fs':fs,'low_ratio':lr,'high_ratio':hr})
    audit.json_write(HERE/'results/H43_precheck.json',{'synthetic_tests':tests,'rule_sha256':audit.digest(__file__),
                     'uses_BT2_WAV':False,'new_native_calls':0,'cutoff_hz':1000,'window_ms':40,
                     'hf_threshold':.05,'minimum_gate_hz_grid':[0,140,170,200]})
    print('PASS synthetic spectral calculation, pitch condition, equality/NaN boundaries and gain/DC invariance')
'''
    rule.write_text(text,encoding='utf-8')
    text=(HERE/'amdf_spectral_controller.py').read_text().replace('H42','H43').replace('amdf_spectral_controller.py','amdf_pitch_spectral_controller.py')
    text=text.replace('import amdf_spectral as anchor_api','import amdf_pitch_spectral as anchor_api')
    start=text.index('def registry(')
    end=text.index('\n\ndef feature_key',start)
    text=text[:start]+'''def registry(family):
    assert family=='H43'
    return [{'id':'praat7_filtered_v0.3','frame_ms':3000/70,'hop_ms':10,'pitch_frame_ms':3000/70,
             'method':'control','voicing_threshold':.3}]+[
        {'id':f'amdf_anchor_w{window}_b200','frame_ms':3000/70,'hop_ms':10,'pitch_frame_ms':window,
         'method':'fixed_window','amdf_window_ms':window} for window in (25,40)]+[
        {'id':f'amdf_pitch_spectral_p{floor:03d}','frame_ms':3000/70,'hop_ms':10,
         'pitch_frame_ms':40,'method':'spectral_window','hf_threshold':.05,'minimum_gate_hz':floor}
        for floor in (0,140,170,200)]
''' +text[end:]
    text=text.replace("HERE / 'amdf_spectral.py'","HERE / 'amdf_pitch_spectral.py'")
    text=text.replace('18fe81a','40916e3')
    text=text.replace('NAMDF spectral window controller under fixed Praat filtered .30 gate','NAMDF pitch-conditioned spectral window controller under fixed Praat filtered .30 gate')
    text=text.replace('Chọn cửa sổ NAMDF theo năng lượng phổ','Chọn cửa sổ NAMDF theo phổ và cao độ')
    text=text.replace('Tỷ lệ thấp dùng40ms, còn lại25ms; undefined dùng25ms.',
                      'Dùng40ms khi tỷ lệ≤.05 vàgateF0≥ngưỡng0/140/170/200Hz; còn lại25ms, undefined dùng25ms.')
    text=text.replace('AMDF_SPECTRAL_SOURCE_NOTE.md','H43_SOURCE_NOTE.md')
    runner.write_text(text,encoding='utf-8')
    text=(HERE/'verify_amdf_spectral.py').read_text().replace('H42','H43').replace('amdf_spectral.py','amdf_pitch_spectral.py')
    text=text.replace("ratio[i]<=option['hf_threshold'] else 25)","ratio[i]<=option['hf_threshold'] and gate[i]>=option['minimum_gate_hz'] else 25)")
    verifier.write_text(text,encoding='utf-8')
    for path in (rule,runner,verifier):
        compile(path.read_text(encoding='utf-8'),str(path),'exec')
    print('Built H43 rule/runner/verifier, no BT2 measurement')


if __name__=='__main__':
    main()
