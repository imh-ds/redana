# Stability validation results

Per `docs/superpowers/specs/2026-08-26-stability-reporting-charter.md`
(Track 1) and `docs/superpowers/plans/2026-08-26-stability-reporting.md`
Task 3. Not a Gate 0 study. Zero new `redana` source beyond Tasks 1-2's
`redana/stability.py` and `redana/detectability.py`. Source revision:
`76b3a21f`.

This closes `outline/plan.md` §14's central open question: is bootstrap
stability -- computable from a single real dataset, which is all a real
researcher ever has -- a trustworthy proxy for actual replication
probability, which requires many independent datasets to observe
directly and which this project can only observe because it's
simulation-based?

## Compute note: this run was sharded across GitHub Actions

The original serial design (2 configurations x (50 actual-replication
reps + 10 bootstrap datasets x 100 resamples)) was interrupted once by
a local machine shutdown and, on restart, was still running after over
an hour with zero results produced. Rather than cut `n_bootstrap` below
the charter-approved 100 (Decision 1), the same computation was split
into ~30 independent matrix jobs (5 chunks x 2 configurations for
actual replication, 1 job per bootstrap dataset x 2 configurations) via
`.github/workflows/stability-validation.yml`, using
`scripts/run_stability_validation_shard.py` for each shard and
`scripts/aggregate_stability_validation.py` to recombine them. Seed
derivation is identical to the serial script
(`derive_seed("stage1", condition_name, index, base_seed)`), so sharding
changes nothing about what was computed -- confirmed below. Total wall
time was under 25 minutes running in parallel, versus a projected many
hours serially. One incidental fix was required along the way:
`pyproject.toml` didn't declare `packages = ["redana"]`, so a clean
`pip install -e .` failed with a flat-layout package-discovery error on
every shard (local dev never hit this because it uses `PYTHONPATH`
instead of an editable install); fixed and verified with a fresh venv
before rerunning.

## Results

Tier counts below use the relabeled tiers from
`docs/superpowers/specs/2026-08-26-stability-tier-relabeling-addendum.md`
(`frequently_selected` / `intermittently_selected` / `rarely_selected` --
same `>=0.75` / `0.40-0.75` / `<0.40` thresholds as originally charted,
labels only changed). Both the bootstrap subset (n=10 datasets) and the
actual-replication rate (n=50 datasets) below carry meaningful Monte
Carlo uncertainty at these sample sizes -- the counts and rates below are
evidence that a gap exists in this cell, not precise population
estimates of its size.

### well_powered (coefficient=0.7, n_rows=1000)

| | actual replication (50 datasets) | mean bootstrap stability (10 datasets) | tier distribution |
| --- | --- | --- | --- |
| X1,X2 | 1.00 | 1.000 | frequently_selected=10 |
| X3,X4 | 1.00 | 1.000 | frequently_selected=10 |
| X5,X6 (incidental, null) | -- | 0.277 (range 0.06-0.78) | -- |

### marginal (coefficient=0.15, n_rows=1000)

| | actual replication (50 datasets) | mean bootstrap stability (10 datasets) | tier distribution |
| --- | --- | --- | --- |
| X1,X2 | 0.34 | 0.780 (range 0.44-0.97) | frequently_selected=7, intermittently_selected=3 |
| X3,X4 | 0.34 | 0.806 (range 0.52-0.98) | frequently_selected=7, intermittently_selected=3 |
| X5,X6 (incidental, null) | -- | 0.244 (range 0.07-0.53) | -- |

(`marginal`'s 0.34 actual replication rate is a fresh, independently-seeded
estimate at the same `coefficient=0.15, n=1000` cell `sample-size-dependence-20260825`
measured at 0.29 -- consistent within ordinary sampling variability
across independently-seeded 50-replication draws, not a discrepancy.)

## Independent spot recompute

Two of the ten bootstrapped datasets per configuration were rerun locally
using `scripts/run_stability_validation_shard.py` directly (not just the
same code path -- literally the same script the GitHub Actions shards
ran): `marginal` dataset index 0, and `well_powered` dataset index 6
(chosen because it produced the single highest incidental-pair stability
value, 0.78, of any dataset). Both recomputations matched the shard
artifacts' JSON output exactly, byte-for-byte, confirming sharded and
local execution produce identical results as the deterministic seeding
scheme guarantees. The tier-distribution counts in the table above were
also hand-verified against each configuration's raw per-dataset stability
list.

## Interpretation

**At a well-powered effect, no disagreement was observed between
bootstrap stability and actual replication -- both sit at ceiling
(1.00).** This is a ceiling comparison, not a test of discrimination
(everything looks perfect when nothing can distinguish "somewhat
reliable" from "extremely reliable" at the top of the scale), so it is
weak evidence that bootstrap stability is *calibrated* in this regime --
only that it isn't obviously wrong here.

**At a marginal effect, bootstrap stability and actual replication are
measuring different quantities, and they diverge sharply.** Actual
replication is an unconditional probability over fresh, independent
datasets: this edge was detected in 0.34 of 50 independent draws.
Bootstrap stability is a conditional, within-dataset selection frequency:
given the one dataset a resample subset came from, how often does the
edge survive reshuffling which rows are kept. In this tested cell, mean
conditional bootstrap selection frequency was about 0.8 versus
unconditional fresh-dataset detection of 0.34 -- and 7 of the 10
bootstrapped datasets landed in the highest ("frequently_selected") tier.
That 7/10 count has real sampling uncertainty at n=10 and should be read
as "the tier can clearly mislead in this cell," not as a precise
population rate. Even accounting for that uncertainty, the direction and
rough size of the gap is not a sampling artifact: a researcher who only
ever has one dataset -- the entire premise of why stability reporting is
useful -- would see the highest tier far more often than the edge
actually replicates.

The proposed mechanism has one part that is structurally guaranteed and
one part that isn't yet isolated. Guaranteed by construction: ordinary
nonparametric bootstrap resampling draws new samples *from the one
dataset already in hand*, with replacement -- it perturbs which rows are
included but can never redraw the underlying population-noise
realization that dataset happened to get. So bootstrap stability measures
**within-sample robustness to which rows you keep**, not
**between-sample replicability on a fresh dataset**, and these concepts
can only coincide, not diverge, when they're forced to agree (e.g. near
ceiling). Not yet isolated: how much of this specific gap's *size* comes
from that structural fact alone, versus pipeline-specific amplifiers
(thresholded edge selection, the FDR step, or the non-smooth
graphical-lasso objective) -- no ablation was run to separate these
contributions.

**A second, smaller-but-real observation: in one of the ten
`well_powered` datasets, a genuinely null pair's bootstrap stability
reached 0.78**, enough to land in the "frequently_selected" tier despite
X5,X6 having no true dependency in either configuration. With only one
such observation among ten datasets, this is an illustrative
counterexample -- proof that a high tier is not proof of a real edge --
not an estimate of how often null pairs land in that tier. It is
consistent with, but does not isolate, graphical_lasso's familiar
small-sample false-positive behavior observed throughout Stage I/II as
the contributing cause.

## Explicit boundary

This investigation does not:

- test any coefficient between 0.15 and 0.7, so the exact point where
  bootstrap stability starts to diverge from actual replication is not
  characterized -- only that a substantial gap exists somewhere in that
  range, confirmed at one point (0.15);
- test any `n_rows` other than 1,000, so whether this divergence widens
  or narrows at other sample sizes is unknown;
- test the other six Stage II degradation dimensions;
- propose or evaluate a fix (recalibrating tier thresholds by estimated
  power, combining stability with the detectability lookup, requiring
  both a stability *and* a detectability signal before reporting "core",
  etc.) -- this note documents the problem, not a remedy;
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 8, the claim above is scoped precisely to
what was measured: bootstrap stability overstates replication confidence
at `coefficient=0.15, n=1000` specifically, not "bootstrap stability is
broken" in general -- it agreed with actual replication perfectly at
`coefficient=0.7`.

That said, per rule 10, this is a moment that warrants pausing rather
than continuing straight through Track 1 as originally scoped. The
charter's stability-tier design (`docs/superpowers/specs/2026-08-26-stability-reporting-charter.md`
Decision 2: Core >=0.75, Provisional 0.40-0.75, Background <0.40,
computed from stability alone) was meant to give researchers -- especially
the low-n, weak-effect researchers this track exists to help, per the
`renca` discussion that motivated Track 1 -- a way to gauge confidence
from the one dataset they actually have. This result shows that, as
currently designed, the tier system would mislead that exact population
most often. Whether to recalibrate the thresholds, condition tier
assignment on the detectability lookup (Task 2) rather than reporting
stability alone, redesign the tier system entirely, or reconsider Track
1's viability as scoped is a decision for the project owner, not
something this evidence note resolves on its own.

## Follow-up: peer review and resolution

This note's initial draft was independently peer-reviewed (adversarial
review requested explicitly, not a rubric pass). The review confirmed the
core finding but flagged overclaiming in the original language (since
corrected above: "doubles true confidence" and "trustworthy proxy" were
too strong for what was directly measured) and identified a flaw in the
fix initially proposed alongside this note (auto-attaching a
detectability-lookup caveat when a result falls in a "comparable regime"
to the tested marginal cell) -- the lookup is keyed on the true
population coefficient, which an applied researcher does not know,
making "comparable regime" unoperationalizable outside simulation.

The adopted resolution, per
`docs/superpowers/specs/2026-08-26-stability-tier-relabeling-addendum.md`:
relabel the tiers (`frequently_selected` / `intermittently_selected` /
`rarely_selected`, thresholds unchanged) and attach a single,
unconditional disclosure caveat
(`redana.stability.STABILITY_DISCLOSURE_CAVEAT`) to every tier, always --
no regime-matching, no identifiability assumption. The
detectability-fusion idea is rejected, not deferred, for applied-data use;
`redana.detectability` remains useful for simulation-facing evidence
notes where the true coefficient is known.
