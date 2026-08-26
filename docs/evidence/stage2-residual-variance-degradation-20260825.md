# Stage II round 5 residual-variance degradation results

Per `docs/superpowers/specs/2026-08-25-stage2-residual-variance-degradation-design.md`.
Not a Gate 0 study: no hash-pinned calibration, no single-official-run
ceremony, no per-replication artifact retention. Six conditions (2
fixture shapes x 3 heteroskedasticity levels), 50 replications each at
`n = 1,000` rows, `coefficient = 0.7`, `noise_scale = 1.0`, and
`distribution = "gaussian"` held fixed throughout, reusing every Step 4
/ Stage I / Stage II component unchanged except the new
`heteroskedasticity` parameter on the two Stage I fixture generators.
Source revision: `7ea6a1db`.

## Confound guard, checked before interpreting results

Round 4 found that applying a distributional change to a *source*
variable (not just downstream noise) silently reintroduced a genuine
linear relationship into the nonlinear fixture, confounding that round's
`skewed` condition. This round's `heteroskedasticity` multiplier is
scoped identically to round 3's `noise_scale` -- it scales only each
downstream variable's own residual noise term by `(1 +
heteroskedasticity * abs(source))`, never touching a source variable's
own draw -- specifically to avoid repeating that confound.
`tests/redana/test_stage2_residual_variance_scenarios.py::test_heteroskedasticity_does_not_reintroduce_linear_covariance_in_the_nonlinear_fixture`
verifies this automatically at `n=50,000` for all three levels, and an
additional large-`n` (`200,000`) check at the actual `coefficient=0.7`
configuration used in this round's runs confirmed
`corr(X1,X2) ~= -0.005` and `corr(X3,X4) ~= 0.004` under
`heteroskedasticity=1.0` -- both indistinguishable from zero. **No
round-4-style confound was found in this round.**

## Linear fixture across heteroskedasticity levels

`X1=e1, X2=0.7*X1+(1+het*|X1|)*e2, X3=0.7*X2+(1+het*|X2|)*e3, X4=e4,
X5=e5, X6=e6`. True edges `{(X1,X2), (X2,X3)}`, unchanged across levels.

| Level | Incumbent precision (mean/median) | Residual precision (mean/median) | Incumbent recall | Residual recall | Incumbent exact-match | Residual exact-match |
| --- | --- | --- | --- | --- | --- | --- |
| homoskedastic (0.0) | 0.643 / 0.667 | 0.943 / 1.000 | 1.000 | 1.000 | 0.180 | 0.840 |
| moderate (0.5) | 0.719 / 0.667 | 0.943 / 1.000 | 1.000 | 1.000 | 0.360 | 0.840 |
| strong (1.0) | 0.797 / 0.667 | 0.953 / 1.000 | 1.000 | 1.000 | 0.460 | 0.860 |

Residual per-edge detection fraction: **1.000 for both edges at all
three heteroskedasticity levels.**

## Nonlinear fixture across heteroskedasticity levels

`X1=e1, X2=0.7*(X1^2-1)+(1+het*|X1|)*e2, X3=e3,
X4=0.7*(X3^2-1)+(1+het*|X3|)*e4, X5=e5, X6=e6`. True edges `{(X1,X2),
(X3,X4)}`, unchanged across levels.

| Level | Incumbent precision (mean/median) | Residual precision (mean/median) | Incumbent recall | Residual recall | Incumbent exact-match | Residual exact-match |
| --- | --- | --- | --- | --- | --- | --- |
| homoskedastic (0.0) | 0.040 / 0.000 | 0.927 / 1.000 | 0.030 | 1.000 | 0.020 | 0.780 |
| moderate (0.5) | 0.040 / 0.000 | 0.960 / 1.000 | 0.020 | 1.000 | 0.000 | 0.880 |
| strong (1.0) | 0.140 / 0.000 | 0.977 / 1.000 | 0.070 | 1.000 | 0.000 | 0.940 |

Residual per-edge detection fraction: **1.000 for both edges at all
three heteroskedasticity levels.**

## Independent spot recompute

Without importing `redana.benchmark`, seed derivation and both fixture
generators' formulas (with the `heteroskedasticity` parameter) were
reimplemented independently and evaluated at replication indices 0, 25,
and 49 for the `homoskedastic` and `strong` conditions on both fixture
shapes. All twelve recomputed seeds, frame shapes, and true edge sets
matched the actual project code exactly -- zero mismatches.

## Interpretation

**No cliff along the residual-variance axis for the residual layer, on
either fixture shape.** Per-edge detection stayed at ceiling (1.000)
across the full tested heteroskedasticity range for both fixtures. This
is now the third of four tested dimensions (after relationship shape and
noise) showing no degradation for the residual layer at
`coefficient = 0.7`; only effect strength itself (round 1) has produced
a detectability cliff so far.

**The incumbent's precision again rose monotonically with the degrading
dimension, on both fixture shapes** (linear: mean `0.643 -> 0.719 ->
0.797`; nonlinear: mean `0.040 -> 0.040 -> 0.140`, all at essentially
floor-level recall). This is the third round in a row (after round 1's
effect-strength sweep and round 3's noise sweep) to show incumbent
precision rising as some form of signal-to-noise ratio weakens --
heteroskedasticity, like noise_scale, widens the effective noise
variance without shifting the systematic relationship, so this is
consistent with, and further strengthens, the pattern already flagged
as unexplained in rounds 1 and 3.

**The nonlinear fixture's incumbent recall stayed low throughout but
ticked up slightly at the strong level** (0.030 -> 0.020 -> 0.070). This
is a small absolute change (7 percentage points at most) on a
metric whose population value should be exactly zero regardless of
heteroskedasticity (confirmed above), so this is most plausibly ordinary
finite-sample noise at `n=1,000`, not a real effect -- but it is reported
as observed rather than dismissed without comment.

## A convergence warning worth reporting

`sklearn.covariance.graphical_lasso` again emitted `ConvergenceWarning:
did not converge after 100 iterations` on a substantial number of fits,
across all six conditions, matching every prior round's evidence notes.
Reported plainly again rather than investigated or suppressed.

## Explicit boundary

This round tested exactly one of `plan.md` §6's remaining degradation
dimensions (residual variance), at one fixed effect strength, noise
level, and distribution. It does not:

- test residual-variance degradation at any effect strength other than
  `0.7` (whether the "no cliff" finding holds near round 1's already-
  found strength cliff is an open question this note does not answer,
  matching the same open question left by rounds 2, 3, and 4);
- test measurement-quality or network-structure degradation
  (`plan.md` §6's remaining two dimensions);
- explain the incumbent's precision-vs-heteroskedasticity pattern
  mechanistically, beyond noting its consistency with rounds 1 and 3's
  precision-vs-signal-to-noise-ratio pattern;
- compare methods at a matched operating point (`plan.md` §8);
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 10, this result does not authorize
further Stage II rounds, the comparator-fairness protocol, or any
package decision. Two natural follow-up questions this note surfaces but
does not answer -- whether any of the four "no cliff" dimensions
(shape, noise, distribution, residual variance) interact with effect
strength near round 1's cliff, and what mechanistically drives the
incumbent's rising precision under a weakening signal-to-noise ratio
across three independent manipulations now -- remain separate, later
owner decisions, not automatic next steps. Only two of `plan.md` §6's
seven named dimensions (measurement quality, network structure) remain
untested.
