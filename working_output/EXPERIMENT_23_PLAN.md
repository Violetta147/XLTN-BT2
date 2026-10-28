# Experiment 23: evaluate median7 F0 smoothing

- Accepted rollback point before this experiment: `6405f05` (baseline remains AMDF + energy gate + median5; EXP22 was rejected).
- Question: can a centered 7-frame median within predicted-voiced runs improve F0 stability beyond the accepted median5 without materially changing F0mean accuracy?
- Hypothesis: median7 lowers mean per-file F0std MAE by at least 0.25 Hz versus median5, while increasing mean F0mean MAE by no more than 0.10 Hz.
- Single variable: smoothing window 5 → 7 frames. Keep the AMDF estimator, energy and pitch thresholds, 25 ms frame, 10 ms hop, frame decisions, valid-F0 handling, and metric definitions fixed. For each predicted-voiced run of length at least 7, replace only interior F0 values having a complete centered 7-value window; preserve the first/last 3 values and runs shorter than 7. Never smooth across a non-voiced frame.
- Evaluation: training-only outer LOFO on the four training files; refit pitch and energy thresholds on the other three training files in each fold. Evaluate median5 and median7 on the same held-out file and predictions. Do not inspect or use TEST.
- Keep median7 as an experiment candidate only if all are true: (1) mean outer F0std MAE improves by at least 0.25 Hz, (2) mean outer F0mean MAE worsens by at most 0.10 Hz, (3) no held-out file's F0mean or F0std MAE worsens by more than 1.0 Hz, and (4) prediction masks and NumF0 match exactly. Otherwise record the result as failed and retain the accepted baseline.
- Report per-file and mean F0mean/F0std MAE plus macro F1, recall V/UV, balanced accuracy, NumF0, and FP_SIL for parity. The four-file LOFO remains limited evidence, not independent external validation.
- Implementation/run is a separate commit after this preregistration. Record exact command, input files, environment, and outputs in the result report.
