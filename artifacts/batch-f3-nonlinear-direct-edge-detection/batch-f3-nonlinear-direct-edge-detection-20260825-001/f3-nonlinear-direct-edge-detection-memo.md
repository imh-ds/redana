# F3 nonlinear direct-edge detection memo

Run ID: `batch-f3-nonlinear-direct-edge-detection-20260825-001`
Terminal outcome: **PASS**

## Copied reference calibration

- Calibration manifest SHA-256: `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`
- Calibration records SHA-256: `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`
- Frozen detection boundary: `0.058242447845091264`

## Nonlinear direct-edge detection check

- Fixture and pair: `F3`, `(X1, X2)`
- Adjustment variables: `(X3, X4, X5, X6)` -- signal-free by construction
- X2 is a direct nonlinear function of X1 (`X2 = 0.7*(X1^2-1)+e2`) with no common cause, mediator, or collider; this isolates raw nonlinear-edge detection from F5's adjustment-transfer problem.
- Complete: `True`
- Detected batches: 100 of 100 (requires 85)

## Governance

- Detection records SHA-256: `797590ac2f16fe29f85293395e1f19f0ac230fc58410ae0afa750a6c9a96ea59`
This result supports detection of one raw nonlinear direct edge only; it makes no general nonlinear-power or package-readiness claim.
It does not authorize recalibration, changed signal strength, a new simulation family, or package work.
Warnings: none
Exceptions: none

Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work.
