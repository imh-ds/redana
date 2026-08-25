# Step 4 first synthetic validation scenario results

This is **not** a Gate 0 study. There is no hash-pinned calibration, no
single-official-run ceremony, and no independent outside verifier here --
that machinery was specific to Gate 0's frozen-boundary, precommitted
single-cell design (`outline/plan.md` §3). This is a single deterministic,
seeded run of the Step 4 minimal prototype (`docs/superpowers/plans/2026-08-25-step4-minimal-prototype.md`,
Task 6), answering the only question Step 4 asks: **does the core
mechanism work?**

## Scenario definition

`redana/scenarios.py::generate_step4_validation_frame`, frozen `p = 6`,
`n = 5000` rows, seed `20260825`:

```text
X1 = e1
X2 = 0.7*X1 + e2                (linear direct edge)
X3 = 0.7*X2 + e3                (linear direct edge, chain continuation)
X4 = e4
X5 = 0.7*(X4^2 - 1) + e5        (pure nonlinear direct edge, zero linear covariance)
X6 = e6                         (fully independent)
```

`e1`...`e6` are independent standard-normal noises. The `X4`-`X5` shape
reuses the F3-validated construction from Gate 0
(`docs/evidence/f3-nonlinear-direct-edge-detection-batch-f3-nonlinear-direct-edge-detection-20260825-001.md`):
`Cov(X4, X4^2-1) = E[X4^3] = 0` for standard-normal `X4`, so the pair has
exactly zero linear covariance in population while remaining strongly
dependent.

True edge sets:

- **Linear** (for scoring the incumbent network): `{(X1,X2), (X2,X3)}`
- **Nonlinear** (added to the linear set for scoring the residual layer):
  `{(X4,X5)}`

## Run configuration

- Incumbent network: `NetworkConfig()` defaults (15-point log-spaced
  alpha grid `0.01`-`1.0`, `gamma = 0.5`).
- Residual layer: `PrototypeConfig()` defaults (five-fold, five-knot
  cubic-spline/Ridge cross-fitted residualization), 199 permutations per
  pair, BH-FDR at `alpha = 0.05` across all `C(6,2) = 15` pairs.
- Command: `python scripts/run_step4_validation_scenario.py` (no flags;
  `n_rows` and `seed` are frozen module constants).

## Results

```text
Incumbent edges: [('X1', 'X2'), ('X2', 'X3'), ('X3', 'X4'), ('X4', 'X5')]
Incumbent vs true linear edges: precision=0.500 recall=1.000 f1=0.667
Residual layer edges: [('X1', 'X2'), ('X2', 'X3'), ('X4', 'X5')]
Residual layer vs all true edges (linear + nonlinear): precision=1.000 recall=1.000 f1=1.000
Nonlinear edge (X4, X5) detected by residual layer: True
```

- **Incumbent network**: recovered both true linear edges (recall 1.0)
  but also selected two edges that are not in the true graph --
  `(X3, X4)` and `(X4, X5)` -- giving precision 0.5. `X3` and `X4` are
  constructed independently of each other by design, and `(X4, X5)`'s
  true linear covariance is exactly zero in population, so both are
  genuine false positives, not scoring artifacts.
- **Residual layer**: recovered all three true edges (the two linear
  ones and the one nonlinear one) with zero false positives -- precision
  and recall both 1.0. It specifically caught `(X4, X5)`, the edge the
  incumbent network cannot see in principle (zero linear covariance).

## Interpretation

The core mechanism works: the residual-dependence layer, using the
unrepaired general-purpose cross-fitted residualizer and BH-FDR, both
(a) reproduces the incumbent linear network's true findings and (b)
recovers a genuinely nonlinear edge with zero linear signal that the
incumbent structurally cannot detect -- with no false positives in this
one run. This matches `outline/plan.md` §5's qualitative expectation for
a mixed linear/nonlinear fixture in miniature.

The incumbent network's two false positives are a real, honestly-reported
observation, not a defect being explained away: at the EBIC-selected
regularization strength for this one seeded draw, sample-covariance noise
around `X3`-`X4` and `X4`-`X5` (both true zeros) was not fully
regularized out. This is a known, unsurprising property of graphical-lasso
model selection under finite samples and is exactly the kind of question
`outline/plan.md` Stage II (§6, controlled degradation across sample
size, effect strength, etc.) exists to characterize -- it is not evidence
of a bug in this implementation, and it is not evidence that the
incumbent network is unreliable in general. One seeded run at one sample
size cannot distinguish "expected sampling noise" from "a systematic
issue" -- that distinction requires exactly the kind of replicated
benchmarking `outline/plan.md` Stage I-III are for, not Step 4.

## Explicit boundary

This is one seeded run, not a Monte Carlo replication. It establishes
only that the six-component mechanism runs end-to-end and produces
sensible, interpretable output on one small mixed scenario. It does not:

- establish detection power, false-positive rates, or reliability under
  realistic conditions (`outline/plan.md` §5-§7, unstarted);
- explain or resolve the incumbent network's two false positives here;
- validate the EBIC-selection approach, the frozen alpha grid, or
  `gamma = 0.5` against any alternative;
- test any nonlinear shape other than the one already validated in
  Gate 0 (`0.7*(Z^2-1)`);
- authorize Stage I/II/III benchmarking, edge typology, detectability
  reporting, or any package decision.

## Retained artifacts

This scenario does not write artifact files (no hash-pinning applies at
this stage); its output is this note and the frozen, deterministic
source in `redana/scenarios.py` and `scripts/run_step4_validation_scenario.py`
(commit `fb33e56f`), reproducible by re-running the script with no
arguments.

## Governance

Per `outline/plan.md` §18 rule 10, this result does not authorize any
further work on its own. Whether to proceed to Stage I benchmarking
(`outline/plan.md` §5), to characterize the incumbent's false-positive
behavior first, or to pause here remains a separate, later owner
decision.
