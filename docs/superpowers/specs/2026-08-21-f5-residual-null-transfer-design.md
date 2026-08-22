# F5 residual-null transfer design

## Purpose

Test whether the frozen, reference-calibrated 1,000-row decision rule
transfers through the actual residual-dependence workflow under a known
conditional-independence null. This is a validation phase, not package work,
an estimator redesign, or a new calibration.

The phase reuses the existing F5 smooth nonlinear common-cause fixture. F5
has a known null target after adjustment: the tested endpoints share a
nonlinear parent but have independent noise terms. A correctly specified
residualization workflow should therefore leave independent residuals.

## Fixed data-generating scenario

For each replication, generate exactly 1,000 rows with the existing `F5`
fixture definition:

```text
Z  = X3
P  = 0.7 * (Z^2 - 1)
X1 = P + e1
X2 = P + e2
```

where `e1` and `e2` are independent standard-normal noises. The existing
fixture also includes independent `X4`, `X5`, and `X6`, and performs its
already-established standardization. The tested pair is exactly `(X1, X2)`.

For each generated frame, form pair-specific cross-fitted residuals for `X1`
and `X2`, adjusting for `(X3, X4, X5, X6)` with the frozen workflow:

- five shuffled folds;
- cubic spline basis with five knots and quantile placement;
- scaling followed by Ridge regression with alpha 1;
- held-out residuals only.

Use all 1,000 resulting residual pairs for dCor. There is no source/evaluation
split and no secondary sampling in this phase: 1,000 rows are both fitted and
evaluated through cross-fitting. Every dCor calculation uses 199 permutations.

## Frozen reference rule

This phase consumes, but does not modify, the committed reference calibration:

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
- a batch passes its p-value guard when at most two of its ten p-values are
  less than or equal to 0.05;
- a batch is null-like when it passes that guard and its median dCor is less
  than or equal to the copied boundary;
- the full run passes when at least 85 of 100 batches are null-like and no
  more than 67 of 1,000 p-values are less than or equal to 0.05.

Terminal outcomes have strict precedence:

1. `STOP`: incomplete/malformed evidence, any retained exception, or more
   than 67 low p-values;
2. `NARROW`: complete evidence and p-value cap pass, but fewer than 85
   null-like batches;
3. `PASS`: complete evidence, at least 85 null-like batches, and at most 67
   low p-values.

The boundary, count thresholds, fixture, residualizer settings, dimensions,
and permutation count are not tunable after results are seen.

## Execution and retention

Create a narrowly scoped F5 transfer runner. It may call only the existing
F5 fixture generator, pair-specific residualizer, dCor metric, fixed batch
policy, and read-only calibration-provenance validation. It must not call the
raw-reference calibration or confirmation runners, create any F1--F8 matrix,
or invoke package functionality.

Use a distinct seed namespace: `batch-f5-null-transfer`. Derive and retain
exact unsigned seeds for fixture generation, residual-fold randomization, and
permutations for every `(batch, replication)` identity.

The official run identity is:

```text
batch-f5-null-transfer-20260821-001
```

Its output directory is:

```text
artifacts/batch-f5-null-transfer/batch-f5-null-transfer-20260821-001
```

For every attempted replication retain:

- F5 fixture identity and tested pair;
- observed dCor and permutation p-value;
- fixture, residual, and permutation seeds;
- a 1,000-row two-column residual sample;
- the 199-value permutation-null array;
- elapsed time, warnings, and exception text.

Write records, input manifest, report manifest, summary, memo, plots, and run
state atomically. The input and report manifests must pin the three calibration
hashes, copied selection boundary, configuration, seed namespace, run ID,
source revision, and hashes of retained F5 records. Refuse a non-empty output
directory.

## Verification and governance

Before the official run:

1. Write focused failing tests, then implement the runner and report paths.
2. Test all 100 x 10 identity handling with a reduced test configuration.
3. Test F5-only selection, the `(X1, X2)` pair, five-fold residualization,
   all-rows evaluation, retained residual samples/null arrays, independent
   seed namespace, missing/malformed evidence, and refusal of altered
   calibration hashes or a non-ready calibration result.
4. Run focused tests, the complete test suite, and lint.
5. Commit source before artifacts.

Execute the exact full run once only. Retain and commit evidence regardless of
terminal outcome. Independently review committed artifacts by recomputing
record/array counts, identities, hashes, seeds, p-value-guard counts, batch
medians, copied-boundary classifications, and terminal outcome.

This phase is limited to the F5 residual-null transfer claim. It does not
authorize recalibration, changing the residualizer, adding a dependent
alternative, running another fixture, expanding the simulation family, or
starting package work. If the result is `PASS`, a separate owner decision may
authorize a matched residual-dependence alternative. If it is `NARROW` or
`STOP`, stop for diagnosis without changing the ruler post hoc.
