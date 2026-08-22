# F4 linear residual-null transfer evidence

Run ID: `batch-f4-linear-null-transfer-20260822-001`
Terminal outcome: **PASS**

This immutable transfer study contains 100 batches of 10 F4 replications
(1,000 retained records), each generated and cross-fit residualized at 1,000
rows before dCor with 199 permutations. It ran from source revision
`e16c5cc9a9fc8fa9a6b971d1e9591f5ff66792cc` using the distinct
`batch-f4-linear-null-transfer` seed namespace.

## Frozen reference calibration

- Calibration evidence: [pointer](batch-null-calibration-batch-null-calibration-20260821-001.md)
- Calibration manifest SHA-256: `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`.
- Calibration records SHA-256: `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`.
- Calibration input-manifest SHA-256: `7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c`.
- Copied inclusive median-dCor boundary: `0.058242447845091264`.

The F4 study did not recompute or alter this selection.

## Transfer check

- Fixture and pair: `F4`, `(X1, X3)`; adjustment variables: `(X2, X4, X5, X6)`.
- Complete replications: 1,000 of 1,000; warnings and exceptions: none.
- Null-like batches: 87 of 100 (PASS requires at least 85).
- Low permutation p-values: 56 of 1,000 (PASS allows at most 67).

Both criteria passed, so the terminal outcome is `PASS`.

## Retained artifacts

- [Manifest](../../artifacts/batch-f4-linear-null-transfer/batch-f4-linear-null-transfer-20260822-001/manifest.json)
- [Runner input manifest](../../artifacts/batch-f4-linear-null-transfer/batch-f4-linear-null-transfer-20260822-001/manifest-input.json)
- [Records](../../artifacts/batch-f4-linear-null-transfer/batch-f4-linear-null-transfer-20260822-001/records.csv)
- [Batch summary](../../artifacts/batch-f4-linear-null-transfer/batch-f4-linear-null-transfer-20260822-001/f4-transfer-summary.csv)
- [Owner memo](../../artifacts/batch-f4-linear-null-transfer/batch-f4-linear-null-transfer-20260822-001/f4-transfer-memo.md)
- [Batch-classification plot](../../artifacts/batch-f4-linear-null-transfer/batch-f4-linear-null-transfer-20260822-001/plots/f4-batch-classifications.png)
- [Completion state](../../artifacts/batch-f4-linear-null-transfer/batch-f4-linear-null-transfer-20260822-001/run_state.json)
- [Residual samples](../../artifacts/batch-f4-linear-null-transfer/batch-f4-linear-null-transfer-20260822-001/residual_samples/)
- [Permutation-null arrays](../../artifacts/batch-f4-linear-null-transfer/batch-f4-linear-null-transfer-20260822-001/null_statistics/)

The F4 manifest pins `records.csv` as
`de6324eda4fc9897e7a5320b49c20f939042751d4339889d9d72f3b4ab06bca5` and
`manifest-input.json` as
`ff808366d2a9b6b2397f9f86aecf57b71d1005c54241714fe87ae4e245b0008a`.

This PASS supports the interpretation that the F5 STOP was primarily a
nonlinear residualization-transfer limitation at 1,000 rows, rather than a
general failure of the frozen rule after residualization. It does not authorize
recalibration, an alternate fixture, a dependent alternative, estimator
redesign, a new simulation family, or package work. An owner decision and
independent evidence review are required before any successor work.
