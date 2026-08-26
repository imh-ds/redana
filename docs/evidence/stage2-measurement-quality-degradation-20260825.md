# Stage II round 6 measurement-quality degradation results

Per `docs/superpowers/specs/2026-08-25-stage2-measurement-quality-degradation-design.md`.
Not a Gate 0 study: no hash-pinned calibration, no single-official-run
ceremony, no per-replication artifact retention. Six conditions (2
fixture shapes x 3 measurement-error levels), 50 replications each at
`n = 1,000` rows, `coefficient = 0.7`, `noise_scale = 1.0`,
`distribution = "gaussian"`, and `heteroskedasticity = 0.0` held fixed
throughout, reusing every Step 4 / Stage I / Stage II component
unchanged except the new `measurement_error` parameter (a
post-processing step applied to all six columns) on the two Stage I
fixture generators. Source revision: `f7788fd0`.

## Confound guard, checked before interpreting results

Independent, zero-mean measurement noise added to an already-realized
column cannot shift a conditional mean, so this round should not repeat
round 4's source-distribution confound.
`tests/redana/test_stage2_measurement_quality_scenarios.py::test_measurement_error_does_not_reintroduce_linear_covariance_in_the_nonlinear_fixture`
verifies this automatically at `n=50,000`, and an additional large-`n`
(`200,000`) check at the actual `coefficient=0.7` configuration used in
this round's runs confirmed `corr(X1,X2) ~= -0.003` and
`corr(X3,X4) ~= 0.002` under `measurement_error=1.0` -- both
indistinguishable from zero. **No round-4-style confound was found in
this round.**

## Linear fixture across measurement-error levels

Each column `X1`-`X6` gets independent Gaussian noise added with
variance `measurement_error * column.var()` (reliability `1 / (1 +
measurement_error)`). True edges `{(X1,X2), (X2,X3)}`, unchanged across
levels.

| Level | Incumbent precision (mean/median) | Residual precision (mean/median) | Incumbent recall | Residual recall | Incumbent exact-match | Residual exact-match |
| --- | --- | --- | --- | --- | --- | --- |
| perfect (0.0) | 0.637 / 0.667 | 0.970 / 1.000 | 1.000 | 1.000 | 0.200 | 0.920 |
| modest (0.25) | 0.614 / 0.667 | 0.833 / 1.000 | 1.000 | 1.000 | 0.020 | 0.540 |
| substantial (1.0) | 0.604 / 0.667 | 0.731 / 0.667 | 1.000 | 1.000 | 0.020 | 0.260 |

Residual per-edge detection fraction: **1.000 for both edges at all
three levels** -- recall never dropped, but precision and exact-match
fraction fell substantially as measurement error increased.

## Nonlinear fixture across measurement-error levels

Same measurement-error construction applied to the pure-nonlinear
fixture's six columns. True edges `{(X1,X2), (X3,X4)}`, unchanged across
levels.

| Level | Incumbent precision (mean/median) | Residual precision (mean/median) | Incumbent recall | Residual recall | Incumbent exact-match | Residual exact-match |
| --- | --- | --- | --- | --- | --- | --- |
| perfect (0.0) | 0.080 / 0.000 | 0.967 / 1.000 | 0.040 | 1.000 | 0.000 | 0.900 |
| modest (0.25) | 0.040 / 0.000 | 0.953 / 1.000 | 0.020 | 1.000 | 0.000 | 0.860 |
| substantial (1.0) | 0.020 / 0.000 | 0.607 / 0.833 | 0.010 | 0.660 | 0.000 | 0.500 |

Residual per-edge detection fraction: `1.000 -> 1.000 -> 0.66` for both
edges as measurement error rose from `perfect` to `substantial`. **This
is the first dimension besides effect strength itself (round 1) to
produce a measurable recall drop for the residual layer.**

## Independent spot recompute

Without importing `redana.benchmark`, seed derivation and both fixture
generators' formulas (with the `measurement_error` parameter) were
reimplemented independently and evaluated at replication indices 0, 25,
and 49 for the `perfect` and `substantial` conditions on both fixture
shapes. All twelve recomputed seeds, frame shapes, and true edge sets
matched the actual project code exactly -- zero mismatches.

## Interpretation

**Measurement error degrades both mechanisms, and does so gracefully
rather than as a sharp cliff -- the first dimension after effect
strength itself to show real degradation for the residual layer.**
Unlike rounds 2, 3, and 5 (relationship shape, noise, residual
variance), which left the residual layer's detection untouched across
their full tested ranges, measurement error visibly erodes it: nonlinear
per-edge detection held at ceiling through `modest` error (reliability
0.8) and only fell at `substantial` error (reliability 0.5, per-edge
detection 0.66). The decline from `1.000` to `0.66` across two steps
(with the intermediate `modest` level still at `1.000`) looks more
gradual than round 1's sharp strength cliff, though only three levels
were tested here, so the shape of the curve between `modest` and
`substantial` is not resolved.

**The linear fixture's incumbent recall never degraded (stayed at
1.000 throughout), consistent with classical attenuation-bias theory
being about correlation *magnitude*, not necessarily detectability under
a fixed EBIC threshold at this effect strength** -- attenuation shrinks
the observed correlation, but `coefficient=0.7` starts strong enough
that even a substantially attenuated version remained large enough for
EBIC selection to find the edge in every replication tested. Incumbent
*precision* was roughly flat across levels (0.637 -> 0.614 -> 0.604),
unlike every prior round's pattern of rising incumbent precision under a
weakening signal-to-noise ratio -- measurement error adds noise to
every column uniformly (including the three independent columns),
which is a different kind of perturbation from the previous rounds'
noise-on-the-relationship-only manipulations, and may explain why the
usual pattern did not reappear here. This is a plausible explanation,
not a verified one.

**Both mechanisms' precision and exact-match fraction eroded
substantially even where recall held (the linear fixture, and the
nonlinear fixture's `modest` level)** -- the residual layer's exact-match
fraction fell from 0.920 to 0.260 on the linear fixture across the three
levels, driven by more frequent spurious pair flags under noisier
observed data, consistent with the same false-positive mechanism already
documented in Stage I and every prior Stage II round, just amplified
here by every column carrying more noise.

## A convergence warning worth reporting

`sklearn.covariance.graphical_lasso` again emitted `ConvergenceWarning:
did not converge after 100 iterations` on a substantial number of fits,
across all six conditions, matching every prior round's evidence notes.
Reported plainly again rather than investigated or suppressed.

## Explicit boundary

This round tested exactly one of `plan.md` §6's remaining degradation
dimensions (measurement quality), at one fixed effect strength, noise
level, distribution, and residual-variance setting. It does not:

- narrow the transition between `modest` (reliability 0.8, no
  degradation) and `substantial` (reliability 0.5, real degradation) --
  the actual boundary between "no measurable effect" and "meaningful
  recall loss" is not pinned down;
- test measurement-quality degradation at any effect strength other
  than `0.7` (whether this newly-found degradation interacts with round
  1's already-found strength cliff is an open question this note does
  not answer);
- test network-structure degradation (`plan.md` §6's last remaining
  dimension);
- explain why the usual incumbent-precision-rises pattern from rounds 1,
  3, and 5 did not reappear here;
- compare methods at a matched operating point (`plan.md` §8);
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 10, this result does not authorize
further Stage II rounds, a boundary-narrowing follow-up, the
comparator-fairness protocol, or any package decision. This is a
genuinely informative finding worth flagging for a deliberate next
decision: unlike rounds 2, 3, and 5, this dimension shows the residual
layer is not universally robust to every kind of assumption violation --
whether to narrow the `modest`-`substantial` transition, test
measurement quality at a weaker effect strength, or move to the last
untested dimension (network structure) is a separate, later owner
decision, not an automatic next step.
