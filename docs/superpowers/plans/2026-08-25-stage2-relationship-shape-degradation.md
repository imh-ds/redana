# Stage II Round 2 Relationship-Shape Degradation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a four-condition benchmark (one fixture family x four
relationship-shape levels, 50 replications each) answering
`outline/plan.md` §6's relationship-shape degradation question, reusing
every existing `redana` component unchanged except for one new fixture
generator.

**Architecture:** Add `generate_stage2_shape_fixture` to
`redana/scenarios.py`, blending a linear term and a centered quadratic
term via a `shape` parameter at fixed `coefficient=0.7`. A CLI script
binds four shape values via `functools.partial` and calls
`redana.benchmark.run_replicated_condition` four times, then prints all
four conditions' aggregates for direct degradation-curve comparison.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-25-stage2-relationship-shape-degradation-design.md`

## Global Constraints

- Reuse `redana.benchmark.run_replicated_condition`,
  `redana.network.NetworkConfig`, `redana.residuals.PrototypeConfig`,
  `redana.scoring.score_edges` unchanged. Do not modify any Step 4,
  Stage I, or Stage II round 1 component's behavior.
- New fixture only: `generate_stage2_shape_fixture(n_rows, seed, shape,
  coefficient=0.7)`. Do not touch `generate_stage1_linear_fixture` or
  `generate_stage1_nonlinear_fixture`.
- Four conditions only this round: `shape in {0.0, 0.33, 0.67, 1.0}` at
  fixed `coefficient=0.7`. No noise, distribution, residual-variance,
  measurement-quality, or network-structure degradation this round. No
  effect-strength sweep this round (already covered by round 1).
- `p = 6`, `n = 1,000`, `199` permutations, BH-FDR `alpha = 0.05`, `50`
  replications per condition at full scale.
- No hyperparameter tuning against this round's results.

---

### Task 1: Add the relationship-shape fixture generator

**Files:** Edit `redana/scenarios.py`; add
`tests/redana/test_stage2_shape_scenarios.py`.

**Interfaces:** `generate_stage2_shape_fixture(n_rows: int, seed: int,
shape: float, coefficient: float = 0.7) -> tuple[pd.DataFrame,
frozenset[tuple[str, str]]]`.

- [ ] **Step 1: Write failing tests**

Add tests asserting: true edges are always `{(X1,X2),(X3,X4)}`
regardless of `shape`; at `shape=0.0`, `X2` equals `coefficient*X1 + e2`
exactly (recompute `e2` from the same seeded RNG draw order and compare
arrays, or assert the linear correlation is high and matches a
hand-derived expected value within tolerance); at `shape=1.0`, the
generated frame is byte-identical (via `pandas.testing.assert_frame_equal`)
to `generate_stage1_nonlinear_fixture(n_rows, seed, coefficient=0.7)`
called with the same `seed` -- this is the key cross-check tying this
round back to Stage I's already-validated fixture; at an intermediate
`shape` (e.g. `0.33`), the frame is neither equal to the `shape=0.0` nor
`shape=1.0` output.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/redana/test_stage2_shape_scenarios.py -v --basetemp .pytest-stage2-shape-red`. Expect failure (function does not exist yet).

- [ ] **Step 3: Implement**

Add `generate_stage2_shape_fixture` to `redana/scenarios.py`, drawing
`e1..e6` from the same seeded RNG pattern as
`generate_stage1_nonlinear_fixture` (six independent standard-normal
draws in one `rng.standard_normal((6, n_rows))` call, same variable
order) so that `shape=1.0` reproduces that fixture's frame exactly when
`coefficient` matches.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-stage2-shape-green`, then
Ruff. Also re-run `tests/redana/test_stage1_scenarios.py` and
`tests/redana/test_stage2_scenarios.py` to confirm no regression.
Commit as `feat: add Stage II relationship-shape fixture generator`.

### Task 2: Run the four-condition relationship-shape benchmark and record results

**Files:** Create `scripts/run_stage2_relationship_shape_degradation.py`;
create `docs/evidence/stage2-relationship-shape-degradation-20260825.md`
after running.

**Interfaces:** The script defines the four named shape levels
(`pure_linear=0.0, slight_curvature=0.33, moderate_curvature=0.67,
strong_nonlinearity=1.0`), binds each with
`functools.partial(generate_stage2_shape_fixture, shape=..., coefficient=0.7)`,
and calls `run_replicated_condition` once per level with `n_reps=50`,
`n_rows=1000`, matching prior rounds' other frozen settings. Prints
results across the four levels for direct comparison.

- [ ] **Step 1: Preflight and commit source**

Run the full pytest suite (`--basetemp .pytest-stage2-shape-preflight`)
and `ruff check research tests scripts redana`; expect full PASS and
lint clean. Commit the script as `feat: add Stage II relationship-shape degradation runner script`.

- [ ] **Step 2: Run all four conditions once each at full scale**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_stage2_relationship_shape_degradation.py`. Four conditions x 50 replications x 15 pairs x 199 permutations at n=1,000 -- roughly Stage I's total compute, expect on the order of several minutes.

- [ ] **Step 3: Independent spot recompute**

Without importing `redana.benchmark`, re-derive a handful of individual
replication seeds across a few of the four conditions, regenerate those
specific fixtures with the corresponding shape value, and confirm
frames and true edge sets match the spec. Specifically re-verify the
`shape=1.0` condition's first replication against
`generate_stage1_nonlinear_fixture` directly, as the cross-check the
design calls for.

- [ ] **Step 4: Record results and commit**

Write `docs/evidence/stage2-relationship-shape-degradation-20260825.md`:
all four conditions' aggregate tables (incumbent and residual side by
side), a plain-language interpretation of whether detection degrades
gracefully or shows a sharper cliff along the shape axis, an explicit
comparison of the `shape=1.0` result against round 1's/Stage I's
existing `coefficient=0.7` nonlinear result (should match closely), and
explicit governance language limiting the claim to this one dimension at
this one fixed effect strength and sample size. Report any surprising
result honestly rather than smoothing it over. Commit as `docs: record Stage II relationship-shape degradation results`.

## Self-review

Task 1 adds exactly one new fixture generator, built from the same
seeded-RNG pattern already used and tested in Stage I, with a built-in
cross-check against Stage I's nonlinear fixture at its `shape=1.0`
endpoint. Task 2 reuses the entire Step 4 / Stage I / Stage II round 1
machinery unchanged and adds only orchestration and reporting. This
round covers exactly one of `plan.md` §6's remaining degradation
dimensions, at one fixed effect strength, on one fixture family --
consistent with this project's practice of one narrowly chartered
addition at a time.
