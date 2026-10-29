# Experiment 25 result: spectral-flatness rejection gate

- Preregistered in [plan](EXPERIMENT_25_PLAN.md); accepted rollback point `93dca9c` (AMDF + energy gate + median5).
- Implementation commit: `6e183f9`; parity/empty-F0 handling fix: `f195410`; script: [experiment_25_spectral_flatness_gate.py](experiment_25_spectral_flatness_gate.py).
- Command: `.venv\Scripts\python.exe working_output\experiment_25_spectral_flatness_gate.py` (Python 3.11.9, NumPy 2.3.5, pandas 3.0.3, scikit-learn 1.9.1).
- Data/protocol: nested outer four-fold LOFO with three-fold inner LOFO on four training WAV/LAB files; 25 ms frame, 10 ms hop. The no-gate branch matched EXP24 on all folds and all recorded metrics. No TEST or Google Drive was accessed.

| Outer held-out file | Inner-selected flatness gate | Macro F1 | Balanced accuracy | Recall V / UV | F0mean MAE (Hz) | F0std MAE (Hz) | NumF0 | FP SIL |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| phone_F1.wav | none | 0.9141 | 0.9325 | 0.9085 / 0.9565 | 0.815 | 4.926 | 143 | 1 |
| phone_M1.wav | none | 0.8003 | 0.8676 | 0.8320 / 0.9032 | 1.815 | 4.456 | 209 | 0 |
| studio_F1.wav | none | 0.9118 | 0.9675 | 0.9350 / 1.0000 | 1.556 | 4.587 | 115 | 0 |
| studio_M1.wav | none | 0.8323 | 0.9149 | 0.8298 / 1.0000 | 2.654 | 1.601 | 78 | 0 |
| **Mean / total** | **none in 4/4 folds** | **0.8646** | **0.9206** | **0.8763 / 0.9649** | **1.710** | **3.892** | **545** | **1** |

**Decision: reject the spectral-flatness gate and retain baseline.** Inner LOFO chose no gate in all four outer folds. Pooled over inner held-out files, no gate scored macro F1 0.8621, BA 0.9187, and recall V 0.8724. The least aggressive threshold in the candidate grid, q=0.95, scored 0.7298 macro F1, 0.8378 BA, and 0.6864 recall V, while rejecting an average of 45.75 predicted-voiced frames per inner held-out file. The gate therefore removed many genuine V frames in these folds and did not justify outer evaluation with a nontrivial threshold; the outer nested strategy correctly selected no gate. The registered F0std improvement criterion was not met.

Artifacts: [outer LOFO CSV](experiment_25_outer_lofo.csv), [inner selection CSV](experiment_25_inner_selection.csv), and [summary JSON](experiment_25_summary.json). No notebook or algorithm integration was made. Four-file LOFO is limited internal evidence, not independent validation.
