# F2 linear direct-edge detection memo

Run ID: `batch-f2-linear-direct-edge-detection-20260825-001`
Terminal outcome: **PASS**

## Copied reference calibration

- Calibration manifest SHA-256: `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`
- Calibration records SHA-256: `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`
- Frozen detection boundary: `0.058242447845091264`

## Linear direct-edge detection check

- Fixture and pair: `F2`, `(X1, X2)`
- Adjustment variables: `(X3, X4, X5, X6)` -- signal-free by construction
- X2 is a direct linear function of X1 (`X2 = 0.7*X1+e2`) with no common cause, mediator, or collider; this completes the direct-edge pair alongside F3's nonlinear direct edge, both under inert adjustment.
- Complete: `True`
- Detected batches: 100 of 100 (requires 85)

## Governance

- Detection records SHA-256: `e84d883942b042917eb33772e9a41826a6022469a689fd1f011f209b023f004e`
This result supports detection of one raw linear direct edge only; it makes no general linear-power or package-readiness claim.
It does not authorize recalibration, changed signal strength, a new simulation family, or package work.
Warnings: none
Exceptions: none

Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work.
