# Stage I clean mechanistic benchmark results

Per `docs/superpowers/specs/2026-08-25-stage1-mechanistic-benchmark-design.md`.
Not a Gate 0 study: no hash-pinned calibration, no single-official-run
ceremony, no per-replication artifact retention. This is 100 replications
per condition at `n = 1,000` rows, reusing every Step 4 component
(`redana/residuals.py`, `redana/dependence.py`, `redana/network.py`,
`redana/fdr.py`, `redana/scoring.py`, `redana/prototype.py`) unchanged.
Source revision: `02126233`.

## Condition A: linear fixture

`X1=e1, X2=0.7*X1+e2, X3=0.7*X2+e3, X4=e4, X5=e5, X6=e6`. True edges:
`{(X1,X2), (X2,X3)}`.

| Metric | Incumbent (mean / median / min-max) | Residual layer (mean / median / min-max) |
| --- | --- | --- |
| Precision | 0.642 / 0.667 / 0.286-1.000 | 0.932 / 1.000 / 0.500-1.000 |
| Recall | 1.000 / 1.000 / 1.000-1.000 | 1.000 / 1.000 / 1.000-1.000 |
| F1 | 0.763 / 0.800 / 0.444-1.000 | 0.959 / 1.000 / 0.667-1.000 |
| Exact-match fraction | 0.190 | 0.800 |

Residual per-edge detection: `(X1,X2)` 1.000, `(X2,X3)` 1.000 (both true
edges detected in all 100 replications).

## Condition B: pure nonlinear fixture

`X1=e1, X2=0.7*(X1^2-1)+e2, X3=e3, X4=0.7*(X3^2-1)+e4, X5=e5, X6=e6`
(zero linear covariance within each pair in population). True edges:
`{(X1,X2), (X3,X4)}`.

| Metric | Incumbent (mean / median / min-max) | Residual layer (mean / median / min-max) |
| --- | --- | --- |
| Precision | 0.050 / 0.000 / 0.000-1.000 | 0.963 / 1.000 / 0.667-1.000 |
| Recall | 0.025 / 0.000 / 0.000-0.500 | 1.000 / 1.000 / 1.000-1.000 |
| F1 | 0.033 / 0.000 / 0.000-0.667 | 0.978 / 1.000 / 0.800-1.000 |
| Exact-match fraction | 0.000 | 0.890 |

Residual per-edge detection: `(X1,X2)` 1.000, `(X3,X4)` 1.000 (both true
nonlinear edges detected in all 100 replications).

## Independent spot recompute

Without importing `redana.benchmark`, seed derivation
(`"stage1"|condition|index|base_seed"` through SHA-256, matching
`redana/dependence.py::derive_seed`) and both fixture generators'
formulas were reimplemented independently and evaluated at replication
indices 0, 50, and 99 for both conditions. All six recomputed seeds,
frame shapes, and true edge sets matched the actual project code
(`redana.dependence.derive_seed`, `redana.scenarios.generate_stage1_*`)
exactly -- zero mismatches. This does not replace a full from-raw-files
verifier (no per-replication artifacts exist to check against, by
design), but confirms the seed derivation and fixture definitions are
exactly what the spec and source claim.

## A convergence warning worth reporting

`sklearn.covariance.graphical_lasso` emitted `ConvergenceWarning:
did not converge after 100 iterations` on a number of fits during
Condition A (visible in the raw run output; not observed during
Condition B). This happens at specific points on the frozen 15-alpha
regularization grid (`NetworkConfig()` defaults, unchanged from Step 4)
and was not suppressed or investigated further here -- reporting it
plainly rather than filtering it out, consistent with this project's
practice throughout. It is a plausible contributor to the incumbent's
precision variability in Condition A (min 0.286) and is exactly the
kind of question `outline/plan.md` Stage II would characterize properly,
not something to patch reactively in this note.

## Interpretation against `plan.md` section 5's stated expectations

- **Linear fixture**: "the incumbent recovers the linear structure well"
  -- confirmed: recall 1.000 in every one of 100 replications. "The
  residual layer adds approximately nothing" -- only partially confirmed:
  the residual layer's recall also reached 1.000 every time (as
  expected, since it independently detects the same real edges), and its
  precision (mean 0.932) was actually *higher* than the incumbent's
  (mean 0.642) on this purely linear fixture -- the residual layer did
  not add spurious detections beyond the incumbent; if anything it was
  cleaner here. This is a stronger result on this specific point than
  `plan.md` §5's cautious phrasing anticipates, on this one fixture and
  dimension.
- **Pure nonlinear fixture**: "the incumbent may miss nonlinear-only
  structure" -- confirmed emphatically: mean recall 0.025, mean precision
  0.050, essentially unable to see this structure at all (as expected,
  since linear covariance is exactly zero in population). "The residual
  layer detects a useful proportion of it" -- confirmed and exceeded:
  100.000% per-edge detection across 100 replications for both nonlinear
  edges, mean precision 0.963.

Both conditions matched or exceeded `plan.md` §5's qualitative
expectations. The core mechanism answers the question Stage I asks:
**yes, the machinery detects the mechanism**, on both fixture types, at
this dimension, with this configuration.

## Explicit boundary

This is 100 replications per condition at one fixed dimension (`n=1,000`,
`p=6`), not a sweep. It does not:

- test sine, threshold/nonmonotonic, or interaction fixtures
  (`plan.md` §5's other named families, deferred to a later round);
- vary sample size, effect strength, noise, or any other dimension
  (`outline/plan.md` Stage II, §6, unstarted);
- compare methods at a matched operating point or false-positive rate
  (`plan.md` §8's comparator-fairness protocol, unstarted);
- explain the graphical-lasso convergence warnings noted above;
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 10, this result does not authorize Stage
II, the comparator-fairness protocol, additional fixture families, or
any package decision. Whether to proceed to Stage II, add the remaining
`plan.md` §5 fixture families to Stage I first, or investigate the
convergence warnings remains a separate, later owner decision.
