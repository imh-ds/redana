# Static threshold justification results

Per `docs/superpowers/specs/2026-08-26-track2-threshold-justification-charter.md`
and `docs/superpowers/plans/2026-08-26-track2-threshold-justification.md`.
Source revision: `f75e754b`. Sharded across 28 parallel GitHub Actions
jobs; total wall time under 15 minutes.

This closes the gap flagged repeatedly since
`docs/evidence/track2-gap-narrowing-20260826.md`: `redana.defaults`'s
`n_rows<=200` cutoff was never actually validated -- it was set to the
edge of the original low-n study's tested grid, not a discovered
inflection point. This study brackets the true strong-coefficient
crossover at 25-row resolution and, per the charter, updates the
threshold to match.

## Results

### coefficient=0.7 (the crossover-determining anchor)

| n_rows | sensitive detection | normal detection | sensitive precision | normal precision | detection improvement | precision delta | classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 125 | 0.680 | 0.420 | 0.503 | 0.337 | +0.260 | +0.167 | safe |
| 150 | 0.870 | 0.580 | 0.589 | 0.527 | +0.290 | +0.062 | safe |
| 175 | 0.970 | 0.780 | 0.633 | 0.733 | +0.190 | -0.101 | safe |
| 200 | 1.000 | 0.900 | 0.692 | 0.820 | +0.100 | -0.128 | safe |
| **225** | 1.000 | 0.940 | 0.632 | 0.843 | **+0.060** | **-0.211** | **safe** |
| 250 | 1.000 | 1.000 | 0.680 | 0.917 | +0.000 | -0.236 | cost_present |
| 275 | 1.000 | 1.000 | 0.733 | 0.943 | +0.000 | -0.210 | cost_present |

### coefficient=0.20 (sanity check)

All 7 points (`125`-`275`) classified **"safe"** -- sensitive detection
improvement ranged `+0.170` to `+0.310` with precision *improving*
alongside it at every point (`+0.126` to `+0.255`), consistent with
every prior weak-coefficient result in this project. No surprises here.

**New threshold: `n_rows<=225`** (mechanically selected as the largest
`coefficient=0.7` point classified "safe," per the rule fixed in the
charter before this run).

## A caveat about n_rows=225's classification, stated plainly

The classification rule requires *both* a detection improvement `<5pp`
*and* a precision loss `<=-5pp` to flag a point as "cost present." At
`n_rows=225`, detection improvement is `+6.0pp` -- just barely above the
`5pp` floor -- while the precision cost is `-21.1pp`, more than four
times the `-5pp` floor. This point is classified "safe" only because it
narrowly clears the detection side of a two-part rule, not because the
tradeoff at `225` is actually favorable in any holistic sense: trading a
21-point precision loss for a 6-point detection gain is a real cost,
even if it's not the *zero*-benefit cost seen at `250` and beyond.

This was reported honestly rather than smoothed over, and the mechanical
rule's output (`225`) was still adopted as the new threshold rather than
overridden, specifically because the rule was fixed *before* this run
per `outline/plan.md` §18 rule 3 -- overturning a pre-registered decision
rule after seeing an inconvenient result would undermine the entire
point of pre-registering it. A reader who wants a more conservative
cutoff should note that `n_rows<=200` (where the tradeoff is a smaller
`+10.0pp`/`-12.8pp`) or `n_rows<=175` (`+19.0pp`/`-10.1pp`) are both
comfortably inside the genuinely favorable zone, if `225`'s narrow
margin is judged too thin in practice.

## Independent spot recompute

Two reps each, both arms, at `n_rows=225` and `n_rows=250` (the exact
crossover boundary) were recomputed directly via
`redana.prototype.run_prototype`, bypassing `redana.benchmark` entirely.
At `n=225`, the `sensitive` arm's extra false-positive edges (e.g.
`(X2,X6)`, `(X3,X5)` in one rep; `(X1,X4)`, `(X2,X4)` in another) beyond
the two true edges directly produced the observed `0.50` precision in
both spot-checked reps, while `normal` cleanly found exactly the two true
edges in every spot-checked rep at both `n_rows` values -- matching the
aggregate pattern exactly.

## The code change

`redana/defaults.py`'s `_LOW_N_THRESHOLD` changed from `200` to `225`;
`tests/redana/test_defaults.py`'s boundary cases updated to match
(`225 -> tuned`, `226 -> default`). No other `redana` source changed.

## Explicit boundary

This investigation does not:

- test coefficients stronger than `0.7`, so a user with, say, a
  coefficient of `0.9` might see the crossover at a smaller `n_rows`
  than `225` -- untested;
- test at finer than `25`-row resolution, so the true crossover could
  sit anywhere in `(225, 250)`, not necessarily exactly at either tested
  point;
- change the arbiter, lever 3, or any Track 1 disclosure work;
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 3, this bracketing grid used entirely
fresh, independently-seeded data -- no reuse of any prior study's seeds
-- so setting the threshold from these results is not circular tuning.
Per rule 8, the new threshold is scoped exactly to what was tested:
`coefficient<=0.7`, `25`-row resolution, the pure nonlinear fixture at
baseline noise/distribution/measurement conditions. Per rule 10,
approving the charter authorized only this bracketing and threshold
update -- not any further Track 2 scope, the arbiter, or lever 3.
