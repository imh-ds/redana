# Adaptive Configuration Selection and Usefulness-Boundary Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether an 80/20 held-out-split arbiter can reliably pick
the objectively-better Track 2 configuration per dataset, against three
required control arms, across a grid that also maps redana's realistic
usefulness boundary, per
`docs/superpowers/specs/2026-08-26-track2-adaptive-selection-charter.md`.

**Architecture:** One new `redana` module (`redana/arbiter.py`) for the
novel held-out-consistency selection mechanism (rule 4: new component
needs tests, not just a script). Everything else is scripts reusing
existing machinery, matching this project's established pattern.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-26-track2-adaptive-selection-charter.md`

## Global Constraints

- Grid (Decision 1, fixed): `n_rows in {100, 300, 500}` x `coefficient in
  {0.15, 0.7}`, 6 cells.
- Reps (Decision 2, fixed): 30 per cell for the arbiter (its pick is
  data-dependent and noisy, needs many reps to estimate accuracy). The
  three baseline methods (always-sensitive, always-normal, static
  `n_rows<=200` rule) are deterministic per cell -- they never look at
  data, so their per-cell "pick" doesn't vary across reps and needs no
  replication to compute, only to be stated once per cell.
- Success bar (Decision 3, fixed): arbiter adopted only if its mean
  per-cell accuracy beats the static rule's by >=15pp on average across
  the 6 cells, with no cell falling more than 10pp below the static
  rule's accuracy there.
- Split method (Decision 4, fixed): single 80/20 split, no k-fold this
  round.
- `(n_rows=100, coefficient=0.7)` is a genuinely untested cell -- no
  prior evidence note ever ran the well-powered coefficient at `n=100`.
  Its "objectively better" ground truth is not yet known and must be
  established (Task 1) before the arbiter's accuracy there can be
  scored -- unlike the other 5 cells, which reuse already-published
  ground truth.

---

### Task 1: Establish ground truth for the untested (n=100, coefficient=0.7) cell

**Files:** Create `scripts/run_adaptive_selection_ground_truth.py`.

**Interfaces:** Runs `run_replicated_condition` for both the
`sensitive` (`n_splits=2, alpha=0.15`) and `normal` (`n_splits=5,
alpha=0.05`) arms at `n_rows=100, coefficient=0.7`, 50 reps each (full
project-standard rep count, since this establishes a ground-truth
reference other results will be scored against, not a per-rep arbiter
comparison), fresh `condition_name` prefix `adaptive-groundtruth-`.
Reports per-edge detection and precision for both arms, and states which
is "objectively better" by the same criterion used throughout Track 2
(detection improvement with no disqualifying precision cost).

- [ ] **Step 1: Preflight**

Run the full pytest suite and `ruff check research tests scripts redana`;
expect full PASS and lint clean.

- [ ] **Step 2: Implement, run, and commit**

Write and run the script (100 replicated runs total, cheap -- no
sharding needed). Commit script and output as `feat: establish ground
truth for the untested n=100 coefficient=0.7 cell`, stating the winning
configuration plainly in the commit message.

### Task 2: Held-out-consistency arbiter

**Files:** Create `redana/arbiter.py`; create `tests/redana/test_arbiter.py`.

**Interfaces:**
- `select_configuration(frame: pd.DataFrame, candidates: dict[str, tuple[PrototypeConfig, float]], permutations: int, seed: int, train_fraction: float = 0.8) -> ArbiterResult`
- `ArbiterResult`: frozen dataclass with `selected: str`, `consistency_scores: dict[str, float]`.

Splits `frame`'s rows via a seeded shuffle into train (`train_fraction`)
and held-out portions. For each named candidate `(PrototypeConfig,
alpha)` pair, runs `run_prototype` independently on the train rows and
on the held-out rows (same config, disjoint data). Consistency score =
`|edges_train ∩ edges_heldout| / |edges_train|` (0.0 if `edges_train` is
empty -- nothing to confirm). Selects the candidate with the higher
consistency score; ties, or both scores `0.0`, fall back to a fixed
default candidate (the caller-specified first key, conventionally
`"normal"`).

- [ ] **Step 1: Write failing tests**

Determinism given the same seed; on a small synthetic frame engineered
with an obvious strong linear/quadratic dependency detectable by both
configs, both candidates should show high, comparable consistency; on a
frame with pure noise columns, both should show low/zero consistency and
fall back to the default; `train_fraction` controls the split size
(check row counts of internal splits via a smaller helper if needed, or
via consistency-score sensitivity); invalid `train_fraction` (e.g. `<=0`
or `>=1`) raises `ValueError`.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/redana/test_arbiter.py -v --basetemp .pytest-arbiter-red`. Expect `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Implement in `redana/arbiter.py`, reusing `redana.prototype.run_prototype`
and `redana.dependence.derive_seed` for the split's own seeding.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-arbiter-green`, then Ruff.
Commit as `feat: add held-out-consistency configuration arbiter`.

### Task 3: Evaluation across the grid (sharded)

**Files:** Create `scripts/run_adaptive_selection_shard.py`; create
`scripts/aggregate_adaptive_selection.py`; create/reuse a GitHub Actions
workflow following Track 1/Track 2's sharding pattern (temporary scoped
push trigger, revert to `workflow_dispatch`-only after verified).

**Interfaces:** One shard per cell (6 shards, `n_rows x coefficient`).
Each shard runs 30 reps; per rep, generates one dataset, runs the Task 2
arbiter (candidates = `{"sensitive": (PrototypeConfig(n_splits=2),
0.15), "normal": (PrototypeConfig(n_splits=5), 0.05)}`), and separately
computes what always-sensitive, always-normal, and the static
`n_rows<=200` rule would have picked for that cell (deterministic, same
for all 30 reps in a cell -- computed once, not per rep). Writes each
rep's arbiter pick to JSON. The aggregation script computes, per cell:
arbiter accuracy (fraction of 30 reps matching the cell's ground-truth
better configuration, from Task 1's new cell and every other cell's
already-published Track 2 evidence), and each baseline's single
deterministic accuracy (0.0 or 1.0) for that cell.

- [ ] **Step 1: Preflight and commit source**

Full pytest + Ruff; commit the shard/aggregate scripts and workflow file
as `feat: add adaptive selection evaluation (sharded)`.

- [ ] **Step 2: Run at full scale**

Push (auto-triggers via the scoped push trigger, per Track 1/Track 2's
established pattern); confirm all shards + aggregation succeed; download
results.

- [ ] **Step 3: Independent spot recompute**

Recompute the arbiter's decision directly (not via the shard script) for
2-3 individual reps across at least 2 different cells, confirming the
consistency scores and final pick match the shard output exactly.

- [ ] **Step 4: Revert the scoped push trigger and commit results**

Revert the workflow to `workflow_dispatch`-only (matching Track 1/Track
2's cleanup step). Commit the aggregated results JSON as `feat: record
adaptive selection evaluation results`.

### Task 4: Evidence note

**Files:** Create `docs/evidence/track2-adaptive-selection-20260826.md`.

**Content:** Report the Task 1 ground-truth finding for `(n=100,
coefficient=0.7)` first (a genuinely new result on its own). Report the
full 6-cell accuracy table for all four methods (arbiter, always-
sensitive, always-normal, static rule). State the verdict against
Decision 3's fixed bar explicitly. Separately from the arbiter verdict,
present the 6-cell grid as a usefulness-boundary map: at which
`(n_rows, coefficient)` combinations does redana (under either
configuration) actually detect anything useful, versus operate at or
near floor -- this is a real deliverable of this study regardless of the
arbiter's outcome, and directly relevant context for any future Core/
Explore engine conversation (not decided here, per rule 9). Explicit
boundary section (k-fold not tested, grid limited to 6 cells, no
real-data claim). Governance section per rule 10, explicitly noting this
does not authorize any engine-splitting product decision.

- [ ] **Step 1: Write and commit**

Commit as `docs: record adaptive selection and usefulness-boundary
results`.

## Self-review

Task 1 fills a real, previously-flagged gap (the untested `n=100,
coefficient=0.7` cell) before it's needed for scoring, rather than
assuming an extrapolated answer. Task 2 is the only genuinely novel
statistical component in this plan and gets full TDD treatment plus the
three required control arms (rule 4), unlike Track 2's original levers
which were purely parameter changes to existing machinery. Task 3 reuses
the proven GitHub Actions sharding pattern from Track 1 and Track 2
rather than inventing a new compute strategy. Task 4 keeps the
usefulness-boundary-mapping deliverable explicitly separate from the
arbiter's pass/fail verdict, since the charter frames these as two
distinct purposes sharing one grid, and keeps the Core/Explore engine
question explicitly unresolved per rule 9.
