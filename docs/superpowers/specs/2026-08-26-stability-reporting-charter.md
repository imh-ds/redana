# Stability and detectability reporting charter (Track 1)

## Purpose

Following the sample-size dependence findings
(`docs/evidence/sample-size-dependence-20260825.md`), the project owner
raised a specific concern: the mechanism cannot achieve `n=1,000`-level
accuracy at the `n=100-300` range common in real psychological and
behavioral research, and no method can. The agreed response ("Track 1")
is not to chase more raw power, but to change what the tool *claims*:
move from a binary detect/no-detect output to a graded, honest signal
about confidence, and make the tool's own detectability limits visible
to the researcher rather than silently underperforming.

This directly implements `outline/plan.md` §13 ("Stability Becomes the
Researcher-Facing Pruning Mechanism"), §14 ("Validate Bootstrap
Stability Against Actual Replication"), and a first, narrow slice of §15
("Detectability Reporting"). Per `plan.md` §19's recommended build
order, these come immediately after Stage II, before edge typology,
before real-data work, and well before any package decision (§17 rule
9: "no package or product work before the core statistical gates
pass"). This charter scopes the *statistical* machinery only -- no
visualization, no rendering, no opacity/width display logic (that is
explicitly `plan.md` §13's later, researcher-facing polish layer, out of
scope here).

## What this charter covers

1. **Bootstrap stability**: for a single dataset, resample rows with
   replacement, rerun the residual-dependence test on each resample, and
   compute each pair's selection frequency across resamples ("bootstrap
   stability").
2. **Validation against actual replication** (`plan.md` §14's central
   question): compare bootstrap stability (computed *within* one
   dataset) against the *actual* between-dataset replication
   probability (already directly measurable via
   `redana.benchmark.run_replicated_condition`'s existing per-edge
   detection fraction across many independently-drawn datasets). Are
   they close? Is bootstrap stability a trustworthy proxy for something
   we cannot normally observe in a real single-sample study (true
   replication probability)?
3. **A minimal stability-tier classifier**: given a bootstrap stability
   value, classify a pair as `core` / `provisional` / `background`,
   implementing `plan.md` §13's three-tier scheme as a pure function --
   no visualization.
4. **A minimal detectability report**: given `n`, `coefficient`, and the
   fixture shape, look up (from already-computed benchmark grids, not a
   new statistical claim) what per-edge detection rate to expect --
   packaging Stage II's and the sample-size investigation's own results
   into a queryable form, as a first slice of §15.

## Decisions requiring explicit approval before implementation

### Decision 1: bootstrap resample count

Propose **100 bootstrap resamples per dataset**. This is deliberately
smaller than the 199 permutations used for each individual pair's
p-value (a different, unrelated randomization), chosen for compute
reasons: bootstrap stability requires rerunning the *entire* prototype
(cross-fitted residualization + permutation test for every pair) on
each resample, which is far more expensive per unit than a single
permutation draw. 100 resamples gives stability estimates accurate to
roughly +/-5 percentage points (rule-of-thumb `1/(2*sqrt(resamples))`),
adequate for tier classification, not for precise stability curves.

### Decision 2: stability-tier thresholds

Propose, as a starting convention (not tuned against any run's
results, chosen before any tier-classification run happens):

- **Core**: bootstrap stability `>= 0.75`
- **Provisional**: `0.40 <= stability < 0.75`
- **Background**: `stability < 0.40`

These are round, defensible starting points (75% and 40% selection
frequency), not derived from this project's own data. Per rule 3 ("no
tuning on the same simulation matrix used for final evaluation"), these
must be fixed before Task 2's validation runs and not adjusted
afterward to make results look cleaner.

### Decision 3: validation configurations

Propose validating on exactly two configurations, chosen to span a
well-powered case and a marginal case near round 1's already-
characterized cliff:

- **Well-powered**: nonlinear fixture, `coefficient=0.7`, `n=1,000`
  (Stage I's baseline -- ceiling detection expected, bootstrap stability
  should sit high and match near-100% actual replication).
- **Marginal**: nonlinear fixture, `coefficient=0.15`, `n=1,000` (Stage
  II round 1's boundary follow-up found ~34%-38% actual replication
  here -- the most informative case for checking whether stability
  correctly reflects genuine uncertainty rather than either false
  confidence or false alarm).

A hybrid, compute-scoped design, since running the full prototype (cross-
fitted residualization + permutation test across all 15 pairs) on every
bootstrap resample of every dataset is far more expensive than any prior
round's single-run-per-replication studies:

- **Actual replication ground truth**: 50 independent datasets per
  configuration (matching every prior round's replication count), each
  run once, unchanged from `run_replicated_condition`'s existing
  behavior -- cheap, consistent with every prior round's compute
  profile.
- **Bootstrap stability**: computed on a **subset of 10 of those 50
  datasets** per configuration, each with 100 bootstrap resamples
  (Decision 1) -- `10 x 100 = 1,000` full prototype runs per
  configuration (`2,000` total across both configurations), a large but
  tractable addition, roughly 3-4x a single prior Stage II round's
  compute rather than 10x+.

This keeps the "actual replication" measurement at full prior precision
(50 datasets) while limiting the expensive bootstrap step to a smaller,
explicitly-acknowledged sample (10 datasets) -- adequate to check
whether bootstrap stability's *distribution* across those 10 datasets
tracks the 50-dataset actual replication rate, not to produce a
precise per-dataset stability estimate for every one of the 50.

## What this charter does not cover

- Any rendering, plotting, width/opacity display logic (`plan.md` §13's
  visual layer).
- Edge typology (`plan.md` §12), explicitly sequenced after this per
  `plan.md` §19.
- The full `plan.md` §15 detectability-reporting vision (shape-specific
  curves for every relationship type) -- only a minimal lookup over
  already-computed grids.
- Track 2 (the technical low-n power levers discussed alongside this
  charter -- adaptive cross-fitting, threshold reconsideration,
  alternate test statistics). Track 2 is explicitly deferred to a
  separate, later charter, to be taken up after Track 1.
- Any change to the incumbent network, the residual test itself, or any
  existing fixture. This is purely additive: new `redana` modules for
  bootstrap stability, tier classification, and detectability lookup.

## Governance

Per `outline/plan.md` §18 rule 10, approving this charter does not
authorize Track 2, edge typology, real-data work, or any package
decision. Those remain separate, later, explicitly-approved phases.
