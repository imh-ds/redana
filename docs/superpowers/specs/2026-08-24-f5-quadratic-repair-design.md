# F5 explicit-quadratic residualization repair design

## Purpose

Test one pre-specified repair for the known F5 nonlinear residual-null
limitation. The original F5 transfer run stopped: its spline-plus-Ridge
residualizer left enough residual association to fail the frozen batch rule.
This experiment asks only whether a simple, explicit quadratic adjustment
basis resolves that exact F5 null at the planned 1,000-row workflow.

It is neither a new calibration nor a general claim about nonlinear
residualization. It does not start package work.

## Fixed scenario and sole design change

Reuse the original F5 conditional-independence null without modification:

```text
Z  = X3
P  = 0.7 * (Z^2 - 1)
X1 = P + e1
X2 = P + e2
```

`e1` and `e2` are independent standard-normal noises. `X4`, `X5`, and `X6`
are the same independent adjustment variables as in F5. Test `(X1, X2)` after
adjustment for `(X3, X4, X5, X6)`. Each replication has 1,000 rows and uses
all cross-fitted residual pairs for the statistic.

Replace only the original spline feature map. For each adjustment variable,
the repair basis contains its raw value and its squared value, in adjustment
variable order. It contains no pairwise interactions, higher powers, splines,
adaptive basis selection, or data-dependent feature search. A scaler then
Ridge regression with alpha 1 is fitted within each training fold. Residuals
remain strictly held out using five shuffled cross-fitting folds.

The targeted rationale is deliberately narrow: the F5 common cause is
quadratic in `X3`, and the supplied basis represents that form directly.
Success would show an exact-structure repair for F5, not general nonlinear
robustness.

## Frozen rule and provenance

Use 199 permutations and the unchanged 100 batches x 10 replications policy.
Read and hash-verify the raw-reference calibration at
`artifacts/batch-null-calibration/batch-null-calibration-20260821-001` and
copy its boundary unchanged:

```text
0.058242447845091264
```

The calibration hashes to pin are records
`267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`, input
manifest `7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c`,
and report manifest
`639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`.

Also pin the original F5 STOP evidence as the comparison baseline:

- records SHA-256: `3f38ac7f324c597cf13b84006cf1af35fbce0fb30b497ef2629b29b79a7fee09`;
- input-manifest SHA-256: `b16367ef572f906df2653447558e31047e0cda0943d3d774725546f213902251`;
- report-manifest SHA-256: `521f35953929d46670eb90687e6a4645684f335d878b90090029c31d87c8dce2`;
- recorded terminal outcome: `STOP` (74 null-like batches; 81 low p-values).

A batch is null-like when at most two of its ten p-values are at or below
0.05 and its median dCor is at or below the copied boundary. The terminal
outcomes retain the established precedence:

1. `STOP`: incomplete or malformed evidence, any retained exception, or more
   than 67 low p-values;
2. `NARROW`: complete evidence with at most 67 low p-values, but fewer than
   85 null-like batches;
3. `PASS`: complete evidence, at least 85 null-like batches, and at most 67
   low p-values.

No threshold, calibration input, sample size, replication count, fixture, or
other residualizer setting changes after results are known.

## Execution, retention, and verification

Use the distinct seed namespace `batch-f5-quadratic-repair`. The official run
identity and output directory are:

```text
batch-f5-quadratic-repair-20260824-001
artifacts/batch-f5-quadratic-repair/batch-f5-quadratic-repair-20260824-001
```

Refuse a non-empty output directory. Retain every attempted record's exact
unsigned fixture, fold, and permutation seeds; dCor; p-value; warnings;
exception text; elapsed time; a 1,000-row two-column residual sample; and a
199-value permutation-null array. Atomically write records, input manifest,
report manifest, summary, memo, plot, and state. The manifests must include
both pinned evidence sets, boundary, configuration, source revision, run ID,
seed namespace, and record hashes.

Before the official run, add focused tests for: the raw-plus-square feature
matrix in the prescribed order; absence of interactions and spline features;
five-fold held-out residualization; F5-only fixture and pair selection;
identity and seed coverage; retained arrays and samples; provenance failure;
malformed evidence; and non-empty output refusal. Run focused tests, the full
suite, and lint; commit source before the one official run. Independently
recompute the committed evidence after the run.

## Governance and interpretation

Perform one official run and retain evidence regardless of outcome. Do not
retry with changed seeds, search bases, add interactions, alter the boundary,
recalibrate, add a nonlinear alternative, or begin package implementation.

- `PASS` supports only that this explicit raw-plus-square basis repairs the
  prescribed F5 quadratic null under this frozen 1,000-row procedure. A
  separate owner decision is required before a matched nonlinear alternative.
- `NARROW` means the repair improved the result enough to clear the p-value
  cap but not the strict batch-count requirement; record it without tuning.
- `STOP` means the repair did not establish clean transfer under the frozen
  rule; record it and stop for diagnosis.
