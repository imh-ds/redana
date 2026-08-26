# Low-n power levers charter (Track 2)

## Purpose

Track 1 (`docs/superpowers/specs/2026-08-26-stability-reporting-charter.md`,
closed out per `docs/superpowers/specs/2026-08-26-stability-tier-relabeling-addendum.md`)
changed what the tool *claims* at low `n` / weak effect sizes, without
changing what it can actually *detect*. This charter takes up the
deferred other half: are there technical changes to the detection
pipeline itself that recover real, meaningful power at low `n`, without
chasing full parity with the `n=1,000` regime (explicitly not the goal --
`n=500`-`1,000`-level accuracy at `n=100`-`300` is not attainable and is
not being attempted here).

This directly follows the project owner's standing goal: stay useful at
the `n=100`-`300` range common in real psychological/behavioral research
(`docs/evidence/sample-size-dependence-20260825.md` established that
detection collapses hard below `n=500` even for a strong effect, and
`plan.md`'s own `n>=200` floor is only a loose guideline, not a
guarantee). The bar for success here is explicitly **"meaningfully
better than doing nothing, and honestly reported,"** not
**"matches high-n performance."**

## What this charter covers

Three known technical levers on the existing pipeline, none requiring a
new estimand or a new comparator concept:

1. **Cross-fitting fold count** (`redana.residuals.PrototypeConfig.n_splits`,
   currently fixed at `5`). At `n=100`, 5-fold cross-fitting trains each
   fold's adjustment model on ~80 rows and holds out ~20 -- fewer folds
   (e.g. `2`-`3`) trade a less rigorous held-out estimate for more
   training data per fold, which may matter more at low `n`.
2. **FDR threshold** (`alpha`, currently `0.05` everywhere in this
   project). A looser threshold (e.g. `0.10`) at low `n` would trade
   some false-positive risk for detection power -- directly the kind of
   "looser assumptions, less rigorous pruning" tradeoff the project
   owner has already said is acceptable at low `n`, as long as it's
   disclosed.
3. **Alternate small-sample test statistic** (currently permutation
   distance correlation via `dcor`; a candidate alternative is HSIC,
   which sometimes behaves better at small sample sizes). This is a
   larger, riskier change than the two above -- it introduces a second
   comparator concept, which `plan.md` §18 rule 4 ("every novel
   component requires an ablation or control arm") and rule 5 ("every
   comparator gets a documented fair-use protocol") apply to directly.

## Decisions requiring explicit approval before implementation

### Decision 1: scope of this first cut

Propose testing **levers 1 and 2 only** (cross-fitting fold count, FDR
threshold) in this charter. Both are parameter-only changes to the
existing pipeline -- no new statistical machinery, no new comparator,
cheap to implement and test. **Defer lever 3** (alternate test statistic
/ HSIC) to a separate, later charter: it requires real implementation
work, an explicit fair-use protocol against the existing dCor-based
statistic, and is a fundamentally riskier change to be doing at the same
time as the first two.

### Decision 2: target regime to test

Propose testing at the specific cells where Track 1's own evidence
(`docs/evidence/sample-size-dependence-20260825.md` Stage A/B) already
showed the sharpest collapse:

- `n_rows` in `{100, 200}` (below and at `plan.md`'s stated floor);
- `coefficient` in `{0.15, 0.20}` (Stage B's grid showed these
  essentially undetectable at `n=500` and only partially recovering by
  `n=1,000`-`2,000` -- the regime where a power lever would matter most
  if it works at all).

This is a 2x2 grid (4 cells), not a full sweep -- enough to show whether
either lever moves the needle, not to trace a precise power surface.

### Decision 3: non-circular tuning design (rule 3)

This charter is explicitly about *tuning* parameters (`n_splits`,
`alpha`), so rule 3 ("no tuning on the same simulation matrix used for
final evaluation") applies more directly here than in any prior round.
Propose a strict two-matrix design:

- **Dev matrix**: a small number of independently-seeded datasets (propose
  10 per cell) used only to compare candidate lever values (e.g.
  `n_splits in {2, 3, 5}`, `alpha in {0.05, 0.10, 0.15}`) against each
  other. Whichever combination looks best here is *fixed* before the
  next step -- no looking back.
- **Final evaluation matrix**: a fresh, independently-seeded 50-dataset
  replication (matching every prior round's precision) run *once*, using
  only the fixed configuration chosen from the dev matrix, plus the
  existing default configuration (`n_splits=5, alpha=0.05`) as the
  control arm for direct comparison. This run's numbers are what gets
  reported -- not the dev matrix's.

### Decision 4: what "meaningfully better" means, fixed in advance

Propose defining success before running anything, per rule 8 (claims no
stronger than measured) and to avoid post-hoc goalpost-moving:

- A lever combination is **worth adopting** if per-edge detection at a
  tested cell improves by at least 15 percentage points over the
  `n_splits=5, alpha=0.05` control arm, **without** residual precision
  dropping by more than 10 percentage points at the same cell (the
  looser-FDR tradeoff made explicit and bounded, not open-ended).
- If no combination clears that bar at any tested cell, the honest
  conclusion is "these two levers don't meaningfully help at this
  regime" -- itself a useful, reportable result, not a failure requiring
  another round of lever-hunting under rule 1 ("no new subsystem after a
  hard-stop failure without a new charter").

## What this charter does not cover

- Lever 3 (alternate test statistic / HSIC), deferred to a later charter
  per Decision 1.
- Any change to the incumbent linear network, the BH-FDR procedure
  itself (only its threshold), or any fixture.
- Any change to Track 1's stability/detectability machinery.
- Real-data evaluation or any package decision (`plan.md` §18 rule 9).
- Testing regimes other than the 2x2 grid in Decision 2 (other Stage II
  degradation dimensions crossed with low `n` remain untested).

## Governance

Per `outline/plan.md` §18 rule 10, approving this charter does not
authorize lever 3, real-data work, or any package decision. If neither
lever clears Decision 4's bar, that closes this specific question
without automatically authorizing a further search for other levers --
that would need its own new charter.
