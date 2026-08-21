# Batch-level null calibration evidence

Run ID: `batch-null-calibration-20260821-001`
Terminal outcome: **READY**

This immutable reference-only calibration contains 100 batches of 10 independent
standard-normal reference replications (1,000 retained records), each using 1,000
evaluation rows and 199 permutations. It ran from source revision
`440b19b6a641eba2a7a98d9c0704fb7c818873e5`.

## Frozen selection

- Guard-passing batches: 100 of 100 (requires at least 90).
- Selected inclusive median-dCor boundary: `0.058242447845091264`.
- Null-like batches at that boundary: 90 of 100.
- Warnings and exceptions: none.

## Retained artifacts

- [Manifest](../../artifacts/batch-null-calibration/batch-null-calibration-20260821-001/manifest.json)
- [Runner input manifest](../../artifacts/batch-null-calibration/batch-null-calibration-20260821-001/manifest-input.json)
- [Records](../../artifacts/batch-null-calibration/batch-null-calibration-20260821-001/records.csv)
- [Batch summary](../../artifacts/batch-null-calibration/batch-null-calibration-20260821-001/batch-summary.csv)
- [Owner memo](../../artifacts/batch-null-calibration/batch-null-calibration-20260821-001/calibration-memo.md)
- [Batch-median plot](../../artifacts/batch-null-calibration/batch-null-calibration-20260821-001/plots/batch-medians.png)
- [Completion state](../../artifacts/batch-null-calibration/batch-null-calibration-20260821-001/run_state.json)

The manifest pins `records.csv` as
`267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5` and
`manifest-input.json` as
`7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c`.

This READY calibration freezes a boundary for an independent review and, only after
that review, a separately authorized confirmation phase. It does not authorize a
confirmation run, F1--F8, residualization, recalibration, estimator redesign, a new
simulation family, or package work.
