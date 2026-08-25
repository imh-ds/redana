# F1 independence null-transfer evidence

Run ID: `batch-f1-null-transfer-20260824-001`
Terminal outcome: **PASS**

This immutable transfer study contains 100 batches of 10 F1 replications
(1,000 retained records), each generated and cross-fit residualized at
1,000 rows before dCor with 199 permutations, using the unmodified
general-purpose spline/Ridge residualizer (the same one already used for
F4, F6, and F7 -- not the F5 quadratic-repair basis). It ran from source
revision `05e5ad9596eefd788cafba124dbda84a15e48e40` using the distinct
`batch-f1-null-transfer` seed namespace.

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

The F1 study did not recompute or alter this selection.

## Transfer check

- Fixture and pair: `F1`, `(X1, X2)`; adjustment variables:
  `(X3, X4, X5, X6)`, all signal-free by construction.
- Structure: complete mutual independence -- `X1 = e1`, `X2 = e2`, with
  no common cause, mediator, collider, or direct edge of any kind.
- Complete replications: 1,000 of 1,000; warnings and exceptions: none.
- Null-like batches: 87 of 100 (PASS requires at least 85).
- Low permutation p-values: 53 of 1,000 (PASS allows at most 67).

Both criteria passed, so the terminal outcome is `PASS`.

## Independent raw recomputation

A separate verifier script did not import
`research.gate0.f1_transfer_runner`, `research.gate0.f1_transfer_report`,
or `research.gate0.batch_null_policy`. It re-derived every fixture/
residual/permutation seed from the frozen identity string, recomputed
observed dCor and all 199 permutation values directly from the retained
1,000-row residual CSVs and null arrays for every one of the 1,000 cells,
recomputed SHA-256 for the current run and the calibration parent, and
reapplied the null-like/p-guard rule from raw values. Results:

- Records: 1,000; unique `(batch, replication)` identities: 1,000; exact
  grid; zero duplicates.
- Frozen record identity (`F1`, `X1`, `X2`, `f1-null-transfer`, run ID,
  seed namespace): exact for all 1,000 records.
- Seed re-derivation: zero mismatches across all 3,000 seed values.
- Residual/null shape and finiteness: zero failures across 1,000 files
  each.
- Observed dCor and permutation-null recomputation: zero mismatches.
- Current and calibration-parent SHA-256: match the manifest exactly.
- Independently recomputed null-like batch count: 87 (matches manifest).
- Independently recomputed low-p-value count: 53 (matches manifest).
- Independent terminal outcome: `PASS` (matches manifest and run state
  exactly).

## Retained artifacts

- [Manifest](../../artifacts/batch-f1-null-transfer/batch-f1-null-transfer-20260824-001/manifest.json)
- [Runner input manifest](../../artifacts/batch-f1-null-transfer/batch-f1-null-transfer-20260824-001/manifest-input.json)
- [Records](../../artifacts/batch-f1-null-transfer/batch-f1-null-transfer-20260824-001/records.csv)
- [Batch summary](../../artifacts/batch-f1-null-transfer/batch-f1-null-transfer-20260824-001/f1-transfer-summary.csv)
- [Owner memo](../../artifacts/batch-f1-null-transfer/batch-f1-null-transfer-20260824-001/f1-transfer-memo.md)
- [Batch-classification plot](../../artifacts/batch-f1-null-transfer/batch-f1-null-transfer-20260824-001/plots/f1-batch-classifications.png)
- [Completion state](../../artifacts/batch-f1-null-transfer/batch-f1-null-transfer-20260824-001/run_state.json)
- [Residual samples](../../artifacts/batch-f1-null-transfer/batch-f1-null-transfer-20260824-001/residual_samples/)
- [Permutation-null arrays](../../artifacts/batch-f1-null-transfer/batch-f1-null-transfer-20260824-001/null_statistics/)

## Interpretation and governance

This closes the most basic remaining gap in the Gate 0 sequence: the
frozen workflow, tested repeatedly against engineered relationships (F4's
chain, F5's common cause, F6's mediated path, F7's collider), also
behaves correctly on the simplest possible case where nothing at all is
present. Unlike a failure on any structure-specific test, a NARROW or
STOP result here would have indicated a problem with the statistic,
permutation procedure, or calibration itself rather than a
structure-specific limitation -- that did not occur.

This PASS supports only that the general-purpose residualizer and frozen
decision rule correctly return a null on complete mutual independence at
the 1,000-row dimensions tested. It does not authorize recalibration, an
alternate fixture, estimator redesign, a new simulation family, or
package work. Moving to the next untested Gate 0 canonical structure
(F2, F3, or F8) remains a separate, later owner decision.
