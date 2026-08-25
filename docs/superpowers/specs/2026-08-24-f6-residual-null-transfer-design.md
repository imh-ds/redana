# F6 residual-null transfer design

## Purpose

Test whether the frozen, reference-calibrated 1,000-row decision rule
transfers through the actual residual-dependence workflow under a second,
distinct known conditional-independence null: a nonlinear indirect path
with no direct edge between the tested pair. This is the next narrowly
chartered Gate 0 canonical structure, per
`docs/evidence/phase-synthesis-quadratic-capability-boundary-20260824.md`.
It is a validation phase only, not package work, an estimator redesign, or
a new calibration.

The phase reuses the existing F6 fixture, already defined in
`research/gate0/fixtures.py` and untouched by this design. F6 has a known
null target after adjustment: `X1` affects `X3` only through the mediator
`X2`, and the `X1 -> X2` leg is nonlinear while the `X2 -> X3` leg is
linear. A correctly specified residualization workflow that adjusts for
`X2` should therefore leave `X1` and `X3` residuals independent. This
structure differs materially from F5's nonlinear common cause: here the
nonlinearity sits on one leg of a mediated chain, not in a shared parent of
both tested endpoints. F4 already showed the frozen general-purpose
residualizer correctly handles the *linear* version of this chain shape;
this phase asks whether it also handles the nonlinear-mediator version, or
whether it needs the same kind of repair F5 needed.

## Fixed data-generating scenario

For each replication, generate exactly 1,000 rows with the existing `F6`
fixture definition:

```text
X1 = e1
X2 = 0.7 * (e1^2 - 1) + e2
X3 = 0.7 * X2 + e3
```

where `e1`, `e2`, and `e3` are independent standard-normal noises. The
existing fixture also includes independent `X4`, `X5`, and `X6`, and
performs its already-established standardization. The tested pair is
exactly `(X1, X3)`.

For each generated frame, form pair-specific cross-fitted residuals for
`X1` and `X3`, adjusting for `(X2, X4, X5, X6)` with the frozen
general-purpose workflow -- the same one already used for F4 and F5, not
the F5 quadratic-repair basis:

- five shuffled folds;
- cubic spline basis with five knots and quantile placement;
- scaling followed by Ridge regression with alpha 1;
- held-out residuals only.

Use all 1,000 resulting residual pairs for dCor. There is no source/
evaluation split and no secondary sampling in this phase. Every dCor
calculation uses 199 permutations.

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

The batch policy is unchanged:

- 100 batches, each with 10 replications (1,000 total records);
- a batch passes its p-value guard when at most two of its ten p-values
  are less than or equal to 0.05;
- a batch is null-like when it passes that guard and its median dCor is
  less than or equal to the copied boundary;
- the full run passes when at least 85 of 100 batches are null-like and
  no more than 67 of 1,000 p-values are less than or equal to 0.05.

Terminal outcomes have strict precedence:

1. `STOP`: incomplete/malformed evidence, any retained exception, or more
   than 67 low p-values;
2. `NARROW`: complete evidence and p-value cap pass, but fewer than 85
   null-like batches;
3. `PASS`: complete evidence, at least 85 null-like batches, and at most
   67 low p-values.

The boundary, count thresholds, fixture, residualizer settings,
dimensions, and permutation count are not tunable after results are seen.

## Execution and retention

Create a narrowly scoped F6 transfer runner and report, built the same
way as `research/gate0/f5_transfer_runner.py` and
`research/gate0/f5_transfer_report.py`. It may call only the existing F6
fixture generator, pair-specific residualizer, dCor metric, fixed batch
policy, and read-only calibration-provenance validation. It must not call
the raw-reference calibration or confirmation runners, create any F1--F8
matrix, or invoke package functionality.

Use a distinct seed namespace: `batch-f6-null-transfer`. Derive and retain
exact unsigned seeds for fixture generation, residual-fold randomization,
and permutations for every `(batch, replication)` identity.

The official run identity is:

```text
batch-f6-null-transfer-20260824-001
```

Its output directory is:

```text
artifacts/batch-f6-null-transfer/batch-f6-null-transfer-20260824-001
```

For every attempted replication retain:

- F6 fixture identity and tested pair;
- observed dCor and permutation p-value;
- fixture, residual, and permutation seeds;
- a 1,000-row two-column residual sample;
- the 199-value permutation-null array;
- elapsed time, warnings, and exception text.

Write records, input manifest, report manifest, summary, memo, plots, and
run state atomically. The input and report manifests must pin the three
calibration hashes, copied selection boundary, configuration, seed
namespace, run ID, source revision, and hashes of retained F6 records.
Refuse a non-empty output directory.

## Verification and governance

Before the official run:

1. Write focused failing tests, then implement the runner and report
   paths.
2. Test all 100 x 10 identity handling with a reduced test configuration.
3. Test F6-only selection, the `(X1, X3)` pair, five-fold
   residualization, all-rows evaluation, retained residual samples/null
   arrays, independent seed namespace, missing/malformed evidence, and
   refusal of altered calibration hashes or a non-ready calibration
   result.
4. Run focused tests, the complete test suite, and lint.
5. Commit source before artifacts.

Execute the exact full run once only. Retain and commit evidence
regardless of terminal outcome. Independently review committed artifacts
by recomputing record/array counts, identities, hashes, seeds,
p-value-guard counts, batch medians, copied-boundary classifications, and
terminal outcome.

This phase is limited to the F6 residual-null transfer claim. It does not
authorize recalibration, changing the residualizer, adding a dependent
alternative, running another fixture, expanding the simulation family, or
starting package work.

- If the result is `PASS`: the frozen general-purpose residualizer
  already handles this nonlinear-mediator structure correctly. No repair
  is needed for F6. Gate 0 proceeds to the next untested canonical
  structure as a separate, later owner decision.
- If the result is `NARROW` or `STOP`: stop for diagnosis without
  changing the ruler post hoc. A structure-matched repair for F6 -- not
  assumed to be the same raw-plus-square basis used for F5, since F6's
  nonlinearity sits on a mediator leg rather than in a shared parent --
  may only be designed as a separate, later, narrowly chartered study
  after an explicit owner decision.
