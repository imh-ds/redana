# Addendum: final threshold decision -- n_rows<=175, not 225

Amends `docs/evidence/track2-threshold-justification-20260826.md`'s
mechanically-selected threshold. This is the authoritative record of
*why* the final number is `175`, not `225` -- read this first if you're
trying to understand the current `redana.defaults` threshold; the
sections below point to every piece of raw evidence behind it.

## Where to find the raw evidence

- **Full per-point measurements** (detection/precision for both arms at
  all 7 bracketed `n_rows` points, both coefficients):
  `docs/evidence/track2-threshold-justification-20260826.md`.
- **Raw machine-readable results** (every shard's numbers, before any
  classification or rounding): `scripts/track2_threshold_results.json`.
- **The scripts that produced them** (rerunnable, deterministic given the
  same seeds): `scripts/run_track2_threshold_shard.py`,
  `scripts/aggregate_track2_threshold.py`.
- **The original charter and plan** (grid design, rep counts, the
  originally-approved classification rule):
  `docs/superpowers/specs/2026-08-26-track2-threshold-justification-charter.md`,
  `docs/superpowers/plans/2026-08-26-track2-threshold-justification.md`.

## Why the mechanical result (225) was not adopted

The charter's pre-registered classification rule flagged a point "cost
present" only if detection gain was `<5pp` **and** precision loss was
`<=-5pp` (both conditions required). This is a structural flaw: it
never compares the two magnitudes to each other, so a point can clear
the detection floor by a hair while paying an arbitrarily large
precision cost and still be classified "safe." That is exactly what
happened at `n_rows=225`: `+6.0pp` detection gain (barely above the
`5pp` floor) paid for a `-21.1pp` precision loss (over 4x its own
floor). `docs/evidence/track2-threshold-justification-20260826.md`
already flagged this transparently at the time; this addendum records
the owner's resulting decision.

## The comparison that decided it

Re-reading the same already-published per-point numbers with a
symmetric "does the gain exceed the cost" lens, not the flawed AND-gate:

| n_rows | detection gain | precision cost | gain vs. cost |
| --- | --- | --- | --- |
| 125 | +26.0pp | precision *improves* (+16.7pp) | favorable, no cost at all |
| 150 | +29.0pp | precision *improves* (+6.2pp) | favorable, no cost at all |
| **175** | **+19.0pp** | **-10.1pp** | **favorable, ~2x margin** |
| 200 | +10.0pp | -12.8pp | roughly even -- cost slightly exceeds gain |
| 225 | +6.0pp | -21.1pp | unfavorable |
| 250 | +0.0pp | -23.6pp | unfavorable |

**The deciding reasoning:** with only `n_reps=50` per arm, each measured
proportion carries a standard error on the rough order of `5-7pp`, so a
detection-gain-vs-precision-cost gap smaller than about `10pp` (as at
`n_rows=200`, gap `2.8pp`) is plausibly just noise -- rerunning that cell
with a different seed could easily show the two swapped. At
`n_rows=175`, the gap (`8.9pp`) is close to but likely past that noise
floor, and the ratio is roughly 2:1 in the gain's favor -- a margin
judged likely to hold up, not merely a favorable point estimate.

## Decision

**`redana.defaults._LOW_N_THRESHOLD = 175`** (changed from the
mechanically-selected `225`, and from the original untested `200`).
`n_rows<=175` uses the tuned low-n values; above that, the original
defaults. No further bracketing was run to refine this -- `175` was
selected by owner judgment from already-published numbers, explicitly
choosing a comfortable margin over a value that merely cleared a
flawed rule, rather than by running a new, tighter-resolution study.

## Governance

Per `outline/plan.md` §18 rule 8, this decision is scoped to the same
evidence as before (`coefficient<=0.7`, `25`-row resolution, pure
nonlinear fixture at baseline conditions) -- picking `175` over `225`
does not constitute new testing, only a different, more conservative
reading of the same measurements, made explicit and recorded here rather
than left as an unstated judgment call. Per rule 10, this addendum
closes the threshold question as currently scoped; further narrowing
(e.g., bracketing between `150` and `200` at finer resolution with more
reps, to directly test whether `175`'s margin holds under less noise)
remains a separate, optional, later step if ever pursued.
