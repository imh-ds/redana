# F6 residual-null transfer memo

Run ID: `batch-f6-null-transfer-20260824-001`
Terminal outcome: **PASS**

## Copied reference calibration

- Calibration directory: `artifacts\batch-null-calibration\batch-null-calibration-20260821-001`
- Calibration manifest SHA-256: `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`
- Calibration records SHA-256: `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`
- Copied selected boundary: `0.058242447845091264`

## F6 transfer check

- Fixture and pair: `F6`, `(X1, X3)`
- Adjustment variables: `(X2, X4, X5, X6)`
- Structure: nonlinear indirect path (X1 -> X2 nonlinearly -> X3 linearly), no direct edge
- Complete: `True`
- Null-like batches: 90 of 100 (requires 85)
- Low p-values: 53 of 1,000 (allows at most 67)

## Provenance and governance

- F6 records SHA-256: `8761d6ec94d4ea18a0327b7dc07227340809e33a19f568a44620e0a3a75d1765`
- Manifest-input SHA-256: `bc504840f38a76306d1277db982cc2754c48d89249aa20a9190ecd9145f272da`
This result does not authorize recalibration, alternate fixtures, dependent alternatives, or package work.
Warnings: none
Exceptions: none

Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work.
