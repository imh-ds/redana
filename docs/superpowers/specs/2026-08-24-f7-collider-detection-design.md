# F7 collider detection design

## Purpose

Test whether the frozen workflow correctly detects a genuine, collider-
induced residual dependence at 1,000 rows -- the next narrowly chartered
Gate 0 canonical structure per
`docs/evidence/phase-synthesis-quadratic-capability-boundary-20260824.md`.
This is the first structure in this sequence where the *correct* answer is
a positive detection, not a null. It is a validation phase only, not
package work, an estimator redesign, or a new calibration.

The phase reuses the existing F7 fixture, already defined in
`research/gate0/fixtures.py` and untouched by this design.

## Why the expected answer here is detection, not a null

`X1` and `X2` are generated independently (`X1 = e1`, `X2 = e2`), with no
direct edge and no shared cause. `X3` is a **collider**:
`X3 = 0.7*X1 + 0.7*X2 + e3`, caused by both `X1` and `X2`. The workflow's
adjustment set is always "every other observed variable," which for pair
`(X1, X2)` is `(X3, X4, X5, X6)` -- so `X3`, the collider, is necessarily
included.

Conditioning on a collider induces real statistical dependence between its
causes ("explaining away"): knowing `X3` and `X1` narrows the plausible
range of `X2`, even though `X1` and `X2` are marginally independent. This
is not an estimator artifact -- it is the mathematically correct
consequence of the adjustment set actually used, and it is consistent with
this project's explicitly narrow estimand: "residual dependence remaining
after adjustment for the other observed variables under the specified
adjustment model," not a claim about the true underlying graph
(`outline/plan.md` §2). The fixture registry already records F7's expected
target class as `non-null` for exactly this reason.

This makes F7 the correct place to check the opposite failure mode from
F5/F6: not "does the workflow wrongly manufacture a relationship that
should not be there," but "does it correctly recognize a relationship that
genuinely is there once you condition on a collider." Missing it here would
indicate the machinery under-detects even a real, injected signal;
manufacturing it in F1 or F4's true-null cases (already passed) would have
indicated the opposite failure. Confirming F7 detects correctly strengthens
confidence that the estimand and statistic behave as intended across this
qualitatively different structure.

## Fixed data-generating scenario

For each replication, generate exactly 1,000 rows with the existing `F7`
fixture definition:

```text
X1 = e1
X2 = e2
X3 = 0.7 * X1 + 0.7 * X2 + e3
```

where `e1`, `e2`, and `e3` are independent standard-normal noises. The
existing fixture also includes independent `X4`, `X5`, and `X6`, and
performs its already-established standardization. The tested pair is
exactly `(X1, X2)`.

For each generated frame, form pair-specific cross-fitted residuals for
`X1` and `X2`, adjusting for `(X3, X4, X5, X6)` with the frozen
general-purpose workflow -- the same one already used for F4, F5's
original null-transfer, and F6 -- not the F5 quadratic-repair basis:

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

Because this is a detection (non-null) check rather than a null-like
check, reuse the existing, fixture-agnostic detection policy in
`research/gate0/f4_link_policy.py` (`F4LinkConfig`,
`summarize_detection_batches`, `check_detection`,
`detection_terminal_status`) unchanged -- the same policy already reused
unmodified for the F4 residual-link alternative and Candidate 1. Do not
write a new policy module.

- detected batch: median dCor strictly above the boundary and at least
  8 of 10 p-values at or below 0.05;
- `PASS`: at least 85 detected batches out of 100, complete evidence;
- `NARROW`: complete evidence but fewer than 85 detected batches;
- `STOP`: incomplete or malformed evidence, any retained exception, or
  any retained warning (STOP has precedence over the batch count).

The boundary, count thresholds, fixture, residualizer settings,
dimensions, and permutation count are not tunable after results are seen.

## Execution and retention

Create a narrowly scoped F7 runner and report, following the shape of
`research/gate0/f6_transfer_runner.py` for generation/residualization and
`research/gate0/f4_link_report.py` for the detection-policy application,
but pinning only the single raw-reference calibration parent (there is no
second "null" parent to match against -- F7 is a standalone canonical
structure, not a matched alternative to a prior study). It may call only
the existing F7 fixture generator, pair-specific residualizer, dCor
metric, the unmodified F4 detection policy, and read-only
calibration-provenance validation. It must not call the raw-reference
calibration or confirmation runners in a way that alters them, create any
F1--F8 matrix, or invoke package functionality.

Use a distinct seed namespace: `batch-f7-collider-detection`. Derive and
retain exact unsigned seeds for fixture generation, residual-fold
randomization, and permutations for every `(batch, replication)` identity.

The official run identity is:

```text
batch-f7-collider-detection-20260824-001
```

Its output directory is:

```text
artifacts/batch-f7-collider-detection/batch-f7-collider-detection-20260824-001
```

For every attempted replication retain:

- F7 fixture identity and tested pair;
- observed dCor and permutation p-value;
- fixture, residual, and permutation seeds;
- a 1,000-row two-column residual sample;
- the 199-value permutation-null array;
- elapsed time, warnings, and exception text.

Write records, input manifest, report manifest, summary, memo, plots, and
run state atomically. The input and report manifests must pin the three
calibration hashes, copied boundary, configuration, seed namespace, run
ID, source revision, and hashes of retained F7 records. Refuse a
non-empty output directory.

## Verification and governance

Before the official run:

1. Write focused failing tests, then implement the runner and report
   paths.
2. Test all 100 x 10 identity handling with a reduced test configuration.
3. Test F7-only selection, the `(X1, X2)` pair, five-fold
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

This phase is limited to the F7 collider-detection claim. It does not
authorize recalibration, changing the residualizer, running another
fixture, expanding the simulation family, or starting package work.

- If the result is `PASS`: the frozen workflow correctly recognizes real,
  collider-induced dependence, reinforcing confidence in the narrow
  estimand's behavior under this structure. Gate 0 proceeds to the next
  untested canonical structure only as a separate, later owner decision.
- If the result is `NARROW` or `STOP`: stop for diagnosis without
  changing the ruler post hoc. This would indicate the workflow
  under-detects a genuine, correctly-expected relationship -- a different
  and arguably more concerning finding than F5's original STOP, since it
  would mean real signal is being lost even before any repair question
  arises. Any follow-up requires a separate, later, narrowly chartered
  study after an explicit owner decision.
