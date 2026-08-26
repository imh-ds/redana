# Stage II Round 3 Noise Degradation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a six-condition benchmark (2 Stage I fixture shapes x 3
noise levels, 50 replications each) answering `outline/plan.md` §6's
noise degradation question, reusing every existing `redana` component
unchanged.

**Architecture:** Generalize `redana/scenarios.py`'s two Stage I fixture
generators to accept a `noise_scale` parameter (default `1.0`,
preserving exact existing behavior) that multiplies each downstream
variable's residual noise term. A CLI script binds three noise-scale
values via `functools.partial` (at fixed `coefficient=0.7`) and calls
`redana.benchmark.run_replicated_condition` six times, then prints all
six conditions' aggregates grouped by fixture shape.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-25-stage2-noise-degradation-design.md`

## Global Constraints

- Reuse `redana.benchmark.run_replicated_condition`,
  `redana.network.NetworkConfig`, `redana.residuals.PrototypeConfig`,
  `redana.scoring.score_edges` unchanged. Do not modify any Step 4,
  Stage I, or prior Stage II round's component behavior at existing
  defaults.
- Adding `noise_scale: float = 1.0` to `generate_stage1_linear_fixture`
  and `generate_stage1_nonlinear_fixture` must not change their behavior
  for any existing caller that omits the argument -- all prior tests and
  evidence must remain valid without modification.
- `noise_scale` multiplies only the downstream residual terms (`e2`,
  `e3` in the linear chain; `e2`, `e4` in the nonlinear pairs), never the
  source variables' own noise (`e1`, `e4`/`e1`, `e3`).
- Six conditions only this round: `{linear, nonlinear} x {low=0.5,
  moderate=1.0, high=2.0}`, `coefficient=0.7` fixed. No distribution,
  residual-variance, measurement-quality, or network-structure
  degradation this round.
- `p = 6`, `n = 1,000`, `199` permutations, BH-FDR `alpha = 0.05`, `50`
  replications per condition at full scale.
- No hyperparameter tuning against this round's results.

---

### Task 1: Add a noise-scale parameter to the Stage I fixtures

**Files:** Edit `redana/scenarios.py`; add
`tests/redana/test_stage2_noise_scenarios.py`.

**Interfaces:** `generate_stage1_linear_fixture(n_rows: int, seed: int,
coefficient: float = 0.7, noise_scale: float = 1.0)` and
`generate_stage1_nonlinear_fixture(n_rows: int, seed: int, coefficient:
float = 0.7, noise_scale: float = 1.0)` -- add the keyword parameter
after `coefficient`, matching that parameter's addition pattern from
round 1.

- [ ] **Step 1: Write failing tests**

Add tests asserting: calling either generator with no `noise_scale`
argument produces byte-identical output to current behavior
(regression-guard); a smaller `noise_scale` (e.g. `0.5`) increases
`abs(frame["X1"].corr(frame["X2"]))` relative to the default, and a
larger one (`2.0`) decreases it, at a fixed `coefficient`; the true edge
sets are unchanged regardless of `noise_scale`.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/redana/test_stage2_noise_scenarios.py -v --basetemp .pytest-stage2-noise-red`. Expect a `TypeError` for the unexpected `noise_scale` keyword.

- [ ] **Step 3: Implement**

Add `noise_scale: float = 1.0` to both function signatures, multiplying
each downstream variable's own noise draw by `noise_scale` before adding
it to the systematic component.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-stage2-noise-green`, then
Ruff. Also re-run `tests/redana/test_stage1_scenarios.py`,
`tests/redana/test_stage2_scenarios.py`, and
`tests/redana/test_stage2_shape_scenarios.py` to confirm no regression.
Commit as `feat: add noise-scale parameter to Stage I fixture generators`.

### Task 2: Run the six-condition noise benchmark and record results

**Files:** Create `scripts/run_stage2_noise_degradation.py`; create
`docs/evidence/stage2-noise-degradation-20260825.md` after running.

**Interfaces:** The script defines the three named noise levels
(`low=0.5, moderate=1.0, high=2.0`), binds each fixture generator with
`functools.partial(generate_stage1_linear_fixture, coefficient=0.7,
noise_scale=...)` (and the nonlinear equivalent), and calls
`run_replicated_condition` once per of the six `(shape, level)`
combinations with `n_reps=50`, `n_rows=1000`, matching prior rounds'
other frozen settings. Prints results grouped by fixture shape across
the three levels.

- [ ] **Step 1: Preflight and commit source**

Run the full pytest suite (`--basetemp .pytest-stage2-noise-preflight`)
and `ruff check research tests scripts redana`; expect full PASS and
lint clean. Commit the script as `feat: add Stage II noise degradation runner script`.

- [ ] **Step 2: Run all six conditions once each at full scale**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_stage2_noise_degradation.py`. Six conditions x 50 replications x 15 pairs x 199 permutations at n=1,000 -- comparable to round 1's total compute.

- [ ] **Step 3: Independent spot recompute**

Without importing `redana.benchmark`, re-derive a handful of individual
replication seeds (matching prior rounds' approach) across a few of the
six conditions, regenerate those specific fixtures with the
corresponding noise_scale, and confirm shapes and true edge sets match
the spec.

- [ ] **Step 4: Record results and commit**

Write `docs/evidence/stage2-noise-degradation-20260825.md`: all six
conditions' aggregate tables, grouped by fixture shape so the
low->moderate->high trend is visible for both mechanisms, a
plain-language interpretation of whether detection degrades gracefully
or shows a cliff, and explicit governance language limiting the claim to
this one dimension at this one fixed effect strength and sample size.
Report any surprising result honestly. Commit as `docs: record Stage II noise degradation results`.

## Self-review

Task 1 changes only add an optional, default-preserving parameter to
two existing, already-tested functions -- no behavior change for any
existing caller. Task 2 reuses the entire Step 4 / Stage I / Stage II
machinery unchanged and adds only orchestration and reporting. This
round covers exactly one of `plan.md` §6's remaining degradation
dimensions, on the two fixture shapes Stage I already validated, at one
fixed effect strength -- consistent with this project's practice of one
narrowly chartered addition at a time.
