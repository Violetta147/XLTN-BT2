# Experiment 23 result: median7 F0 smoothing

- Preregistered in [plan](EXPERIMENT_23_PLAN.md); rollback/accepted baseline: `6405f05`, AMDF + energy gate + median5.
- Implementation: [script](experiment_23_median7_f0.py), committed separately as `3a5dc24`.
- Command: `.venv\Scripts\python.exe working_output\experiment_23_median7_f0.py` (Python 3.11.9, NumPy 2.3.5, pandas 3.0.3, scikit-learn 1.9.1).
- Data/protocol: four `TinHieuHuanLuyen` WAV/LAB files; outer leave-one-training-file-out; pitch and energy thresholds refit on the other three files. Frame 25 ms, hop 10 ms. Same held-out predictions compared under median5 and median7. No TEST files accessed.

| Held-out file | F0mean MAE median5 → median7 (Hz) | F0std MAE median5 → median7 (Hz) | Macro F1 | Balanced accuracy | Recall V / UV | NumF0 | FP SIL |
|---|---:|---:|---:|---:|---:|---:|---:|
| phone_F1.wav | 2.430 → 2.686 | 7.552 → 8.817 | 0.9141 | 0.9325 | 0.9085 / 0.9565 | 143 | 1 |
| phone_M1.wav | 1.827 → 2.205 | 4.753 → 4.318 | 0.8003 | 0.8676 | 0.8320 / 0.9032 | 209 | 0 |
| studio_F1.wav | 1.521 → 1.294 | 4.524 → 4.556 | 0.9118 | 0.9675 | 0.9350 / 1.0000 | 115 | 0 |
| studio_M1.wav | 2.686 → 2.607 | 1.609 → 1.562 | 0.8323 | 0.9149 | 0.8298 / 1.0000 | 78 | 0 |
| **Mean / total** | **2.116 → 2.198** | **4.609 → 4.813** | **0.8646** | **0.9206** | **0.8763 / 0.9649** | **545** | **1** |

**Decision: reject median7; retain median5.** The registered requirement was a ≥0.25 Hz mean F0std MAE improvement; instead F0std MAE worsened by 0.204 Hz. F0mean worsened by 0.082 Hz, within its tolerance, but one file's F0mean MAE worsened by 1.264 Hz, exceeding the per-file limit. Classification and NumF0 stayed identical as expected because smoothing only changes F0 values, not predictions. This is a failed four-file training-only experiment, not independent validation.

Reproducible outputs: [per-file CSV](experiment_23_lofo.csv) and [summary JSON](experiment_23_summary.json). No algorithm/notebook integration was made.
