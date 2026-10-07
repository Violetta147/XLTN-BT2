import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'AMDF_ANCHOR_LOCAL.ipynb'
    assert not path.exists()
    book=json.loads((HERE/'YAAPT_AMDF_LOCAL.ipynb').read_text(encoding='utf-8'))
    code=[cell for cell in book['cells'] if cell['cell_type']=='code']
    for cell in code:
        cell['source']=cell['source'].replace('H40','H41').replace('yaapt_notebook','amdf_anchor_notebook')
        cell['source']=cell['source'].replace('build_yaapt_notebook','build_amdf_anchor_notebook').replace('execute_yaapt_notebook','execute_amdf_anchor_notebook')
        cell['execution_count']=None
        cell['outputs']=[]
    code[0]['source']=code[0]['source'].replace('import yaapt_reference as reference','import amdf_praat_anchor as reference')
    code[0]['source']=code[0]['source'].replace('yaapt_proof=reference.yaapt_api.metadata()',
        "reference.anchor_api.OUTPUT_PREFIX='amdf_anchor_notebook'\nreference.anchor_api.SOURCE_CACHE.clear()\nreference.anchor_api.CURVE_CACHE.clear()")
    code[0]['source']=code[0]['source'].replace("'; YAAPT port',yaapt_proof['package_version']","'; NAMDF kernel từ notebook frozen'")
    code[1]['source']=code[1]['source'].replace('PASS20 fixed rows','PASS44 fixed rows')
    code[2]['source']=code[2]['source'].replace('len(table)==24','len(table)==48')
    code[3]['source']=code[3]['source'].replace("labels=['Praat .45']+[f'YAAPT{x[\"frame_ms\"]}' for x in registries[family][1:]]",
        "labels=['Praat .30']+[f'w{x[\"amdf_window_ms\"]}/b{x[\"agreement_cents\"]}' for x in registries[family][1:]]")
    code[3]['source']=code[3]['source'].replace("rotation=20","rotation=45,labelsize=8").replace('spectral window ghi trên trục x; TDA35ms giữ.','AMDF window/band ghi trên trục x; gate giữ.')
    code[4]['source']=code[4]['source'].replace("'yaapt_port_commit':yaapt_proof['python_port_commit']",
        "'source_calls':{key[0]+'|'+key[1]:value[2] for key,value in reference.anchor_api.SOURCE_CACHE.items()}")
    code[4]['source']=code[4]['source'].replace('len(native_calls)==16 and len(fit_logs)==24','len(native_calls)==40 and len(fit_logs)==48')
    code[4]['source']=code[4]['source'].replace('PASS24 measured rows: H24 AMDF control4 + H41 fixed16 + nested4.','PASS48 measured rows: H24 AMDF control4 + H41 fixed40 + nested4.')
    code[4]['source']=code[4]['source'].replace('Native/backend16 calls','4 actual Praat calls/40 derived option groups/12 NAMDF feature groups')
    text=[
        '# AMDF candidates dưới gate Praat: tái lập WAV\n\nF0 là tần số cơ bản; V/UV/SIL là hữu thanh/vô thanh/khoảng lặng. NAMDF là AMDF chuẩn hóa theo biên độ trên phần chồng lấp. H41 giữ quyết định hữu thanh củaPraatfiltered.30 và dùng đáyNAMDF gần cao độneo để tinhchỉnhpitch. Mục tiêu mỗifileAverageMAPE≤2%, lỗi trungbình của mean/std(ddof0)/count. LAB chứafile-stat/nhãnđoạn, khôngF0chuẩntừngkhung. Đây là engineeringhypothesis từkernelnotebook, khôngexactAAMDFpaperreplication.',
        '## Fixed: mọi cấu hình đã đăng ký\n\nGrid25/40/55ms×50/100/200cents cùngPraatcontrol. Chọnlocaldipthấpnhấttrongband; tiecents rồiF0. Khôngứngviên, thiếuwindow hoặcflat giữPraat. Window quanhtâmPraat phảiđủaudio; khôngpadding/noise/clip/filter/resamplemới. Allcandidates/parabolicrefine, khôngtop12truncation. Canonical25/10/timealignment giữ; count/VUV/SIL ycontrol. H24AMDFcontrolđượcfit bằngbafilekhác vàtínhlạithựcWAV. Không chọnbesttheochínhfileheld.',
        '## Nested: giữ riêng file được chấm\n\nBa filekhác chọnwindow/band theo minimaxworstfile rồimean/ID; finite/F1/recall/SILguard. Notebook dùngchoiceđãlưucủaH41, không mởgrid/selectionmới. Lịch sửn4 khiếnnestedexploratory, chưa kiểmchứngdữliệumới.',
        '## Thành phần mean/std/count\n\nBa lỗi chia3 cộngthành AverageMAPE. Đường2% ápdụngmỗifile. Không phải MAPE củaF0từngkhung. Fixed vànestedtáchriêng; tấtcảcấuhìnhfailuresgiữ. Count/VUV/SIL giữtheocontrol, chỉ nguồnF0đổi.',
        '## Provenance\n\n4actualPraatcalls,12NAMDFfeaturegroups và40derivedoption-filegroups. Curvesalllags/time/start/frame-inputhash/source/tags/selectedindices giữNPZ/JSON đểverify. NotebooktínhlạitừWAV, khôngcopytable; giữAMPFbaselinegốc.',
        '## Nguồn và giới hạn\n\nAMDF_ANCHOR_SOURCE_NOTE.md mapping côngthứcNAMDFfrozen vàgiớihạnISCAabstractAlignedAMDF2006; không đủcôngthứcAAMDFexact, khôngPDF. CitationScientificAgentSkills/K-Denseworkflow đãghi. H41_REPORT.md/H41_REGISTRATION.md giữmetric/gates; nearPraat khôngGT. Pythonexec/headlessdisplay nguyênnămcodecells, khôngJupyterkernel. Khôngtest/Drive/deeplearning/MCP retry hoặc thayfrozen/originalnotebooks.'
    ]
    markdown=[cell for cell in book['cells'] if cell['cell_type']=='markdown']
    assert len(markdown)==6 and len(code)==5
    for index,cell in enumerate(markdown):
        cell['source']=text[index]+'\n'
        cell['id']=f'amdf-anchor-text-{index}'
    for index,cell in enumerate(code):
        cell['id']=f'amdf-anchor-code-{index}'
        compile(cell['source'],f'AMDF anchorcell{index}','exec')
    book['metadata'].pop('bt2_local_execution',None)
    path.write_text(json.dumps(book,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    executor=(HERE/'execute_yaapt_notebook.py').read_text().replace('YAAPT_AMDF_LOCAL','AMDF_ANCHOR_LOCAL').replace('H40 YAAPT notebook','H41 AMDF anchor notebook')
    (HERE/'execute_amdf_anchor_notebook.py').write_text(executor,encoding='utf-8')
    verifier=(HERE/'verify_yaapt_notebook.py').read_text().replace('YAAPT_AMDF_LOCAL','AMDF_ANCHOR_LOCAL').replace('yaapt_notebook','amdf_anchor_notebook').replace('H40','H41').replace('==24','==48')
    start=verifier.index("    proof=json.loads((HERE/'results/yaapt_source_discovery.json')")
    end=verifier.index("    assert provenance['test_read']",start)
    verifier=verifier[:start]+'''    experiment=json.loads((HERE/'results/H41_experiment.json').read_text())
    assert len(provenance['native_calls'])==40 and len(provenance['source_calls'])==4
    checked_curves=set()
    for identity,call in provenance['native_calls'].items():
        file=identity.split('|')[-1]
        option=identity.split('|')[-2]
        expected=experiment['native_calls'][option+'|'+file]
        assert call['returncode']==0 and call['exe_sha256']==provenance['praat_native_sha256']
        assert call['command']==expected['command'] and call['script_sha256']==digest(call['command'][2])
        for key in ('output_f0_sha256','rule_sha256','source','selected_curve_indices'):
            assert call[key]==expected[key],key
        if call['AMDF_evidence']:
            proof=call['AMDF_evidence']
            assert digest(HERE/proof['path'])==proof['sha256'] and proof['source_sha256']==digest(HERE/'amdf_anchor.py')
            if proof['path'] not in checked_curves:
                fresh=dict(np.load(HERE/proof['path'],allow_pickle=False))
                prior=dict(np.load(HERE/expected['AMDF_evidence']['path'],allow_pickle=False))
                assert set(fresh)==set(prior)
                for key in fresh:
                    if fresh[key].dtype.kind in 'f':
                        assert np.allclose(fresh[key],prior[key],atol=1e-12,equal_nan=True),key
                    else:
                        assert np.array_equal(fresh[key],prior[key]),key
                checked_curves.add(proof['path'])
    assert len(checked_curves)==12
    for identity,call in provenance['source_calls'].items():
        assert call['command']==experiment['source_calls'][identity]['command']
''' +verifier[end:]
    compile(verifier,'verify_amdf_anchor_notebook.py','exec')
    (HERE/'verify_amdf_anchor_notebook.py').write_text(verifier,encoding='utf-8')
    print('Built source-only AMDF anchor notebook/executor/verifier; no measurement.')


if __name__=='__main__':
    main()
