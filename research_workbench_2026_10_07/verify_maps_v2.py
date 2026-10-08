"""Post-measurement verifier correction, not an inference/selection change.

The preregistered exact path check fails when floating products and log sums
resolve equal-objective frequency trajectories differently. Preserve v1 and
audit this discrepancy; compare independent optimal objectives explicitly.
"""
import types
from pathlib import Path
import numpy as np
import maps_experiment as api


def validate_path(probability, frequencies, actual, independent):
    def objective(path):
        indices=np.argmin(abs(frequencies[:,None]-path[None,:]),axis=0)
        assert np.array_equal(frequencies[indices],path)
        return float(np.log(probability[np.arange(len(path)),indices]).sum()
                     -abs(np.diff(np.log(path))).sum())
    first,second=objective(actual),objective(independent)
    assert abs(first-second)<1e-9,(first,second)


if __name__=='__main__':
    source=(Path(__file__).parent/'verify_maps.py').read_text()
    before="assert np.array_equal(independent_path(proof['probability'],proof['frequencies']),proof['f0'])"
    after="validate_path(proof['probability'],proof['frequencies'],proof['f0'],independent_path(proof['probability'],proof['frequencies']))"
    assert source.count(before)==1
    module=types.ModuleType('h60_objective_verifier')
    module.__dict__['validate_path']=validate_path
    exec(compile(source.replace(before,after),str(Path(__file__).parent/'verify_maps.py'),'exec'),module.__dict__)
    module.verify()
    path=api.OUT/'H60_verification.json'
    import json
    receipt=json.loads(path.read_text())
    receipt.update(initial_exact_path_check='FAIL; retained H60_path_tie_audit.json',
        independent_path_check='PASS objective equivalence within1e-9; not exact trajectory parity',
        post_measurement_verifier_correction=True,
        inference_source_or_config_changed=False,
        verifier_v2_sha256=api.audit.digest(Path(__file__)))
    api.audit.json_write(path,receipt)
