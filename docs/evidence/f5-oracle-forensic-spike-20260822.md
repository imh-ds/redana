# F5 oracle-residual forensic spike

## Scope and status

This read-only forensic analysis examines committed F5 transfer evidence. It
creates no new simulation artifact, changes no calibration, and does not alter
the F5 terminal result.

- F5 evidence commit: `bb74631`
- F5 run ID: `batch-f5-null-transfer-20260821-001`
- Frozen boundary: `0.058242447845091264`
- F5 outcome: `STOP`

## Question and method

F5 stopped with 74 null-like batches and 81 low p-values. To distinguish a
raw-reference-ruler problem from fitted-residualization error, all 1,000
retained F5 identities were regenerated from their retained fixture seeds.
The oracle noises `e1` and `e2` were reconstructed from F5's exact generator
and assessed with the same retained permutation seed and 199 permutations.
These oracle results were compared with the committed cross-fitted residual
records under the same frozen boundary and batch policy.

This is a diagnostic aid, not a new confirmatory simulation.

## Results

| Residual representation | Null-like batches | Low p-values | Rule result |
| --- | ---: | ---: | --- |
| Oracle independent noises | 83 / 100 | 63 / 1,000 | `NARROW` |
| Fitted cross-fitted residuals | 74 / 100 | 81 / 1,000 | `STOP` |

The oracle p-value cap passed (63 is at most 67), but 17 batch medians exceeded
the boundary, leaving 83 rather than the required 85 null-like batches. This
is compatible with the strict precommitted rule having a nonzero false-NARROW
probability in a finite 100-batch draw.

Fitted residuals were materially less null-like than oracle noises:

- fitted-minus-oracle dCor median: `+0.001795`; mean: `+0.001920`;
- positive difference in 619 of 1,000 identities;
- 10 batches changed from oracle median-pass to fitted median-fail, versus two
  in the reverse direction;
- fitted residuals remained close to oracle noises (median endpoint correlation
  about `0.979`; median standardized-unit RMSE about `0.149`).

## Interpretation and decision

The spike does not establish that the raw-reference ruler is inherently
invalid: this true-null oracle realization narrowly missed the strict batch
criterion but did not breach the low-p cap. It does show an additional upward
dCor and low-p shift after F5's fitted nonlinear residualization. The F5 STOP
therefore combines ordinary finite-batch variation and residualization error
large enough to affect the diagnostic.

Decision: do not recalibrate, relax thresholds, repeat F5, or run a dependent
alternative. Precommit an F4 linear residual-null transfer with the same
1,000-row dimensions and frozen rule. That test separates nonlinear F5
approximation limitations from a general residualization-transfer problem.
Package work remains out of scope.
