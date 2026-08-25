# Stage II round 1 effect-strength degradation results

Per `docs/superpowers/specs/2026-08-25-stage2-effect-strength-degradation-design.md`.
Not a Gate 0 study: no hash-pinned calibration, no single-official-run
ceremony, no per-replication artifact retention. Six conditions (2
fixture shapes x 3 strength levels), 50 replications each at
`n = 1,000` rows, reusing every Step 4 / Stage I component unchanged.
Source revision: `c9747af5`.

## Linear fixture across strength levels

`X1=e1, X2=coef*X1+e2, X3=coef*X2+e3, X4=e4, X5=e5, X6=e6`. True edges:
`{(X1,X2), (X2,X3)}`, unchanged across levels.

| Level | Incumbent precision (mean/median) | Residual precision (mean/median) | Incumbent recall | Residual recall | Incumbent exact-match | Residual exact-match |
| --- | --- | --- | --- | --- | --- | --- |
| strong (0.7) | 0.623 / 0.583 | 0.963 / 1.000 | 1.000 | 1.000 | 0.160 | 0.900 |
| moderate (0.4) | 0.890 / 1.000 | 0.967 / 1.000 | 1.000 | 1.000 | 0.700 | 0.900 |
| weak (0.2) | 0.943 / 1.000 | 0.950 / 1.000 | 1.000 | 1.000 | 0.840 | 0.860 |

Residual per-edge detection fraction: **1.000 for both edges at all
three strength levels.**

## Nonlinear fixture across strength levels

`X1=e1, X2=coef*(X1^2-1)+e2, X3=e3, X4=coef*(X3^2-1)+e4, X5=e5, X6=e6`
(zero linear covariance regardless of `coef`). True edges:
`{(X1,X2), (X3,X4)}`, unchanged across levels.

| Level | Incumbent precision (mean/median) | Residual precision (mean/median) | Incumbent recall | Residual recall | Incumbent exact-match | Residual exact-match |
| --- | --- | --- | --- | --- | --- | --- |
| strong (0.7) | 0.000 / 0.000 | 0.937 / 1.000 | 0.000 | 1.000 | 0.000 | 0.820 |
| moderate (0.4) | 0.040 / 0.000 | 0.923 / 1.000 | 0.020 | 1.000 | 0.000 | 0.780 |
| weak (0.2) | 0.000 / 0.000 | 0.783 / 1.000 | 0.000 | 0.840 | 0.000 | 0.680 |

Residual per-edge detection fraction: `(X1,X2)` and `(X3,X4)` both
**1.000 at strong and moderate**, dropping to **0.840 each at weak**
(0.2).

## Independent spot recompute

Without importing `redana.benchmark`, seed derivation and both fixture
generators' formulas (with the `coefficient` parameter) were
reimplemented independently and evaluated at replication indices 0, 25,
and 49 for the two weak-strength conditions (`stage2-linear-weak`,
`stage2-nonlinear-weak`) -- the conditions closest to a detectability
boundary and therefore most worth double-checking. All six recomputed
seeds, frame shapes, and true edge sets matched the actual project code
exactly -- zero mismatches.

## Interpretation

**The linear fixture stayed at ceiling recall (1.000) across the entire
tested strength range for both mechanisms.** Neither mechanism ever
missed a true linear edge, even at the weakest level tested
(`coefficient = 0.2`). This means the tested strength range (0.2-0.7)
did not reach a detectability boundary for the linear case at `n=1,000`
-- a genuinely weaker linear signal, or a smaller sample size, would be
needed to see recall degrade.

**A genuine, unexplained finding worth reporting plainly: the
incumbent's precision *improved* as the linear signal weakened** (0.623
mean at strong, up to 0.943 mean at weak) rather than degrading. This is
counter to the naive expectation that a weaker true signal makes
detection strictly harder across the board. A plausible but unverified
explanation is that stronger true edges inflate sample-covariance noise
on nearby pairs more than weak edges do, making the incumbent's other,
false-positive edges more likely to cross the EBIC selection threshold
when the true signal is strong -- but this is speculation, not a tested
claim. This is not something this note resolves.

**The nonlinear fixture shows the expected graceful degradation pattern
Stage II exists to characterize.** At strong and moderate strength, the
residual layer detected both true nonlinear edges in 100% of
replications. At the weakest level tested (`coefficient = 0.2`),
per-edge detection dropped to 84%, and overall recall/precision softened
correspondingly (mean recall 1.000 -> 1.000 -> 0.840; mean precision
0.937 -> 0.923 -> 0.783). The incumbent, as expected, remained unable to
detect this structure at any strength level (recall approximately zero
throughout, since linear covariance is exactly zero in population
regardless of `coefficient`).

This gives a first, rough sense that a detectability boundary for this
specific nonlinear shape at `n=1,000` sits somewhere below
`coefficient = 0.2` -- not established precisely, since only three
levels were tested and none of them is where detection first starts to
fail (0.7 and 0.4 were both still near-ceiling; 0.2 is the first level
showing any softening at all, not a floor).

## A convergence warning worth reporting

`sklearn.covariance.graphical_lasso` again emitted `ConvergenceWarning:
did not converge after 100 iterations` on a number of fits, at every
strength level, matching what was already noted in
`docs/evidence/stage1-mechanistic-benchmark-20260825.md`. Reported
plainly again rather than investigated or suppressed.

## Explicit boundary

This round tested exactly one of `plan.md` §6's seven degradation
dimensions (effect strength), at one fixed sample size (`n=1,000`), on
two fixture shapes, at three strength levels chosen without any prior
knowledge of where a detectability boundary would fall. It does not:

- pin down where detection actually starts to fail for either fixture
  shape (the linear fixture never degraded within the tested range; the
  nonlinear fixture only started softening at the weakest level tested);
- test noise, distribution, residual-variance, measurement-quality, or
  network-structure degradation (`plan.md` §6's other six dimensions);
- explain the incumbent's counter-intuitive precision-vs-strength
  pattern on the linear fixture, or the recurring graphical-lasso
  convergence warnings;
- compare methods at a matched operating point (`plan.md` §8);
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 10, this result does not authorize
further Stage II rounds, the comparator-fairness protocol, or any
package decision. Natural follow-up questions this note surfaces but
does not answer -- narrowing in on the nonlinear detectability boundary
below `coefficient = 0.2`, and investigating the incumbent's
precision-vs-strength pattern -- remain separate, later owner decisions,
not automatic next steps.
