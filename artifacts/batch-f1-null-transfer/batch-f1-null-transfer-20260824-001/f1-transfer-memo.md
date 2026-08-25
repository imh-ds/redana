# F1 independence null-transfer memo

Run ID: `batch-f1-null-transfer-20260824-001`
Terminal outcome: **PASS**

## Copied reference calibration

- Calibration directory: `artifacts\batch-null-calibration\batch-null-calibration-20260821-001`
- Calibration manifest SHA-256: `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`
- Calibration records SHA-256: `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`
- Copied selected boundary: `0.058242447845091264`

## F1 transfer check

- Fixture and pair: `F1`, `(X1, X2)`
- Adjustment variables: `(X3, X4, X5, X6)` -- signal-free by construction
- Structure: complete mutual independence; no common cause, mediator, collider, or direct edge
- Complete: `True`
- Null-like batches: 87 of 100 (requires 85)
- Low p-values: 53 of 1,000 (allows at most 67)

## Provenance and governance

- F1 records SHA-256: `d01f3ed2f8d2d85f3c0f2cb0ac667880b0880dd285c922a45b0485b95c8db515`
- Manifest-input SHA-256: `3e2fa97cd9b75451449cd8c06515fc1417b28133d16473775cc08eec3246c78e`
This result does not authorize recalibration, alternate fixtures, dependent alternatives, or package work.
Warnings: none
Exceptions: none

Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work.
