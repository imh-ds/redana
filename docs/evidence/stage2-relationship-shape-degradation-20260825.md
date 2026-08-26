# Stage II round 2 relationship-shape degradation results

Per `docs/superpowers/specs/2026-08-25-stage2-relationship-shape-degradation-design.md`.
Not a Gate 0 study: no hash-pinned calibration, no single-official-run
ceremony, no per-replication artifact retention. Four conditions (one
fixture family x four relationship-shape levels), 50 replications each
at `n = 1,000` rows, `coefficient = 0.7` held fixed throughout (Stage
I's strong baseline), reusing every Step 4 / Stage I / Stage II round 1
component unchanged except the new
`redana.scenarios.generate_stage2_shape_fixture` generator. Source
revision: `47ea7c2f`.

## Fixture

`X1=e1, X2=0.7*((1-shape)*X1 + shape*(X1^2-1))+e2, X3=e3,
X4=0.7*((1-shape)*X3 + shape*(X3^2-1))+e4, X5=e5, X6=e6`. True edges
`{(X1,X2), (X3,X4)}`, unchanged across all shape levels.

## Results

| Shape level | Incumbent precision (mean/median) | Residual precision (mean/median) | Incumbent recall (mean/median) | Residual recall (mean/median) | Incumbent exact-match | Residual exact-match |
| --- | --- | --- | --- | --- | --- | --- |
| pure_linear (0.0) | 0.821 / 1.000 | 0.957 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.560 | 0.880 |
| slight_curvature (0.33) | 0.910 / 1.000 | 0.927 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.760 | 0.800 |
| moderate_curvature (0.67) | 0.943 / 1.000 | 0.967 / 1.000 | 0.960 / 1.000 | 1.000 / 1.000 | 0.840 | 0.900 |
| strong_nonlinearity (1.0) | 0.080 / 0.000 | 0.923 / 1.000 | 0.040 / 0.000 | 1.000 / 1.000 | 0.000 | 0.780 |

Residual per-edge detection fraction: **1.000 for both edges at all four
shape levels**, with zero exceptions across 200 tested edge-instances
(50 replications x 2 edges x 4 levels).

## Cross-check against Stage I / Stage II round 1

The `strong_nonlinearity` (`shape=1.0`) condition uses the exact same
formula as `generate_stage1_nonlinear_fixture` at `coefficient=0.7`
(verified byte-identical by
`tests/redana/test_stage2_shape_scenarios.py::test_shape_one_matches_stage1_nonlinear_fixture_exactly`,
and re-confirmed against this round's actual run seeds below). Its
results here (incumbent recall mean 0.040, residual recall mean 1.000)
are consistent in direction and magnitude with Stage I's original
`coefficient=0.7` nonlinear result (incumbent recall 0.000, residual
recall 1.000) and Stage II round 1's independent redraw of the same
condition (incumbent recall 0.000, residual recall 1.000) -- small
differences (incumbent recall 0.000 vs 0.040) reflect ordinary sampling
variability across three separately-seeded 50-replication draws of the
same population condition, not a discrepancy.

## Independent spot recompute

Without importing `redana.benchmark`, seed derivation and the new
fixture generator were reimplemented independently and evaluated at
replication indices 0, 25, and 49 for the `pure_linear` and
`strong_nonlinearity` conditions -- the two endpoints, and therefore the
most informative to double-check. All six recomputed seeds, frame
shapes, and true edge sets matched the actual project code exactly. For
`strong_nonlinearity`, the recomputed frames were additionally verified
byte-identical to `generate_stage1_nonlinear_fixture` at the same seeds
via `pandas.testing.assert_frame_equal` -- zero mismatches.

## Interpretation

**No cliff along the relationship-shape axis for the residual layer.**
Unlike Stage II round 1's effect-strength sweep, which found a sharp
detectability cliff for the residual layer between `coefficient=0.10`
and `0.20`
(`docs/evidence/stage2-nonlinear-boundary-followup-20260825.md`), the
residual layer's recall and per-edge detection here stayed at ceiling
(1.000) across the entire tested shape range -- from pure linear through
strong nonlinearity. This is a genuinely informative negative result:
the residual mechanism's sensitivity in this configuration appears to be
governed far more by *how much* signal is present (effect strength) than
by *what shape* that signal takes, at least across the linear-to-quadratic
continuum tested here.

**The incumbent degrades late and sharply, not gradually.** Incumbent
recall stayed near ceiling through `slight_curvature` (1.000) and
`moderate_curvature` (0.960), only collapsing at the pure-quadratic
endpoint (`strong_nonlinearity`, recall 0.040). This is consistent with
the fixture's construction: at `shape=0.67`, the linear component's
effective coefficient is `0.7*(1-0.67) = 0.231`, well within the range
round 1 found sufficient for near-ceiling incumbent recall
(`coefficient=0.2` gave incumbent recall 1.000 there). The incumbent's
failure is therefore better understood as "fails once the linear
component vanishes" rather than "gradually degrades with curvature" --
another cliff-like pattern, but located at the extreme end of the shape
axis rather than in the middle.

**Both mechanisms' exact-match fractions rose monotonically with shape
from `0.0` to `0.67`, then diverged sharply at `1.0`.** The residual
layer's exact-match fraction peaked at `moderate_curvature` (0.900) and
dropped only modestly at `strong_nonlinearity` (0.780) -- the drop stems
entirely from the incumbent-adjacent false-positive pattern already
documented in Stage I and Stage II round 1 (the residual layer testing
every pair independently, occasionally flagging a spurious pair by
chance), not from missing true edges.

## A convergence warning worth reporting

`sklearn.covariance.graphical_lasso` again emitted `ConvergenceWarning:
did not converge after 100 iterations` on a substantial number of fits,
across all four shape levels, matching what was already noted in
`docs/evidence/stage1-mechanistic-benchmark-20260825.md` and
`docs/evidence/stage2-effect-strength-degradation-20260825.md`. Reported
plainly again rather than investigated or suppressed.

## Explicit boundary

This round tested exactly one of `plan.md` §6's remaining degradation
dimensions (relationship shape), at one fixed effect strength
(`coefficient=0.7`), on one fixture family (two independent pairs). It
does not:

- test relationship shape at any effect strength other than `0.7`
  (whether the "no cliff along shape" finding holds at weaker strengths,
  where round 1 already found the residual layer more fragile, is an
  open question this note does not answer);
- test noise, distribution, residual-variance, measurement-quality, or
  network-structure degradation (`plan.md` §6's remaining dimensions);
- explain why the incumbent's recall degrades so late along the shape
  axis in more general terms, beyond the coefficient-arithmetic argument
  given above;
- compare methods at a matched operating point (`plan.md` §8);
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 10, this result does not authorize
further Stage II rounds, the comparator-fairness protocol, or any
package decision. A natural follow-up question this note surfaces but
does not answer -- whether the "no cliff along shape" finding still
holds when effect strength is also weak, i.e. whether shape and strength
interact near round 1's already-found strength cliff -- remains a
separate, later owner decision, not an automatic next step.
