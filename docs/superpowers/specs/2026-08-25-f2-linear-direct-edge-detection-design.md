# F2 linear direct-edge detection design

## Purpose

Test whether the frozen workflow, using the unmodified general-purpose
residualizer (no repair basis), correctly detects a genuine **linear**
direct edge at 1,000 rows when there is no common cause or other
confounding structure to complicate adjustment -- the next narrowly
chartered Gate 0 canonical structure per
`docs/evidence/phase-synthesis-quadratic-capability-boundary-20260824.md`.
It is a validation phase only, not package work, an estimator redesign,
or a new calibration.

The phase reuses the existing F2 fixture, already defined in
`research/gate0/fixtures.py` and untouched by this design.

## Why this completes the direct-edge pair with F3

F3 confirmed that the unrepaired workflow detects a raw **nonlinear**
direct edge when adjustment is inert. F2 is the linear counterpart: `X2`
is a plain linear function of `X1` (`X2 = 0.7*X1+e2`), with no common
cause, no mediator, and no collider in play. `X3`--`X6` carry no
information about either endpoint, so adjustment is inert here too. F2
is the simplest possible non-null Gate 0 structure and completes the
direct-edge check (linear and nonlinear) using the same *unrepaired*
general-purpose residualizer already validated against F4-link (chain),
F7 (collider), and F3 (nonlinear edge).

## Fixed data-generating scenario

For each replication, generate exactly 1,000 rows with the existing `F2`
fixture definition:

```text
X1 = e1
X2 = 0.7 * X1 + e2
```

where `e1` and `e2` are independent standard-normal noises, and `X3`
(`= e3`), `X4`, `X5`, and `X6` are independent standard normals with no
functional relationship to `X1` or `X2`. The existing fixture performs
its already-established standardization. The tested pair is exactly
`(X1, X2)`.

For each generated frame, form pair-specific cross-fitted residuals for
`X1` and `X2`, adjusting for `(X3, X4, X5, X6)` with the frozen
general-purpose workflow -- the same one already used for F4, F6, F7, and
F3 -- not the F5 quadratic-repair basis:

- five shuffled folds;
- cubic spline basis with five knots and quantile placement;
- scaling followed by Ridge regression with alpha 1;
- held-out residuals only.

Use all 1,000 resulting residual pairs for dCor. Every dCor calculation
uses 199 permutations.

## Frozen reference rule

This phase consumes, but does not modify, the committed reference
calibration:

- calibration directory:
  `artifacts/batch-null-calibration/batch-null-calibration-20260821-001`;
- copied boundary: `0.058242447845091264`;
- calibration records SHA-256:
  `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`;
- calibration input-manifest SHA-256:
  `7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c`;
- calibration manifest SHA-256:
  `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`.

Because this is a detection (non-null) check, reuse the existing,
fixture-agnostic detection policy in `research/gate0/f4_link_policy.py`
(`F4LinkConfig`, `summarize_detection_batches`, `check_detection`,
`detection_terminal_status`) unchanged -- the same policy already reused
unmodified for the F4 residual-link alternative, Candidate 1, F7, and F3.
Do not write a new policy module.

- detected batch: median dCor strictly above the boundary and at least
  8 of 10 p-values at or below 0.05;
- `PASS`: at least 85 detected batches out of 100, complete evidence;
- `NARROW`: complete evidence but fewer than 85 detected batches;
- `STOP`: incomplete or malformed evidence, any retained exception, or
  any retained warning (STOP has precedence over the batch count).

The boundary, count thresholds, fixture, residualizer settings,
dimensions, and permutation count are not tunable after results are seen.

## Execution and retention

Create a narrowly scoped F2 runner and report, following the shape of
`research/gate0/f3_nonlinear_direct_edge_detection_runner.py` and
`research/gate0/f3_nonlinear_direct_edge_detection_report.py` exactly,
substituting fixture `F2` for `F3` and the corresponding phase/namespace.
It may call only the existing F2 fixture generator, pair-specific
residualizer, dCor metric, the unmodified F4 detection policy, and
read-only calibration-provenance validation. It must not call the
raw-reference calibration or confirmation runners in a way that alters
them, create any F1--F8 matrix, or invoke package functionality.

Use a distinct seed namespace: `batch-f2-linear-direct-edge-detection`.
Derive and retain exact unsigned seeds for fixture generation,
residual-fold randomization, and permutations for every
`(batch, replication)` identity.

The official run identity is:

```text
batch-f2-linear-direct-edge-detection-20260825-001
```

Its output directory is:

```text
artifacts/batch-f2-linear-direct-edge-detection/batch-f2-linear-direct-edge-detection-20260825-001
```

For every attempted replication retain:

- F2 fixture identity and tested pair;
- observed dCor and permutation p-value;
- fixture, residual, and permutation seeds;
- a 1,000-row two-column residual sample;
- the 199-value permutation-null array;
- elapsed time, warnings, and exception text.

Write records, input manifest, report manifest, summary, memo, plots, and
run state atomically. The input and report manifests must pin the three
calibration hashes, copied boundary, configuration, seed namespace, run
ID, source revision, and hashes of retained F2 records. Refuse a
non-empty output directory.

## Verification and governance

Before the official run:

1. Write focused failing tests, then implement the runner and report
   paths.
2. Test all 100 x 10 identity handling with a reduced test configuration.
3. Test F2-only selection, the `(X1, X2)` pair, five-fold
   residualization, all-rows evaluation, retained residual samples/null
   arrays, independent seed namespace, missing/malformed evidence, and
   refusal of altered calibration hashes or a non-ready calibration
   result.
4. Run focused tests, the complete test suite, and lint.
5. Commit source before artifacts.

Execute the exact full run once only. Retain and commit evidence
regardless of terminal outcome. Independently review committed artifacts
by recomputing record/array counts, identities, hashes, seeds, detection
counts, and terminal outcome from raw files, without importing the
project's runner/report/policy modules.

This phase is limited to the F2 linear direct-edge detection claim. It
does not authorize recalibration, changing the residualizer, running
another fixture, expanding the simulation family, or starting package
work.

- If the result is `PASS`: the unrepaired general-purpose workflow
  correctly detects raw linear dependence when adjustment is not the
  obstacle, completing the direct-edge pair alongside F3 and confirming
  the detection machinery handles both linear and nonlinear direct edges
  under inert adjustment. Gate 0 proceeds to the next untested canonical
  structure only as a separate, later owner decision.
- If the result is `NARROW` or `STOP`: this would be a surprising basic
  failure, since linear detection is the simplest possible non-null case
  and the same machinery already passed F4-link (chain, linear) and F3
  (nonlinear edge). Stop for diagnosis without changing the ruler post
  hoc. Any follow-up requires a separate, later, narrowly chartered study
  after an explicit owner decision.
