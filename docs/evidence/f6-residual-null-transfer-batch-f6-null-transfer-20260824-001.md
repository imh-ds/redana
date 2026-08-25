# F6 residual-null transfer evidence

Run ID: `batch-f6-null-transfer-20260824-001`
Terminal outcome: **PASS**

This immutable transfer study contains 100 batches of 10 F6 replications
(1,000 retained records), each generated and cross-fit residualized at
1,000 rows before dCor with 199 permutations, using the unmodified
general-purpose spline/Ridge residualizer (the same one already used for
F4 and originally F5 -- not the F5 quadratic-repair basis). It ran from
source revision `de25c2086d5e5b4a37dd42a671e432f4d88152d9` using the
distinct `batch-f6-null-transfer` seed namespace.

## Frozen reference calibration

- Calibration directory:
  `artifacts/batch-null-calibration/batch-null-calibration-20260821-001`
- Calibration manifest SHA-256:
  `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`
- Calibration records SHA-256:
  `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`
- Calibration input-manifest SHA-256:
  `7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c`
- Copied inclusive median-dCor boundary: `0.058242447845091264`

The F6 study did not recompute or alter this selection.

## Transfer check

- Fixture and pair: `F6`, `(X1, X3)`; adjustment variables:
  `(X2, X4, X5, X6)`.
- Structure: nonlinear indirect path -- `X1 -> X2` nonlinear
  (`X2 = 0.7*(X1^2-1)+e2`), `X2 -> X3` linear (`X3 = 0.7*X2+e3`) -- no
  direct `X1`-`X3` edge.
- Complete replications: 1,000 of 1,000; warnings and exceptions: none.
- Null-like batches: 90 of 100 (PASS requires at least 85).
- Low permutation p-values: 53 of 1,000 (PASS allows at most 67).

Both criteria passed, so the terminal outcome is `PASS`.

## Independent raw recomputation

A separate verifier script did not import
`research.gate0.f6_transfer_runner`, `research.gate0.f6_transfer_report`,
or `research.gate0.batch_null_policy`. It re-derived every fixture/
residual/permutation seed from the frozen identity string, recomputed
observed dCor and all 199 permutation values directly from the retained
1,000-row residual CSVs and null arrays for every one of the 1,000 cells,
recomputed SHA-256 for the current run and the calibration parent, and
reapplied the null-like/p-guard rule from raw values. Results:

- Records: 1,000; unique `(batch, replication)` identities: 1,000; exact
  grid; zero duplicates.
- Frozen record identity (`F6`, `X1`, `X3`, `f6-null-transfer`, run ID,
  seed namespace): exact for all 1,000 records.
- Seed re-derivation: zero mismatches across all 3,000 seed values.
- Residual/null shape and finiteness: zero failures across 1,000 files
  each.
- Observed dCor and permutation-null recomputation: zero mismatches.
- Current and calibration-parent SHA-256: match the manifest exactly.
- Independently recomputed null-like batch count: 90 (matches manifest).
- Independently recomputed low-p-value count: 53 (matches manifest).
- Independent terminal outcome: `PASS` (matches manifest and run state
  exactly).

## Retained artifacts

- [Manifest](../../artifacts/batch-f6-null-transfer/batch-f6-null-transfer-20260824-001/manifest.json)
- [Runner input manifest](../../artifacts/batch-f6-null-transfer/batch-f6-null-transfer-20260824-001/manifest-input.json)
- [Records](../../artifacts/batch-f6-null-transfer/batch-f6-null-transfer-20260824-001/records.csv)
- [Batch summary](../../artifacts/batch-f6-null-transfer/batch-f6-null-transfer-20260824-001/f6-transfer-summary.csv)
- [Owner memo](../../artifacts/batch-f6-null-transfer/batch-f6-null-transfer-20260824-001/f6-transfer-memo.md)
- [Batch-classification plot](../../artifacts/batch-f6-null-transfer/batch-f6-null-transfer-20260824-001/plots/f6-batch-classifications.png)
- [Completion state](../../artifacts/batch-f6-null-transfer/batch-f6-null-transfer-20260824-001/run_state.json)
- [Residual samples](../../artifacts/batch-f6-null-transfer/batch-f6-null-transfer-20260824-001/residual_samples/)
- [Permutation-null arrays](../../artifacts/batch-f6-null-transfer/batch-f6-null-transfer-20260824-001/null_statistics/)

## Interpretation and governance

Unlike F5 (a nonlinear *common cause*, where the same general-purpose
residualizer STOPped and needed a structure-matched repair), F6's
nonlinear *mediator* structure is handled correctly by the unmodified
general-purpose residualizer with no repair required. This is a genuinely
informative Gate 0 result: nonlinearity's effect on this workflow depends
on *where* it sits in the causal structure, not just whether it is present
at all.

This PASS supports only that the general-purpose spline/Ridge residualizer
correctly nulls this one nonlinear indirect-path structure at the frozen
1,000-row dimensions. It does not authorize recalibration, an alternate
fixture, a dependent alternative, estimator redesign, a new simulation
family, or package work. Per the design's governance section, no F6 repair
work is needed or authorized -- a repair is only relevant on `NARROW`/
`STOP`, which did not occur. Moving to the next untested Gate 0 canonical
structure remains a separate, later owner decision.
