# Stage II round 2: relationship-shape degradation design

## Purpose

Per `outline/plan.md` §6 (Benchmark Stage II -- Controlled Degradation):
"progressively violate ideal assumptions one dimension at a time." Round 1
(`docs/superpowers/specs/2026-08-25-stage2-effect-strength-degradation-design.md`)
covered effect strength and located a sharp detectability cliff for one
specific pure-quadratic shape between `coefficient=0.10` and `0.20`
(`docs/evidence/stage2-nonlinear-boundary-followup-20260825.md`). This
round covers `plan.md` §6's **relationship shape** dimension: "pure
linear -> slight curvature -> moderate curvature -> strong nonlinearity."
The other five remaining dimensions (noise, distribution, residual
variance, measurement quality, network structure) are explicitly
deferred to separate, later, narrowly chartered rounds.

## Why relationship shape next

Both Stage I and Stage II round 1 only ever tested one nonlinear shape:
a pure quadratic (`coefficient*(X^2-1)`) with zero linear component by
construction. That leaves an open question the round-1 boundary note
explicitly flagged: is the cliff a property of *how much* signal there
is (effect strength, already characterized), or does it also depend on
*how nonlinear* the relationship is? A relationship shape sweep answers
this directly and is a natural sequel: it reuses the same pair-based
fixture design, varies a different, independent axis, and its two
endpoints exactly match structure already validated (pure linear
matches Stage I's linear mechanism; pure quadratic at the same
coefficient matches Stage I's nonlinear mechanism), giving a built-in
consistency check.

## Fixture design

One new parameterized fixture,
`redana/scenarios.py::generate_stage2_shape_fixture`, with two
independent source/downstream pairs (mirroring Stage I's nonlinear
fixture's pair structure, not its chain structure, so the two pairs are
symmetric and shape is the only thing varied):

```text
X1 = e1
X2 = coefficient * ((1 - shape) * X1 + shape * (X1^2 - 1)) + e2
X3 = e3
X4 = coefficient * ((1 - shape) * X3 + shape * (X3^2 - 1)) + e4
X5 = e5
X6 = e6
```

True edges: `{(X1,X2), (X3,X4)}`, unchanged across all shape levels.

`coefficient` is held fixed at Stage I's strong baseline (`0.7`)
throughout this round -- relationship shape is the only varied
dimension; effect strength stays out of scope here (already covered by
round 1).

`shape` ranges over `[0, 1]`, linearly blending a pure linear term and a
centered quadratic term:

- `shape = 0.0` -- **pure linear**: `X2 = 0.7*X1 + e2`, structurally
  identical to Stage I's linear-fixture pair relationship (not its
  three-node chain, but the same pairwise linear mechanism).
- `shape = 0.33` -- **slight curvature**.
- `shape = 0.67` -- **moderate curvature**.
- `shape = 1.0` -- **strong nonlinearity**: `X2 = 0.7*(X1^2-1) + e2`,
  byte-for-byte the same formula as Stage I's nonlinear fixture at
  `coefficient=0.7`.

Four levels, one fixture shape (two pairs) -- four conditions total.

## Expected behavior and what this tests

At `shape=0`, the incumbent (linear network) should recover both edges
well, matching Stage I's linear-fixture pattern -- the residual layer
should add little beyond it. As `shape` increases, the linear component
shrinks and the quadratic component grows, so the incumbent's recall is
expected to degrade while the residual layer's recall should hold, since
the residual mechanism does not care whether the dependence is linear or
not. At `shape=1` this should reduce to Stage I's already-validated
nonlinear result (incumbent near-zero recall, residual layer detects
both edges in most replications).

This directly tests whether detection is graceful or cliff-like *along
the shape axis*, complementing round 1's already-established cliff
*along the strength axis*.

## Everything else held constant

- `p = 6`, `n = 1,000` rows per replication (unchanged).
- `coefficient = 0.7` fixed (Stage I's strong baseline; not swept here).
- `199` permutations per pair, BH-FDR `alpha = 0.05` (unchanged).
- `NetworkConfig()` and `PrototypeConfig()` frozen defaults (unchanged,
  not tuned against these or any prior results).
- Noise distribution (Gaussian), residual variance (homoskedastic),
  measurement quality (perfect), and network structure (independent
  pairs, same as Stage I's nonlinear fixture) held at baseline.

## Replication design

**50 replications per condition** (matching round 1's per-condition
count; four conditions this round). Every replication uses a distinct,
deterministically derived seed
(`derive_seed("stage2-shape", condition_name, replication_index,
base_seed)`), matching round 1's approach exactly (with a distinct seed
namespace so seeds never collide with round 1's `"stage1"`-prefixed
derivation inside `redana.benchmark.run_replicated_condition`).

## Metrics and reporting

Reuse `redana.benchmark.run_replicated_condition` and its aggregation
unchanged -- no new statistical machinery, since this round only adds a
new fixture generator. Report the four shape levels' aggregate
precision/recall/F1 (mean/median/min/max) and per-edge detection
fraction for both the incumbent and the residual layer, side by side, so
the trend from pure linear to strong nonlinearity is directly visible.

## Execution and verification

Same lighter-than-Gate-0 approach as prior Step 4 / Stage I / Stage II
rounds: no hash-pinned calibration, no per-replication artifact
retention. Write focused failing tests for the new fixture generator
(exact formula at each endpoint, true edges unchanged across shape,
`shape=1.0` byte-identical to
`generate_stage1_nonlinear_fixture(coefficient=0.7)`, `shape=0.0`
producing the expected pure-linear covariance). Implement, verify GREEN,
lint, commit source. Run all four conditions once each at full scale.
Independently spot-recompute a handful of seeds and fixture values.
Record results in an evidence note, reporting the pattern honestly,
including any surprising non-monotonicity.

## Governance

This round is limited to the relationship-shape dimension, at one fixed
effect strength, on one fixture family. It does not authorize noise,
distribution, residual-variance, measurement-quality, or
network-structure degradation rounds, the comparator-fairness protocol
(`plan.md` §8), real-data work, or any package decision. Per
`outline/plan.md` §18 rule 10, what comes next after this round's
results remains a separate, later owner decision.
