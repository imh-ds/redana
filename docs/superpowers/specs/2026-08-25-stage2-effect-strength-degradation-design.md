# Stage II round 1: effect-strength degradation design

## Purpose

Per `outline/plan.md` §6 (Benchmark Stage II -- Controlled Degradation):
"progressively violate ideal assumptions one dimension at a time" and
estimate "how does each procedure degrade as assumptions become less
favorable?"

`plan.md` §6 names seven degradation dimensions: effect strength, noise,
distribution, residual variance, measurement quality, relationship
shape, and network structure. Attempting all seven in one pass would
violate this project's own consistent practice of never batching
multiple untested dimensions into a single round (the same discipline
Gate 0 applied across eight canonical structures one at a time, and
Stage I applied across two of five named fixture families). This design
covers exactly **one** dimension: **effect strength** (`plan.md` §6's
first-listed dimension), holding every other dimension at Stage I's
already-validated baseline. The other six dimensions are explicitly
deferred to separate, later, narrowly chartered rounds.

## Why effect strength first

Stage I (`docs/evidence/stage1-mechanistic-benchmark-20260825.md`)
established that both mechanisms work cleanly at one strong, clean
signal level (`coefficient = 0.7`). It did not test whether detection
holds up as the signal weakens -- the single most natural next question,
and the literal first item in `plan.md` §6's own list. This also
connects directly to `plan.md` §10's stated primary project metric:
"among relationships substantially missed by the linear network, how
many does the nonlinear residual layer recover" -- a question that only
becomes interesting once signals are no longer trivially strong.

## Fixture designs

Reuses Stage I's exact two fixture shapes
(`redana/scenarios.py::generate_stage1_linear_fixture` and
`generate_stage1_nonlinear_fixture`), generalized to accept a
coefficient parameter instead of the fixed `0.7`:

```text
Linear:    X1=e1, X2=coef*X1+e2, X3=coef*X2+e3, X4=e4, X5=e5, X6=e6
Nonlinear: X1=e1, X2=coef*(X1^2-1)+e2, X3=e3, X4=coef*(X3^2-1)+e4, X5=e5, X6=e6
```

True edge sets are unchanged from Stage I: `{(X1,X2),(X2,X3)}` for the
linear fixture, `{(X1,X2),(X3,X4)}` for the nonlinear fixture.

Three strength levels:

- **strong**: `coef = 0.7` (Stage I's exact baseline, included here as
  the reference point for the degradation curve, not re-litigated);
- **moderate**: `coef = 0.4`;
- **weak**: `coef = 0.2`.

This gives six conditions total (2 fixture shapes x 3 strength levels).

## Everything else held constant

- `p = 6`, `n = 1,000` rows per replication (unchanged from Stage I).
- `199` permutations per pair, BH-FDR `alpha = 0.05` (unchanged).
- `NetworkConfig()` and `PrototypeConfig()` frozen defaults (unchanged,
  not tuned against these or any prior results).
- Noise distribution (Gaussian), residual variance (homoskedastic),
  measurement quality (perfect), and network structure (the same chain /
  two-independent-pairs shapes) are all held at Stage I's baseline.
  Varying any of those is a separate, later Stage II round.

## Replication design

**50 replications per condition** (the floor of `plan.md` §9's 50-100+
range; six conditions this round instead of Stage I's two, so a lower
per-condition count keeps total compute proportionate -- roughly 1.5x
Stage I's total replication count across all six conditions combined).
Every replication uses a distinct, deterministically derived seed
(`derive_seed("stage2-strength", condition_name, replication_index,
base_seed)`), matching Stage I's approach exactly.

## Metrics and reporting

Reuse `redana.benchmark.run_replicated_condition` and its aggregation
unchanged -- no new statistical machinery, since this round only
parameterizes existing fixtures differently. Report, per fixture shape,
the three strength levels' aggregate precision/recall/F1
(mean/median/min/max) and per-edge detection fraction side by side, so
the degradation trend across strong -> moderate -> weak is directly
visible for both the incumbent and the residual layer.

## Execution and verification

Same lighter-than-Gate-0 approach as Step 4 and Stage I: no hash-pinned
calibration, no per-replication artifact retention. Write focused failing
tests for the parameterized fixture generators (small `n_reps` for the
runner reuse, since `redana.benchmark` itself is already tested).
Implement, verify GREEN, lint, commit source. Run all six conditions once
each at full scale. Independently spot-recompute a handful of seeds and
fixture values (matching Stage I's verification approach). Record
results in an evidence note, reporting the degradation pattern honestly,
including if detection fails to degrade gracefully or shows any
surprising non-monotonicity.

## Governance

This round is limited to the effect-strength dimension on Stage I's two
existing fixture shapes. It does not authorize noise, distribution,
residual-variance, measurement-quality, or network-structure degradation
rounds, the comparator-fairness protocol (`plan.md` §8), real-data work,
or any package decision. Per `outline/plan.md` §18 rule 10, what comes
next after this round's results remains a separate, later owner
decision.
