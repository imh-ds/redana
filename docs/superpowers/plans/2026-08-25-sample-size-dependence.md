# Sample-Size Dependence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Answer whether sample size affects detection at all (Stage A,
5 conditions) and whether Stage II round 1's effect-strength cliff
shifts with sample size (Stage B, 9 conditions), closing the open
question every effect-strength-related evidence note in this project has
flagged since round 1.

**Architecture:** Zero new `redana` source -- `n_rows` is already a
first-class parameter of `redana.benchmark.run_replicated_condition`.
Two new orchestration scripts call it with varying `n_rows` (Stage A)
and a `coefficient x n_rows` grid (Stage B), reusing
`generate_stage1_nonlinear_fixture` unchanged.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-25-sample-size-dependence-design.md`

## Global Constraints

- No changes to any `redana` source file. This plan is orchestration
  and reporting only.
- Stage A: `coefficient=0.7` fixed, `n_rows in {100, 200, 500, 1000,
  2000}`, 50 replications each.
- Stage B: `coefficient in {0.10, 0.15, 0.20}` x `n_rows in {500, 1000,
  2000}`, 50 replications each (9 conditions).
- All other fixture parameters at Stage I baseline (`noise_scale=1.0`,
  `distribution="gaussian"`, `heteroskedasticity=0.0`,
  `measurement_error=0.0`), `199` permutations, BH-FDR `alpha=0.05`.
- No hyperparameter tuning against results.
- Run Stage A first; inspect its smallest-`n` results before trusting
  Stage B's `n=500` level (per the spec's stated dependency).

---

### Task 1: Run Stage A (sample size alone, strong signal fixed)

**Files:** Create `scripts/run_sample_size_stage_a.py`.

**Interfaces:** Script defines `_N_ROWS_LEVELS = (100, 200, 500, 1000,
2000)`, calls `run_replicated_condition` once per level with
`generate_stage1_nonlinear_fixture` at `coefficient=0.7`, `n_reps=50`,
condition names `f"sample-size-a-{n_rows}"`. Prints per-edge detection
fraction and recall per level.

- [ ] **Step 1: Preflight and commit source**

No new tests needed (no new `redana` source). Run the full pytest suite
(`--basetemp .pytest-sample-size-a-preflight`) and `ruff check research
tests scripts redana` to confirm the new script alone doesn't break
anything; expect full PASS and lint clean. Commit the script as `feat: add sample-size dependence Stage A script`.

- [ ] **Step 2: Run all five conditions at full scale**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_sample_size_stage_a.py`. Five conditions x 50 replications x 15 pairs x 199 permutations, at varying `n_rows` -- total compute less than a single `n=1000`-only round since three of five levels are smaller than 1,000.

- [ ] **Step 3: Independent spot recompute**

Without importing `redana.benchmark`, re-derive a handful of individual
replication seeds across the five levels, regenerate those specific
fixtures, and confirm shapes and true edge sets match. Inspect the
`n=100` result specifically for signs of outright breakage (e.g.
`NetworkConfig`'s alpha grid or cross-fitting producing degenerate
output at very small `n`) before proceeding to Task 2.

### Task 2: Run Stage B (coefficient x sample size grid) and record both stages' results

**Files:** Create `scripts/run_sample_size_stage_b.py`; create
`docs/evidence/sample-size-dependence-20260825.md` after both stages
have run.

**Interfaces:** Script defines `_COEFFICIENT_LEVELS = (0.10, 0.15,
0.20)` and `_N_ROWS_LEVELS = (500, 1000, 2000)`, calls
`run_replicated_condition` once per of the nine `(coefficient, n_rows)`
combinations, condition names `f"sample-size-b-{coefficient}-{n_rows}"`.
Prints per-edge detection fraction as a grid.

- [ ] **Step 1: Preflight and commit source**

Run the full pytest suite (`--basetemp .pytest-sample-size-b-preflight`)
and `ruff check research tests scripts redana`; expect full PASS and
lint clean. Commit the script as `feat: add sample-size dependence Stage B script`.

- [ ] **Step 2: Run all nine conditions at full scale**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_sample_size_stage_b.py`. Nine conditions x 50 replications x 15 pairs x 199 permutations.

- [ ] **Step 3: Independent spot recompute**

Without importing `redana.benchmark`, re-derive a handful of individual
replication seeds across a few of the nine conditions, regenerate those
specific fixtures, and confirm shapes and true edge sets match.

- [ ] **Step 4: Record both stages' results and commit**

Write `docs/evidence/sample-size-dependence-20260825.md` covering both
stages: Stage A's detection-vs-`n` table (including any breakage at
`n=100`), Stage B's `coefficient x n_rows` grid, and a plain-language
interpretation of whether the cliff shifts with sample size in the
expected direction, by how much, and whether the shift is large enough
to matter practically at the sample sizes `plan.md` §1 scopes this
project to (`n >= 200`). Report any surprising result -- non-monotonic
behavior, an unexpected breakage point, or a shift much larger or
smaller than basic power-theory intuition predicts -- honestly. Commit
as `docs: record sample-size dependence results`.

## Self-review

Zero new `redana` source across both tasks -- this is purely an
orchestration and reporting exercise reusing already-validated
machinery (`run_replicated_condition`'s existing `n_rows` parameter and
`generate_stage1_nonlinear_fixture` unchanged). Stage A is run and
inspected before Stage B proceeds, so a low-`n` breakage is caught
before it could silently confound Stage B's smallest level. This closes
a specific, repeatedly-flagged open question (does the effect-strength
cliff shift with `n`) without opening a broader multi-dimension
sample-size sweep, consistent with the design spec's explicit scope
limit.
