# F5 residual-null transfer evidence

Run ID: `batch-f5-null-transfer-20260821-001`
Terminal outcome: **STOP**

This immutable transfer study contains 100 batches of 10 F5 replications
(1,000 retained records), each generated and cross-fit residualized at 1,000
rows before dCor with 199 permutations. It ran from source revision
`0953f4f61b41f973299f2f0a9dfb936b7f19cc67` using the distinct
`batch-f5-null-transfer` seed namespace.

## Frozen reference calibration

- Calibration evidence: [pointer](batch-null-calibration-batch-null-calibration-20260821-001.md)
- Calibration manifest SHA-256: `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`.
- Calibration records SHA-256: `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`.
- Calibration input-manifest SHA-256: `7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c`.
- Copied inclusive median-dCor boundary: `0.058242447845091264`.

The F5 study did not recompute or alter this selection.

## Transfer check

- Fixture and pair: `F5`, `(X1, X2)`; adjustment variables: `(X3, X4, X5, X6)`.
- Complete replications: 1,000 of 1,000; warnings and exceptions: none.
- Null-like batches: 74 of 100 (PASS requires at least 85).
- Low permutation p-values: 81 of 1,000 (allows at most 67).

The low-p-value cap has strict precedence, so the terminal outcome is `STOP`.

## Retained artifacts

- [Manifest](../../artifacts/batch-f5-null-transfer/batch-f5-null-transfer-20260821-001/manifest.json)
- [Runner input manifest](../../artifacts/batch-f5-null-transfer/batch-f5-null-transfer-20260821-001/manifest-input.json)
- [Records](../../artifacts/batch-f5-null-transfer/batch-f5-null-transfer-20260821-001/records.csv)
- [Batch summary](../../artifacts/batch-f5-null-transfer/batch-f5-null-transfer-20260821-001/f5-transfer-summary.csv)
- [Owner memo](../../artifacts/batch-f5-null-transfer/batch-f5-null-transfer-20260821-001/f5-transfer-memo.md)
- [Batch-classification plot](../../artifacts/batch-f5-null-transfer/batch-f5-null-transfer-20260821-001/plots/f5-batch-classifications.png)
- [Completion state](../../artifacts/batch-f5-null-transfer/batch-f5-null-transfer-20260821-001/run_state.json)
- [Residual samples](../../artifacts/batch-f5-null-transfer/batch-f5-null-transfer-20260821-001/residual_samples/)
- [Permutation-null arrays](../../artifacts/batch-f5-null-transfer/batch-f5-null-transfer-20260821-001/null_statistics/)

The F5 manifest pins `records.csv` as
`3f38ac7f324c597cf13b84006cf1af35fbce0fb30b497ef2629b29b79a7fee09` and
`manifest-input.json` as
`b16367ef572f906df2653447558e31047e0cda0943d3d774725546f213902251`.

This STOP does not authorize recalibration, an alternate fixture, a dependent
alternative, estimator redesign, a new simulation family, or package work. An
owner decision and independent evidence review are required before any
successor work.
