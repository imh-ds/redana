# Low-n Power Levers (Track 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether cross-fitting fold count and FDR threshold, tuned
away from their current fixed defaults, meaningfully improve detection
power at low `n` / weak coefficient, without a disqualifying precision
cost, per
`docs/superpowers/specs/2026-08-26-track2-low-n-power-charter.md`.

**Architecture:** Zero new `redana` source. `n_splits`
(`redana.residuals.PrototypeConfig`) and `alpha`
(`redana.benchmark.run_replicated_condition`'s existing parameter) are
already first-class, independently-settable parameters -- this whole
study is new scripts driving existing machinery at different parameter
values, exactly like the sample-size-dependence study needed zero new
source for varying `n_rows`. Two scripts: a dev-matrix sweep (Task 1)
that mechanically selects one winning `(n_splits, alpha)` combination per
Decision 4's pre-registered rule, and a final-evaluation run (Task 2)
that evaluates only that selected combination plus the current default
as a control arm, on fresh independently-seeded data.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-26-track2-low-n-power-charter.md`

## Global Constraints

- No changes to `redana.residuals`, `redana.dependence`, `redana.fdr`,
  `redana.network`, `redana.prototype`, `redana.benchmark`, `redana.stability`,
  `redana.detectability`, or any existing fixture. Purely additive scripts.
- Target grid (Decision 2, fixed): `n_rows in {100, 200}` x
  `coefficient in {0.15, 0.20}` on `generate_stage1_nonlinear_fixture`,
  4 cells total.
- Candidate lever values (fixed before Task 1 runs, per rule 3): `n_splits
  in {2, 3, 5}`, `alpha in {0.05, 0.10, 0.15}` -- 9 combinations per cell,
  including `(5, 0.05)` (the current default) as an anchor inside the dev
  matrix itself.
- Dev matrix: 10 independently-seeded datasets per (cell, combination)
  pair (Decision 3) -- `4 cells x 9 combinations x 10 datasets = 360`
  replicated runs total. Used **only** to select one winning combination;
  its numbers are never reported as the study's result.
- Final matrix: a **fresh**, independently-seeded 50-dataset replication
  per (cell, arm) pair, two arms only (the selected combination, and the
  `(5, 0.05)` control) -- `4 cells x 2 arms x 50 datasets = 400`
  replicated runs. This is what gets reported.
- Selection rule (Decision 4, fixed before Task 1 runs): among dev-matrix
  combinations whose mean residual precision (averaged across the 4
  cells) does not fall more than 10 percentage points below the `(5,
  0.05)` control's mean precision, pick the one with the largest mean
  per-edge detection improvement (also averaged across the 4 cells) over
  control. If no combination satisfies the precision floor, select
  nothing and report that outcome directly -- do not relax the floor
  post-hoc.
- One combination is selected globally (not per-cell) and applied
  uniformly across all 4 cells in the final matrix, to avoid a subtler
  form of per-cell overfitting to the same dev data.

---

### Task 1: Dev-matrix sweep and mechanical selection

**Files:** Create `scripts/run_track2_dev_matrix.py`.

**Interfaces:** For each of the 4 grid cells and each of the 9
`(n_splits, alpha)` combinations, calls
`redana.benchmark.run_replicated_condition` with `n_reps=10`,
`residual_config=PrototypeConfig(n_splits=n_splits)`, `alpha=alpha`,
reusing `generate_stage1_nonlinear_fixture` and a fresh
`condition_name` per (cell, combination) pair so seeds never collide
with any prior study's. Collects each combination's mean per-edge
detection fraction and mean residual precision, averaged across the 4
cells. Applies the fixed selection rule above and prints/returns the
winning combination (or `None` if no combination clears the precision
floor).

- [ ] **Step 1: Preflight**

Run the full pytest suite (`--basetemp .pytest-track2-dev-preflight`)
and `ruff check research tests scripts redana`; expect full PASS and
lint clean (no source changes expected, but confirm nothing upstream
drifted since the last check).

- [ ] **Step 2: Implement and run**

Write the script per the interface above. Run it
(`PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_track2_dev_matrix.py`),
in the background if it runs long (360 replicated runs, no bootstrap
multiplier -- expect well under the stability-validation study's
runtime, but budget for potentially 30-60+ minutes locally; use the
same GitHub Actions sharding pattern from Track 1 if it proves
impractically slow, sharding by (cell, combination) pair).

- [ ] **Step 3: Commit dev-matrix results**

Commit the script and its raw output (as a small JSON or text artifact
alongside it, e.g. `scripts/track2_dev_matrix_results.json`) as `feat:
add Track 2 dev-matrix sweep and selection`. Note the selected
combination (or "none selected") plainly in the commit message.

### Task 2: Final evaluation on fresh data

**Files:** Create `scripts/run_track2_final_evaluation.py`.

**Interfaces:** Takes the winning combination from Task 1 (hardcoded
into the script once known, with a comment citing the dev-matrix commit
it came from -- not re-derived at runtime, to keep the two steps
cleanly separated). For each of the 4 grid cells, runs
`run_replicated_condition` with `n_reps=50` for both the selected
combination and the `(5, 0.05)` control arm, using a `condition_name`
distinct from every dev-matrix run (fresh seeds, not a re-run of dev
data). Reports per-edge detection fraction and residual precision for
both arms at each cell, and the improvement/precision-delta against
Decision 4's fixed bar (+15pp detection, -10pp precision cap).

If Task 1 selected no combination, this task still runs the control arm
alone (50 reps per cell) to have a clean baseline on record, and the
evidence note (Task 3) reports "no combination cleared the pre-registered
bar" directly.

- [ ] **Step 1: Preflight**

Run the full pytest suite (`--basetemp .pytest-track2-final-preflight`)
and Ruff; expect full PASS and lint clean.

- [ ] **Step 2: Run at full scale**

Run the script (background if long-running; 400 replicated runs across 2
arms x 4 cells x 50 reps, or 200 if Task 1 selected nothing).

- [ ] **Step 3: Independent spot recompute**

Re-derive seeds and regenerate the fixture for a handful of datasets
(both arms, at least 2 of the 4 cells) without importing
`redana.benchmark`, confirming the regenerated frame and true-edge set
match; for one dataset per arm, rerun the residualization + dependence
test directly and confirm the detection outcome matches what the script
reported.

- [ ] **Step 4: Commit final-evaluation results**

Commit the script and its output as `feat: add Track 2 final evaluation`.

### Task 3: Evidence note and verdict

**Files:** Create `docs/evidence/track2-low-n-power-levers-20260826.md`.

**Content:** Report the dev-matrix's selected combination (or lack
thereof) and why, per the fixed selection rule -- not as the study's
result, but as a transparent record of how the final arm was chosen.
Report the final-evaluation matrix's per-cell, per-arm numbers in full.
State the verdict against Decision 4's pre-registered bar explicitly and
plainly: did the selected combination clear +15pp detection with at most
-10pp precision loss, at each cell, on average, or not at all. If it
did not clear the bar, say so as directly as every prior "no degradation
found" or "confound found" evidence note has -- this is a legitimate,
useful negative result, not a failure requiring another lever search
under rule 1. Explicit boundary section (what wasn't tested: lever 3/HSIC,
cells outside the 2x2 grid, any interaction with Track 1's stability/
detectability reporting). Governance section per rule 10.

- [ ] **Step 1: Write and commit**

Write the evidence note per the content above, referencing exact numbers
from Tasks 1-2's committed output files. Commit as `docs: record Track 2
low-n power lever results`.

## Self-review

Zero new `redana` source across all three tasks -- every lever tested is
already a first-class parameter of existing, unchanged machinery
(`PrototypeConfig.n_splits`, `run_replicated_condition`'s `alpha`),
matching this project's established "additive scripts over new
statistical claims" pattern for scoped studies. The dev/final matrix
split, the pre-registered selection rule, and the pre-registered success
bar are all fixed in the charter and this plan *before* Task 1 runs,
directly implementing rule 3's non-circularity requirement -- the
sharpest test of that rule this project has run so far, since this is
the first study whose explicit purpose is parameter tuning. Lever 3
(alternate test statistic) is excluded entirely, matching the charter's
Decision 1 scope limit.
