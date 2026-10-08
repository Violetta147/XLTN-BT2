"""Algebra on saved H48 metrics only: no audio/inference/parameter selection."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE/'results'


def main():
    source = OUT/'H48_all_files.csv'
    receipt = OUT/'H66_count_budget_audit.json'
    assert not receipt.exists(), 'Completed cached-artifact analysis: do not rerun'
    table = pd.read_csv(source, float_precision='round_trip')
    assert len(table) == 8 and table.file.is_unique and set(table.split) == {'train', 'test'}
    components = table[['F0mean_mape', 'F0std_mape', 'F0num_mape']]
    assert (components >= 0).all().all()
    assert np.allclose(components.mean(axis=1), table.average_mape, rtol=1e-12, atol=1e-12)
    audit = table[['split', 'file', 'F0num', 'F0num_mape']].copy()
    audit['minimum_average_mape_with_fixed_count'] = table.F0num_mape/3
    audit['strict_mean_plus_std_mape_budget'] = 6-table.F0num_mape
    audit['pitch_only_target_algebraically_possible'] = audit.strict_mean_plus_std_mape_budget > 0
    # Nonnegative mean/std errors must have sum strictly below this remaining budget.
    assert (audit.minimum_average_mape_with_fixed_count < 2).all()
    destination = OUT/'H66_fixed_count_budget.csv'
    audit.to_csv(destination, index=False)
    receipt.write_text(json.dumps(dict(status='PASS',scope='algebra on cached H48 accepted pipeline',
        source=str(source.relative_to(HERE)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        output_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),rows=8,
        new_audio_or_test_inference=False,parameters_selected=False,
        statement='Average MAPE=(mean_error+std_error+count_error)/3; fixed count leaves strict budget 6-count_error.',
        limitation='Algebraic feasibility does not prove a signal estimator can attain the required mean/std simultaneously; test has historical exposure.'),indent=2)+'\n',encoding='utf-8')
    print(audit.to_string(index=False))


if __name__ == '__main__':
    main()
