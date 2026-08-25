# Stage II Round 1 Effect-Strength Degradation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a six-condition benchmark (2 Stage I fixture shapes x 3 effect-strength levels, 50 replications each) answering `outline/plan.md` §6's effect-strength degradation question, reusing every existing `redana` component unchanged.

**Architecture:** Generalize `redana/scenarios.py`'s two Stage I fixture generators to accept a `coefficient` parameter (default `0.7`, preserving Stage I's exact behavior). A CLI script binds three coefficient values via `functools.partial` and calls `redana.benchmark.run_replicated_condition` six times, then prints all six conditions' aggregates grouped by fixture shape for direct degradation-curve comparison.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-25-stage2-effect-strength-degradation-design.md`

## Global Constraints

- Reuse `redana.benchmark.run_replicated_condition`, `redana.network.NetworkConfig`, `redana.residuals.PrototypeConfig`, `redana.scoring.score_edges` unchanged. Do not modify any Step 4 or Stage I component's behavior at the default coefficient.
- Generalizing `generate_stage1_linear_fixture`/`generate_stage1_nonlinear_fixture` to accept `coefficient: float = 0.7` must not change their behavior for any existing caller that omits the argument -- Stage I's own tests and evidence must remain valid without modification.
- Six conditions only this round: `{linear, nonlinear} x {strong=0.7, moderate=0.4, weak=0.2}`. No noise, distribution, residual-variance, measurement-quality, or network-structure degradation this round.
- `p = 6`, `n = 1,000`, `199` permutations, BH-FDR `alpha = 0.05`, `50` replications per condition at full scale.
- No hyperparameter tuning against this round's results.

---

### Task 1: Generalize the Stage I fixtures to accept an effect-strength coefficient

**Files:** Edit `redana/scenarios.py`; edit `tests/redana/test_stage1_scenarios.py` (add coverage) or add a new `tests/redana/test_stage2_scenarios.py` for the coefficient-specific behavior.

**Interfaces:** `generate_stage1_linear_fixture(n_rows: int, seed: int, coefficient: float = 0.7)` and `generate_stage1_nonlinear_fixture(n_rows: int, seed: int, coefficient: float = 0.7)` -- add the keyword parameter with the exact Stage I default so every existing call site and test is unaffected.

- [ ] **Step 1: Write failing tests**

Add tests asserting: calling either generator with no `coefficient` argument produces byte-identical output to the current Stage I behavior (regression-guard against accidentally changing the default); calling with a different `coefficient` changes the generated values in the expected direction (e.g., a smaller coefficient shrinks the covariance between the linear pair, verified via `frame["X1"].corr(frame["X2"])` decreasing in magnitude as `coefficient` decreases); the true edge sets are unchanged regardless of `coefficient` (the structure, not the strength, defines the true edges).

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/redana/test_stage1_scenarios.py tests/redana/test_stage2_scenarios.py -v --basetemp .pytest-stage2-scenarios-red` (whichever file holds the new tests). Expect a `TypeError` for the unexpected `coefficient` keyword.

- [ ] **Step 3: Implement**

Add `coefficient: float = 0.7` to both function signatures, replacing the hardcoded `_FIXTURE_COEFFICIENT` module constant with the parameter inside each function body (leave `_FIXTURE_COEFFICIENT` as the default value source or remove it if it becomes unused after this change -- check `generate_step4_validation_frame`, which must keep using the fixed `0.7` unconditionally since it is not part of this round's scope).

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-stage2-scenarios-green`, then Ruff. Run the existing `tests/redana/test_stage1_scenarios.py` and `tests/redana/test_step4_validation_scenario.py` too, to confirm no regression. Commit as `feat: add effect-strength coefficient to Stage I fixture generators`.

### Task 2: Run the six-condition effect-strength benchmark and record results

**Files:** Create `scripts/run_stage2_effect_strength_degradation.py`; create `docs/evidence/stage2-effect-strength-degradation-20260825.md` after running.

**Interfaces:** The script defines the three named strength levels (`strong=0.7, moderate=0.4, weak=0.2`), binds each fixture generator with `functools.partial(generate_stage1_linear_fixture, coefficient=...)` (and the nonlinear equivalent), and calls `run_replicated_condition` once per of the six `(shape, level)` combinations with `n_reps=50`, `n_rows=1000`, matching Stage I's other frozen settings. Prints results grouped by fixture shape across the three levels.

- [ ] **Step 1: Preflight and commit source**

Run the full pytest suite (`--basetemp .pytest-stage2-preflight`) and `ruff check research tests scripts redana`; expect full PASS and lint clean. Commit the script as `feat: add Stage II effect-strength degradation runner script`.

- [ ] **Step 2: Run all six conditions once each at full scale**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_stage2_effect_strength_degradation.py`. Six conditions x 50 replications x 15 pairs x 199 permutations at n=1,000 -- roughly 1.5x Stage I's total compute, expect on the order of ten minutes.

- [ ] **Step 3: Independent spot recompute**

Without importing `redana.benchmark`, re-derive a handful of individual replication seeds (matching Stage I's approach) across a few of the six conditions, regenerate those specific fixtures with the corresponding coefficient, and confirm shapes and true edge sets match the spec.

- [ ] **Step 4: Record results and commit**

Write `docs/evidence/stage2-effect-strength-degradation-20260825.md`: all six conditions' aggregate tables, grouped by fixture shape so the strong->moderate->weak trend is visible for both mechanisms, a plain-language interpretation of whether detection degrades gracefully or shows a sharper cliff, and explicit governance language limiting the claim to this one dimension at this one sample size. Report any surprising result (a strength level where the residual layer underperforms the incumbent, non-monotonic degradation, etc.) honestly rather than smoothing it over. Commit as `docs: record Stage II effect-strength degradation results`.

## Self-review

Task 1 changes only add an optional, default-preserving parameter to two existing, already-tested functions -- no behavior changes for any existing caller. Task 2 reuses the entire Step 4 / Stage I machinery unchanged and adds only orchestration and reporting. This round covers exactly one of `plan.md` §6's seven degradation dimensions, on exactly the two fixture shapes Stage I already validated, at one fixed sample size -- consistent with this project's practice of one narrowly chartered addition at a time.
