# Stage II round 5: residual variance degradation design

## Purpose

Per `outline/plan.md` §6 (Benchmark Stage II -- Controlled Degradation):
"progressively violate ideal assumptions one dimension at a time."
Rounds 1-4 covered effect strength (a sharp cliff), relationship shape
(no cliff), noise (no cliff), and distribution (no cliff, once the
skewed-nonlinear confound is set aside). This round covers `plan.md`
§6's **residual variance** dimension: "homoskedastic -> heteroskedastic."
The remaining two dimensions (measurement quality, network structure)
stay explicitly deferred to separate, later, narrowly chartered rounds.

## Why residual variance is a distinct dimension

Rounds 1-4 all gave every downstream variable's residual noise a fixed
variance, regardless of the source variable's value. This round instead
makes the residual noise's *variance* depend on the source variable's
magnitude -- classic heteroskedasticity, where scatter around a
relationship widens (or narrows) as the predictor moves away from zero.
This is mechanistically distinct from round 3's `noise_scale` (a single
fixed multiplier applied uniformly to every row) and from round 4's
`distribution` (the shape of the noise, not its magnitude's dependence
on another variable).

## Fixture design

Reuses Stage I's exact two fixture shapes
(`redana/scenarios.py::generate_stage1_linear_fixture` and
`generate_stage1_nonlinear_fixture`), generalized to accept a
`heteroskedasticity` parameter that scales each downstream variable's
residual noise standard deviation by `(1 + heteroskedasticity *
abs(source))`, where `source` is that specific downstream variable's own
source column (`X1` for `X2`, `X2` for `X3` in the linear chain; `X1` for
`X2`, `X3` for `X4` in the nonlinear pairs):

```text
Linear:    X1=e1, X2=coef*X1+noise_scale*(1+het*|X1|)*e2,
                  X3=coef*X2+noise_scale*(1+het*|X2|)*e3, X4=e4, X5=e5, X6=e6
Nonlinear: X1=e1, X2=coef*(X1^2-1)+noise_scale*(1+het*|X1|)*e2,
           X3=e3, X4=coef*(X3^2-1)+noise_scale*(1+het*|X3|)*e4, X5=e5, X6=e6
```

At `heteroskedasticity = 0.0`, the multiplier is exactly `1` for every
row, reproducing the existing homoskedastic fixtures byte-for-byte.
`coefficient = 0.7` and `noise_scale = 1.0` (Stage I's baselines) are
held fixed throughout this round; `distribution` stays at its default
(`"gaussian"`). True edge sets are unchanged from Stage I:
`{(X1,X2),(X2,X3)}` for the linear fixture, `{(X1,X2),(X3,X4)}` for the
nonlinear fixture.

Three levels, mirroring rounds 1, 3, and 4's three-level structure even
though `plan.md` §6 itself names only two poles ("homoskedastic ->
heteroskedastic") -- an intermediate level gives a degradation curve
rather than a single before/after comparison, consistent with this
project's practice everywhere else in Stage II:

- **homoskedastic**: `heteroskedasticity = 0.0` (Stage I's exact
  baseline, included here as the reference point, not re-litigated);
- **moderate**: `heteroskedasticity = 0.5`;
- **strong**: `heteroskedasticity = 1.0`.

This gives six conditions total (2 fixture shapes x 3 levels).

## Everything else held constant

- `p = 6`, `n = 1,000` rows per replication (unchanged).
- `coefficient = 0.7`, `noise_scale = 1.0`, `distribution = "gaussian"`
  fixed (not swept this round).
- `199` permutations per pair, BH-FDR `alpha = 0.05` (unchanged).
- `NetworkConfig()` and `PrototypeConfig()` frozen defaults (unchanged,
  not tuned against these or any prior results).
- Relationship shape (pure linear / pure quadratic, matching Stage I)
  and network structure (chain / two independent pairs) held at
  baseline.

## Everything held constant, and a lesson carried over from round 4

Round 4's evidence note
(`docs/evidence/stage2-distribution-degradation-20260825.md`) found that
applying a distributional change to the *source* variable, not just the
downstream noise, silently broke the nonlinear fixture's zero-linear-
covariance guarantee. This round's heteroskedasticity multiplier is
scoped identically to round 3's `noise_scale` -- it touches only each
downstream variable's own residual noise term, never a source variable's
own draw -- specifically to avoid repeating that confound. The
population-level linear covariance between a source and its downstream
variable is unaffected by heteroskedasticity in the noise term, since
`Cov(X1, X2) = coefficient * Cov(X1, f(X1)) + Cov(X1, noise_scale *
(1 + het*|X1|) * e2)`, and the second term is still zero in population
because `e2` is independent of `X1` regardless of the multiplier
attached to it (the multiplier changes the noise's *conditional
variance*, not its *conditional mean*, which stays zero). This will be
verified with a Monte Carlo check before interpreting results, the same
way round 4's confound was caught.

## Replication design

**50 replications per condition** (matching prior rounds' per-condition
count; six conditions this round). Seed derivation unchanged, via
`redana.benchmark.run_replicated_condition`.

## Metrics and reporting

Reuse `redana.benchmark.run_replicated_condition` and its aggregation
unchanged -- no new statistical machinery, since this round only adds a
`heteroskedasticity` parameter to existing fixtures. Report, per fixture
shape, the three levels' aggregate precision/recall/F1
(mean/median/min/max) and per-edge detection fraction side by side.

## Execution and verification

Same lighter-than-Gate-0 approach as prior rounds: no hash-pinned
calibration, no per-replication artifact retention. Write focused
failing tests for the parameterized fixture generators (default
`heteroskedasticity=0.0` preserves existing behavior exactly for all
prior rounds' tests; a nonzero `heteroskedasticity` increases the
downstream variable's conditional variance for large `|source|` rows
relative to small `|source|` rows; true edges unchanged regardless of
`heteroskedasticity`). Implement, verify GREEN, lint, commit source.
Before running the full benchmark, run a large-`n` Monte Carlo spot
check (matching round 4's approach) confirming population-level linear
covariance is unaffected by `heteroskedasticity`, to rule out a round-4-
style confound up front rather than discovering it after the full run.
Run all six conditions once each at full scale. Independently
spot-recompute a handful of seeds and fixture values. Record results in
an evidence note, reporting the degradation pattern honestly.

## Governance

This round is limited to the residual-variance dimension on Stage I's
two existing fixture shapes, at one fixed effect strength, noise level,
and distribution. It does not authorize measurement-quality or
network-structure degradation rounds, the comparator-fairness protocol
(`plan.md` §8), real-data work, or any package decision. Per
`outline/plan.md` §18 rule 10, what comes next after this round's
results remains a separate, later owner decision.
