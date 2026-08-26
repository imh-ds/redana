# Track 2 low-n power lever results

Per `docs/superpowers/specs/2026-08-26-track2-low-n-power-charter.md`
and `docs/superpowers/plans/2026-08-26-track2-low-n-power-levers.md`.
Not a Gate 0 study. Zero new `redana` source -- both levers tested
(`redana.residuals.PrototypeConfig.n_splits`, the FDR `alpha` threshold)
are already first-class parameters of existing, unchanged machinery.
Source revision: `21417330`.

This is the first study in this project whose explicit purpose is
parameter tuning, so `outline/plan.md` §18 rule 3 ("no tuning on the same
simulation matrix used for final evaluation") applies more directly here
than in any prior round. The design below keeps dev-matrix selection and
final evaluation on two completely separate, independently-seeded
matrices, per the charter's Decision 3.

## Dev-matrix selection (not the reported result)

9 `(n_splits, alpha)` combinations were run across the 4 target cells
(`n_rows in {100, 200} x coefficient in {0.15, 0.20}`), 10 reps each
(`scripts/run_track2_dev_matrix.py`, committed `4aa4192c`). Applying the
charter's fixed selection rule (among combinations whose mean precision
doesn't fall more than 10pp below the `n_splits=5, alpha=0.05` control,
pick the one with the largest mean detection improvement) selected
**`n_splits=2, alpha=0.15`**. At only 10 reps per cell, several individual
cells had single-digit hit counts out of 20 opportunities -- this
selection was expected to be noisy, which is exactly why it was evaluated
fresh below rather than reported directly.

## Final evaluation (the reported result)

`n_splits=2, alpha=0.15` (selected) vs. `n_splits=5, alpha=0.05`
(control), 50 independently-seeded reps per cell, run on data with no
overlap with the dev matrix's seeds (`scripts/run_track2_final_evaluation.py`,
committed `21417330`):

| cell | selected detection | control detection | detection improvement | selected precision | control precision | precision delta | clears +15pp/-10pp bar |
| --- | --- | --- | --- | --- | --- | --- | --- |
| n=100, coefficient=0.15 | 0.140 | 0.010 | +0.130 | 0.149 | 0.010 | +0.139 | No (detection short by 2pp) |
| n=100, coefficient=0.20 | 0.140 | 0.010 | +0.130 | 0.127 | 0.010 | +0.117 | No (detection short by 2pp) |
| n=200, coefficient=0.15 | 0.150 | 0.000 | +0.150 | 0.138 | 0.000 | +0.138 | Yes |
| n=200, coefficient=0.20 | 0.210 | 0.010 | +0.200 | 0.222 | 0.010 | +0.212 | Yes |
| **mean across cells** | 0.160 | 0.008 | **+0.1525** | 0.159 | 0.008 | **+0.1515** | -- |

A caveat on "precision" at these near-floor control values: `redana.scoring.score_edges`
defines precision as `0.0` when a replication selects zero edges (not
undefined or excluded), which is why control's precision tracks its
detection so closely -- most control replications simply made no calls at
all. So the "precision delta" above is not "the same number of calls,
now more accurate" -- it's "near-total silence, versus modest real
signal." **0.13-0.22 precision is low in absolute terms**; the finding is
that it is a meaningful improvement over a baseline that is close to
making no calls whatsoever at these cells, not that the selected
combination produces high-confidence edges.

## Verdict against the pre-registered bar

**Two of four cells (`n=200`, both coefficient levels) formally clear the
charter's fixed +15pp detection / -10pp precision bar. The other two
(both `n=100`) fall just short of the detection threshold alone (+13.0pp
vs. the +15pp bar) while showing the same directional pattern and no
precision cost.** Averaged across all 4 cells, mean detection improvement
(+15.25pp) does clear the bar and mean precision moved in the favorable
direction (+15.15pp, nowhere near the -10pp floor) -- but per-cell
verdicts are reported above rather than only the average, since the
charter's Decision 4 states the bar in terms of "at a tested cell," and
collapsing to a single mean would understate that `n=100` did not
individually clear it.

**The direction and consistency of the result across all 4 cells is the
strongest part of the finding.** Detection improved, and precision moved
with it rather than against it, in every single cell tested -- this is
not a tradeoff where one metric was sacrificed for the other, which is
what the charter's asymmetric bar (generous on detection, capped on
precision loss) was designed to guard against. That consistency, plus the
directional match to the mechanism hypothesized in the charter (fewer
folds leave more training data per fold at low `n`; a looser FDR
threshold trades some false-positive risk for power), is more convincing
than any single cell's number in isolation.

**A real caveat: `n=50` reps per cell still carries meaningful Monte
Carlo uncertainty, especially where control sits at or near literal zero**
(`0.000` at `n=200, coefficient=0.15` means zero detections in 100
opportunities; `0.010` elsewhere means one detection in 100). The
*relative* improvement looks dramatic against such a small base rate;
the absolute effect sizes above should be read as "clearly better than
near-silence," not as precisely-calibrated percentages.

## Independent spot recompute

Two replications each for the `selected` and `control` arms at the
`n=200, coefficient=0.15` cell were recomputed directly via
`redana.prototype.run_prototype` (bypassing `redana.benchmark` entirely),
re-deriving seeds with the same `derive_seed("stage1", condition_name,
index, base_seed)` formula `run_replicated_condition` uses internally.
Frame shapes, true edge sets, and per-replication residual edges/scores
all matched the aggregate script's implied outcomes and the reported
cell-level pattern (control found nothing in both spot-checked
replications; selected found the true edge, plus one false positive, in
one of two).

## Explicit boundary

This investigation does not:

- test lever 3 (alternate test statistic / HSIC), deferred to a separate
  charter per the Track 2 charter's Decision 1;
- test any cell outside the 2x2 grid (`n_rows` above 200, coefficient
  above 0.20, or any other Stage II degradation dimension crossed with
  low `n`);
- test `n_splits` or `alpha` values outside the 3x3 candidate grid used
  for dev-matrix selection -- a finer search might find an even better
  combination, or might not;
- test whether the improvement holds under any distributional,
  measurement-quality, or network-structure degradation from Stage II;
- interact this finding with Track 1's stability/detectability reporting
  in any way -- whether bootstrap stability's own overconfidence problem
  (`docs/evidence/stability-validation-20260826.md`) changes shape under
  the selected combination is untested;
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 8, the claim is scoped precisely to what
was measured: `n_splits=2, alpha=0.15` improves detection with no
precision cost at the 4 tested cells, formally clearing the pre-registered
bar at 2 of 4 and coming close at the other 2. This is not a claim that
the mechanism is now reliable at low `n` in any general sense, and it is
not a claim that this is the best possible combination -- only that it
is better than the current default at the cells tested.

Per rule 10: this is a genuinely positive result, and per rule 4 ("every
novel component requires an ablation or control arm") the control arm
built into this design satisfies that requirement for the two levers
tested. Whether to adopt `n_splits=2, alpha=0.15` as a new default (fully,
or only below some `n` threshold), whether to widen the candidate search,
whether to proceed to lever 3, or whether to fold this into Track 1's
disclosure language (e.g. noting when a non-default configuration was
used) are decisions for the project owner, not resolved by this note.
