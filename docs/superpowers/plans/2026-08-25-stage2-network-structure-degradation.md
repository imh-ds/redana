# Stage II Round 7 Network Structure Degradation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a four-condition benchmark (chain, hub, community,
redundant_predictors topologies, 50 replications each) answering
`outline/plan.md` §6's network-structure degradation question -- the
last of its seven named dimensions -- reusing every existing `redana`
component unchanged except three new fixture generators.

**Architecture:** Add `generate_stage2_hub_fixture`,
`generate_stage2_community_fixture`, and
`generate_stage2_redundant_predictors_fixture` to `redana/scenarios.py`,
each a standalone p=6 fixture at `coefficient=0.7` with its own fixed
topology (not a parameterized sweep, since this dimension is
categorical). The chain condition reuses
`generate_stage1_linear_fixture` unchanged. A CLI script calls
`redana.benchmark.run_replicated_condition` once per of the four
conditions.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-25-stage2-network-structure-degradation-design.md`

## Global Constraints

- Reuse `redana.benchmark.run_replicated_condition`,
  `redana.network.NetworkConfig`, `redana.residuals.PrototypeConfig`,
  `redana.scoring.score_edges`, and `generate_stage1_linear_fixture`
  unchanged. Do not modify any prior round's component behavior.
- All three new fixtures use `coefficient: float = 0.7` as their default
  edge strength (not swept this round) and otherwise draw errors exactly
  like `generate_stage1_linear_fixture` (`rng.standard_normal((6,
  n_rows))`, Gaussian, homoskedastic, perfectly measured).
- `generate_stage2_redundant_predictors_fixture` must declare true edges
  as `{(X1, X3)}` only -- `(X1, X2)` and `(X2, X3)` must NOT appear in
  the declared true-edge set, even though `X1` and `X2` are strongly
  correlated by construction.
- Four conditions only this round: `chain`, `hub`, `community`,
  `redundant_predictors`, each `coefficient=0.7`. No sweeping of
  redundancy strength or any other parameter.
- `p = 6`, `n = 1,000`, `199` permutations, BH-FDR `alpha = 0.05`, `50`
  replications per condition at full scale.
- No hyperparameter tuning against this round's results.

---

### Task 1: Add the hub, community, and redundant-predictors fixture generators

**Files:** Edit `redana/scenarios.py`; add
`tests/redana/test_stage2_network_structure_scenarios.py`.

**Interfaces:**
- `generate_stage2_hub_fixture(n_rows: int, seed: int, coefficient: float = 0.7) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]`
- `generate_stage2_community_fixture(n_rows: int, seed: int, coefficient: float = 0.7) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]`
- `generate_stage2_redundant_predictors_fixture(n_rows: int, seed: int, coefficient: float = 0.7, redundancy: float = 0.9) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]`

- [ ] **Step 1: Write failing tests**

Add tests asserting: each generator returns a `(1000, 6)`-shaped frame
with columns `X1`..`X6`; `hub`'s true edges are `{(X1,X2),(X1,X3),(X1,X4)}`;
`community`'s true edges are `{(X1,X2),(X2,X3),(X4,X5),(X5,X6)}`;
`redundant_predictors`'s true edges are exactly `{(X1,X3)}` (assert
`(X1,X2)` and `(X2,X3)` are NOT in the set); each generator is
deterministic given the same seed and differs across seeds;
`redundant_predictors`'s `X1`/`X2` columns have `abs(corr) > 0.8` at
`n=5000` (confirming the intended near-collinearity), while `X2`/`X3`
have much weaker correlation than `X1`/`X3` (confirming `X2`'s
correlation with `X3` is only inherited through `X1`, not a direct
effect).

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/redana/test_stage2_network_structure_scenarios.py -v --basetemp .pytest-stage2-network-structure-red`. Expect `ImportError`/`AttributeError` for the three missing functions.

- [ ] **Step 3: Implement**

Add the three generators to `redana/scenarios.py`, following the
existing fixtures' structure (seeded RNG, `pd.DataFrame` construction,
`frozenset` true edges).

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-stage2-network-structure-green`,
then Ruff. Also re-run `tests/redana/test_stage1_scenarios.py` to
confirm the reused chain fixture is untouched. Commit as
`feat: add hub, community, and redundant-predictors network-structure fixtures`.

### Task 2: Run the four-condition network-structure benchmark and record results

**Files:** Create `scripts/run_stage2_network_structure_degradation.py`;
create `docs/evidence/stage2-network-structure-degradation-20260825.md`
after running.

**Interfaces:** The script calls `run_replicated_condition` once per of
the four conditions (`chain` using `generate_stage1_linear_fixture`,
`hub`, `community`, `redundant_predictors` using the three new
generators), each with `coefficient=0.7`, `n_reps=50`, `n_rows=1000`,
matching prior rounds' other frozen settings. Prints all four
conditions' results, with an extra line for `redundant_predictors`
reporting how often `(X2,X3)` specifically was flagged as a false
positive by the residual layer.

- [ ] **Step 1: Preflight and commit source**

Run the full pytest suite
(`--basetemp .pytest-stage2-network-structure-preflight`) and `ruff
check research tests scripts redana`; expect full PASS and lint clean.
Commit the script as `feat: add Stage II network-structure degradation runner script`.

- [ ] **Step 2: Run all four conditions once each at full scale**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_stage2_network_structure_degradation.py`. Four conditions x 50 replications x 15 pairs x 199 permutations at n=1,000.

- [ ] **Step 3: Independent spot recompute**

Without importing `redana.benchmark`, re-derive a handful of individual
replication seeds across all four conditions, regenerate those specific
fixtures, and confirm shapes and true edge sets match the spec.

- [ ] **Step 4: Record results and commit**

Write `docs/evidence/stage2-network-structure-degradation-20260825.md`:
all four conditions' aggregate tables, an explicit report of the
`redundant_predictors` condition's `(X2,X3)` false-positive rate, a
plain-language interpretation of whether hub/community/redundant
topology degrades either mechanism relative to the chain baseline, and
explicit governance language marking this as the completion of all seven
`plan.md` §6 dimensions and flagging the rule-10 checkpoint. Report any
surprising result honestly. Commit as `docs: record Stage II network-structure degradation results`.

## Self-review

Task 1 adds three new, narrowly-scoped fixture generators that mirror
the existing chain fixture's construction pattern exactly, with no
changes to any existing function. Task 2 reuses the entire Step 4 /
Stage I / Stage II machinery unchanged and adds only orchestration and
reporting. This round covers `plan.md` §6's seventh and final named
dimension, completing the full set -- an explicit governance milestone,
not a reason to keep going without a deliberate decision.
