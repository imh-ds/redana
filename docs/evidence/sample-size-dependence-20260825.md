# Sample-size dependence results

Per `docs/superpowers/specs/2026-08-25-sample-size-dependence-design.md`
and `docs/superpowers/plans/2026-08-25-sample-size-dependence.md`. Not a
Gate 0 study: no hash-pinned calibration, no single-official-run
ceremony, no per-replication artifact retention. Zero new `redana`
source -- `n_rows` is already a first-class parameter of
`redana.benchmark.run_replicated_condition`; both stages reuse
`generate_stage1_nonlinear_fixture` unchanged. Source revision:
`f63f59c5`.

This closes the open question every effect-strength-related evidence
note in this project has flagged since Stage II round 1: does sample
size matter, and does the effect-strength cliff (found at
`coefficient=0.10`-`0.20`, `n=1,000`) shift as `n` changes?

## Stage A: sample size alone, strong signal fixed (coefficient=0.7)

| n_rows | Residual precision (mean/median) | Residual recall (mean/median) | Per-edge detection |
| --- | --- | --- | --- |
| 100 | 0.129 / 0.000 | 0.160 / 0.000 | 0.16 |
| 200 | 0.867 / 1.000 | 0.920 / 1.000 | 0.92 |
| 500 | 0.973 / 1.000 | 1.000 / 1.000 | 1.00 |
| 1000 | 0.953 / 1.000 | 1.000 / 1.000 | 1.00 |
| 2000 | 0.973 / 1.000 | 1.000 / 1.000 | 1.00 |

## Stage B: coefficient x n_rows grid (per-edge detection fraction)

| coefficient | n=500 | n=1000 | n=2000 |
| --- | --- | --- | --- |
| 0.10 | 0.00 | 0.05 | 0.28 |
| 0.15 | 0.02 | 0.29 | 0.92 |
| 0.20 | 0.20 | 0.90 | 1.00 |

(`n=1000` column reproduces Stage II round 1's boundary follow-up
closely: `0.02/0.34/0.80` there vs. `0.05/0.29/0.90` here -- consistent
within ordinary sampling variability across independently-seeded
50-replication draws, not a discrepancy.)

## Independent spot recompute

Without importing `redana.benchmark`, seed derivation and the fixture
formula were reimplemented independently and evaluated at replication
indices 0, 25, and 49 across several cells in both stages (`n=100,
200, 2000` for Stage A; `(0.1,500), (0.2,2000), (0.15,1000)` for Stage
B). All recomputed seeds, frame shapes, and true edge sets matched the
actual project code exactly -- zero mismatches.

## Interpretation

**Sample size matters a great deal, and `plan.md` §1's own stated floor
(`n >= 200`) is empirically justified -- with a caveat.** Even at a
strong signal (`coefficient=0.7`, ~49.5% variance explained -- comfortably
above every dimension's tested danger zone), detection collapses almost
entirely at `n=100` (per-edge detection `0.16`, precision/recall both
near floor). At the project's stated minimum (`n=200`), detection is
much better but not yet at ceiling (`0.92`, not `1.00`). Ceiling
detection for a strong signal only appears at `n=500` and above. This
means `plan.md`'s stated `n >= 200` floor is a reasonable minimum for a
*strong* signal to be usually detected, but not a guarantee of reliable
detection -- `n=500` looks like a safer practical floor for strong
signals, and the true floor for weaker signals is considerably higher
(see Stage B).

**The effect-strength cliff shifts in exactly the direction basic
statistical power theory predicts, with no surprises.** More data pushes
detection up at every coefficient level tested; less data pushes it
down. At `n=500`, even `coefficient=0.20` (round 1's strongest "boundary"
level, ~7.4% variance explained) barely detects (`0.20` per-edge
detection) -- a coefficient that looked comfortably "still working" at
`n=1,000` (`0.80`-`0.90` in round 1 and here) is nearly undetectable at
half that sample size. Conversely, at `n=2,000`, `coefficient=0.15`
(~4.3% variance explained, which looked like a collapsed, barely-detected
level at `n=1,000`) reaches `0.92` per-edge detection -- close to
ceiling. **The cliff is not a fixed property of the coefficient value;
it is a property of the combination of effect strength and sample
size**, exactly as expected, but now confirmed directly rather than
inferred from formula.

**Practical takeaway for reading every earlier Stage II round's
results:** every finding in rounds 1-7 was measured at `n=1,000`. The
"cliff" location (`coefficient` `0.10`-`0.20`) and every "no
degradation" finding are specific to that sample size. A study run at
`n=500` would find the cliff at a noticeably stronger effect size; a
study run at `n=2,000` or beyond would find it at a noticeably weaker
one. This project's Stage II results describe behavior at one point on
a two-dimensional surface (effect strength x sample size), not a
universal boundary.

## A convergence warning worth reporting

`sklearn.covariance.graphical_lasso` again emitted `ConvergenceWarning:
did not converge after 100 iterations` on a number of fits across both
stages, matching every prior round's evidence notes. Reported plainly
again rather than investigated or suppressed.

## Explicit boundary

This investigation does not:

- trace the full detectability surface at fine resolution -- five
  sample sizes (Stage A) and a 3x3 grid (Stage B) establish direction
  and rough magnitude of the shift, not a publication-grade power curve;
- test sample-size dependence for any dimension other than effect
  strength (shape, noise, distribution, residual variance, measurement
  quality, network structure all remain untested against varying `n`);
- test sample sizes below `100` or above `2,000`, or `p` values other
  than `6`, so `plan.md` §10's broader "behavior as `n/p` changes"
  metric remains only partially addressed;
- compare methods at a matched operating point (`plan.md` §8);
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 10, this result does not authorize a
full sample-size sweep across every other dimension, the
comparator-fairness protocol, Stage III, real-data work, or any package
decision. It closes one specific, repeatedly-flagged open question.
Whether to extend sample-size testing to other dimensions, tighten the
detectability surface's resolution, or move toward Stage III remains a
separate, later owner decision.
