# F8 mixed direct-and-indirect path detection design

## Purpose

Test whether the frozen workflow, using the unmodified general-purpose
residualizer (no repair basis), correctly detects dependence between a
pair connected by **both** a direct edge and a separate indirect
(mediated) path at 1,000 rows -- the eighth and final untested Gate 0
canonical structure per
`docs/evidence/phase-synthesis-quadratic-capability-boundary-20260824.md`.
It is a validation phase only, not package work, an estimator redesign,
or a new calibration.

The phase reuses the existing F8 fixture, already defined in
`research/gate0/fixtures.py` and untouched by this design.

## Why this closes out the Gate 0 canonical-structure checklist

Every prior Gate 0 structure isolated one causal shape at a time: a pure
chain (F4), a pure nonlinear common cause (F5), a pure nonlinear
mediator (F6), a pure collider (F7), plain independence (F1), and pure
direct edges, linear (F2) and nonlinear (F3). F8 is the only fixture
that combines two of these mechanisms on the same tested pair at once:
`X1` affects `X2` **directly**, and `X1` also affects `X2` **indirectly**
through the mediator `X3`. Because the general-purpose residualizer
adjusts for every other column automatically (including `X3`, per
`predictor_columns` in `research/gate0/residuals.py`), this design tests
whether the workflow still detects the pair's dependence when part of
that dependence routes through a variable the residualizer is itself
conditioning on. It is the natural last structure to validate before any
package-readiness discussion, since it is the closest analogue in this
simulation family to how the residual-dependence estimand would actually
be used against a real mixed-path graph.

## Fixed data-generating scenario

For each replication, generate exactly 1,000 rows with the existing `F8`
fixture definition:

```text
X1 = e1
X3 = 0.7 * X1 + e3
X2 = 0.7 * X1 + 0.7 * X3 + e2
```

where `e1`, `e2`, and `e3` are independent standard-normal noises, and
`X4`, `X5`, and `X6` are independent standard normals with no functional
relationship to `X1`, `X2`, or `X3`. The existing fixture performs its
already-established standardization. The tested pair is exactly
`(X1, X2)`.

For each generated frame, form pair-specific cross-fitted residuals for
`X1` and `X2`. `predictor_columns` automatically selects every column
other than the tested pair as the adjustment set -- here `(X3, X4, X5,
X6)`, which includes the mediator `X3` -- using the frozen
general-purpose workflow already used for F4, F6, F7, F3, and F2, not the
F5 quadratic-repair basis:

- five shuffled folds;
- cubic spline basis with five knots and quantile placement;
- scaling followed by Ridge regression with alpha 1;
- held-out residuals only.

Use all 1,000 resulting residual pairs for dCor. Every dCor calculation
uses 199 permutations.

Adjusting linearly for the mediator `X3` does not fully remove the
`X1`-`X2` dependence, because `X1` itself is excluded from the predictor
set for its own residual and because part of the relationship is the
direct edge, which conditioning on `X3` does not block. This is exactly
why the fixture is classified `non-null` in `FIXTURES` -- the population
residual covariance under this adjustment set is nonzero.

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
unmodified for the F4 residual-link alternative, Candidate 1, F7, F3, and
F2. Do not write a new policy module.

- detected batch: median dCor strictly above the boundary and at least
  8 of 10 p-values at or below 0.05;
- `PASS`: at least 85 detected batches out of 100, complete evidence;
- `NARROW`: complete evidence but fewer than 85 detected batches;
- `STOP`: incomplete or malformed evidence, any retained exception, or
  any retained warning (STOP has precedence over the batch count).

The boundary, count thresholds, fixture, residualizer settings,
dimensions, and permutation count are not tunable after results are seen.

## Execution and retention

Create a narrowly scoped F8 runner and report, following the shape of
`research/gate0/f2_linear_direct_edge_detection_runner.py` and
`research/gate0/f2_linear_direct_edge_detection_report.py` exactly,
substituting fixture `F8` for `F2` and the corresponding phase/namespace.
It may call only the existing F8 fixture generator, pair-specific
residualizer, dCor metric, the unmodified F4 detection policy, and
read-only calibration-provenance validation. It must not call the
raw-reference calibration or confirmation runners in a way that alters
them, create any F1--F8 matrix, or invoke package functionality.

Use a distinct seed namespace: `batch-f8-mixed-direct-indirect-path-detection`.
Derive and retain exact unsigned seeds for fixture generation,
residual-fold randomization, and permutations for every
`(batch, replication)` identity.

The official run identity is:

```text
batch-f8-mixed-direct-indirect-path-detection-20260825-001
```

Its output directory is:

```text
artifacts/batch-f8-mixed-direct-indirect-path-detection/batch-f8-mixed-direct-indirect-path-detection-20260825-001
```

For every attempted replication retain:

- F8 fixture identity and tested pair;
- observed dCor and permutation p-value;
- fixture, residual, and permutation seeds;
- a 1,000-row two-column residual sample;
- the 199-value permutation-null array;
- elapsed time, warnings, and exception text.

Write records, input manifest, report manifest, summary, memo, plots, and
run state atomically. The input and report manifests must pin the three
calibration hashes, copied boundary, configuration, seed namespace, run
ID, source revision, and hashes of retained F8 records. Refuse a
non-empty output directory.

## Verification and governance

Before the official run:

1. Write focused failing tests, then implement the runner and report
   paths.
2. Test all 100 x 10 identity handling with a reduced test configuration.
3. Test F8-only selection, the `(X1, X2)` pair, five-fold
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

This phase is limited to the F8 mixed direct-and-indirect path detection
claim. It does not authorize recalibration, changing the residualizer,
running another fixture, expanding the simulation family, or starting
package work.

- If the result is `PASS`: the unrepaired general-purpose workflow
  correctly detects pair dependence that routes through both a direct
  edge and a mediated indirect path simultaneously, even though the
  mediator sits inside the automatic adjustment set. This closes out all
  eight Gate 0 canonical structures. Whether Gate 0 is now sufficient to
  support package-readiness discussion remains a separate, later owner
  decision.
- If the result is `NARROW` or `STOP`: this would indicate the
  general-purpose residualizer over-adjusts when a mediator on an
  indirect path is present alongside a direct edge -- a distinct failure
  mode from F5's common-cause STOP, since here the confounding variable
  is a true mediator, not a shared parent. Stop for diagnosis without
  changing the ruler post hoc. Any follow-up requires a separate, later,
  narrowly chartered study after an explicit owner decision.
