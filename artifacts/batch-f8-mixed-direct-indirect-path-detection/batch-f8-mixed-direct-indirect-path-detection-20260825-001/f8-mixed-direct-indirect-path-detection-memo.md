# F8 mixed direct-and-indirect path detection memo

Run ID: `batch-f8-mixed-direct-indirect-path-detection-20260825-001`
Terminal outcome: **PASS**

## Copied reference calibration

- Calibration manifest SHA-256: `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`
- Calibration records SHA-256: `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`
- Frozen detection boundary: `0.058242447845091264`

## Mixed direct-and-indirect path detection check

- Fixture and pair: `F8`, `(X1, X2)`
- Adjustment variables: `(X3, X4, X5, X6)` -- automatically selected, includes the mediator `X3`
- `X3 = 0.7*X1+e3` (mediator) and `X2 = 0.7*X1+0.7*X3+e2`: X1 affects X2 both directly and indirectly through X3, with the mediator inside the automatic adjustment set. This is the eighth and final untested Gate 0 canonical structure.
- Complete: `True`
- Detected batches: 100 of 100 (requires 85)

## Governance

- Detection records SHA-256: `21c91e1edf7b9c6e21b1f037c6420bba80c405cd9e95c5690332e20dfb205629`
This result supports detection of one mixed direct-and-indirect path only; it makes no general power or package-readiness claim.
It does not authorize recalibration, changed signal strength, a new simulation family, or package work.
Warnings: none
Exceptions: none

Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work.
