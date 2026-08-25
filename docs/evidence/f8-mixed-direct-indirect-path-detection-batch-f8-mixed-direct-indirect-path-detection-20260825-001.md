# F8 mixed direct-and-indirect path detection evidence

Run ID: `batch-f8-mixed-direct-indirect-path-detection-20260825-001`
Terminal outcome: **PASS**

This immutable detection study contains 100 batches of 10 F8 replications
(1,000 retained records), each generated and cross-fit residualized at
1,000 rows before dCor with 199 permutations, using the unmodified
general-purpose spline/Ridge residualizer (the same one already used for
F4, F6, F7, F3, and F2 -- not the F5 quadratic-repair basis) and the
unmodified, fixture-agnostic F4 detection policy
(`research/gate0/f4_link_policy.py`). It ran from source revision
`76491898` using the distinct
`batch-f8-mixed-direct-indirect-path-detection` seed namespace.

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

The F8 study did not recompute or alter this selection.

## Detection check

- Fixture and pair: `F8`, `(X1, X2)`; adjustment variables:
  `(X3, X4, X5, X6)` -- automatically selected by `predictor_columns`,
  which includes the mediator `X3`.
- Structure: `X1 = e1`; `X3 = 0.7*X1 + e3` (mediator); `X2 = 0.7*X1 +
  0.7*X3 + e2` -- `X1` affects `X2` both directly and indirectly through
  `X3`, with the mediator sitting inside the automatic adjustment set.
  This was the eighth and final untested Gate 0 canonical structure.
- Complete replications: 1,000 of 1,000; warnings and exceptions: none.
- Detected batches: 100 of 100 (PASS requires at least 85).
- Individual low p-values: 1,000 of 1,000 at or below 0.05.
- Observed dCor across all records: min 0.3671, mean 0.4536, max 0.5351
  -- roughly six to nine times the copied boundary (0.0582) in every
  single batch, a saturated and unambiguous detection with no borderline
  cases. Batch-level median dCor ranged 0.4351-0.4754.

## Independent raw recomputation

A separate verifier script did not import
`research.gate0.f8_mixed_direct_indirect_path_detection_runner`,
`research.gate0.f8_mixed_direct_indirect_path_detection_report`, or
`research.gate0.f4_link_policy`. It re-derived every fixture/residual/
permutation seed from the frozen identity string, recomputed observed
dCor and all 199 permutation values directly from the retained
1,000-row residual CSVs and null arrays for every one of the 1,000
cells, recomputed SHA-256 for the current run and the calibration
parent, and reapplied the detection rule (median dCor strictly above the
boundary, at least 8 of 10 p-values at or below 0.05, at least 85
detected batches for PASS) from raw values. Results:

- Records: 1,000; unique `(batch, replication)` identities: 1,000; exact
  grid; zero duplicates.
- Frozen record identity (`F8`, `X1`, `X2`,
  `f8-mixed-direct-indirect-path-detection`, run ID, seed namespace):
  exact for all 1,000 records.
- Seed re-derivation: zero mismatches across all 3,000 seed values.
- Residual/null shape and finiteness: zero failures across 1,000 files
  each.
- Observed dCor and permutation-null recomputation: zero mismatches.
- Current and calibration-parent SHA-256: match the manifest exactly.
- Independently recomputed detected-batch count: 100 (matches
  manifest).
- Independent terminal outcome: `PASS` (matches manifest and run state
  exactly).

## Retained artifacts

- [Manifest](../../artifacts/batch-f8-mixed-direct-indirect-path-detection/batch-f8-mixed-direct-indirect-path-detection-20260825-001/manifest.json)
- [Runner input manifest](../../artifacts/batch-f8-mixed-direct-indirect-path-detection/batch-f8-mixed-direct-indirect-path-detection-20260825-001/manifest-input.json)
- [Records](../../artifacts/batch-f8-mixed-direct-indirect-path-detection/batch-f8-mixed-direct-indirect-path-detection-20260825-001/records.csv)
- [Batch summary](../../artifacts/batch-f8-mixed-direct-indirect-path-detection/batch-f8-mixed-direct-indirect-path-detection-20260825-001/f8-mixed-direct-indirect-path-detection-summary.csv)
- [Owner memo](../../artifacts/batch-f8-mixed-direct-indirect-path-detection/batch-f8-mixed-direct-indirect-path-detection-20260825-001/f8-mixed-direct-indirect-path-detection-memo.md)
- [Batch-classification plot](../../artifacts/batch-f8-mixed-direct-indirect-path-detection/batch-f8-mixed-direct-indirect-path-detection-20260825-001/plots/f8-mixed-direct-indirect-path-detections.png)
- [Completion state](../../artifacts/batch-f8-mixed-direct-indirect-path-detection/batch-f8-mixed-direct-indirect-path-detection-20260825-001/run_state.json)
- [Residual samples](../../artifacts/batch-f8-mixed-direct-indirect-path-detection/batch-f8-mixed-direct-indirect-path-detection-20260825-001/residual_samples/)
- [Permutation-null arrays](../../artifacts/batch-f8-mixed-direct-indirect-path-detection/batch-f8-mixed-direct-indirect-path-detection-20260825-001/null_statistics/)

## Interpretation and governance

This confirms that the unrepaired general-purpose workflow correctly
detects dependence between a pair connected by both a direct edge and a
mediated indirect path, even though the mediator sits inside the
automatic adjustment set. Linear adjustment for the mediator does not
fully null the pair's dependence here, both because part of it is a
direct edge that conditioning on the mediator cannot block, and because
the tested left variable itself is excluded from its own predictor set,
so the mediator only partially proxies the shared upstream noise. This
is a distinct mechanism from F5's common-cause STOP (a shared parent the
residualizer failed to null), F6's mediator null (a pure indirect path
correctly nulled), and F7's collider detection (induced dependence from
conditioning on a downstream collider).

With F8's PASS, all eight Gate 0 canonical structures have now been
validated: independence (F1), linear direct edge (F2), nonlinear direct
edge (F3), chain (F4), nonlinear common cause (F5, repaired), nonlinear
mediator (F6), collider (F7), and this mixed direct-and-indirect path
(F8).

This PASS supports only that the unrepaired general-purpose workflow
correctly detects this one mixed direct-and-indirect structure at the
frozen 1,000-row dimensions. It does not authorize recalibration, an
alternate fixture, estimator redesign, a new simulation family, or
package work. Whether Gate 0's coverage is now sufficient to support any
package-readiness discussion remains a separate, later owner decision.
