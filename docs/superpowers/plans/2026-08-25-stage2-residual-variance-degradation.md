# Stage II Round 5 Residual Variance Degradation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a six-condition benchmark (2 Stage I fixture shapes x 3
heteroskedasticity levels, 50 replications each) answering
`outline/plan.md` §6's residual-variance degradation question, reusing
every existing `redana` component unchanged.

**Architecture:** Generalize `redana/scenarios.py`'s two Stage I fixture
generators to accept a `heteroskedasticity: float = 0.0` parameter that
multiplies each downstream variable's residual noise by `(1 +
heteroskedasticity * abs(source))`, scoped only to the noise term (never
a source variable's own draw), mirroring round 3's `noise_scale` scoping
to avoid round 4's source-distribution confound. A CLI script binds
three heteroskedasticity values via `functools.partial` (at fixed
`coefficient=0.7, noise_scale=1.0`) and calls
`redana.benchmark.run_replicated_condition` six times.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-25-stage2-residual-variance-degradation-design.md`

## Global Constraints

- Reuse `redana.benchmark.run_replicated_condition`,
  `redana.network.NetworkConfig`, `redana.residuals.PrototypeConfig`,
  `redana.scoring.score_edges` unchanged. Do not modify any prior
  round's component behavior at existing defaults.
- Adding `heteroskedasticity: float = 0.0` to
  `generate_stage1_linear_fixture` and `generate_stage1_nonlinear_fixture`
  must not change their behavior for any existing caller that omits the
  argument.
- The heteroskedasticity multiplier applies only to each downstream
  variable's own residual noise term, scaled by that variable's own
  source column's absolute value -- never to a source variable's own
  draw.
- Six conditions only this round: `{linear, nonlinear} x
  {homoskedastic=0.0, moderate=0.5, strong=1.0}`, `coefficient=0.7`,
  `noise_scale=1.0` fixed. No measurement-quality or network-structure
  degradation this round.
- `p = 6`, `n = 1,000`, `199` permutations, BH-FDR `alpha = 0.05`, `50`
  replications per condition at full scale.
- No hyperparameter tuning against this round's results.

---

### Task 1: Add a heteroskedasticity parameter to the Stage I fixtures

**Files:** Edit `redana/scenarios.py`; add
`tests/redana/test_stage2_residual_variance_scenarios.py`.

**Interfaces:** `generate_stage1_linear_fixture(n_rows: int, seed: int,
coefficient: float = 0.7, noise_scale: float = 1.0, distribution: str =
"gaussian", heteroskedasticity: float = 0.0)` and the nonlinear
equivalent -- add the keyword parameter after `distribution`.

- [ ] **Step 1: Write failing tests**

Add tests asserting: calling either generator with no
`heteroskedasticity` argument produces byte-identical output to current
behavior (regression-guard); at a nonzero `heteroskedasticity`, the
conditional variance of the downstream residual (measured by comparing
`X2` values where `|X1|` is in the top decile vs. the bottom decile,
after removing the systematic `coefficient * f(X1)` component) is larger
for the top-decile rows than the bottom-decile rows; true edges are
unchanged regardless of `heteroskedasticity`; a large-`n` (`50,000`)
Monte Carlo check confirms `corr(X1, X2)` under
`heteroskedasticity=1.0` stays close to its value under
`heteroskedasticity=0.0` (within `0.05`) for both fixture shapes --
this is the round-4-confound guard called for in the design spec, run
here as an automated test rather than only a manual notebook check.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/redana/test_stage2_residual_variance_scenarios.py -v --basetemp .pytest-stage2-residual-variance-red`. Expect a `TypeError` for the unexpected `heteroskedasticity` keyword.

- [ ] **Step 3: Implement**

Add `heteroskedasticity: float = 0.0` to both function signatures,
multiplying each downstream variable's noise term by `(1 +
heteroskedasticity * np.abs(source_column))` before adding it to the
systematic component.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-stage2-residual-variance-green`,
then Ruff. Also re-run `tests/redana/test_stage1_scenarios.py`,
`tests/redana/test_stage2_scenarios.py`,
`tests/redana/test_stage2_shape_scenarios.py`,
`tests/redana/test_stage2_noise_scenarios.py`, and
`tests/redana/test_stage2_distribution_scenarios.py` to confirm no
regression. Commit as `feat: add heteroskedasticity parameter to Stage I fixture generators`.

### Task 2: Run the six-condition residual-variance benchmark and record results

**Files:** Create `scripts/run_stage2_residual_variance_degradation.py`;
create `docs/evidence/stage2-residual-variance-degradation-20260825.md`
after running.

**Interfaces:** The script defines the three named heteroskedasticity
levels (`homoskedastic=0.0, moderate=0.5, strong=1.0`), binds each
fixture generator with `functools.partial(generate_stage1_linear_fixture,
coefficient=0.7, heteroskedasticity=...)` (and the nonlinear
equivalent), and calls `run_replicated_condition` once per of the six
`(shape, level)` combinations with `n_reps=50`, `n_rows=1000`, matching
prior rounds' other frozen settings. Prints results grouped by fixture
shape.

- [ ] **Step 1: Preflight and commit source**

Run the full pytest suite
(`--basetemp .pytest-stage2-residual-variance-preflight`) and `ruff
check research tests scripts redana`; expect full PASS and lint clean.
Commit the script as `feat: add Stage II residual-variance degradation runner script`.

- [ ] **Step 2: Run all six conditions once each at full scale**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_stage2_residual_variance_degradation.py`. Six conditions x 50 replications x 15 pairs x 199 permutations at n=1,000.

- [ ] **Step 3: Independent spot recompute**

Without importing `redana.benchmark`, re-derive a handful of individual
replication seeds across a few of the six conditions, regenerate those
specific fixtures with the corresponding heteroskedasticity value, and
confirm shapes and true edge sets match the spec. Re-run the large-`n`
population-covariance check at the actual `coefficient`/`noise_scale`
combination used, as a final confound guard before writing the evidence
note.

- [ ] **Step 4: Record results and commit**

Write `docs/evidence/stage2-residual-variance-degradation-20260825.md`:
all six conditions' aggregate tables, grouped by fixture shape, explicit
confirmation that the round-4-style confound was checked and not found
(or, if found, reported with the same prominence round 4's note gave
its confound), a plain-language interpretation of whether detection
degrades under heteroskedasticity, and explicit governance language
limiting the claim to this one dimension at this one fixed effect
strength, noise level, and sample size. Report any surprising result
honestly. Commit as `docs: record Stage II residual-variance degradation results`.

## Self-review

Task 1 changes only add an optional, default-preserving parameter to
two existing, already-tested functions, scoped narrowly to avoid
repeating round 4's source-distribution confound, and includes an
automated Monte Carlo regression test for that confound rather than
relying on a manual check discovered after the fact. Task 2 reuses the
entire Step 4 / Stage I / Stage II machinery unchanged and adds only
orchestration and reporting. This round covers exactly one of
`plan.md` §6's remaining degradation dimensions, on the two fixture
shapes Stage I already validated, at one fixed effect strength, noise
level, and distribution -- consistent with this project's practice of
one narrowly chartered addition at a time.
