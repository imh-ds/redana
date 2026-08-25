# F7 collider detection evidence

Run ID: `batch-f7-collider-detection-20260824-001`
Terminal outcome: **PASS**

This immutable detection study contains 100 batches of 10 F7 replications
(1,000 retained records), each generated and cross-fit residualized at
1,000 rows before dCor with 199 permutations, using the unmodified
general-purpose spline/Ridge residualizer and the unmodified,
fixture-agnostic F4 detection policy (`research/gate0/f4_link_policy.py`).
It ran from source revision `2f620c908361cc01fc33090fe794dbb30970c605`
using the distinct `batch-f7-collider-detection` seed namespace.

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

The F7 study did not recompute or alter this selection.

## Detection check

- Fixture and pair: `F7`, `(X1, X2)`; adjustment variables:
  `(X3, X4, X5, X6)`.
- Structure: `X1 = e1`, `X2 = e2` (marginally independent by construction);
  `X3 = 0.7*X1 + 0.7*X2 + e3` is a collider. Adjusting for `X3` -- required
  because the adjustment set is always "every other observed variable" --
  induces real dependence between `X1` and `X2` ("explaining away").
  Detection here is the mathematically correct outcome under this
  project's stated estimand, not a false positive.
- Complete replications: 1,000 of 1,000; warnings and exceptions: none.
- Detected batches: 100 of 100 (PASS requires at least 85).
- Individual low p-values: 1,000 of 1,000 at or below 0.05.
- Observed dCor across all records: min 0.2112, mean 0.2988, max 0.3774
  -- three to six times the copied boundary (0.0582) in every single
  batch, a saturated and unambiguous detection with no borderline cases.

## Independent raw recomputation

A separate verifier script did not import
`research.gate0.f7_collider_detection_runner`,
`research.gate0.f7_collider_detection_report`, or
`research.gate0.f4_link_policy`. It re-derived every fixture/residual/
permutation seed from the frozen identity string, recomputed observed dCor
and all 199 permutation values directly from the retained 1,000-row
residual CSVs and null arrays for every one of the 1,000 cells, recomputed
SHA-256 for the current run and the calibration parent, and reapplied the
detection rule (median dCor strictly above the boundary, at least 8 of 10
p-values at or below 0.05, at least 85 detected batches for PASS) from raw
values. Results:

- Records: 1,000; unique `(batch, replication)` identities: 1,000; exact
  grid; zero duplicates.
- Frozen record identity (`F7`, `X1`, `X2`, `f7-collider-detection`, run
  ID, seed namespace): exact for all 1,000 records.
- Seed re-derivation: zero mismatches across all 3,000 seed values.
- Residual/null shape and finiteness: zero failures across 1,000 files
  each.
- Observed dCor and permutation-null recomputation: zero mismatches.
- Current and calibration-parent SHA-256: match the manifest exactly.
- Independently recomputed detected-batch count: 100 (matches manifest).
- Independent terminal outcome: `PASS` (matches manifest and run state
  exactly).

## Retained artifacts

- [Manifest](../../artifacts/batch-f7-collider-detection/batch-f7-collider-detection-20260824-001/manifest.json)
- [Runner input manifest](../../artifacts/batch-f7-collider-detection/batch-f7-collider-detection-20260824-001/manifest-input.json)
- [Records](../../artifacts/batch-f7-collider-detection/batch-f7-collider-detection-20260824-001/records.csv)
- [Batch summary](../../artifacts/batch-f7-collider-detection/batch-f7-collider-detection-20260824-001/f7-collider-detection-summary.csv)
- [Owner memo](../../artifacts/batch-f7-collider-detection/batch-f7-collider-detection-20260824-001/f7-collider-detection-memo.md)
- [Batch-classification plot](../../artifacts/batch-f7-collider-detection/batch-f7-collider-detection-20260824-001/plots/f7-collider-detections.png)
- [Completion state](../../artifacts/batch-f7-collider-detection/batch-f7-collider-detection-20260824-001/run_state.json)
- [Residual samples](../../artifacts/batch-f7-collider-detection/batch-f7-collider-detection-20260824-001/residual_samples/)
- [Permutation-null arrays](../../artifacts/batch-f7-collider-detection/batch-f7-collider-detection-20260824-001/null_statistics/)

## Interpretation and governance

This PASS supports only that the frozen workflow correctly detects real,
collider-induced residual dependence at the frozen 1,000-row dimensions,
consistent with the project's explicitly narrow estimand ("dependence
remaining after adjustment for the stated set," not a claim about the true
underlying graph). Combined with F4's prior confirmed null and F5/F6's findings, this
strengthens confidence that the estimand and statistic behave as intended
across a qualitatively different structure -- one where the *correct*
answer is a positive finding rather than a null.

It does not authorize recalibration, an alternate fixture, estimator
redesign, a new simulation family, or package work. Moving to the next
untested Gate 0 canonical structure remains a separate, later owner
decision.
