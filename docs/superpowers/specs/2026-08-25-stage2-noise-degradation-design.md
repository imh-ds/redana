# Stage II round 3: noise degradation design

## Purpose

Per `outline/plan.md` §6 (Benchmark Stage II -- Controlled Degradation):
"progressively violate ideal assumptions one dimension at a time." Round
1 covered effect strength (a sharp cliff between `coefficient=0.10` and
`0.20`); round 2 covered relationship shape (no cliff at all, holding
effect strength fixed at `0.7`). This round covers `plan.md` §6's
**noise** dimension: "low -> moderate -> high." The remaining four
dimensions (distribution, residual variance, measurement quality,
network structure) stay explicitly deferred to separate, later, narrowly
chartered rounds.

## Why noise is a distinct dimension from effect strength

`plan.md` §6 lists effect strength and noise as two separate items, and
they are mechanistically distinct in this project's fixtures: effect
strength (`coefficient`) scales the *systematic* component of a
downstream variable's dependence on its source; noise scales the
*residual/error* component (`e2`, `e4` in the existing fixtures) that is
independent of the source by construction. Round 1 already swept
`coefficient` while holding the residual noise term fixed at unit
variance. This round holds `coefficient` fixed at Stage I's strong
baseline (`0.7`) and instead scales the residual noise term itself,
asking a different question: not "how strong is the true relationship"
but "how much unrelated variability is mixed into the downstream
variable on top of a fixed-strength true relationship."

## Fixture design

Reuses Stage I's exact two fixture shapes
(`redana/scenarios.py::generate_stage1_linear_fixture` and
`generate_stage1_nonlinear_fixture`), generalized to accept a
`noise_scale` parameter that multiplies each downstream variable's own
residual noise term (`e2`, `e3` in the linear chain; `e2`, `e4` in the
nonlinear pairs) -- not the source variables' variance (`e1`, `e4`/`e1`,
`e3` respectively), which stay fixed at unit variance throughout, since
those represent the independent variables being related, not
measurement or residual noise on the dependent side.

```text
Linear:    X1=e1, X2=coef*X1+noise_scale*e2, X3=coef*X2+noise_scale*e3, X4=e4, X5=e5, X6=e6
Nonlinear: X1=e1, X2=coef*(X1^2-1)+noise_scale*e2, X3=e3, X4=coef*(X3^2-1)+noise_scale*e4, X5=e5, X6=e6
```

`coefficient` is held fixed at `0.7` (Stage I's strong baseline)
throughout this round. True edge sets are unchanged from Stage I:
`{(X1,X2),(X2,X3)}` for the linear fixture, `{(X1,X2),(X3,X4)}` for the
nonlinear fixture.

Three noise levels:

- **low**: `noise_scale = 0.5` (half the residual noise variance
  relative to the existing baseline);
- **moderate**: `noise_scale = 1.0` (Stage I's exact existing baseline,
  included here as the reference point -- this is byte-identical to the
  existing fixtures at their current defaults, not re-litigated);
- **high**: `noise_scale = 2.0` (double the residual noise variance).

This gives six conditions total (2 fixture shapes x 3 noise levels),
mirroring round 1's exact structure.

## Everything else held constant

- `p = 6`, `n = 1,000` rows per replication (unchanged).
- `coefficient = 0.7` fixed (not swept this round).
- `199` permutations per pair, BH-FDR `alpha = 0.05` (unchanged).
- `NetworkConfig()` and `PrototypeConfig()` frozen defaults (unchanged,
  not tuned against these or any prior results).
- Relationship shape (pure linear / pure quadratic, matching Stage I),
  distribution (Gaussian), measurement quality (perfect), and network
  structure (chain / two independent pairs) held at baseline.

## Replication design

**50 replications per condition** (matching round 1's per-condition
count; six conditions this round). Every replication uses a distinct,
deterministically derived seed
(`derive_seed("stage1", condition_name, replication_index, base_seed)`,
matching `redana.benchmark.run_replicated_condition`'s existing seed
derivation exactly -- the literal `"stage1"` prefix is a known cosmetic
quirk baked into that function from Stage I, already noted in round 1
and round 2, and harmless here since `condition_name` still
differentiates every seed).

## Metrics and reporting

Reuse `redana.benchmark.run_replicated_condition` and its aggregation
unchanged -- no new statistical machinery, since this round only adds a
`noise_scale` parameter to existing fixtures. Report, per fixture shape,
the three noise levels' aggregate precision/recall/F1 (mean/median/min/max)
and per-edge detection fraction side by side, so the degradation trend
across low -> moderate -> high is directly visible for both mechanisms.

## Execution and verification

Same lighter-than-Gate-0 approach as prior rounds: no hash-pinned
calibration, no per-replication artifact retention. Write focused
failing tests for the parameterized fixture generators (default
`noise_scale=1.0` preserves existing Stage I / round 1 / round 2
behavior exactly; a smaller `noise_scale` increases the observed
correlation magnitude for a fixed `coefficient`; a larger `noise_scale`
decreases it; true edges unchanged regardless of `noise_scale`).
Implement, verify GREEN, lint, commit source. Run all six conditions
once each at full scale. Independently spot-recompute a handful of
seeds and fixture values. Record results in an evidence note, reporting
the degradation pattern honestly, including any surprising
non-monotonicity or cliff-like behavior.

## Governance

This round is limited to the noise dimension on Stage I's two existing
fixture shapes, at one fixed effect strength. It does not authorize
distribution, residual-variance, measurement-quality, or
network-structure degradation rounds, the comparator-fairness protocol
(`plan.md` §8), real-data work, or any package decision. Per
`outline/plan.md` §18 rule 10, what comes next after this round's
results remains a separate, later owner decision.
