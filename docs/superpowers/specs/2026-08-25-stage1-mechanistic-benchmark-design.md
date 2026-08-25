# Stage I clean mechanistic benchmark design

## Purpose

Per `outline/plan.md` §5 (Benchmark Stage I -- Clean Mechanistic Tests),
answer the question Stage I exists to answer: **can the machinery detect
the mechanism at all?** -- not which method a researcher should prefer in
practice (that is out of scope; `plan.md` §5 says so explicitly).

This follows the Step 4 minimal prototype
(`docs/superpowers/plans/2026-08-25-step4-minimal-prototype.md`) and its
first synthetic validation scenario
(`docs/evidence/step4-first-validation-scenario-20260825.md`,
`docs/evidence/step4-multi-seed-follow-up-20260825.md`). Those showed the
mechanism works on one small mixed scenario across a handful of seeds.
This phase replaces "a handful of seeds on one mixed scenario" with a
proper replicated benchmark on the two clean fixture types `plan.md` §5
names explicitly, each run enough times to report a distribution instead
of a point estimate, per `plan.md` §9's replication guidance
(50-100+ independent draws per condition).

## Scope for this round

`plan.md` §5 names five candidate fixture families: Gaussian linear,
quadratic, sine, threshold/nonmonotonic, and an optional interaction
fixture. This round implements exactly the two fixture types `plan.md`
§5 itself describes expected behavior for -- **the linear fixture** and
**the pure nonlinear fixture** -- using the quadratic shape already
validated repeatedly in this project (Gate 0 F3/F5/Candidate 1, Step 4).
Sine, threshold/nonmonotonic, and interaction fixtures are explicitly
**not** included this round; they are separate, later, narrowly
chartered additions, consistent with this project's practice of never
batching multiple untested structures into one pass.

This also does not include `plan.md` Stage II (§6, controlled
degradation across sample size, effect strength, noise, etc.), the
comparator fairness protocol (§8), or any real-data work (§16). Those
remain separate, later owner decisions.

## Fixture designs

Both fixtures use `p = 6` variables (matching Step 4's dimension) and
`n = 1,000` rows per replication (the dimension Gate 0 validated
extensively and ran quickly at -- not the frozen Gate 0 dCor boundary
itself, which does not apply here: Step 4's mechanism uses its own
permutation-based p-values and BH-FDR, not the pinned Gate 0
boundary-comparison rule).

### Linear fixture (Condition A)

```text
X1 = e1
X2 = 0.7*X1 + e2   (true linear edge)
X3 = 0.7*X2 + e3   (true linear edge)
X4 = e4            (independent)
X5 = e5            (independent)
X6 = e6            (independent)
```

True edge set: `{(X1,X2), (X2,X3)}`. Expected behavior per `plan.md` §5:
the incumbent recovers the linear structure well; the residual layer
adds approximately nothing beyond it (no material excess of detections
past the two true edges).

### Pure nonlinear fixture (Condition B)

```text
X1 = e1
X2 = 0.7*(X1^2 - 1) + e2   (true nonlinear edge, zero linear covariance)
X3 = e3
X4 = 0.7*(X3^2 - 1) + e4   (true nonlinear edge, zero linear covariance)
X5 = e5                    (independent)
X6 = e6                    (independent)
```

Two independent nonlinear pairs (not chained, to keep each edge's
population properties identical and separately interpretable), reusing
exactly the F3/Step4-validated shape (`Cov(X, 0.7*(X^2-1)) = 0` for
standard-normal `X`, so linear covariance is exactly zero in population
while the pair remains strongly dependent). True edge set:
`{(X1,X2), (X3,X4)}`. Expected behavior per `plan.md` §5: the incumbent
may miss this nonlinear-only structure; the residual layer detects a
useful proportion of it. `plan.md` deliberately does not promise 100%
detection here -- "a useful proportion," not perfection.

## Replication design

- **Replications per condition: 100** (top of `plan.md` §9's 50-100+
  range, matching this project's own established batch-count precedent
  from every Gate 0 study).
- **Rows per replication: 1,000.**
- **Permutations per pair: 199** (unchanged from Gate 0 and Step 4).
- **BH-FDR alpha: 0.05** (unchanged from Step 4).
- Every replication uses a distinct, deterministically derived seed
  (`derive_seed("stage1", condition_name, replication_index)`), so the
  full run is reproducible without storing per-replication raw data.
- `NetworkConfig` and `PrototypeConfig` are the unchanged Step 4 frozen
  defaults. No hyperparameter is tuned against this benchmark's results
  (`outline/plan.md` §18 rule 3: no tuning on the same simulation matrix
  used for final evaluation).

## Metrics and reporting

For each replication, score both the incumbent network's edges and the
residual layer's BH-FDR-significant edges against that condition's true
edge set (`redana.scoring.score_edges`, unchanged from Step 4).

Aggregate across the 100 replications per condition and report, per
`plan.md` §9's instruction to report distributions rather than a single
mean:

- mean, median, min, and max precision, recall, and F1 for each
  mechanism;
- the fraction of replications where each mechanism's edge set exactly
  matched the true edge set;
- for Condition B specifically, the fraction of replications in which
  each individual true nonlinear edge was detected by the residual
  layer (mirroring Gate 0's "detected batch count" framing, applied per
  edge rather than per batch).

This stage answers only "does the machinery detect the mechanism at
all, and roughly how often." It does not estimate a calibrated
detection-power curve, does not sweep sample size or effect strength,
and does not compare methods on a matched operating point -- those are
Stage II (`plan.md` §6) and the comparator-fairness protocol (`plan.md`
§8).

## Execution and verification

Unlike Gate 0, this is not a single hash-pinned official run -- it is a
100-replication-per-condition benchmark, closer in spirit to Step 4's
scenario work than to Gate 0's frozen-boundary ceremony. Still:

1. Write focused failing tests for the two new fixture generators and
   the replication/aggregation runner (small `n_reps` for fast tests).
2. Implement, verify GREEN, lint, commit source.
3. Run both conditions once each at the full 100-replication / 1,000-row
   dimensions.
4. Record the aggregate results in a evidence note, honestly reporting
   whatever the numbers show (including any surprises), the same way the
   Step 4 validation note reported the incumbent's false positives
   without softening them.
5. Sanity-check the aggregate numbers with an independent spot recompute
   (not a full from-raw-files verifier like Gate 0, since no artifacts
   are retained per-replication by design -- but re-deriving a handful of
   individual replication seeds and confirming their scores match what
   the aggregate implies).

## Governance

This phase does not authorize Stage II, the comparator-fairness
protocol, sine/threshold/interaction fixtures, real-data work, or any
package decision. Per `outline/plan.md` §18 rule 10, what comes after
Stage I's results are recorded remains a separate, later owner decision.
