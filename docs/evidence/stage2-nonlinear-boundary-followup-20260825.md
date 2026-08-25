# Stage II nonlinear detectability boundary follow-up

Follow-up to `docs/evidence/stage2-effect-strength-degradation-20260825.md`,
which found the residual layer's per-edge detection on the pure
nonlinear fixture held at 100% for `coefficient` in `{0.7, 0.4}` and
dropped to 84% at `coefficient=0.2`, without pinning down where
detection actually starts to fail. Not a new Stage II dimension, not a
Gate 0 study: reuses `redana.benchmark.run_replicated_condition` and
`redana.scenarios.generate_stage1_nonlinear_fixture` exactly as built
for Stage II round 1, no new `redana` source. Source revision:
`8ec3288a`.

## What ran

`scripts/run_stage2_nonlinear_boundary_followup.py`: the pure nonlinear
fixture only (`X1=e1, X2=coef*(X1^2-1)+e2, X3=e3, X4=coef*(X3^2-1)+e4,
X5=e5, X6=e6`), at four coefficient levels -- `0.20` (rerun as an anchor
point, distinct replication seeds from round 1's `0.2` run), `0.15`,
`0.10`, `0.05` -- 50 replications each at `n=1,000`, otherwise identical
configuration to Stage II round 1.

## Results

| Coefficient | Residual precision (mean/median) | Residual recall (mean/median) | Per-edge detection |
| --- | --- | --- | --- |
| 0.20 | 0.760 / 1.000 | 0.810 / 1.000 | `(X1,X2)` 0.80, `(X3,X4)` 0.82 |
| 0.15 | 0.308 / 0.000 | 0.360 / 0.000 | `(X1,X2)` 0.34, `(X3,X4)` 0.38 |
| 0.10 | 0.007 / 0.000 | 0.010 / 0.000 | `(X1,X2)` 0.02, `(X3,X4)` 0.00 |
| 0.05 | 0.000 / 0.000 | 0.000 / 0.000 | `(X1,X2)` 0.00, `(X3,X4)` 0.00 |

The `0.20` anchor point's per-edge detection here (80-82%) is close to,
though not identical to, round 1's independently-drawn `0.2` result
(84%) -- consistent with each other within ordinary sampling variability
across two separate 50-replication draws with different seeds, not a
discrepancy.

## Interpretation

This is a **sharp cliff, not a gradual decline**. Detection is still
reasonably strong at `0.20` (~80% per-edge), collapses to roughly a
third at `0.15`, is nearly gone at `0.10` (0-2%), and is completely
absent at `0.05` across all 100 tested edge-instances (50 replications x
2 edges). The boundary where this specific nonlinear shape becomes
undetectable at `n=1,000` with this configuration sits narrowly between
roughly `0.10` and `0.20` -- most of the transition happens between
`0.15` and `0.20`, not spread evenly across the tested range.

This is exactly the kind of degradation curve `outline/plan.md` §6
exists to characterize, and it is a genuinely informative result: the
mechanism does not fail gracefully across a wide range here -- it holds
up reasonably well and then falls off sharply over a narrow band. That
band's exact edges (is it closer to 0.15 or 0.18? does it shift with
`n`?) are not established by this note.

## Explicit boundary

Two coefficient values (`0.10`, `0.15`) sit inside the observed
transition band and were not resolved further. This note does not:

- narrow the boundary more precisely (e.g., testing `0.12`, `0.17`,
  `0.18`);
- test whether the boundary's location shifts with sample size `n`
  (a natural, separate Stage II follow-up combining the effect-strength
  and sample-size dimensions -- not attempted here, since combining two
  dimensions at once would violate the "one dimension at a time"
  discipline this project has held throughout);
- test the linear fixture's own weak-signal boundary (round 1 showed no
  degradation across `0.2`-`0.7`, so its boundary, if any, lies below
  `0.2` and was not probed here);
- extend to any other `plan.md` §6 degradation dimension.

## Governance

Per `outline/plan.md` §18 rule 10, this result does not authorize
further boundary-narrowing runs, a sample-size sweep, or any other
Stage II dimension. Whether to narrow the `0.10`-`0.20` band further, to
sweep sample size at a fixed coefficient instead, or to move to a
different degradation dimension remains a separate, later owner
decision.
