# Stage I Clean Mechanistic Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a 100-replication-per-condition benchmark on the two `outline/plan.md` §5 clean mechanistic fixtures (linear, pure nonlinear), reusing every existing Step 4 component unchanged, and report distributions of precision/recall/F1 for both the incumbent network and the residual layer.

**Architecture:** Two new fixture generators in `redana/scenarios.py`. A new small replication/aggregation module `redana/benchmark.py` that runs `redana.prototype.run_prototype` `n_reps` times with deterministically derived seeds and aggregates `redana.scoring.score_edges` results into summary statistics. A CLI script that runs both conditions once each at full scale and prints the aggregate report.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-25-stage1-mechanistic-benchmark-design.md`

## Global Constraints

- Reuse `redana.prototype.run_prototype`, `redana.network.NetworkConfig`, `redana.residuals.PrototypeConfig`, and `redana.scoring.score_edges` unchanged. Do not modify any Step 4 component or its frozen defaults.
- Two fixture conditions only this round: linear (`{(X1,X2),(X2,X3)}` true edges, `X4-X6` independent) and pure nonlinear (`{(X1,X2),(X3,X4)}` true edges, zero linear covariance, `X5-X6` independent). No sine/threshold/interaction fixtures, no Stage II degradation sweeps.
- `p = 6`, `n = 1,000` rows per replication, `199` permutations per pair, BH-FDR `alpha = 0.05`, `100` replications per condition at full scale.
- Every replication seed is deterministically derived (`derive_seed("stage1", condition_name, replication_index)`); no raw per-replication artifacts are retained (this is not a Gate 0 hash-pinned study).
- Report distributions (mean/median/min/max), not single point estimates, per `outline/plan.md` §9.
- No hyperparameter tuning against this benchmark's own results.

---

### Task 1: Implement and test the two Stage I fixture generators

**Files:** Edit `redana/scenarios.py` (add alongside the existing `generate_step4_validation_frame`); edit `tests/redana/test_step4_validation_scenario.py` or add `tests/redana/test_stage1_scenarios.py` (prefer a new file to keep Step 4's existing tests untouched).

**Interfaces:** `generate_stage1_linear_fixture(n_rows: int, seed: int) -> tuple[pd.DataFrame, frozenset[tuple[str,str]]]` and `generate_stage1_nonlinear_fixture(n_rows: int, seed: int) -> tuple[pd.DataFrame, frozenset[tuple[str,str]]]`, each returning the frame and its true edge set (no separate linear/nonlinear split needed here since each fixture is single-mechanism).

- [ ] **Step 1: Write failing tests**

For each generator: assert columns are exactly `X1..X6`; assert row count matches `n_rows`; assert the returned true edge set matches the spec exactly; assert two calls with the same seed produce identical frames (determinism); assert two calls with different seeds produce different frames.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/redana/test_stage1_scenarios.py -v --basetemp .pytest-stage1-scenarios-red`. Expect import failure for the two new functions.

- [ ] **Step 3: Implement**

Add both functions to `redana/scenarios.py`, following the exact DGPs in the spec (linear chain for Condition A; two independent quadratic pairs, reusing the `0.7*(X^2-1)` shape, for Condition B).

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-stage1-scenarios-green`, then Ruff. Commit as `feat: add Stage I linear and pure nonlinear fixture generators`.

### Task 2: Implement and test the replicated benchmark runner

**Files:** Create `redana/benchmark.py`, `tests/redana/test_benchmark.py`.

**Interfaces:** `run_replicated_condition(fixture_fn, condition_name, n_reps, n_rows, residual_config, network_config, permutations, alpha, base_seed) -> ConditionResult`, where `fixture_fn` is one of Task 1's generators (called with `(n_rows, replication_seed)`), and `ConditionResult` holds per-replication `EdgeScore` pairs (incumbent, residual) plus aggregate summary statistics (`ConditionSummary`: mean/median/min/max precision/recall/F1 for each mechanism, exact-match fraction for each mechanism, and per-true-edge detection fraction for the residual layer).

- [ ] **Step 1: Write failing tests**

Test with a small `n_reps` (e.g. 5) and reduced `n_rows`/permutations that the runner calls `fixture_fn` exactly `n_reps` times with distinct deterministic seeds, that `ConditionResult` holds exactly `n_reps` score pairs, that aggregate statistics are computed correctly against a hand-constructed list of known `EdgeScore` values (mock the per-replication scoring to isolate the aggregation math from the full pipeline), and that per-true-edge detection fractions are computed correctly for a fixture with more than one true edge.

- [ ] **Step 2: Verify RED**

Run the focused suite; expect import failure for `redana.benchmark`.

- [ ] **Step 3: Implement**

For each replication index in `range(n_reps)`, derive a seed via `derive_seed("stage1", condition_name, index)`, generate the fixture, run `run_prototype`, score both edge sets against the fixture's true edges, and collect results. Compute aggregate statistics with plain NumPy (`np.mean`, `np.median`, `np.min`, `np.max` over the per-replication metric arrays) plus the two fraction metrics.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-stage1-benchmark-green`, then Ruff. Commit as `feat: add Stage I replicated benchmark runner and aggregation`.

### Task 3: Run both Stage I conditions at full scale and record results

**Files:** Create `scripts/run_stage1_mechanistic_benchmark.py`; create `docs/evidence/stage1-mechanistic-benchmark-20260825.md` after running.

**Interfaces:** The script runs Condition A and Condition B, each via `run_replicated_condition` at `n_reps=100`, `n_rows=1000`, `permutations=199`, `alpha=0.05`, using the frozen Step 4 `NetworkConfig()`/`PrototypeConfig()` defaults, and prints both conditions' aggregate summaries.

- [ ] **Step 1: Preflight and commit source**

Run the full pytest suite (`--basetemp .pytest-stage1-preflight`) and `ruff check research tests scripts redana`; expect full PASS and lint clean. Commit the script as `feat: add Stage I mechanistic benchmark runner script`.

- [ ] **Step 2: Run both conditions once each at full scale**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_stage1_mechanistic_benchmark.py`. Each condition is 100 replications x 15 pairs x 199 permutations at n=1,000 -- comparable total compute to a single Gate 0 official run, expected to complete in single-digit minutes per condition.

- [ ] **Step 3: Independent spot recompute**

Without importing `redana.benchmark`, re-derive 3-5 individual replication seeds per condition from the frozen identity string, regenerate those specific fixtures, and confirm their true edge sets match the spec. This is a lighter check than Gate 0's full from-raw-files verifier (no per-replication artifacts are retained by design), but confirms the seed derivation and fixture definitions are exactly what the spec claims.

- [ ] **Step 4: Record results and commit**

Write `docs/evidence/stage1-mechanistic-benchmark-20260825.md`: both conditions' full aggregate tables (mean/median/min/max precision/recall/F1, exact-match fractions, per-edge detection fractions for Condition B), a plain-language interpretation against `plan.md` §5's stated expectations (incumbent recovers linear well and residual layer adds little on Condition A; residual layer detects "a useful proportion" of Condition B while the incumbent may miss it), and explicit governance language matching every prior evidence note in this project (no Stage II, no comparator-fairness protocol, no real-data work, no package decision authorized by this result). Commit as `docs: record Stage I mechanistic benchmark results`.

## Self-review

Tasks 1-3 build exactly the two `plan.md` §5-named fixture conditions with proper replication (100 per condition, meeting `plan.md` §9's floor), reuse every Step 4 component unchanged, and report distributions rather than point estimates. No sine/threshold/interaction fixture, no Stage II sweep, no comparator-fairness work, and no package-readiness claim appears. The independent spot recompute in Task 3 keeps this from being a purely self-reported result even though full Gate 0-style hash-pinning does not apply to a replicated benchmark with no retained per-replication artifacts.
