# Stage II round 6: measurement quality degradation design

## Purpose

Per `outline/plan.md` §6 (Benchmark Stage II -- Controlled Degradation):
"progressively violate ideal assumptions one dimension at a time."
Rounds 1-5 covered effect strength (a sharp cliff), relationship shape,
noise, distribution, and residual variance (no cliff on any of the
latter four). This round covers `plan.md` §6's **measurement quality**
dimension: "perfect measurement -> modest measurement error ->
substantial error." The remaining dimension (network structure) stays
explicitly deferred to a separate, later, narrowly chartered round.

## Why measurement quality is a distinct dimension

Every prior round perturbed something about the *data-generating
process itself* (the systematic relationship's strength or shape, or
the structural noise's magnitude, distribution, or variance pattern).
Measurement error is different: it is added to the *already-realized*
variables, representing observation/instrument imprecision on top of a
fixed, unperturbed true structure. Classical measurement-error theory
predicts **attenuation bias** -- adding independent noise to an observed
predictor systematically shrinks the observed correlation toward zero,
even though the true underlying relationship is unchanged. This is a
mechanistically distinct threat to detection from anything tested in
rounds 1-5, and is a well-understood, named statistical phenomenon this
round can check for directly.

## Fixture design

Reuses Stage I's exact two fixture shapes
(`redana/scenarios.py::generate_stage1_linear_fixture` and
`generate_stage1_nonlinear_fixture`), generalized to accept a
`measurement_error` parameter applied as a **post-processing step**
after the six true columns (`x1`..`x6`) are fully constructed (with
`coefficient`, `noise_scale`, `distribution`, and `heteroskedasticity`
applied exactly as in prior rounds):

```text
observed_i = true_i + sqrt(measurement_error) * std(true_i) * m_i
```

where `m1`..`m6` are six additional independent standard-normal draws
(always Gaussian, regardless of the `distribution` parameter, since
measurement error is conventionally modeled as Gaussian instrument
noise, distinct from the structural error terms) and `std(true_i)` is
each column's own realized sample standard deviation, so
`measurement_error` is interpretable as a noise-to-signal *variance
ratio* relative to each variable's own scale, equivalently expressed as
reliability `rho = 1 / (1 + measurement_error)`. At
`measurement_error = 0.0`, `sqrt(0) = 0` and the observed columns are
numerically identical to the true columns -- the existing fixtures'
exact behavior is preserved.

Unlike round 3's `noise_scale` and round 5's `heteroskedasticity` (which
touch only downstream residual terms), measurement error applies to
**all six** columns, including the independent columns (`X4`-`X6` in the
linear fixture; `X5`-`X6` in the nonlinear fixture) and the source
variables -- because observation error affects every measured variable,
not just the ones with a structural relationship.

`coefficient = 0.7`, `noise_scale = 1.0`, `distribution = "gaussian"`,
`heteroskedasticity = 0.0` (Stage I's baselines) are held fixed
throughout this round. True edge sets are unchanged from Stage I:
`{(X1,X2),(X2,X3)}` for the linear fixture, `{(X1,X2),(X3,X4)}` for the
nonlinear fixture -- the *labels* being tested for stay the same, only
the *observed values* carry added noise.

Three levels, matching `plan.md` §6's own three-point description:

- **perfect** (`measurement_error = 0.0`): reliability 1.0, Stage I's
  exact existing baseline, included here as the reference point;
- **modest** (`measurement_error = 0.25`): reliability 0.8;
- **substantial** (`measurement_error = 1.0`): reliability 0.5.

This gives six conditions total (2 fixture shapes x 3 levels).

## Everything else held constant

- `p = 6`, `n = 1,000` rows per replication (unchanged).
- `coefficient = 0.7`, `noise_scale = 1.0`, `distribution = "gaussian"`,
  `heteroskedasticity = 0.0` fixed (not swept this round).
- `199` permutations per pair, BH-FDR `alpha = 0.05` (unchanged).
- `NetworkConfig()` and `PrototypeConfig()` frozen defaults (unchanged,
  not tuned against these or any prior results).
- Relationship shape (pure linear / pure quadratic, matching Stage I)
  and network structure (chain / two independent pairs) held at
  baseline.

## A confound check carried over from rounds 4 and 5

Applying independent, zero-mean noise to an already-realized variable
does not shift its conditional mean given any other variable, so this
should not reintroduce the round-4-style confound (a genuine population-
level linear relationship appearing where the fixture claims none). This
will be verified with the same large-`n` Monte Carlo check used in
rounds 4 and 5 before interpreting results.

## Replication design

**50 replications per condition** (matching prior rounds' per-condition
count; six conditions this round). Seed derivation unchanged, via
`redana.benchmark.run_replicated_condition`.

## Metrics and reporting

Reuse `redana.benchmark.run_replicated_condition` and its aggregation
unchanged -- no new statistical machinery, since this round only adds a
`measurement_error` post-processing step to existing fixtures. Report,
per fixture shape, the three levels' aggregate precision/recall/F1
(mean/median/min/max) and per-edge detection fraction side by side.

## Execution and verification

Same lighter-than-Gate-0 approach as prior rounds: no hash-pinned
calibration, no per-replication artifact retention. Write focused
failing tests for the parameterized fixture generators (default
`measurement_error=0.0` preserves existing behavior exactly for all
prior rounds' tests; a nonzero `measurement_error` measurably increases
each column's own variance relative to the perfect-measurement case,
consistent with added independent noise; true edges unchanged regardless
of `measurement_error`; a large-`n` Monte Carlo check confirms the
nonlinear fixture's near-zero population linear covariance is preserved
under `measurement_error`, guarding against a round-4-style confound).
Implement, verify GREEN, lint, commit source. Run all six conditions
once each at full scale. Independently spot-recompute a handful of
seeds and fixture values. Record results in an evidence note, reporting
whether the classical attenuation-bias prediction is observed for the
incumbent, and whether the residual layer degrades gracefully, shows a
cliff, or (as in rounds 2-5) shows no meaningful degradation.

## Governance

This round is limited to the measurement-quality dimension on Stage I's
two existing fixture shapes, at one fixed effect strength, noise level,
distribution, and residual-variance setting. It does not authorize a
network-structure degradation round (the last remaining `plan.md` §6
dimension), the comparator-fairness protocol (`plan.md` §8), real-data
work, or any package decision. Per `outline/plan.md` §18 rule 10, what
comes next after this round's results remains a separate, later owner
decision.
