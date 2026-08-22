# F4 linear residual-null transfer design

## Purpose

Test whether the frozen 1,000-row raw-reference rule transfers through
residualization in existing F4 linear conditional independence. This separates
F5's likely nonlinear-approximation limitation from a broader transfer issue.

## Fixed scenario

Reuse F4 exactly: `X1 -> X2 -> X3`, with independent `X4`--`X6`. Test
`(X1, X3)` after cross-fitted adjustment for `(X2, X4, X5, X6)`. Each of 100
batches x 10 replications generates 1,000 rows, uses all 1,000 residual pairs,
five shuffled folds, five-knot cubic quantile splines, scaler, Ridge alpha 1,
and 199 permutations.

## Frozen rule

Read and hash-verify `artifacts/batch-null-calibration/batch-null-calibration-20260821-001`.
Copy boundary `0.058242447845091264` without recalibration. A batch is
null-like when at most two p-values are at or below .05 and its median dCor is
at or below the boundary. `PASS` needs at least 85 null-like batches and at
most 67 low p-values; `NARROW` misses only the batch count; `STOP` covers
incomplete/malformed evidence, retained exceptions, or more than 67 low p-values.

## Retention

Use namespace `batch-f4-linear-null-transfer`. Retain every fixture,
residual, and permutation UInt64 seed; F4/pair identity; dCor/p-value; a
1,000-row residual sample; a 199-value null array; warnings, exceptions, and
elapsed time. Pin calibration hashes, boundary, source revision, configuration,
and record hashes in atomic manifests, summary, plot, memo, and state.

Official identity and directory: `batch-f4-linear-null-transfer-20260822-001`
and `artifacts/batch-f4-linear-null-transfer/batch-f4-linear-null-transfer-20260822-001`.
Refuse non-empty output.

## Governance

Write tests first, pass focused tests/full suite/lint, commit source, run once,
commit evidence, and independently recompute all retained claims. No
recalibration, F5 repeat, dependent alternative, other fixture, or package work
follows automatically. A reviewed PASS supports a nonlinear F5 limitation; a
reviewed NARROW or STOP supports a broader residualization-transfer concern.
