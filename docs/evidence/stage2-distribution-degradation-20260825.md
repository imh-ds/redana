# Stage II round 4 distribution degradation results

Per `docs/superpowers/specs/2026-08-25-stage2-distribution-degradation-design.md`.
Not a Gate 0 study: no hash-pinned calibration, no single-official-run
ceremony, no per-replication artifact retention. Six conditions (2
fixture shapes x 3 distribution levels), 50 replications each at
`n = 1,000` rows, `coefficient = 0.7` and `noise_scale = 1.0` held fixed
throughout, reusing every Step 4 / Stage I / Stage II component
unchanged except the new `distribution` parameter on the two Stage I
fixture generators. Source revision: `d8d20406`.

## A design confound, reported first because it changes how to read everything below

This round's `_draw_errors` helper (`redana/scenarios.py`) applies the
chosen distribution to **all six** error draws, including the source
variables (`e1`, `e3` in the nonlinear fixture), not just the downstream
residual terms. For the **skewed** distribution this breaks a property
the nonlinear fixture was built to guarantee: "zero linear covariance
with its source in population regardless of `coefficient`" (see
`generate_stage1_nonlinear_fixture`'s docstring). That guarantee relies
on the source variable `X1` being *symmetric*, since
`Cov(X1, X2) = coefficient * Cov(X1, X1^2) = coefficient * E[X1^3]` when
`E[X1] = 0`, and `E[X1^3] = 0` only for a symmetric distribution. The
skewed distribution used here (centered/scaled chi-squared, df=3) has
population skewness `~1.63`, so `E[X1^3] != 0`, and a large Monte Carlo
check (`n=200,000`) confirms a substantial genuine population-level
linear correlation: `corr(X1, X2) ~= 0.57` under `distribution="skewed"`,
versus `~-0.01` under `"gaussian"`.

**This means the nonlinear-fixture "skewed" condition below is not a
clean test of "does nonlinear detection degrade under skew" -- it is
partly a test of an accidentally-reintroduced linear relationship.** The
incumbent's high recall there (1.000) reflects that real, if unintended,
linear signal, not linear-network robustness to skewed nonlinear
structure. This was not anticipated in the design spec and is reported
here rather than smoothed over, per this project's practice of surfacing
surprising results honestly.

The **heavy_tailed** distribution (Student's t, df=3) is symmetric, so
it does not share this confound at the population level (Monte Carlo
check: `corr(X1,X2) ~= -0.06` under `"heavy_tailed"`, close to the
Gaussian baseline). The nonlinear fixture's incumbent recall still rose
substantially under `"heavy_tailed"` (0.670 vs. Gaussian's 0.020) in the
actual `n=1,000` runs below; the most plausible explanation is finite-sample
instability, not a population-level confound: `t_3` has infinite
theoretical kurtosis, so individual `n=1,000` samples can show large
spurious sample correlations driven by a small number of extreme values,
even though the population correlation is near zero. This is a
plausible but unverified explanation, not a tested claim.

The linear fixture's results below are not subject to either issue,
since a genuine linear relationship's population correlation does not
depend on the source distribution's symmetry the way the nonlinear
fixture's zero-covariance property does.

## Linear fixture across distribution levels

`X1=e1, X2=0.7*X1+e2, X3=0.7*X2+e3, X4=e4, X5=e5, X6=e6`, with `e1..e6`
drawn from the given distribution. True edges `{(X1,X2), (X2,X3)}`,
unchanged across levels.

| Level | Incumbent precision (mean/median) | Residual precision (mean/median) | Incumbent recall | Residual recall | Incumbent exact-match | Residual exact-match |
| --- | --- | --- | --- | --- | --- | --- |
| gaussian | 0.642 / 0.667 | 0.963 / 1.000 | 1.000 | 1.000 | 0.180 | 0.900 |
| skewed | 0.654 / 0.667 | 0.973 / 1.000 | 1.000 | 1.000 | 0.200 | 0.920 |
| heavy_tailed | 0.640 / 0.667 | 0.951 / 1.000 | 1.000 | 1.000 | 0.180 | 0.880 |

Residual per-edge detection fraction: **1.000 for both edges at all
three distribution levels.** All metrics are essentially flat across
distribution levels for the linear fixture -- no confound, no
degradation, for either mechanism.

## Nonlinear fixture across distribution levels

`X1=e1, X2=0.7*(X1^2-1)+e2, X3=e3, X4=0.7*(X3^2-1)+e4, X5=e5, X6=e6`,
with `e1..e6` drawn from the given distribution. True edges `{(X1,X2),
(X3,X4)}`, unchanged across levels. **Read the confound section above
before interpreting the `skewed` row.**

| Level | Incumbent precision (mean/median) | Residual precision (mean/median) | Incumbent recall | Residual recall | Incumbent exact-match | Residual exact-match |
| --- | --- | --- | --- | --- | --- | --- |
| gaussian | 0.040 / 0.000 | 0.967 / 1.000 | 0.020 | 1.000 | 0.000 | 0.900 |
| skewed | 0.778 / 0.667 | 0.957 / 1.000 | 1.000 | 1.000 | 0.460 | 0.880 |
| heavy_tailed | 0.740 / 1.000 | 0.957 / 1.000 | 0.670 | 1.000 | 0.340 | 0.880 |

Residual per-edge detection fraction: **1.000 for both edges at all
three distribution levels**, including `skewed` and `heavy_tailed`.

## Independent spot recompute

Without importing `redana.benchmark`, seed derivation and both fixture
generators' formulas (with the `distribution` parameter) were
reimplemented independently and evaluated at replication indices 0, 25,
and 49 for the `skewed` and `heavy_tailed` conditions on both fixture
shapes -- the two non-Gaussian levels, and therefore the most important
to double-check. All twelve recomputed seeds, frame shapes, and true
edge sets matched the actual project code exactly -- zero mismatches. A
separate large-`n` (`200,000`) Monte Carlo check (reported above)
confirmed the population-level correlation values underlying the
confound finding.

## Interpretation

**The residual layer's per-edge detection stayed at ceiling (1.000)
across every condition in this round, on both fixture shapes, including
the two non-Gaussian distributions.** This is consistent with the
permutation-based distance-correlation test and BH-FDR procedure making
no distributional assumption about the input data -- there was no reason
to expect distribution shape alone to degrade this mechanism, and it
did not.

**The nonlinear fixture's incumbent-recall results are not a clean
measurement of distribution degradation, because of the confound
described above.** The `skewed` row's high incumbent recall (1.000) is
substantially explained by a genuine, unintended linear relationship the
skewed source distribution introduces, not by the incumbent successfully
generalizing to non-Gaussian nonlinear structure. The `heavy_tailed`
row's elevated incumbent recall (0.670, vs. 0.020 at gaussian) is not
explained by a population-level confound (Monte Carlo check found
population correlation near zero) and is more plausibly finite-sample
instability from `t_3`'s heavy tails, though this explanation is not
independently verified here.

**The linear fixture is unaffected by either issue and shows no
meaningful change across distribution levels for either mechanism** --
the cleanest read this round produces: distribution shape alone, when
it does not interact with fixture construction, does not measurably
change detection for structure that genuinely has the claimed
population properties.

## A convergence warning worth reporting

`sklearn.covariance.graphical_lasso` again emitted `ConvergenceWarning:
did not converge after 100 iterations` on a substantial number of fits,
across all six conditions, matching every prior round's evidence notes.
Reported plainly again rather than investigated or suppressed.

## Explicit boundary

This round tested exactly one of `plan.md` §6's remaining degradation
dimensions (distribution), at one fixed effect strength and noise level.
It does not:

- provide a clean measurement of nonlinear-detection-under-skew, due to
  the confound identified above -- a corrected fixture (applying
  distribution shape only to downstream residual terms, `e2`/`e4`,
  leaving the source variables `e1`/`e3` Gaussian, mirroring round 3's
  `noise_scale` design) would be needed to isolate that question
  cleanly, and is not attempted here;
- independently verify the finite-sample-instability explanation offered
  for the `heavy_tailed` nonlinear result (e.g. by re-running at a much
  larger `n` to see whether incumbent recall falls back toward the
  Gaussian baseline);
- test residual-variance, measurement-quality, or network-structure
  degradation (`plan.md` §6's remaining dimensions);
- compare methods at a matched operating point (`plan.md` §8);
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 10, this result does not authorize
further Stage II rounds, a corrected re-run of this dimension, the
comparator-fairness protocol, or any package decision. The corrected
source-preserving distribution fixture this note identifies as the
natural fix for the confound is a separate, later owner decision, not an
automatic next step -- the confound is reported here as a finding, not
silently patched and re-run.
