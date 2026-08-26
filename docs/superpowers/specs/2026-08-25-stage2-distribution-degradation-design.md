# Stage II round 4: distribution degradation design

## Purpose

Per `outline/plan.md` §6 (Benchmark Stage II -- Controlled Degradation):
"progressively violate ideal assumptions one dimension at a time."
Rounds 1-3 covered effect strength (a sharp cliff), relationship shape
(no cliff), and noise (no cliff), all holding the error terms Gaussian.
This round covers `plan.md` §6's **distribution** dimension: "Gaussian
-> skewed -> heavy-tailed." The remaining three dimensions (residual
variance, measurement quality, network structure) stay explicitly
deferred to separate, later, narrowly chartered rounds.

## Why distribution is a distinct dimension

Rounds 1-3 all drew every error term from a standard normal. This round
instead varies the *shape* of those error distributions -- skewness and
tail weight -- while holding their mean at 0 and variance at 1, so any
change in detection is attributable to distributional shape alone, not
to a change in signal strength or noise magnitude (both already isolated
in rounds 1 and 3). Unlike round 3's `noise_scale`, which touched only
downstream residual terms, distribution shape is applied to **every**
error term in the fixture (source and downstream alike), since `plan.md`
§6 frames this as a property of the data-generating process's error
terms generally, not specifically the residual noise.

## Fixture design

Reuses Stage I's exact two fixture shapes
(`redana/scenarios.py::generate_stage1_linear_fixture` and
`generate_stage1_nonlinear_fixture`), generalized to accept a
`distribution` parameter controlling how all six error draws
(`e1`..`e6`) are generated, each standardized to mean 0 and variance 1
regardless of choice:

- **gaussian** (default): `e = rng.standard_normal(n)` -- unchanged from
  every prior round.
- **skewed**: `e = (rng.chisquare(df=3, size=n) - 3) / sqrt(6)` -- a
  right-skewed distribution (chi-squared with 3 degrees of freedom has
  mean 3, variance 6; centering and scaling gives mean 0, variance 1,
  with positive skew ~1.63).
- **heavy_tailed**: `e = rng.standard_t(df=3, size=n) / sqrt(3)` -- a
  Student's t distribution with 3 degrees of freedom has variance 3;
  scaling by `1/sqrt(3)` gives variance 1, with substantially heavier
  tails than Gaussian (t_3 has no finite kurtosis in the usual sense,
  but noticeably more extreme values in finite samples than a normal).

`coefficient` is held fixed at `0.7` (Stage I's strong baseline)
throughout this round; `noise_scale` stays at its default (`1.0`,
Stage I's baseline). True edge sets are unchanged from Stage I:
`{(X1,X2),(X2,X3)}` for the linear fixture, `{(X1,X2),(X3,X4)}` for the
nonlinear fixture.

Three distribution levels x two fixture shapes = six conditions total,
mirroring rounds 1 and 3's exact structure.

## Everything else held constant

- `p = 6`, `n = 1,000` rows per replication (unchanged).
- `coefficient = 0.7`, `noise_scale = 1.0` fixed (not swept this round).
- `199` permutations per pair, BH-FDR `alpha = 0.05` (unchanged).
- `NetworkConfig()` and `PrototypeConfig()` frozen defaults (unchanged,
  not tuned against these or any prior results).
- Relationship shape (pure linear / pure quadratic, matching Stage I),
  residual variance (homoskedastic), measurement quality (perfect), and
  network structure (chain / two independent pairs) held at baseline.

## Replication design

**50 replications per condition** (matching prior rounds' per-condition
count; six conditions this round). Every replication uses a distinct,
deterministically derived seed via
`redana.benchmark.run_replicated_condition`'s existing seed derivation,
unchanged.

## Metrics and reporting

Reuse `redana.benchmark.run_replicated_condition` and its aggregation
unchanged -- no new statistical machinery, since this round only adds a
`distribution` parameter to existing fixtures (plus a small internal
error-generation helper). Report, per fixture shape, the three
distribution levels' aggregate precision/recall/F1
(mean/median/min/max) and per-edge detection fraction side by side.

## Execution and verification

Same lighter-than-Gate-0 approach as prior rounds: no hash-pinned
calibration, no per-replication artifact retention. Write focused
failing tests for the parameterized fixture generators (default
`distribution="gaussian"` preserves existing behavior exactly for all
prior rounds' tests; `"skewed"` and `"heavy_tailed"` draws have
approximately zero mean and unit variance at large `n`, and the
`"skewed"` draw has positive sample skewness while `"gaussian"` does
not; true edges unchanged regardless of `distribution`). Implement,
verify GREEN, lint, commit source. Run all six conditions once each at
full scale. Independently spot-recompute a handful of seeds and fixture
values. Record results in an evidence note, reporting the degradation
pattern honestly, including any surprising non-monotonicity or cliff-like
behavior, and noting that the permutation-based dCor test and BH-FDR
procedure make no distributional assumption, so any degradation here
would need a distribution-specific explanation rather than an assumed
one.

## Governance

This round is limited to the distribution dimension on Stage I's two
existing fixture shapes, at one fixed effect strength and noise level.
It does not authorize residual-variance, measurement-quality, or
network-structure degradation rounds, the comparator-fairness protocol
(`plan.md` §8), real-data work, or any package decision. Per
`outline/plan.md` §18 rule 10, what comes next after this round's
results remains a separate, later owner decision.
