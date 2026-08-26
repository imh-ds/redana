# Static Threshold Justification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bracket the strong-coefficient crossover between `n_rows=100`
(sensitive safe) and `n_rows=300` (sensitive costly) at 25-row
resolution, classify each point, and update
`redana.defaults.recommended_settings`'s threshold to the largest
confirmed-safe point, per
`docs/superpowers/specs/2026-08-26-track2-threshold-justification-charter.md`.

**Architecture:** Scripts reusing existing machinery (no new `redana`
source needed for the grid itself, same pattern as every prior Track 2
study), sharded via GitHub Actions. The one actual `redana` change is a
constant update in `redana/defaults.py` plus updated tests, done *after*
results are in, not before.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-26-track2-threshold-justification-charter.md`

## Global Constraints

- Grid (Decisions 1 & 4, fixed): `n_rows in {125, 150, 175, 200, 225,
  250, 275}` x `coefficient in {0.20, 0.7}` -- 14 cells, both arms
  (`sensitive`: `n_splits=2, alpha=0.15`; `normal`: `n_splits=5,
  alpha=0.05`), 50 reps each (Decision 2) -- 1,400 replicated runs, 28
  shards (one per cell x arm).
- Fresh, independently-seeded condition names (`track2-threshold-`
  prefix), no overlap with any prior study.
- Classification rule (Decision 3, fixed): a cell is "cost present" if
  `coefficient=0.7`'s detection improvement `<5pp` AND precision delta
  `<=-5pp`; otherwise "safe."
- Threshold selection rule (fixed): new threshold = largest `n_rows`
  among the `coefficient=0.7` cells classified "safe." The
  `coefficient=0.20` cells are a sanity check only -- expected to be
  "safe" throughout (per the already-published `100`-`700` results);
  if any weak-coefficient cell instead shows cost, stop and treat that
  as its own finding requiring the project owner's attention rather than
  proceeding to update the threshold.

---

### Task 1: Bracketing grid (sharded)

**Files:** Create `scripts/run_track2_threshold_shard.py`; create
`scripts/aggregate_track2_threshold.py`; create
`.github/workflows/track2-threshold-justification.yml` (Track 1/2's
established sharding pattern: temporary scoped push trigger, revert
after verified).

**Interfaces:** One shard per `(n_rows, coefficient, arm)`. Each runs 50
reps via `run_replicated_condition`, reporting mean detection and
precision. The aggregation script computes, per `(n_rows, coefficient)`
cell: detection improvement and precision delta (sensitive - normal),
and the "safe"/"cost present" classification for `coefficient=0.7` cells
per the fixed rule.

- [ ] **Step 1: Preflight and commit source**

Full pytest + Ruff; commit shard/aggregate scripts and workflow as
`feat: add threshold justification bracketing grid (sharded)`.

- [ ] **Step 2: Run at full scale**

Push (auto-triggers); confirm all 28 shards + aggregation succeed;
download results.

- [ ] **Step 3: Independent spot recompute**

Recompute 2-3 individual reps directly (not via the shard script) at the
`n_rows` point nearest the apparent crossover, both arms, confirming
results match.

- [ ] **Step 4: Revert the scoped push trigger and commit results**

Revert to `workflow_dispatch`-only. Commit the aggregated results JSON
and printed classification table as `feat: record threshold
justification bracketing results`.

### Task 2: Update the static threshold

**Files:** Modify `redana/defaults.py`; modify `tests/redana/test_defaults.py`.

**Interfaces:** Update `_LOW_N_THRESHOLD` to the value determined by
Task 1's results (largest `coefficient=0.7` cell classified "safe").
Update the module and function docstrings to cite this study instead of
(or alongside) the original low-n study. Update
`tests/redana/test_defaults.py`'s parametrized boundary cases to match
the new threshold value.

- [ ] **Step 1: Update tests to reflect the new threshold**

Change the boundary-value parametrization to the new cutoff (e.g. if the
result is `225`: `225 -> sensitive`, `226 -> normal`, etc.), keeping the
existing structure.

- [ ] **Step 2: Update `redana/defaults.py`**

Change `_LOW_N_THRESHOLD` and the docstrings.

- [ ] **Step 3: Verify GREEN and commit**

Full pytest + Ruff. Commit as `feat: update static threshold to
n_rows=<value> per bracketing study`, citing the exact evidence in the
commit message.

### Task 3: Evidence note

**Files:** Create `docs/evidence/track2-threshold-justification-20260826.md`.

**Content:** Full 14-cell results table (both coefficients). The
classification per `coefficient=0.7` cell and where the crossover
actually falls. The `coefficient=0.20` sanity-check outcome. The old vs.
new threshold and the reasoning connecting them. Explicit boundary
(coefficients above `0.7` untested, resolution is `25` rows not
continuous, only the pure nonlinear fixture at baseline
noise/distribution/etc. was tested). Governance section per rule 10.

- [ ] **Step 1: Write and commit**

Commit as `docs: record threshold justification results and update the
static default`.

## Self-review

Unlike every prior study in this line, this plan is explicitly designed
to *change* `redana.defaults`'s threshold based on real evidence rather
than leave it as an untested assumption -- Task 2 only proceeds after
Task 1's results are in, and the new value is a direct, mechanical
function of the classification rule fixed in the charter before any run,
not a post-hoc judgment call. The `coefficient=0.20` sanity check
doubles this study's cost but directly guards against silently narrowing
the weak-coefficient safe zone while widening the strong-coefficient
threshold.
