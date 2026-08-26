# Stage II Round 6 Measurement Quality Degradation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a six-condition benchmark (2 Stage I fixture shapes x 3
measurement-error levels, 50 replications each) answering
`outline/plan.md` §6's measurement-quality degradation question, reusing
every existing `redana` component unchanged.

**Architecture:** Generalize `redana/scenarios.py`'s two Stage I fixture
generators to accept a `measurement_error: float = 0.0` parameter,
applied as a post-processing step: after all six true columns are
constructed (unchanged from prior rounds), add
`sqrt(measurement_error) * column.std() * m_i` to each column, where
`m1..m6` are six additional Gaussian draws independent of the
`distribution` parameter. A CLI script binds three measurement-error
values via `functools.partial` (at fixed `coefficient=0.7`) and calls
`redana.benchmark.run_replicated_condition` six times.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-25-stage2-measurement-quality-degradation-design.md`

## Global Constraints

- Reuse `redana.benchmark.run_replicated_condition`,
  `redana.network.NetworkConfig`, `redana.residuals.PrototypeConfig`,
  `redana.scoring.score_edges` unchanged. Do not modify any prior
  round's component behavior at existing defaults.
- Adding `measurement_error: float = 0.0` to
  `generate_stage1_linear_fixture` and `generate_stage1_nonlinear_fixture`
  must not change their behavior for any existing caller that omits the
  argument.
- Measurement error applies to **all six** columns as a final
  post-processing step, using each column's own realized sample standard
  deviation, and always draws Gaussian noise regardless of the
  `distribution` parameter.
- Six conditions only this round: `{linear, nonlinear} x
  {perfect=0.0, modest=0.25, substantial=1.0}`, `coefficient=0.7` fixed.
  No network-structure degradation this round.
- `p = 6`, `n = 1,000`, `199` permutations, BH-FDR `alpha = 0.05`, `50`
  replications per condition at full scale.
- No hyperparameter tuning against this round's results.

---

### Task 1: Add a measurement-error parameter to the Stage I fixtures

**Files:** Edit `redana/scenarios.py`; add
`tests/redana/test_stage2_measurement_quality_scenarios.py`.

**Interfaces:** `generate_stage1_linear_fixture(n_rows: int, seed: int,
coefficient: float = 0.7, noise_scale: float = 1.0, distribution: str =
"gaussian", heteroskedasticity: float = 0.0, measurement_error: float =
0.0)` and the nonlinear equivalent -- add the keyword parameter after
`heteroskedasticity`.

- [ ] **Step 1: Write failing tests**

Add tests asserting: calling either generator with no
`measurement_error` argument produces byte-identical output to current
behavior (regression-guard); a nonzero `measurement_error` increases
each column's own sample variance relative to the perfect-measurement
case; true edges are unchanged regardless of `measurement_error`; a
large-`n` (`50,000`) Monte Carlo check confirms the nonlinear fixture's
population linear covariance stays near zero under
`measurement_error=1.0` (the round-4/round-5-style confound guard).

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/redana/test_stage2_measurement_quality_scenarios.py -v --basetemp .pytest-stage2-measurement-quality-red`. Expect a `TypeError` for the unexpected `measurement_error` keyword.

- [ ] **Step 3: Implement**

Add a private `_apply_measurement_error(columns: dict[str, np.ndarray],
rng, measurement_error: float) -> dict[str, np.ndarray]` helper and the
`measurement_error` parameter to both generators, applying the helper to
the six constructed columns immediately before building the
`pd.DataFrame`.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-stage2-measurement-quality-green`,
then Ruff. Also re-run `tests/redana/test_stage1_scenarios.py`,
`tests/redana/test_stage2_scenarios.py`,
`tests/redana/test_stage2_shape_scenarios.py`,
`tests/redana/test_stage2_noise_scenarios.py`,
`tests/redana/test_stage2_distribution_scenarios.py`, and
`tests/redana/test_stage2_residual_variance_scenarios.py` to confirm no
regression. Commit as `feat: add measurement-error parameter to Stage I fixture generators`.

### Task 2: Run the six-condition measurement-quality benchmark and record results

**Files:** Create `scripts/run_stage2_measurement_quality_degradation.py`;
create `docs/evidence/stage2-measurement-quality-degradation-20260825.md`
after running.

**Interfaces:** The script defines the three named levels
(`perfect=0.0, modest=0.25, substantial=1.0`), binds each fixture
generator with `functools.partial(generate_stage1_linear_fixture,
coefficient=0.7, measurement_error=...)` (and the nonlinear equivalent),
and calls `run_replicated_condition` once per of the six `(shape,
level)` combinations with `n_reps=50`, `n_rows=1000`, matching prior
rounds' other frozen settings. Prints results grouped by fixture shape.

- [ ] **Step 1: Preflight and commit source**

Run the full pytest suite
(`--basetemp .pytest-stage2-measurement-quality-preflight`) and `ruff
check research tests scripts redana`; expect full PASS and lint clean.
Commit the script as `feat: add Stage II measurement-quality degradation runner script`.

- [ ] **Step 2: Run all six conditions once each at full scale**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_stage2_measurement_quality_degradation.py`. Six conditions x 50 replications x 15 pairs x 199 permutations at n=1,000.

- [ ] **Step 3: Independent spot recompute**

Without importing `redana.benchmark`, re-derive a handful of individual
replication seeds across a few of the six conditions, regenerate those
specific fixtures with the corresponding measurement_error value, and
confirm shapes and true edge sets match the spec. Re-run the large-`n`
population-covariance confound guard at the actual configuration used.

- [ ] **Step 4: Record results and commit**

Write `docs/evidence/stage2-measurement-quality-degradation-20260825.md`:
all six conditions' aggregate tables, grouped by fixture shape, explicit
confirmation of the confound guard, a plain-language interpretation of
whether the classical attenuation-bias prediction is observed for the
incumbent and whether either mechanism degrades, and explicit governance
language limiting the claim to this one dimension at this one fixed
effect strength, noise level, distribution, and residual-variance
setting. Report any surprising result honestly. Commit as `docs: record Stage II measurement-quality degradation results`.

## Self-review

Task 1 changes only add an optional, default-preserving parameter to
two existing, already-tested functions, applied as a post-processing
step that cannot shift conditional means (only adds independent noise),
with an automated Monte Carlo confound guard carried over from rounds 4
and 5. Task 2 reuses the entire Step 4 / Stage I / Stage II machinery
unchanged and adds only orchestration and reporting. This round covers
exactly one of `plan.md` §6's remaining degradation dimensions, on the
two fixture shapes Stage I already validated, at one fixed effect
strength, noise level, distribution, and residual-variance setting --
consistent with this project's practice of one narrowly chartered
addition at a time.
