# Stage II Round 4 Distribution Degradation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a six-condition benchmark (2 Stage I fixture shapes x 3
distribution levels, 50 replications each) answering `outline/plan.md`
§6's distribution degradation question, reusing every existing `redana`
component unchanged.

**Architecture:** Add a private `_draw_errors(rng, n_rows, distribution)`
helper to `redana/scenarios.py` returning six standardized (mean 0,
variance 1) error columns drawn from Gaussian, skewed (shifted
chi-squared), or heavy-tailed (scaled Student's t) distributions.
Generalize `generate_stage1_linear_fixture` and
`generate_stage1_nonlinear_fixture` to accept a `distribution: str =
"gaussian"` parameter that selects the helper instead of calling
`rng.standard_normal` directly. A CLI script binds three distribution
values via `functools.partial` (at fixed `coefficient=0.7,
noise_scale=1.0`) and calls `redana.benchmark.run_replicated_condition`
six times, then prints all six conditions' aggregates grouped by fixture
shape.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-25-stage2-distribution-degradation-design.md`

## Global Constraints

- Reuse `redana.benchmark.run_replicated_condition`,
  `redana.network.NetworkConfig`, `redana.residuals.PrototypeConfig`,
  `redana.scoring.score_edges` unchanged. Do not modify any Step 4,
  Stage I, or prior Stage II round's component behavior at existing
  defaults.
- Adding `distribution: str = "gaussian"` to
  `generate_stage1_linear_fixture` and `generate_stage1_nonlinear_fixture`
  must not change their behavior for any existing caller that omits the
  argument -- all prior tests and evidence must remain valid without
  modification.
- Only three distribution values are valid this round: `"gaussian"`,
  `"skewed"`, `"heavy_tailed"`. Raise `ValueError` on anything else
  (fail loudly rather than silently falling back).
- Six conditions only this round: `{linear, nonlinear} x {gaussian,
  skewed, heavy_tailed}`, `coefficient=0.7`, `noise_scale=1.0` fixed. No
  residual-variance, measurement-quality, or network-structure
  degradation this round.
- `p = 6`, `n = 1,000`, `199` permutations, BH-FDR `alpha = 0.05`, `50`
  replications per condition at full scale.
- No hyperparameter tuning against this round's results.

---

### Task 1: Add a distribution parameter to the Stage I fixtures

**Files:** Edit `redana/scenarios.py`; add
`tests/redana/test_stage2_distribution_scenarios.py`.

**Interfaces:** `_draw_errors(rng: np.random.Generator, n_rows: int,
distribution: str) -> tuple[np.ndarray, ...]` (six arrays). Both Stage I
generators gain `distribution: str = "gaussian"` after `noise_scale`.

- [ ] **Step 1: Write failing tests**

Add tests asserting: calling either generator with no `distribution`
argument produces byte-identical output to current behavior
(regression-guard); at `n_rows=20000`, `"gaussian"`, `"skewed"`, and
`"heavy_tailed"` draws each have sample mean within `0.05` of `0` and
sample variance within `0.1` of `1`; the `"skewed"` draw's sample
skewness is positive and greater than `0.5` while `"gaussian"`'s is near
`0`; true edges are unchanged regardless of `distribution`; an invalid
`distribution` string raises `ValueError`.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/redana/test_stage2_distribution_scenarios.py -v --basetemp .pytest-stage2-distribution-red`. Expect a `TypeError` for the unexpected `distribution` keyword.

- [ ] **Step 3: Implement**

Add `_draw_errors` and the `distribution` parameter to both generators,
replacing the direct `rng.standard_normal((6, n_rows))` call with
`_draw_errors(rng, n_rows, distribution)`.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-stage2-distribution-green`,
then Ruff. Also re-run `tests/redana/test_stage1_scenarios.py`,
`tests/redana/test_stage2_scenarios.py`,
`tests/redana/test_stage2_shape_scenarios.py`, and
`tests/redana/test_stage2_noise_scenarios.py` to confirm no regression.
Commit as `feat: add distribution parameter to Stage I fixture generators`.

### Task 2: Run the six-condition distribution benchmark and record results

**Files:** Create `scripts/run_stage2_distribution_degradation.py`;
create `docs/evidence/stage2-distribution-degradation-20260825.md` after
running.

**Interfaces:** The script defines the three distribution levels
(`gaussian`, `skewed`, `heavy_tailed`), binds each fixture generator
with `functools.partial(generate_stage1_linear_fixture, coefficient=0.7,
distribution=...)` (and the nonlinear equivalent), and calls
`run_replicated_condition` once per of the six `(shape, level)`
combinations with `n_reps=50`, `n_rows=1000`, matching prior rounds'
other frozen settings. Prints results grouped by fixture shape.

- [ ] **Step 1: Preflight and commit source**

Run the full pytest suite
(`--basetemp .pytest-stage2-distribution-preflight`) and `ruff check
research tests scripts redana`; expect full PASS and lint clean. Commit
the script as `feat: add Stage II distribution degradation runner script`.

- [ ] **Step 2: Run all six conditions once each at full scale**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_stage2_distribution_degradation.py`. Six conditions x 50 replications x 15 pairs x 199 permutations at n=1,000.

- [ ] **Step 3: Independent spot recompute**

Without importing `redana.benchmark`, re-derive a handful of individual
replication seeds across a few of the six conditions, regenerate those
specific fixtures with the corresponding distribution, and confirm
shapes and true edge sets match the spec.

- [ ] **Step 4: Record results and commit**

Write `docs/evidence/stage2-distribution-degradation-20260825.md`: all
six conditions' aggregate tables, grouped by fixture shape, a
plain-language interpretation of whether detection degrades as errors
move away from Gaussian, and explicit governance language limiting the
claim to this one dimension at this one fixed effect strength, noise
level, and sample size. Report any surprising result honestly. Commit
as `docs: record Stage II distribution degradation results`.

## Self-review

Task 1 changes only add an optional, default-preserving parameter (plus
a small validated helper) to two existing, already-tested functions --
no behavior change for any existing caller. Task 2 reuses the entire
Step 4 / Stage I / Stage II machinery unchanged and adds only
orchestration and reporting. This round covers exactly one of
`plan.md` §6's remaining degradation dimensions, on the two fixture
shapes Stage I already validated, at one fixed effect strength and noise
level -- consistent with this project's practice of one narrowly
chartered addition at a time.
