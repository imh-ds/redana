# F1 independence null-transfer design

## Purpose

Test whether the frozen, reference-calibrated 1,000-row decision rule
transfers through the actual residual-dependence workflow under the
simplest possible conditional-independence null: complete mutual
independence, with no common cause, no mediator, no collider, and no
direct edge of any kind between the tested pair. This is the next
narrowly chartered Gate 0 canonical structure per
`docs/evidence/phase-synthesis-quadratic-capability-boundary-20260824.md`,
and the first item on `outline/plan.md`'s own Gate 0 checklist
("independent variables"). It is a validation phase only, not package
work, an estimator redesign, or a new calibration.

The phase reuses the existing F1 fixture, already defined in
`research/gate0/fixtures.py` and untouched by this design. Every column in
F1 is an independent standard-normal draw: `X1 = e1`, `X2 = e2`, `X3 = e3`,
`X4 = e4`, `X5 = e5`, `X6 = e6`. There is no relationship of any kind to
detect, so the frozen general-purpose residualizer -- adjusting `X1` and
`X2` for `(X3, X4, X5, X6)`, none of which carry any signal about either
endpoint -- should leave residuals that are themselves independent.

Every other structure tested in this sequence (F4's chain, F5's common
cause, F6's mediated path, F7's collider) has been an engineered,
non-trivial relationship. F1 closes the most basic remaining gap: the
workflow has been shown repeatedly to detect real and induced signal
(F4's clear link, Candidate 1, F7's collider) but has not yet been checked
against a fixture with no signal at all, under this exact calibrated
100x10 batch procedure.

## Fixed data-generating scenario

For each replication, generate exactly 1,000 rows with the existing `F1`
fixture definition:

```text
X1 = e1
X2 = e2
```

where `e1` and `e2` are independent standard-normal noises, and `X3`--`X6`
are independently drawn standard normals with no functional relationship
to `X1`, `X2`, or each other. The existing fixture performs its
already-established standardization. The tested pair is exactly
`(X1, X2)`.

For each generated frame, form pair-specific cross-fitted residuals for
`X1` and `X2`, adjusting for `(X3, X4, X5, X6)` with the frozen
general-purpose workflow -- the same one already used for F4, F6, and F7,
not the F5 quadratic-repair basis:

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

The batch policy is unchanged (the same null-like policy already reused
for F4, F5, and F6 -- not the detection policy used for the F4 link
alternative, Candidate 1, or F7):

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

Create a narrowly scoped F1 transfer runner and report, built the same
way as `research/gate0/f6_transfer_runner.py` and
`research/gate0/f6_transfer_report.py`. It may call only the existing F1
fixture generator, pair-specific residualizer, dCor metric, fixed batch
policy, and read-only calibration-provenance validation. It must not call
the raw-reference calibration or confirmation runners in a way that
alters them, create any F1--F8 matrix, or invoke package functionality.

Use a distinct seed namespace: `batch-f1-null-transfer`. Derive and
retain exact unsigned seeds for fixture generation, residual-fold
randomization, and permutations for every `(batch, replication)`
identity.

The official run identity is:

```text
batch-f1-null-transfer-20260824-001
```

Its output directory is:

```text
artifacts/batch-f1-null-transfer/batch-f1-null-transfer-20260824-001
```

For every attempted replication retain:

- F1 fixture identity and tested pair;
- observed dCor and permutation p-value;
- fixture, residual, and permutation seeds;
- a 1,000-row two-column residual sample;
- the 199-value permutation-null array;
- elapsed time, warnings, and exception text.

Write records, input manifest, report manifest, summary, memo, plots, and
run state atomically. The input and report manifests must pin the three
calibration hashes, copied selection boundary, configuration, seed
namespace, run ID, source revision, and hashes of retained F1 records.
Refuse a non-empty output directory.

## Verification and governance

Before the official run:

1. Write focused failing tests, then implement the runner and report
   paths.
2. Test all 100 x 10 identity handling with a reduced test configuration.
3. Test F1-only selection, the `(X1, X2)` pair, five-fold
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
terminal outcome from raw files, without importing the project's
runner/report/policy modules.

This phase is limited to the F1 independence null-transfer claim. It does
not authorize recalibration, changing the residualizer, running another
fixture, expanding the simulation family, or starting package work.

- If the result is `PASS`: the frozen general-purpose residualizer
  correctly returns a null on the simplest possible case, the expected
  and unremarkable baseline result. Gate 0 proceeds to the next untested
  canonical structure only as a separate, later owner decision.
- If the result is `NARROW` or `STOP`: this would be the most concerning
  possible finding in this entire sequence -- a spurious detection with
  no engineered relationship of any kind present would indicate a basic
  problem with the statistic, permutation procedure, or calibration
  itself, not a structure-specific limitation. Stop for diagnosis
  without changing the ruler post hoc; do not attempt a same-pass repair.
