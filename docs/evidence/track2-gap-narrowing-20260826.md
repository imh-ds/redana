# Track 2 gap-narrowing results

Per `docs/superpowers/specs/2026-08-26-track2-gap-narrowing-addendum.md`.
Not a Gate 0 study, not a tuning study -- both arms (`n_splits=2, alpha=0.15`
"selected" vs. `n_splits=5, alpha=0.05` "control") were already fixed by
`docs/evidence/track2-low-n-power-levers-20260826.md`. This is direct
characterization of the previously-untested `n_rows` range between 200
and 1,000. Source revision: `d1514089`. Sharded across 18 parallel
GitHub Actions jobs (no bootstrap multiplier, so much cheaper than the
stability-validation study's shards) -- total wall time under 15 minutes.

## Results

| n_rows | coefficient | selected detection | control detection | detection improvement | selected precision | control precision | precision delta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 300 | 0.15 | 0.210 | 0.010 | +0.200 | 0.181 | 0.010 | +0.171 |
| 300 | 0.20 | 0.330 | 0.040 | +0.290 | 0.309 | 0.040 | +0.269 |
| 300 | 0.70 | 1.000 | 1.000 | +0.000 | 0.691 | 0.930 | **-0.239** |
| 500 | 0.15 | 0.290 | 0.030 | +0.260 | 0.325 | 0.023 | +0.301 |
| 500 | 0.20 | 0.780 | 0.250 | +0.530 | 0.701 | 0.210 | +0.491 |
| 500 | 0.70 | 1.000 | 1.000 | +0.000 | 0.797 | 0.953 | **-0.156** |
| 700 | 0.15 | 0.620 | 0.080 | +0.540 | 0.613 | 0.080 | +0.533 |
| 700 | 0.20 | 0.900 | 0.530 | +0.370 | 0.752 | 0.497 | +0.256 |
| 700 | 0.70 | 1.000 | 1.000 | +0.000 | 0.875 | 0.933 | **-0.059** |

(`n=1,000, coefficient=0.7`, from the prior regression check in
`docs/superpowers/specs/2026-08-26-track2-default-adoption-addendum.md`:
detection +0.000, precision delta **-0.142** -- included for reference,
not rerun here.)

## Independent spot recompute

Two reps each at `n=500, coefficient=0.7` (both arms) and `n=700,
coefficient=0.15` (both arms) were recomputed directly via
`redana.prototype.run_prototype`, bypassing `redana.benchmark` entirely.
At `n=500, coefficient=0.7`, one `selected`-arm rep showed two extra
false-positive edges (`(X2,X4)`, `(X4,X6)`) beyond the two true edges,
while both `control`-arm reps and the other `selected`-arm rep found
exactly the two true edges -- a direct, visible instance of the
precision-cost mechanism. At `n=700, coefficient=0.15`, one rep was
missed by both arms and one was caught by `selected` while `control`
found nothing -- consistent with the aggregate pattern. All frame shapes,
true-edge sets, and residual-edge sets matched what the shard artifacts
implied.

## Interpretation

**The crossover is not simply about `n_rows` -- it is about whether the
control configuration is already near detection ceiling.** For weak
coefficients (0.15, 0.20), the detection benefit does not fade across
this entire gap -- if anything it grows (`coefficient=0.20`'s
improvement: `+0.290` at `n=300`, peaking at `+0.530` at `n=500`, still
`+0.370` at `n=700`), and precision improves right alongside it at every
single point, exactly matching the original low-`n` finding's pattern.
For the strong coefficient (0.7), both arms are already at ceiling
detection (`1.000`) at every tested `n_rows` from `300` through `1,000`
-- so there is no detection benefit anywhere in this range, only a
precision cost, present at every point tested (`-0.239` to `-0.059`
across `300`-`700`, `-0.142` at `1,000` -- not a clean monotonic shrink,
likely reflecting ordinary Monte Carlo noise at `n_reps=50` rather than a
smooth trend, but never reaching zero at any tested point).

**This means the current `n_rows<=200` recommendation in
`redana.defaults.recommended_settings` should NOT be extended based on
this data.** The mechanism driving the crossover is effect strength
(is the true relationship already easily detected under control
settings, or not), not sample size in isolation -- and a real user's
true coefficient is exactly what they don't know in advance (the same
identifiability problem flagged during Track 1's peer review for a
different reason). Raising the threshold to, say, `n_rows<=700` would
help a user with a weak true effect at that sample size, but would
silently cost precision for a user with a strong true effect at the same
sample size -- and this study shows that cost is real and present
starting at `n_rows=300`, the smallest point tested in this gap. `n_rows`
alone cannot distinguish which user is which.

**A related, more uncomfortable observation: the current `n_rows<=200`
recommendation was itself never tested at a strong coefficient.** The
original Track 2 charter tested `coefficient in {0.15, 0.20}` at
`n_rows in {100, 200}`; the well-powered check was only ever run at
`n_rows=1,000` and now `{300, 500, 700}`. Whether a strong-coefficient
user at `n_rows=200` (right at the current recommended cutoff) would also
see a precision cost from the tuned values is **untested** -- and given
that `n_rows=300` already shows a `-0.239` cost, it would not be
surprising if `n_rows=200` did too. The current recommendation's safety
for strong-coefficient users at `n_rows<=200` is an assumption carried
over from the original charter's scope, not a directly-tested fact.

## Decision: no threshold change

**`redana.defaults.recommended_settings`'s `n_rows<=200` cutoff is left
unchanged.** This gap-narrowing study does not support raising it -- it
actively argues against doing so, since the well-powered precision cost
is confirmed present as low as `n_rows=300` with no sign of vanishing
within the tested range. No code change accompanies this evidence note.

A genuinely new idea surfaced by this study, **not implemented here**:
since the real driver is whether control-arm detection is already near
ceiling rather than `n_rows` itself, an *adaptive* selection -- e.g., run
the cheap control configuration first, check some observable proxy for
whether it's already finding strong signal, and only fall back to the
tuned configuration if not -- could in principle sidestep the
identifiability problem entirely, unlike a static `n_rows`-keyed lookup.
This is a new, unchartered idea (closer to Track 2's originally-deferred
lever 3 territory than to this addendum's scope) and is not evaluated,
designed, or endorsed here -- flagged only as a candidate for a future,
separately-scoped charter.

## Explicit boundary

This investigation does not:

- test any coefficient other than `{0.15, 0.20, 0.7}`, so the exact
  coefficient at which the crossover from "helps" to "hurts" occurs
  remains uncharacterized (somewhere between `0.20` and `0.7`, untested);
- test `n_rows=200` at `coefficient=0.7`, or any `n_rows` below `300` at
  `coefficient=0.7` other than the original charter's own regression
  check at `1,000` -- the gap between the tested low-`n`/weak-coefficient
  cells and the tested higher-`n`/strong-coefficient cells still has an
  untested corner (weak `n_rows`, strong coefficient, other than the
  charter's own `100`/`200` cells which used only weak coefficients);
- design, implement, or evaluate the adaptive-selection idea above;
- test lever 3 (alternate test statistic / HSIC);
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 8, no threshold or default changes because
none are supported by this data -- extending the cutoff would be a claim
stronger than what was measured. Per rule 10, this closes the
gap-narrowing question as scoped; it surfaces but does not authorize the
adaptive-selection idea, which would need its own charter, nor lever 3,
nor any further Track 2 scope.
