# Stage II round 7: network structure degradation design

## Purpose

Per `outline/plan.md` §6 (Benchmark Stage II -- Controlled Degradation):
"progressively violate ideal assumptions one dimension at a time."
Rounds 1-6 covered effect strength, relationship shape, noise,
distribution, residual variance, and measurement quality -- six of
`plan.md` §6's seven named dimensions. This round covers the seventh and
last: **network structure**: "chain -> hubs -> communities -> redundant
predictors." Completing this round closes out every named dimension in
`plan.md` §6, which makes it a natural point for the rule-10 checkpoint
("does this project still deserve to exist") once results are in.

## Why this round is structured differently from rounds 1-6

Every prior round perturbed a single *scalar* parameter (a coefficient,
a scale factor, a distribution choice, a variance multiplier) on top of
one or two fixed *topologies* (a three-node chain, or two independent
pairs). Network structure is not a scalar -- it is the topology itself.
`plan.md` §6 names four discrete structural categories, not a
strength/level continuum, so this round tests **four fixture shapes,
each with its own fixed topology**, rather than sweeping a level across
a small number of shapes the way rounds 1, 3, 4, 5, and 6 did. Each
fixture still uses `coefficient = 0.7` (Stage I's strong baseline) for
every true edge, and every other parameter (`noise_scale`,
`distribution`, `heteroskedasticity`, `measurement_error`) at its Stage
I default -- this round isolates topology alone, holding every
previously-tested dimension at its clean baseline.

## Fixture design

All four fixtures keep `p = 6` for direct comparability with every prior
round.

- **chain**: reuses `generate_stage1_linear_fixture` unchanged (no new
  code) -- `X1=e1, X2=0.7*X1+e2, X3=0.7*X2+e3, X4=e4, X5=e5, X6=e6`, true
  edges `{(X1,X2),(X2,X3)}`. This is the structure every prior round
  already validated repeatedly and serves as this round's reference
  point.

- **hub** (new: `generate_stage2_hub_fixture`): one central variable
  with three spokes -- `X1=e1, X2=0.7*X1+e2, X3=0.7*X1+e3, X4=0.7*X1+e4,
  X5=e5, X6=e6`, true edges `{(X1,X2),(X1,X3),(X1,X4)}`. Tests whether a
  single high-degree node degrades detection relative to a chain, where
  every node has degree <= 2.

- **community** (new: `generate_stage2_community_fixture`): two disjoint
  three-node chains instead of one chain plus three independent columns
  -- `X1=e1, X2=0.7*X1+e2, X3=0.7*X2+e3, X4=e4, X5=0.7*X4+e5,
  X6=0.7*X5+e6`, true edges `{(X1,X2),(X2,X3),(X4,X5),(X5,X6)}`. Tests
  whether having *two* independent structural clusters (rather than one
  cluster plus noise columns) changes detection, holding the per-cluster
  topology identical to the already-validated chain.

- **redundant_predictors** (new:
  `generate_stage2_redundant_predictors_fixture`): two highly correlated
  ("redundant") predictors, only one of which is a true cause of a third
  variable -- `X1=e1, X2=0.9*X1+0.436*e2` (chosen so `X2` has unit
  variance: `0.9^2 + 0.436^2 ~= 1`), `X3=0.7*X1+e3` (the true edge is
  `X1->X3`; `X2` is *not* a direct cause of `X3`, but is strongly
  correlated with `X1` and therefore, through that correlation, with
  `X3`), `X4=e4, X5=e5, X6=e6`, true edges `{(X1,X3)}` only -- `(X2,X3)`
  is explicitly *not* a true edge, and detecting it would be a false
  positive driven by collinearity. This directly tests the scenario
  `plan.md` §6 names: does high redundancy between predictors cause
  spurious detections on the redundant partner?

## Everything else held constant

- `p = 6`, `n = 1,000` rows per replication (unchanged).
- `coefficient = 0.7` for every true edge in every fixture; `redundancy
  = 0.9` fixed for the collinear pair in the redundant-predictors
  fixture (not swept -- this round tests the categorical presence of
  redundancy, not its strength, consistent with `plan.md` §6 naming
  discrete structural categories here rather than a continuum).
- `noise_scale = 1.0`, `distribution = "gaussian"`,
  `heteroskedasticity = 0.0`, `measurement_error = 0.0` (Stage I's
  baselines) throughout.
- `199` permutations per pair, BH-FDR `alpha = 0.05` (unchanged).
- `NetworkConfig()` and `PrototypeConfig()` frozen defaults (unchanged,
  not tuned against these or any prior results).

## Replication design

**50 replications per condition** (matching every prior round's
per-condition count; four conditions this round, since this round tests
four discrete topologies rather than two shapes x three levels). Seed
derivation unchanged, via `redana.benchmark.run_replicated_condition`.

## Metrics and reporting

Reuse `redana.benchmark.run_replicated_condition` and its aggregation
unchanged -- no new statistical machinery, since this round only adds
two new fixture generators (`hub`, `community`) plus one more
(`redundant_predictors`) alongside the already-existing chain fixture.
Report all four conditions' aggregate precision/recall/F1
(mean/median/min/max) and per-edge detection fraction. For the
redundant-predictors condition specifically, report the false-positive
rate on the untested `(X2,X3)` pair explicitly, since that is the
condition's central question.

## Execution and verification

Same lighter-than-Gate-0 approach as prior rounds: no hash-pinned
calibration, no per-replication artifact retention. Write focused
failing tests for the two new fixture generators (correct shape, correct
true edges, deterministic given seed, differs across seeds; the
redundant-predictors fixture's `X1`-`X2` pair shows high correlation
(reflecting the intended near-collinearity) while `(X2,X3)` is not in
the declared true-edge set). Implement, verify GREEN, lint, commit
source. Run all four conditions once each at full scale. Independently
spot-recompute a handful of seeds and fixture values. Record results in
an evidence note, reporting whether hub, community, or redundant-
predictor topology degrades either mechanism relative to the
already-validated chain baseline, with particular attention to whether
the residual layer produces a spurious `(X2,X3)` detection in the
redundant-predictors condition.

## Governance

This round tests the last of `plan.md` §6's seven named degradation
dimensions. It does not authorize the comparator-fairness protocol
(`plan.md` §8), Stage III (`plan.md` §7), real-data work, or any package
decision. Per `outline/plan.md` §18 rule 10, once this round's results
are recorded, the project has completed every named dimension in
`plan.md` §6 -- this is an explicit, appropriate point to ask whether the
project still deserves to continue past this stage, not an automatic
trigger to proceed to Stage III.
