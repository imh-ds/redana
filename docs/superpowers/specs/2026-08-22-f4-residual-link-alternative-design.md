# F4 residual-link alternative design

## Purpose

Test whether the frozen 1,000-row workflow detects one clear, intentional
linear residual dependence after adjustment. This is the matched alternative
to the reviewed F4 linear residual-null PASS.

## Fixed scenario

For each 1,000-row replication, use independent standard-normal errors and
independent X4--X6:

```text
X1 = e1
X2 = 0.7 * X1 + e2
X3 = 0.7 * X2 + 0.7 * e1 + e3
```

Test `(X1, X3)` after cross-fitted adjustment for `(X2, X4, X5, X6)`. The
`0.7 * e1` term remains after adjustment. Freeze five folds, five-knot cubic
quantile splines, scaling, Ridge alpha 1, all 1,000 residual rows, and 199
permutations.

## Detection rule

Copy raw-reference boundary `0.058242447845091264` as dCor effect-size
threshold only; do not recalibrate. Across 100 batches of 10:

- detected batch: median dCor strictly above boundary and at least 8/10
  p-values at or below .05;
- PASS: at least 85 detected batches;
- NARROW: complete evidence but fewer than 85 detected batches;
- STOP: incomplete/malformed evidence, retained exceptions, or invalidating
  warnings.

This is a clear-signal sensitivity check, not a weak-effect power claim.

## Retention and governance

Use namespace `batch-f4-residual-link`; retain all exact UInt64 seeds, records,
1,000 residual samples, 199-value arrays, warnings, exceptions, elapsed time,
manifests, summary, plot, memo, and state. Pin reviewed F4-null evidence and
all raw-reference calibration hashes. Official output is
`artifacts/batch-f4-residual-link/batch-f4-residual-link-20260822-001` with
run ID `batch-f4-residual-link-20260822-001`; refuse nonempty output.

Write tests first, pass preflight, commit source, run once, commit evidence,
and independently review it. Do not change signal, residualizer, thresholds,
or rule after results. PASS supports this one clear link only; no automatic
package work or successor simulation follows.
