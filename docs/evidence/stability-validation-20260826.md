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

### well_powered (coefficient=0.7, n_rows=1000)

| | actual replication (50 datasets) | mean bootstrap stability (10 datasets) | tier distribution |
| --- | --- | --- | --- |
| X1,X2 | 1.00 | 1.000 | core=10 |
| X3,X4 | 1.00 | 1.000 | core=10 |
| X5,X6 (incidental, null) | -- | 0.277 (range 0.06-0.78) | -- |

### marginal (coefficient=0.15, n_rows=1000)

| | actual replication (50 datasets) | mean bootstrap stability (10 datasets) | tier distribution |
| --- | --- | --- | --- |
| X1,X2 | 0.34 | 0.780 (range 0.44-0.97) | core=7, provisional=3 |
| X3,X4 | 0.34 | 0.806 (range 0.52-0.98) | core=7, provisional=3 |
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

**At a well-powered effect, bootstrap stability is a trustworthy proxy
for actual replication -- both sit at ceiling and agree.** No surprise
here, and not the interesting case.

**At a marginal effect, bootstrap stability is not a trustworthy proxy
for actual replication -- it substantially overstates confidence.** Actual
replication says this edge would only be detected in about 1 of every 3
independent fresh datasets (0.34). Bootstrap stability, computed from a
*single* dataset, says "core" (>=0.75, the highest tier) 7 times out of
10. A researcher who only ever has one dataset -- the entire premise of
why stability reporting is useful -- would see "core" stability roughly
70% of the time for an edge that in truth only replicates a third of the
time. **This is the opposite of a conservative error: it is false
reassurance, delivered most often in exactly the low-power regime this
whole track exists to serve.**

The mechanism is straightforward in hindsight: bootstrap resampling draws
new samples *from the one dataset already in hand*, with replacement. It
perturbs which rows are included, but it can never redraw the underlying
population noise realization that dataset happened to get. If that one
dataset's particular draw happened to show the relationship clearly
(likely by chance when the true population effect is weak, since roughly
a third of draws will), its resamples will keep finding it too -- because
they're all built from the same lucky draw. Bootstrap stability measures
**within-sample robustness to which rows you keep**, not
**between-sample replicability on a fresh dataset**. These two concepts
coincide when the signal is strong enough that almost every sample
detects it (well_powered), and diverge sharply when detection is a
coin-flip across samples (marginal) -- exactly where §14 asked the
question.

**A second, smaller-but-real caveat: bootstrap stability on a genuinely
null pair is not reliably low, even in a well-powered configuration.**
X5,X6 has no true dependency in either configuration, yet its bootstrap
stability ranged as high as 0.78 in one `well_powered` dataset -- enough
to land in the "core" tier for a pair with zero real relationship. This
is graphical_lasso's familiar small-sample false-positive behavior
(observed throughout Stage I/II) resurfacing inside the bootstrap
procedure specifically; it means even a "core"-tier stability reading
should not, on its own, be read as proof an edge is real.

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
