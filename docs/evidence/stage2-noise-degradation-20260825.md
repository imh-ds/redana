# Stage II round 3 noise degradation results

Per `docs/superpowers/specs/2026-08-25-stage2-noise-degradation-design.md`.
Not a Gate 0 study: no hash-pinned calibration, no single-official-run
ceremony, no per-replication artifact retention. Six conditions (2
fixture shapes x 3 noise levels), 50 replications each at `n = 1,000`
rows, `coefficient = 0.7` held fixed throughout (Stage I's strong
baseline), reusing every Step 4 / Stage I / Stage II component unchanged
except the new `noise_scale` parameter on the two Stage I fixture
generators. Source revision: `09cb300f`.

## Linear fixture across noise levels

`X1=e1, X2=0.7*X1+noise_scale*e2, X3=0.7*X2+noise_scale*e3, X4=e4,
X5=e5, X6=e6`. True edges `{(X1,X2), (X2,X3)}`, unchanged across levels.

| Level | Incumbent precision (mean/median) | Residual precision (mean/median) | Incumbent recall | Residual recall | Incumbent exact-match | Residual exact-match |
| --- | --- | --- | --- | --- | --- | --- |
| low (0.5) | 0.385 / 0.400 | 0.963 / 1.000 | 1.000 | 1.000 | 0.000 | 0.900 |
| moderate (1.0) | 0.602 / 0.500 | 0.928 / 1.000 | 1.000 | 1.000 | 0.140 | 0.800 |
| high (2.0) | 0.724 / 0.667 | 0.953 / 1.000 | 1.000 | 1.000 | 0.340 | 0.860 |

Residual per-edge detection fraction: **1.000 for both edges at all
three noise levels.**

## Nonlinear fixture across noise levels

`X1=e1, X2=0.7*(X1^2-1)+noise_scale*e2, X3=e3,
X4=0.7*(X3^2-1)+noise_scale*e4, X5=e5, X6=e6`. True edges `{(X1,X2),
(X3,X4)}`, unchanged across levels.

| Level | Incumbent precision (mean/median) | Residual precision (mean/median) | Incumbent recall | Residual recall | Incumbent exact-match | Residual exact-match |
| --- | --- | --- | --- | --- | --- | --- |
| low (0.5) | 0.060 / 0.000 | 0.930 / 1.000 | 0.030 | 1.000 | 0.000 | 0.800 |
| moderate (1.0) | 0.000 / 0.000 | 0.987 / 1.000 | 0.000 | 1.000 | 0.000 | 0.960 |
| high (2.0) | 0.020 / 0.000 | 0.967 / 1.000 | 0.010 | 1.000 | 0.000 | 0.900 |

Residual per-edge detection fraction: **1.000 for both edges at all
three noise levels.**

## Independent spot recompute

Without importing `redana.benchmark`, seed derivation and both fixture
generators' formulas (with the `noise_scale` parameter) were
reimplemented independently and evaluated at replication indices 0, 25,
and 49 for the four most extreme conditions (`stage2-noise-linear-low`,
`stage2-noise-linear-high`, `stage2-noise-nonlinear-low`,
`stage2-noise-nonlinear-high`) -- the two noise extremes on both fixture
shapes. All twelve recomputed seeds, frame shapes, and true edge sets
matched the actual project code exactly -- zero mismatches.

## Interpretation

**No cliff along the noise axis for the residual layer, on either
fixture shape.** Per-edge detection stayed at ceiling (1.000) across the
full tested noise range (`noise_scale` 0.5 to 2.0) for both the linear
and nonlinear fixtures. Combined with round 2's relationship-shape
result (also no cliff, holding effect strength fixed), this round adds
a second independent dimension along which the residual layer showed no
degradation at `coefficient = 0.7`. So far, only the effect-strength
dimension itself (round 1) has produced a detectability cliff for the
residual layer.

**The incumbent's linear-fixture recall also never degraded (stayed at
1.000 throughout), but its precision rose monotonically with noise**
(mean 0.385 -> 0.602 -> 0.724 as `noise_scale` went 0.5 -> 1.0 -> 2.0).
This is the same counter-intuitive pattern already flagged in
`docs/evidence/stage2-effect-strength-degradation-20260825.md`, where
incumbent precision rose as the *signal* weakened (lower `coefficient`)
rather than degrading. Here the *noise* increases instead of the signal
decreasing, but both manipulations lower the same underlying
signal-to-noise ratio -- and produce the same directional effect on
incumbent precision. This strengthens the case that the pattern is a
real, reproducible property of the incumbent's EBIC-selected
graphical-lasso behavior under a weakening signal-to-noise ratio (from
either side), not noise in a single round's results. It remains
unexplained mechanistically; still not resolved here.

**The nonlinear fixture's incumbent recall stayed near zero throughout**
(0.030, 0.000, 0.010), as expected -- linear covariance is exactly zero
in population for this shape regardless of `noise_scale`, so the
incumbent has no signal to find whether noise is low or high.

## A convergence warning worth reporting

`sklearn.covariance.graphical_lasso` again emitted `ConvergenceWarning:
did not converge after 100 iterations` on a substantial number of fits,
across all six conditions, matching what was already noted in Stage I,
Stage II round 1, and Stage II round 2's evidence notes. Reported
plainly again rather than investigated or suppressed.

## Explicit boundary

This round tested exactly one of `plan.md` §6's remaining degradation
dimensions (noise), at one fixed effect strength (`coefficient=0.7`), on
Stage I's two existing fixture shapes. It does not:

- test noise degradation at any effect strength other than `0.7`
  (whether the "no cliff along noise" finding holds near round 1's
  already-found strength cliff, i.e. whether noise and strength
  interact, is an open question this note does not answer);
- test distribution, residual-variance, measurement-quality, or
  network-structure degradation (`plan.md` §6's remaining dimensions);
- explain the incumbent's precision-vs-noise pattern mechanistically,
  beyond noting its consistency with round 1's precision-vs-strength
  pattern;
- compare methods at a matched operating point (`plan.md` §8);
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 10, this result does not authorize
further Stage II rounds, the comparator-fairness protocol, or any
package decision. Two natural follow-up questions this note surfaces but
does not answer -- whether noise and effect strength interact near
round 1's cliff, and what mechanistically drives the incumbent's rising
precision under a weakening signal-to-noise ratio from either
direction -- remain separate, later owner decisions, not automatic next
steps.
