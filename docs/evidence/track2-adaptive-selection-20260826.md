# Adaptive configuration selection and usefulness-boundary results

Per `docs/superpowers/specs/2026-08-26-track2-adaptive-selection-charter.md`
and `docs/superpowers/plans/2026-08-26-track2-adaptive-selection.md`.
Source revision: `631307e9`. Sharded across 6 parallel GitHub Actions
jobs (30 reps each); total wall time under 15 minutes.

## Results

| n_rows | coefficient | ground truth | arbiter accuracy | always-sensitive | always-normal | static rule (n<=200) |
| --- | --- | --- | --- | --- | --- | --- |
| 100 | 0.15 | sensitive | 0.133 | 1.0 | 0.0 | 1.0 |
| 100 | 0.70 | sensitive | 0.267 | 1.0 | 0.0 | 1.0 |
| 300 | 0.15 | sensitive | 0.267 | 1.0 | 0.0 | 0.0 |
| 300 | 0.70 | normal | 0.500 | 0.0 | 1.0 | 1.0 |
| 500 | 0.15 | sensitive | 0.133 | 1.0 | 0.0 | 0.0 |
| 500 | 0.70 | normal | 0.400 | 0.0 | 1.0 | 1.0 |
| **mean** | | | **0.283** | **0.667** | 0.333 | **0.667** |

**The arbiter's mean accuracy (0.283) is worse than a coin flip (0.5), and
28.4 points below the static rule's (0.667) -- the opposite of the
required +15pp improvement.** It does not clear Decision 3's bar at any
cell; the bar's per-cell floor (static rule accuracy minus 10pp) is also
missed at every cell where the static rule scored 0.0 or 1.0 -- there is
no cell where the arbiter comes close to matching, let alone beating,
either deterministic baseline.

## Independent spot recompute and root-cause mechanism

Three reps each at `(n_rows=100, coefficient=0.15)` and `(n_rows=500,
coefficient=0.15)` (both ground-truth "sensitive") were recomputed
directly via `redana.arbiter.select_configuration`, inspecting the raw
`consistency_scores`, not just the final pick. **Both candidates scored
exactly `0.0` in every single one of these six spot-checked reps, at
both sample sizes**, and the arbiter fell back to its default
(`"normal"`) every time -- which is wrong at every one of these cells.

The mechanism: a consistency score is `0.0` by definition whenever a
candidate detects *zero* edges on the training split (nothing to check
consistency of). At `coefficient=0.15` (the weak-effect case), the
80%-of-n training split frequently detects nothing at all for either
candidate -- not just at `n_rows=100`, but still at `n_rows=500` (400
training rows). This isn't noise in the held-out check; it's that the
premise of the mechanism -- "check whether train-detected edges hold up
on held-out data" -- has nothing to work with in the majority of
weak-effect replications, because the *training* half alone often can't
detect anything in the first place. The arbiter then silently defaults
to `"normal"`, systematically wrong at every ground-truth-"sensitive"
cell.

This directly and concretely answers the project owner's original
question that motivated Decision 4 (test a single 80/20 split before
k-fold): **no, an 80/20 split is not viable here, and the problem isn't
specific to `n=100` as originally suspected -- it persists up to at least
`n=500`.**

## A secondary observation: the naive full-sensitive baseline matches the static rule

`always-sensitive` alone achieves the same 0.667 mean accuracy as the
static `n_rows<=200` rule in this specific 6-cell grid (by coincidence of
which cells were tested: 4 of 6 have ground truth "sensitive"), while
requiring no data-driven decision, no split, and no extra compute. This
is not a general endorsement of always using sensitive settings -- the
gap-narrowing study already showed `always-sensitive` fails badly at
larger `n_rows`/coefficient=0.7 cells not included in this 6-cell grid --
but it reinforces, in this grid specifically, that a free heuristic
matched a genuinely non-trivial static rule, while the actual
data-driven mechanism this study built came in far behind both.

## Usefulness-boundary map (secondary deliverable, independent of the arbiter's verdict)

The ground-truth column above, combined with
`docs/evidence/track2-low-n-power-levers-20260826.md` and
`docs/evidence/track2-gap-narrowing-20260826.md`, gives the fullest
picture yet of which configuration actually wins where:

| n_rows | coefficient=0.15 | coefficient=0.7 |
| --- | --- | --- |
| 100 | sensitive | sensitive |
| 300 | sensitive | normal |
| 500 | sensitive | normal |
| 700 | sensitive | normal |
| 1000 | (untested) | normal |

`(n_rows=100, coefficient=0.7)` -- established fresh in this study's
Task 1 -- is the one cell that breaks the simpler "coefficient alone
decides it" story from the gap-narrowing study: at `n=100`, even a
strong true effect isn't near detection ceiling under normal settings
(`0.210` detection there, consistent with the original Stage A finding),
so sensitive mode still wins. This map remains a real, useful artifact
of this study regardless of the arbiter's failure -- though it is not a
new capability (`redana.defaults.recommended_settings`'s static rule
already reflects the safe, tested portion of it), just a fuller record
of the evidence behind that rule.

## Explicit boundary

This investigation does not:

- test k-fold or nested-CV versions of the arbiter, deliberately
  sequenced after this single-split test per Decision 4 -- given how
  decisively the single split failed and why (too little training-split
  power to produce a signal to check, not merely "too noisy an
  estimate"), it is unclear k-fold would fix the underlying problem
  rather than just average over more instances of the same failure;
- test alternative consistency-scoring designs (e.g., a partial-credit
  score instead of exact edge-set overlap, or a different default
  fallback);
- test split ratios other than 80/20;
- test lever 3 (alternate test statistic / HSIC);
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 8, the claim is scoped precisely: this
specific arbiter design (80/20 single split, exact train/held-out edge
overlap, default-to-normal fallback) fails decisively at this specific
6-cell grid. It is not a claim that no adaptive selection mechanism could
ever work, only that this one, tested this way, does not.

Per rule 1, this negative result does not automatically authorize a
search for a better arbiter design (k-fold, alternate scoring, etc.) --
that would need its own charter if pursued. Per rule 10: this closes the
adaptive-selection question as scoped. Combined with
`docs/superpowers/specs/2026-08-26-track2-default-adoption-addendum.md`
and `docs/evidence/track2-gap-narrowing-20260826.md`'s findings, the
project's static `n_rows<=200` rule remains the most defensible
mechanism tested so far for this choice -- not because it's been proven
optimal, but because every attempt to do better with a data-driven
alternative has, so far, either been unsupported by evidence (raising
the threshold) or performed worse than it (this arbiter). Whether to
pursue a redesigned arbiter, accept the static rule as final for now, or
revisit the Core/Explore engine framing discussed alongside this charter
(not decided here, per rule 9) is a decision for the project owner.
