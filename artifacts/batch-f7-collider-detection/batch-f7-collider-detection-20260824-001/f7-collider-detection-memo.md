# F7 collider detection memo

Run ID: `batch-f7-collider-detection-20260824-001`
Terminal outcome: **PASS**

## Copied reference calibration

- Calibration manifest SHA-256: `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`
- Calibration records SHA-256: `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`
- Frozen detection boundary: `0.058242447845091264`

## Collider detection check

- Fixture and pair: `F7`, `(X1, X2)`
- Adjustment variables: `(X3, X4, X5, X6)`
- X3 is a collider (`X3 = 0.7*X1 + 0.7*X2 + e3`); adjusting for it induces real dependence between X1 and X2, so detection here is the mathematically correct outcome.
- Complete: `True`
- Detected batches: 100 of 100 (requires 85)

## Governance

- Detection records SHA-256: `194e729438b1e9fccb26165d8b911776f6a89184eaaf2f89723945792218beeb`
This result supports detection of one collider-induced dependence only; it makes no general nonlinear-power or package-readiness claim.
It does not authorize recalibration, changed signal strength, a new simulation family, or package work.
Warnings: none
Exceptions: none

Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work.
