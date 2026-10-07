import json
import subprocess
from pathlib import Path

import numpy as np

import sptk_adapter as native

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent/'.bt2-tools/sptk-reference'
exe = ROOT/'build-mingw/pitch.exe'
assert exe.exists()
commit = subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
assert commit=='0ebff5a9b1fb5851709130efa1d3efb186ef702a'
keys = ['CMakeLists.txt','LICENSE','src/main/pitch.cc','src/analysis/pitch_extraction.cc',
        'src/analysis/pitch_extraction_by_swipe.cc','src/analysis/pitch_extraction_by_reaper.cc',
        'third_party/SWIPE/swipe.cc','third_party/SWIPE/vector.cc',
        'third_party/REAPER/epoch_tracker/epoch_tracker.cc']
help_result = subprocess.run([str(exe),'-h'],capture_output=True)
help_text = (help_result.stdout+help_result.stderr).decode('utf-8',errors='replace')
assert 'SPTK: version 4.4' in help_text and "SWIPE'" in help_text
tools_root = ROOT.parent
compiler = json.loads((HERE/'results/llvm_mingw_provenance.json').read_text())
cmake = tools_root/'cmake-runtime/cmake/data/bin/cmake.exe'
ninja = tools_root/'ninja-runtime/bin/ninja.exe'
toolchain = {name:{'path':str(path.resolve()),'sha256':native.digest(path),
                  'version':subprocess.check_output([str(path),'--version'],text=True).strip()}
             for name,path in [('cmake',cmake),('ninja',ninja),('clangxx',Path(compiler['clangxx']))]}
cache = (ROOT/'build-mingw/CMakeCache.txt').read_text()
assert 'CMAKE_CXX_FLAGS_RELEASE:STRING=-O3 -DNDEBUG -include algorithm' in cache
assert 'CMAKE_EXE_LINKER_FLAGS:STRING=-static' in cache
assert not subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain','--untracked-files=no'],text=True).strip()
proof = {'version':'4.4','commit':commit,'source_url':'https://github.com/sp-nitech/SPTK',
         'source_root':str(ROOT.resolve()),'exe':str(exe.resolve()),'exe_sha256':native.digest(exe),
         'key_source_sha256':{key:native.digest(ROOT/key) for key in keys},'help':help_text,
         'build_directory':'build-mingw; original MSVC configure failure retained',
         'toolchain':toolchain,'cmake_cache':cache,'cmake_cache_sha256':native.digest(ROOT/'build-mingw/CMakeCache.txt'),
         'configure_generator':'Ninja','build_target':'pitch','parallel_jobs':2,
         'reference_source_clean':True,'build_exit_code':0,
         'compiler_proof_sha256':native.digest(HERE/'results/llvm_mingw_provenance.json'),
         'generator_sha256':native.digest(__file__),'real_wav_read':False}
(HERE/'results/sptk_native_provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
rows = []
for fs in (16000,44100):
    time = np.arange(fs)/fs
    tone = np.sin(2*np.pi*173*time)+.4*np.sin(2*np.pi*346*time)
    tone = tone/np.max(abs(tone))*.75
    for name,audio in [('tone',tone),('silence',np.zeros(fs))]:
        for threshold in (.2,.5):
            times,f0,log = native.pitch(audio,fs,'swipe',threshold)
            valid = f0[f0>0]
            # Keep any valid abstention at the strict threshold; record coverage explicitly.
            if name=='tone' and threshold==.2:
                assert len(valid)>80 and np.max(abs(valid-173))<2
            elif name=='silence':
                assert not len(valid)
            rows.append({'fs':fs,'signal':name,'threshold':threshold,'native_frames':len(f0),
                         'voiced_frames':len(valid),'max_error_hz':float(np.max(abs(valid-173))) if len(valid) else None,'call':log})
probe = {'rows':rows,'real_wav_read':False,'adapter_sha256':native.digest(HERE/'sptk_adapter.py'),
         'generator_sha256':native.digest(__file__),'provenance_sha256':native.digest(HERE/'results/sptk_native_provenance.json')}
(HERE/'results/swipe_synthetic_probe.json').write_text(json.dumps(probe,indent=2)+'\n')
print('PASS SPTK4.4 binary/source identity and eight SWIPE tone/silence probes; no BT2 WAV.')
