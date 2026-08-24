# F4 residual-link alternative evidence

Run ID: `batch-f4-residual-link-20260822-001`  
Recorded terminal outcome: **PASS**

This immutable clear-signal study contains 100 batches of 10 F4-plus-link
replications (1,000 retained records). Each replication used 1,000 rows,
cross-fit residualization of `(X1, X3)` on `(X2, X4, X5, X6)`, and 199 dCor
permutations. It ran from source revision
`c43ebb7acecf1f416f1571ee03b1e6a189c3d97c` with seed namespace
`batch-f4-residual-link`.

## Frozen parents

- Successful F4-null comparator manifest SHA-256:
  `c96ac45595af6eb2ecefbce1531ed84c5435e4b187f5073d36360ad659b0a44c`.
- Successful F4-null comparator records SHA-256:
  `de6324eda4fc9897e7a5320b49c20f939042751d4339889d9d72f3b4ab06bca5`.
- Reference-calibration manifest SHA-256:
  `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`.
- Reference-calibration records SHA-256:
  `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`.
- Frozen effect-size boundary: `0.058242447845091264`.

Neither the F4-null comparator nor the raw-reference calibration was
recomputed or changed for this study.

## Precommitted detection check

- Complete replications: 1,000 of 1,000; retained warnings and exceptions: none.
- Detected batches: 100 of 100 (PASS requires at least 85).
- A detected batch requires median dCor strictly above the frozen boundary and
  at least 8 of 10 permutation p-values at or below .05.

The recorded run therefore meets the precommitted `PASS` rule. Independent
review remains required before interpretation. A PASS applies only to this one
clear linear residual-link scenario; it makes no weak-effect power,
recalibration, estimator-redesign, or package-readiness claim.

## Retained artifacts

- [Manifest](../../artifacts/batch-f4-residual-link/batch-f4-residual-link-20260822-001/manifest.json)
- [Runner input manifest](../../artifacts/batch-f4-residual-link/batch-f4-residual-link-20260822-001/manifest-input.json)
- [Records](../../artifacts/batch-f4-residual-link/batch-f4-residual-link-20260822-001/records.csv)
- [Detection summary](../../artifacts/batch-f4-residual-link/batch-f4-residual-link-20260822-001/f4-link-summary.csv)
- [Owner memo](../../artifacts/batch-f4-residual-link/batch-f4-residual-link-20260822-001/f4-link-memo.md)
- [Detection plot](../../artifacts/batch-f4-residual-link/batch-f4-residual-link-20260822-001/plots/f4-link-detections.png)
- [Completion state](../../artifacts/batch-f4-residual-link/batch-f4-residual-link-20260822-001/run_state.json)
- [Residual samples](../../artifacts/batch-f4-residual-link/batch-f4-residual-link-20260822-001/residual_samples/)
- [Permutation-null arrays](../../artifacts/batch-f4-residual-link/batch-f4-residual-link-20260822-001/null_statistics/)

The run manifest pins `records.csv` as
`98a02b54636d870b4308e57b477e5723fbc3840cd5fb2e2de72a53da577393b5` and
`manifest-input.json` as
`7fcf98aaffdee00fd7248b105ea523d32218014d351dcede0ac2ad63e8f97795`.
