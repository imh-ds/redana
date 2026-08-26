# Adaptive configuration selection and usefulness-boundary mapping charter

## Purpose

`docs/evidence/track2-gap-narrowing-20260826.md` found that the choice
between the tuned low-n settings ("sensitive": `n_splits=2, alpha=0.15`)
and the original defaults ("normal": `n_splits=5, alpha=0.05`) is driven
by whether the true effect is already easily detected under normal
settings -- not by `n_rows` -- and flagged, without building it, an
adaptive idea: use a held-out data split to let each dataset pick its own
configuration, sidestepping the fact that a real researcher's true
effect strength is unobservable.

This charter has two purposes, deliberately combined because they share
one simulation grid:

1. **Test whether a held-out-split arbiter can reliably tell, from one
   dataset alone, which configuration is objectively better for it** --
   compared against just guessing, always using one configuration, or the
   existing static `n_rows<=200` rule.
2. **Map the realistic boundary of where redana is useful at all**,
   across a wider `n_rows` x `coefficient` grid than any single prior
   round covered -- directly useful regardless of whether the arbiter
   works, and directly relevant to the project owner's longer-term
   interest in a possible future "Core" (rigorous, higher-data) vs.
   "Explore" (looser, low-n/noisy, directional-pattern-only) engine
   split. **Building that split is explicitly out of scope here** --
   `outline/plan.md` §18 rule 9 bars package/product decisions before
   Stage III, comparator fairness, and real-data validation pass. This
   charter produces evidence that could inform such a decision later, not
   the decision itself.

## What this charter covers

**The arbiter mechanism** (novel component -- rule 4 applies, control
arms required): for one dataset, split rows into a training portion and
a held-out portion (or k folds). For each candidate configuration
(sensitive, normal), fit the full pipeline on the training portion,
record which pairs it flags as edges, then check how many of those
flagged pairs *also* show significant dependence on the held-out
portion -- a genuine independent-data check, unlike Track 1's bootstrap
resampling of the same rows. The configuration with the higher held-out
consistency rate is selected; ties or "neither found anything" fall back
to a fixed rule (normal settings). The final reported result refits the
selected configuration on the full dataset.

**Control arms** (rule 4): always-sensitive, always-normal, and the
existing static `n_rows<=200` rule, evaluated on the same simulated
datasets as the arbiter.

**Ground truth for evaluation**: since this is simulation, each
condition's "objectively better" configuration is already known from
`docs/evidence/track2-low-n-power-levers-20260826.md` and
`docs/evidence/track2-gap-narrowing-20260826.md`'s existing results
(sensitive wins at weak coefficients, normal wins at strong ones) --
the arbiter's per-dataset pick is scored against that, and, separately,
each cell's full grid of results characterizes the usefulness boundary
regardless of the arbiter's accuracy.

## Decisions requiring explicit approval before implementation

### Decision 1: grid scope

Propose (moderate; can expand later if warranted): `n_rows in {100, 300,
500}` x `coefficient in {0.15, 0.7}` -- 6 cells, bounding the
already-characterized faint/loud extremes at three sample sizes,
including the specific `n=100` case the project owner asked about
directly. An expanded alternative would add intermediate coefficients
(e.g. `0.20`, `0.40`) and/or `n_rows in {200, 700}` for a finer boundary
map, at proportionally higher compute cost.

### Decision 2: reps per cell

Propose **30 reps per (cell, method)** -- lighter than the project's
usual 50, because the arbiter mechanism requires multiple fits per
dataset (train-fit x 2 configurations, held-out consistency checks, plus
a final refit), making each "replication" several times more expensive
than a normal single-condition run. 30 keeps this tractable while still
giving a usable signal; an alternative is the full 50 at correspondingly
higher compute cost (likely still shardable via GitHub Actions, per
Track 1/Track 2's established pattern).

### Decision 3: success criterion for the arbiter

Propose: the arbiter is **worth adopting** if its per-cell accuracy
(fraction of reps where it picks the objectively-better configuration)
beats the static `n_rows<=200` rule's accuracy by at least 15 percentage
points *on average across cells*, without falling more than 10 points
below it at any individual cell (mirroring the asymmetric-bar pattern
from the original Track 2 charter). If it does not clear this bar, that
is a legitimate, reportable negative result -- not a failure requiring
another mechanism search under rule 1.

### Decision 4: held-out split ratio

Propose an **80/20 single split** for the arbiter's internal train/test
division (not k-fold) for this first test, specifically *because* the
project owner's question was whether 80/20 is even viable at low `n` --
testing the simpler single-split version first answers that directly.
K-fold averaging is a natural follow-up if single-split shows promise but
is too noisy, not needed to answer the core viability question.

## What this charter does not cover

- Building, naming, or shipping a "Core"/"Explore" engine split --
  `plan.md` §18 rule 9.
- k-fold or nested-CV versions of the arbiter (deferred pending Decision
  4's single-split result).
- Lever 3 (alternate test statistic / HSIC).
- Any change to `redana.defaults.recommended_settings`'s current static
  rule unless this study's results directly support one.
- Real-data evaluation or any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 4, the three control arms (always-
sensitive, always-normal, static rule) are required alongside the novel
arbiter component, not optional. Per rule 10, approving this charter
authorizes only the arbiter test and boundary-mapping grid described
above -- not k-fold extensions, not lever 3, not any Core/Explore
packaging decision, all of which remain separate, later, explicitly-
approved phases.
