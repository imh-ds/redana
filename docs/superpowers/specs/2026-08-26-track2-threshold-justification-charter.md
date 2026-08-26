# Static threshold justification charter

## Purpose

`redana.defaults.recommended_settings`'s `n_rows<=200` cutoff has never
actually been justified by evidence -- it was set to the edge of the
original Track 2 low-n study's tested grid (`n_rows in {100, 200}`,
weak coefficients only), not chosen because `n=200` showed any special
behavior. Since then:

- Weak coefficients (`0.15`, `0.20`) have been confirmed safe for
  sensitive settings all the way through `n_rows=700` -- no cost
  anywhere tested.
- Strong coefficient (`0.7`) favors sensitive at `n_rows=100` (normal
  settings aren't near ceiling there) but favors normal at `n_rows=300`
  (a real, persistent precision cost with zero detection benefit).
- **`n_rows=200` at `coefficient=0.7` has never been tested.** The true
  crossover -- the largest `n_rows` at which sensitive settings are still
  safe for a strong effect -- is known only to lie somewhere in
  `(100, 300)`.

This charter closes that gap directly: bracket the crossover finely
enough to pick a specific, evidence-backed threshold, then update
`redana.defaults` to match it (unlike prior studies in this line, which
left the threshold unchanged for lack of evidence -- this one is
explicitly designed to produce enough evidence to move it, in either
direction).

## What this charter covers

**Bracketing grid**: `coefficient=0.7` (the project's established
well-powered anchor -- not testing coefficients stronger than `0.7` is an
explicit scope limit, not an oversight) at several `n_rows` points
between the two already-known bracket ends (`100`: sensitive safe;
`300`: sensitive costly). For each point, compare sensitive vs. normal
using the same methodology as every prior Track 2 study (`n_reps`
independently-seeded datasets per arm, mean detection and precision).

**Classification rule per point**: a point is **"cost present"** (normal
should be used) if sensitive's detection improvement over normal is
negligible (`<5pp`) *and* its precision delta is a meaningful loss
(`<=-5pp`); otherwise **"safe"** (sensitive still justified -- either it
still meaningfully helps, or costs nothing worth caring about).

**Threshold selection**: once points are classified, the new threshold is
set to the **largest tested `n_rows` classified "safe"** -- directly
analogous to how the original `200` was chosen (edge of the
confirmed-safe tested range), except this time the edge is actually
observed via bracketing rather than being an arbitrary stopping point.

## Decisions requiring explicit approval before implementation

### Decision 1: bracketing resolution

Propose a **fine 7-point grid**: `n_rows in {125, 150, 175, 200, 225,
250, 275}`, spanning the full `(100, 300)` gap at `25`-row resolution --
fine enough that the resulting threshold is a real, specific,
evidence-backed number rather than "somewhere in a wide range." A
coarser alternative (`{150, 200, 250}`, 3 points) would be cheaper but
risks leaving nearly as much uncertainty as before (e.g., if `150` is
safe and `250` is not, we still wouldn't know whether the true crossover
is `160` or `240`).

### Decision 2: reps per point

Propose **50 reps per (n_rows, arm)** -- the project's full standard
rep count, matching the original regression checks this threshold
decision rests on, since this result will directly set a number used
going forward, not just characterize a broad pattern.

### Decision 3: cost-classification thresholds

Propose the `<5pp` detection / `<=-5pp` precision rule stated above
(tighter than Track 2's original `+15pp/-10pp` adoption bar, since this
is a safety check -- deciding when sensitive stops being safe -- not an
adoption bar for a new benefit). An alternative, looser rule (matching
the original `+15pp/-10pp` bar exactly) would classify more points as
"safe," pushing the resulting threshold higher, at the cost of tolerating
a larger unflagged precision loss at the chosen cutoff.

### Decision 4: weak-coefficient sanity re-check

Propose **also re-running `coefficient=0.20` at the same 7 points**
(cheap -- doubles this study's cost, not the whole project's) as an
insurance check, confirming weak coefficients remain safe throughout this
specific bracket too, rather than relying solely on extrapolation from
the already-published `100`-`700` results at coarser resolution. The
alternative is to skip this and rely on existing evidence alone.

## What this charter does not cover

- Coefficients stronger than `0.7`.
- Any change to the arbiter (`redana/arbiter.py`) or lever 3.
- Any change to the tier-relabeling or Track 1 disclosure work.
- Real-data evaluation or any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 3, this bracketing grid is entirely new
data -- none of it reuses seeds from any prior study, so setting the
threshold from its results is not circular tuning on already-evaluated
data. Per rule 8, the resulting threshold is scoped exactly to what's
tested: safe up to the largest confirmed-safe point, unknown beyond the
grid's range, and specific to `coefficient<=0.7`. Per rule 10, approving
this charter authorizes only bracketing the crossover and updating the
static threshold accordingly -- not any further Track 2 scope.
