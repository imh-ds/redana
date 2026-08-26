# Noise-scale boundary follow-up: does noise reach the same cliff as effect strength?

Lightweight for-completeness follow-up (no new spec/plan, no new
`redana` source): tests whether round 3's "noise doesn't degrade
detection" finding was genuine, or just under-tested relative to round
1's effect-strength cliff. Reuses
`redana.scenarios.generate_stage1_nonlinear_fixture` and
`redana.benchmark.run_replicated_condition` exactly as built for round
3, at `coefficient = 0.7` fixed, sweeping `noise_scale` to levels chosen
so variance-explained (`0.98 / (0.98 + noise_scale^2)`) lands near round
1's already-tested coefficient levels. 50 replications per level,
`n=1,000`. Source revision: `ad7dd11a`.

## Why this follow-up exists

Round 3 tested `noise_scale` only up to `2.0`, which -- at
`coefficient=0.7` -- pushes variance explained down to only `~19.7%`,
nowhere near round 1's cliff zone (`~2%`-`~7.4%`). Round 3's "no
degradation" finding was therefore never actually tested against the
same signal-to-noise range where round 1 found a cliff. This follow-up
closes that gap directly.

## Results, alongside round 1's matching coefficient levels for comparison

| noise_scale | Variance explained | Residual per-edge detection | Round 1's matching coefficient level | Round 1's per-edge detection |
| --- | --- | --- | --- | --- |
| 2.0 | ~19.7% | 1.00 / 1.00 | (above round 1's tested range) | -- |
| 3.5 | ~7.4% | 0.82 / 0.84 | 0.20 (~7.4%) | 0.80 / 0.82 |
| 4.7 | ~4.2% | 0.40 / 0.42 | 0.15 (~4.3%) | 0.34 / 0.38 |
| 6.9 | ~2.0% | 0.08 / 0.06 | 0.10 (~2.0%) | 0.02 / 0.00 |

## Independent spot recompute

Seed derivation and the fixture formula were reimplemented
independently and evaluated at replication indices 0, 25, and 49 for
the `2.0` and `6.9` levels. All six recomputed seeds, frame shapes, and
true edge sets matched exactly -- zero mismatches.

## Interpretation

**Confirmed: pushed far enough, noise produces essentially the same
cliff effect strength did, at closely matching variance-explained
levels.** At each of the three matched levels, noise_scale's per-edge
detection tracks round 1's coefficient-based result closely (0.82-0.84
vs. 0.80-0.82 at ~7.4%; 0.40-0.42 vs. 0.34-0.38 at ~4.3%; 0.06-0.08 vs.
0.00-0.02 at ~2.0%) -- close enough, given each is a separate 50-
replication draw at a different seed, to say these are the same
underlying phenomenon reached from two different directions, not two
different findings.

**This means round 3's "no degradation" conclusion should be read as
"no degradation within the noise range actually tested," not "noise
doesn't matter."** The detectability cliff is governed by the
underlying signal-to-noise ratio (equivalently, variance explained),
regardless of whether that ratio is weakened by shrinking the true
relationship (`coefficient`) or by growing the unrelated noise
(`noise_scale`). This directly answers the "aren't weak signal and
noisy data the same thing?" question raised earlier in this
conversation: yes, they are the same underlying quantity, and this
result confirms it empirically rather than just by formula.

## Explicit boundary

This does not retract round 3's evidence note -- its tested range
(`noise_scale` up to `2.0`) genuinely showed no degradation, and that
remains true. It only clarifies that round 3's tested range never
reached the danger zone, so "no degradation" should not be read as "this
dimension is immune to the effect-strength cliff." This follow-up does
not retest relationship shape, residual variance, distribution, or
measurement quality against the same matched-variance-explained
standard -- whether any of those "no cliff" findings are similarly
under-tested relative to round 1's range is a separate, later question,
not addressed here.

## Governance

Per `outline/plan.md` §18 rule 10, this result does not authorize
further boundary-narrowing follow-ups on any other dimension, a
combined multi-dimension study, or any package decision.
