# Experiment 24 result: AMDF competing-minimum confidence gate

- Plan: [registered protocol](EXPERIMENT_24_PLAN.md); accepted rollback point `a3b504b` (AMDF + energy gate + median5).
- Implementation commit: `ac1a6be`; script: [experiment_24_amdf_confidence_gate.py](experiment_24_amdf_confidence_gate.py).
- Command: `.venv\Scripts\python.exe working_output\experiment_24_amdf_confidence_gate.py` (Python 3.11.9, NumPy 2.3.5, pandas 3.0.3, scikit-learn 1.9.1).
- Data: four training WAV/LAB files only, frame 25 ms / hop 10 ms. Nested outer LOFO with inner LOFO selecting the margin quantile. The scorer's best AMDF score was parity-checked against the existing implementation; the no-gate outer metrics matched EXP14 on every file. No TEST or Google Drive was used.

| Outer held-out file | Selected gate | Macro F1 | Balanced accuracy | Recall V / UV | F0mean MAE (Hz) | F0std MAE (Hz) | NumF0 | FP SIL |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| phone_F1.wav | none | 0.9141 | 0.9325 | 0.9085 / 0.9565 | 0.815 | 4.926 | 143 | 1 |
| phone_M1.wav | none | 0.8003 | 0.8676 | 0.8320 / 0.9032 | 1.815 | 4.456 | 209 | 0 |
| studio_F1.wav | none | 0.9118 | 0.9675 | 0.9350 / 1.0000 | 1.556 | 4.587 | 115 | 0 |
| studio_M1.wav | none | 0.8323 | 0.9149 | 0.8298 / 1.0000 | 2.654 | 1.601 | 78 | 0 |
| **Mean / total** | **none in 4/4 folds** | **0.8646** | **0.9206** | **0.8763 / 0.9649** | **1.710** | **3.892** | **545** | **1** |

**Decision: reject the confidence gate; retain the existing baseline.** Inner selection chose no gate in all four outer folds. Across inner held-out files, no gate scored mean macro F1 0.8621 and BA 0.9187. The smallest candidate (q=0.10) fell to macro F1 0.7860, BA 0.8739, V recall 0.7828 and rejected 12.75 voiced predictions per inner file on average. This suggests low margins in this sample were strongly associated with true V frames, not just incorrect period choices. The selected outer candidate therefore equals the baseline and does not satisfy the required F0std improvement.

Artifacts: [outer LOFO CSV](experiment_24_outer_lofo.csv), [inner selection CSV](experiment_24_inner_selection.csv), and [summary JSON](experiment_24_summary.json). No notebook or algorithm integration was made. Four-file LOFO is limited internal evidence, not independent validation.
