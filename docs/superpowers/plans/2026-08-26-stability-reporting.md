# Stability and Detectability Reporting (Track 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement bootstrap edge stability, a stability-tier classifier,
a minimal detectability lookup, and validate bootstrap stability against
actual between-dataset replication on two configurations (well-powered
and marginal), per `docs/superpowers/specs/2026-08-26-stability-reporting-charter.md`.

**Architecture:** Two new `redana` modules. `redana/stability.py`:
`bootstrap_edge_stability` (resample rows with replacement, rerun
`run_prototype` per resample, tally per-pair selection frequency) and
`classify_stability_tier` (pure function, approved thresholds:
`core >= 0.75`, `0.40 <= provisional < 0.75`, `background < 0.40`).
`redana/detectability.py`: a frozen table of already-published
per-edge-detection-fraction results from this project's own evidence
notes, plus `lookup_detectability` (exact match only) and
`nearest_detectability` (nearest tested point, explicitly labeled
approximate). A validation script runs 50 independent datasets per
configuration (actual replication, via existing
`run_replicated_condition`) and bootstrap stability on the first 10 of
those 50 datasets' seeds (100 resamples each), then compares the two.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-26-stability-reporting-charter.md`

## Global Constraints

- No changes to `redana.residuals`, `redana.dependence`, `redana.fdr`,
  `redana.network`, `redana.prototype`, `redana.benchmark`, or any
  existing fixture. Purely additive new modules.
- Bootstrap resamples rows with replacement to the original sample size
  (`n_rows` unchanged per resample), each resample given a distinct
  deterministic seed derived from the dataset's own seed and the
  resample index.
- Stability-tier thresholds (`0.75`, `0.40`) are fixed by the approved
  charter and must not be adjusted after seeing Task 3's validation
  results.
- The detectability table is a frozen, hand-transcribed record of
  values already published in this project's own evidence notes (cite
  the source note per entry) -- not a new statistical claim, not
  interpolated or curve-fit.
- 100 bootstrap resamples per dataset (approved); bootstrap stability
  computed on 10 of each configuration's 50 datasets.

---

### Task 1: Bootstrap edge stability and tier classification

**Files:** Create `redana/stability.py`; create
`tests/redana/test_stability.py`.

**Interfaces:**
- `bootstrap_edge_stability(frame: pd.DataFrame, residual_config: PrototypeConfig, network_config: NetworkConfig, permutations: int, alpha: float, seed: int, n_bootstrap: int) -> dict[tuple[str, str], float]`
- `classify_stability_tier(stability: float) -> str` (returns `"core"`, `"provisional"`, or `"background"`; raises `ValueError` outside `[0, 1]`)

- [ ] **Step 1: Write failing tests**

For `bootstrap_edge_stability`: returns a dict covering all `C(6,2)=15`
pairs for a `p=6` frame; every value in `[0, 1]`; deterministic given the
same seed; using a small, fast configuration (`n_rows=300`,
`n_bootstrap=10`, `coefficient=0.7` on
`generate_stage1_nonlinear_fixture`), the true edges' stability is
substantially higher than an unrelated pair's stability. For
`classify_stability_tier`: `0.75 -> "core"`, `0.80 -> "core"`,
`0.74999 -> "provisional"`, `0.40 -> "provisional"`, `0.399 ->
"background"`, `0.0 -> "background"`, `1.0 -> "core"`; `-0.1` and `1.1`
both raise `ValueError`.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/redana/test_stability.py -v --basetemp .pytest-stability-red`. Expect `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Implement both functions in `redana/stability.py`, reusing
`redana.prototype.run_prototype`, `redana.dependence.derive_seed`, and
`itertools.combinations` for the full pair list.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-stability-green`, then Ruff.
Commit as `feat: add bootstrap edge stability and tier classification`.

### Task 2: Detectability lookup table

**Files:** Create `redana/detectability.py`; create
`tests/redana/test_detectability.py`.

**Interfaces:**
- `@dataclass(frozen=True) class DetectabilityEntry: coefficient: float; n_rows: int; per_edge_detection_fraction: float; source_note: str`
- `lookup_detectability(coefficient: float, n_rows: int) -> DetectabilityEntry | None`
- `nearest_detectability(coefficient: float, n_rows: int) -> tuple[DetectabilityEntry, bool]` (second element `True` if it was an exact match, `False` if nearest-approximate)

- [ ] **Step 1: Write failing tests**

Transcribe the known table from
`docs/evidence/stage2-nonlinear-boundary-followup-20260825.md` (coef
0.05/0.10/0.15/0.20 at n=1000) and
`docs/evidence/sample-size-dependence-20260825.md` (Stage A's coef=0.7
at n=100/200/500/1000/2000; Stage B's grid). Test: `lookup_detectability`
returns the exact recorded value for a known `(coefficient, n_rows)`
pair (e.g. `(0.15, 1000) -> 0.36`, matching the boundary follow-up's
recorded fraction) and returns `None` for an untested combination (e.g.
`(0.15, 100)`); `nearest_detectability` returns that same exact match
with `True` for a known point, and for an untested point returns some
entry with `False`.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/redana/test_detectability.py -v --basetemp .pytest-detectability-red`. Expect `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Build the frozen tuple of `DetectabilityEntry` from the two evidence
notes' recorded numbers (use each condition's *mean* per-edge detection
fraction across its two edges, as already reported in each note's
table), and both lookup functions.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-detectability-green`, then
Ruff. Commit as `feat: add detectability lookup table`.

### Task 3: Validate bootstrap stability against actual replication

**Files:** Create `scripts/run_stability_validation.py`; create
`docs/evidence/stability-validation-20260826.md` after running.

**Interfaces:** Script runs, for each of the two approved configurations
(`coefficient=0.7` and `coefficient=0.15`, both `n=1,000`): (a) the
existing 50-replication `run_replicated_condition` call (actual
replication, per-edge detection fraction, unchanged from every prior
round); (b) for the first 10 of those 50 replications' seeds
(re-derived via `derive_seed("stage1", condition_name, index,
base_seed)`, matching `run_replicated_condition`'s internal derivation),
regenerate each dataset and compute `bootstrap_edge_stability` with
`n_bootstrap=100`; averages the 10 datasets' bootstrap stability per
true edge and reports it alongside the 50-dataset actual replication
rate for direct comparison, plus each true edge's tier classification
under `classify_stability_tier` at each of the 10 datasets (reporting
the tier distribution, e.g. "8/10 core, 2/10 provisional").

- [ ] **Step 1: Preflight and commit source**

Run the full pytest suite (`--basetemp .pytest-stability-validation-preflight`)
and `ruff check research tests scripts redana`; expect full PASS and
lint clean. Commit the script as `feat: add stability validation script`.

- [ ] **Step 2: Run both configurations at full scale**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_stability_validation.py`. Two configurations: 50 replications each (actual replication) plus 10 x 100 bootstrap resamples each (1,000 full prototype runs per configuration, 2,000 total) -- expect substantially longer runtime than any prior single round; run in the background.

- [ ] **Step 3: Independent spot recompute**

Without importing `redana.stability` or `redana.benchmark`, re-derive a
handful of the 10 bootstrapped datasets' seeds and confirm the
regenerated fixture matches; manually recompute one dataset's bootstrap
stability for a single pair by resampling rows and rerunning
`run_prototype` directly, to confirm `bootstrap_edge_stability`'s
tallying logic is correct.

- [ ] **Step 4: Record results and commit**

Write `docs/evidence/stability-validation-20260826.md`: both
configurations' actual replication rate vs. mean bootstrap stability
(per true edge and per an incidental non-edge pair, to check
false-positive-side stability too), the tier distribution across the 10
bootstrapped datasets, and a plain-language interpretation of whether
bootstrap stability -- computable from a single real dataset -- is a
trustworthy stand-in for true replication probability -- which a real
researcher can never directly observe. Report any divergence (bootstrap
over- or under-confident relative to actual replication) honestly. This
is `plan.md` §14's central question, answered directly. Commit as `docs: record stability validation results`.

## Self-review

Task 1 and Task 2 are purely additive new modules with no changes to
any existing `redana` component; Task 1's bootstrap function reuses
`run_prototype` unchanged, and Task 2's table is a transcription of
already-published numbers, not a new claim. Task 3 directly answers
`plan.md` §14's stated validation question using machinery built in
Tasks 1-2 plus the existing `run_replicated_condition`, at the two
charter-approved configurations, within the charter-approved compute
budget (10-of-50 bootstrap subset, not all 50). No visualization,
edge typology, Track 2, or real-data work is included, matching the
charter's explicit scope limits.
