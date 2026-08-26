# Addendum: narrowing the untested n_rows=200-to-1,000 gap

Follows `docs/superpowers/specs/2026-08-26-track2-default-adoption-addendum.md`,
which left `redana.defaults.recommended_settings`'s `n_rows<=200` cutoff
as a conservative "where testing stopped" boundary, not a validated
inflection point. This addendum characterizes the gap directly.

## What this covers

The two arms are already fixed (`n_splits=2, alpha=0.15` "selected" vs.
`n_splits=5, alpha=0.05` "control") -- this is **not** a new tuning
study, so `outline/plan.md` §18 rule 3's dev/final-matrix split does not
apply the same way it did for Track 2's original charter. This is
characterization: run both fixed arms across new points in the gap and
observe where the pattern changes.

**Grid** (approved): `n_rows in {300, 500, 700}` x `coefficient in {0.15,
0.20, 0.7}` -- 9 cells, both arms, 50 independently-seeded reps per
(cell, arm) -- `900` replicated runs total. `coefficient in {0.15, 0.20}`
extends the low-power regime where the tuned values helped; `coefficient=0.7`
extends the well-powered regime where they cost precision for no
benefit. Together these trace both where the detection benefit fades and
where the precision cost appears, rather than only one direction.

Fresh, independently-seeded condition names (`track2-gap-` prefix), no
overlap with any prior study's seeds.

## What updates as a result

`redana.defaults.recommended_settings`'s `_LOW_N_THRESHOLD=200` cutoff
will be revised based on this grid's findings -- either raised (if the
tuned values keep helping without cost further into the gap), left as-is
(if the crossover happens close to 200), or replaced with something
coefficient-dependent (if the crossover point differs meaningfully
between `coefficient=0.15/0.20` and `coefficient=0.7`) -- documented in a
follow-up evidence note and a corresponding code change with tests,
exactly as the original conditional default was.

## Governance

Per `outline/plan.md` §18 rule 8, any revised threshold is scoped
strictly to the `n_rows` and `coefficient` values actually tested in this
grid plus the two already tested previously (100, 200, 1000) -- not
extrapolated beyond the combined tested set. Per rule 10, this closes the
specific "where's the crossover" question; it does not authorize lever 3
or any further Track 2 scope.
