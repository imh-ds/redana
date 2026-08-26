# Addendum: adopting Track 2's lever findings as a conditional default

Follows `docs/evidence/track2-low-n-power-levers-20260826.md`. The
project owner asked to adopt `n_splits=2, alpha=0.15` as the new default.
Before making that change, a regression check was run at the well-powered
baseline used throughout Stage I/II and Track 1
(`n_rows=1000, coefficient=0.7`, 50 reps per arm, fresh seeds, condition
name prefix `track2-regression-check-wellpowered-`):

| | detection | precision | recall |
| --- | --- | --- | --- |
| `n_splits=2, alpha=0.15` | 1.000 | **0.838** | 1.000 |
| `n_splits=5, alpha=0.05` (original) | 1.000 | **0.980** | 1.000 |

Detection stays at ceiling either way. Precision drops by ~14 percentage
points with the tuned values -- a pure cost, since detection had nothing
to gain (already at 1.000 under either setting). This is exactly the
kind of regression `docs/evidence/track2-low-n-power-levers-20260826.md`'s
"Explicit boundary" section flagged as untested: the tuned values were
only validated at `n_rows in {100, 200}`, never at `n_rows=1000`, and a
looser FDR threshold with no detection to gain is a pure false-positive
cost there.

## Decision

**A global default change is rejected.** Adopting `n_splits=2, alpha=0.15`
everywhere would silently regress precision on every well-powered result
this project has already published, for zero benefit, violating
`outline/plan.md` §18 rule 8 (no claim stronger than what's measured) --
the tuned values were never validated as safe outside the tested low-n
regime.

**Adopted instead: a conditional recommendation, gated on sample size.**
`redana.defaults.recommended_settings(n_rows)` returns `n_splits=2,
alpha=0.15` for `n_rows <= 200` (the tested regime) and the original
`n_splits=5, alpha=0.05` for `n_rows > 200`. No existing `redana`
function signature or default value changes -- `PrototypeConfig.n_splits`
remains `5` as a bare dataclass default, and no `alpha` default is added
to `run_prototype` or `run_replicated_condition`, both of which require
it explicitly as before. This is purely additive: a new opt-in helper
function callers can use going forward.

Existing scripts (every Stage I/II round, the sample-size-dependence
study, Track 1's validation, Track 2's own dev/final matrices) are
**not** retroactively rewritten to call this helper -- they remain
historical records of what was actually run to produce their
already-published numbers. Future scripts should call
`recommended_settings(n_rows)` rather than hardcoding
`PrototypeConfig()` and a literal `alpha=0.05`, by convention going
forward.

## What remains untested

`n_rows` strictly between `200` and `1,000` -- whether the tuned values
help, hurt, or are roughly neutral in that gap is unknown; the `200`
threshold is precisely where testing stopped, not a validated inflection
point. Any future study that narrows this gap should update
`_LOW_N_THRESHOLD` accordingly, with its own regression check at
whatever new boundary is proposed.

## Governance

Per `outline/plan.md` §18 rule 8, `redana.defaults.recommended_settings`
recommends the tuned values only within the exact regime they were
measured in, not by extrapolation. Per rule 10, this addendum resolves
only the default-adoption question -- it does not authorize narrowing
the untested gap, lever 3, or any further Track 2 work.
