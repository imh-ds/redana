# F5 explicit-quadratic repair memo

Run ID: `batch-f5-quadratic-repair-20260824-001`
Terminal outcome: **PASS**

## Frozen basis and parents

- Basis: raw value followed by its square for each adjustment variable
- Splines and interactions: none
- Copied raw-calibration boundary: `0.058242447845091264`
- Calibration manifest SHA-256: `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`
- Original F5 STOP manifest SHA-256: `521f35953929d46670eb90687e6a4645684f335d878b90090029c31d87c8dce2`
- Original F5 outcome: `STOP` (74 null-like batches; 81 low p-values)

## Frozen confirmation rule

- Complete: `True`
- Null-like batches: 90 of 100 (requires 85)
- Low p-values: 44 of 1,000 (allows at most 67)

## Scope and governance

- Repair records SHA-256: `f4fbf588fdd66198fcbce18fdb0031f41e4d42787922bfa4cdd1f4a745277836`
A PASS supports only that this explicit raw-plus-square basis repairs the prescribed F5 quadratic null under this frozen 1,000-row procedure.
It does not establish general nonlinear robustness or authorize tuning, a matched alternative, recalibration, or package work.
Warnings: none
Exceptions: none

Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work.
