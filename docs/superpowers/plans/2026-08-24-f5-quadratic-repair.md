# F5 Explicit-Quadratic Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run one hash-pinned F5 quadratic-basis residual-null repair study under the unchanged 1,000-row decision rule.

**Architecture:** A small residualization primitive builds a deterministic raw-plus-square basis without interactions. A dedicated F5 runner/report/CLI reuses the original fixture and frozen batch policy while recording the new basis and both parent evidence sets. The official artifact is created exactly once only after source preflight is committed.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, matplotlib, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-24-f5-quadratic-repair-design.md`

## Global Constraints

- Use only F5 and pair `(X1, X2)` adjusting for `(X3, X4, X5, X6)`, with 100 batches x 10 replications x 1,000 rows, five shuffled folds, all held-out residual rows, Ridge alpha 1, and 199 permutations.
- Replace only F5's spline map with ordered raw-plus-square columns; no interactions, powers above two, splines, search, or adaptive selection.
- Copy raw calibration boundary `0.058242447845091264`; PASS requires >=85 null-like batches and <=67 low p-values, NARROW misses only the batch count, and STOP has precedence for incomplete/malformed/exception evidence or >67 low p-values.
- Namespace is `batch-f5-quadratic-repair`; official run ID is `batch-f5-quadratic-repair-20260824-001`; refuse non-empty output.
- Pin and verify the raw calibration and original F5 STOP evidence; do not recalibrate, retry, alter seeds/basis/rule, add an alternative, or begin package work.

---

### Task 1: Add the testable explicit-quadratic residualizer

**Files:** Modify `research/gate0/residuals.py`; modify `tests/gate0/test_residuals.py`.

**Interfaces:** `quadratic_adjustment_features(design: pd.DataFrame) -> pd.DataFrame` returns columns in `[X3, X3_squared, X4, X4_squared, ...]` order. `cross_fitted_pair_quadratic_residuals(frame: pd.DataFrame, left: str, right: str, config: Gate0Config, seed: int) -> pd.DataFrame` returns held-out residual columns `[left, right]`.

- [ ] **Step 1: Write failing feature-basis tests**

```python
def test_quadratic_adjustment_features_keep_raw_then_square_per_column() -> None:
    design = pd.DataFrame({"X3": [2.0, -1.0], "X4": [3.0, 4.0]})
    actual = quadratic_adjustment_features(design)
    assert list(actual.columns) == ["X3", "X3_squared", "X4", "X4_squared"]
    assert actual.to_dict("list") == {
        "X3": [2.0, -1.0], "X3_squared": [4.0, 1.0],
        "X4": [3.0, 4.0], "X4_squared": [9.0, 16.0],
    }
```

Add a cross-fitting test that monkeypatches the quadratic pipeline, asserts five fit calls per endpoint, preserves original row index, emits finite held-out `X1`/`X2` residuals, and proves no `SplineTransformer` is constructed.

- [ ] **Step 2: Verify RED**

Run: `C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_residuals.py -v --basetemp .pytest-f5-quadratic-residuals-red`.

Expected: import failure for the two new interfaces.

- [ ] **Step 3: Implement the minimal basis and cross-fitted path**

```python
def quadratic_adjustment_features(design: pd.DataFrame) -> pd.DataFrame:
    features = {name: design[name] for name in design.columns}
    # Build in a loop instead so every raw column is immediately followed by its square.

def cross_fitted_pair_quadratic_residuals(...):
    predictors = predictor_columns(frame.columns, left, right)
    design = quadratic_adjustment_features(frame.loc[:, predictors])
    # Five-fold KFold and StandardScaler/Ridge are fitted on train rows only.
```

Use a private `Pipeline([("scale", StandardScaler()), ("ridge", Ridge(...))])`; do not modify the existing spline path.

- [ ] **Step 4: Verify GREEN and commit**

Run the focused residual tests and `C:\tmp\scova-v4-test\Scripts\ruff.exe check research/gate0/residuals.py tests/gate0/test_residuals.py`; expect clean. Commit as `feat: add quadratic residualizer`.

### Task 2: Add the immutable quadratic-repair runner

**Files:** Create `research/gate0/f5_quadratic_repair_runner.py`; create `tests/gate0/test_f5_quadratic_repair_runner.py`.

**Interfaces:** `F5QuadraticRepairConfig` defaults to the frozen dimensions and exposes `gate0_config() -> Gate0Config`. `run_f5_quadratic_repair(output_dir: Path, run_id: str, config: F5QuadraticRepairConfig) -> pd.DataFrame` creates `records.csv` and `manifest-input.json`.

- [ ] **Step 1: Write failing runner tests**

For `F5QuadraticRepairConfig(batches=2, replications_per_batch=3, rows=100, permutations=19)`, assert all six `(batch, replication)` identities, F5-only `(X1, X2)` records, phase `f5-quadratic-repair`, namespace `batch-f5-quadratic-repair`, three UInt64 seed columns, 100-row two-column residual CSVs, and 19-value `.npy` null arrays. Spy on residualization and assert it calls `cross_fitted_pair_quadratic_residuals`, never the spline residualizer. Inject one residualization exception and assert its record is retained while later cells complete. Assert non-empty output is refused without changing the sentinel file.

- [ ] **Step 2: Verify RED**

Run: `C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f5_quadratic_repair_runner.py -v --basetemp .pytest-f5-quadratic-runner-red`.

Expected: missing `f5_quadratic_repair_runner` import.

- [ ] **Step 3: Implement the dedicated runner**

Start from the already-reviewed F5 transfer runner shape, but hard-code:

```python
_NAMESPACE = "batch-f5-quadratic-repair"
_PHASE = "f5-quadratic-repair"
frame = generate_fixture("F5", config.rows, fixture_seed)
residuals = cross_fitted_pair_quadratic_residuals(
    frame, "X1", "X2", gate0_config, residual_seed % (2**32)
)
```

Atomically write every residual CSV, null array, records CSV, and input manifest. The input manifest must include basis `"raw-plus-square"`, `uses_splines: false`, frozen dimensions, fixture/pair, namespace, run ID, and source revision.

- [ ] **Step 4: Verify GREEN and commit**

Run focused runner tests and Ruff on the new runner/test; expect clean. Commit as `feat: run F5 quadratic repair`.

### Task 3: Add evidence report and locked CLI

**Files:** Create `research/gate0/f5_quadratic_repair_report.py`, `scripts/run_f5_quadratic_repair.py`, `tests/gate0/test_f5_quadratic_repair_report.py`, and `tests/gate0/test_f5_quadratic_repair_cli.py`.

**Interfaces:** `write_f5_quadratic_repair_report(records: pd.DataFrame, output_dir: Path, run_id: str, calibration_dir: Path, f5_stop_dir: Path, config: F5QuadraticRepairConfig) -> Path` writes summary, plot, `manifest.json`, memo, and state. CLI exposes only `--output-dir` and `--run-id`.

- [ ] **Step 1: Write failing report and CLI tests**

Build hash-valid synthetic calibration and F5 STOP parent directories. Assert: 85 null-like batches/zero low p-values produces PASS; 84 produces NARROW; 68 low p-values or a retained exception produces STOP; each manifest contains the copied boundary, basis metadata, and both parent hash blocks; wrong phase/fixture/pair/namespace, missing residual CSV or null array, and tampered parent evidence refuse report output. CLI must refuse altered parent provenance before creating output, use `F5QuadraticRepairConfig()` only, refuse reuse, and reject flags for rows, thresholds, fixture, basis, seeds, calibration paths, and F5 STOP paths.

- [ ] **Step 2: Verify RED**

Run: `C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f5_quadratic_repair_report.py tests/gate0/test_f5_quadratic_repair_cli.py -v --basetemp .pytest-f5-quadratic-report-red`.

Expected: missing report and CLI imports.

- [ ] **Step 3: Implement report and CLI**

Reuse the frozen `BatchNullConfig`, `summarize_batches`, `check_confirmation`, and `batch_terminal_status`. Validate complete quadratic-repair records and every residual/null path. Hash-verify the raw calibration with its three exact hashes, and hash-verify original F5 STOP `records.csv`, `manifest-input.json`, and `manifest.json` against the three exact hashes from the spec before runner initialization. Write a plot, summary, manifest, memo, and `run_state.json`; memo wording must limit a PASS to this exact F5 quadratic null. The CLI catches refusal exceptions, prints a single `F5 QUADRATIC REPAIR ...` line, and returns 2.

- [ ] **Step 4: Verify GREEN and commit source**

Run all quadratic-repair tests, all F5 transfer tests, full pytest with a unique `.pytest-f5-quadratic-preflight` base temp, and Ruff on `research`, `tests`, and `scripts`; expect clean. Commit as `feat: add F5 quadratic repair runner`.

### Task 4: Execute the one official study and preserve reviewable evidence

**Files:** Create `docs/evidence/f5-quadratic-repair-batch-f5-quadratic-repair-20260824-001.md`; create and commit `artifacts/batch-f5-quadratic-repair/batch-f5-quadratic-repair-20260824-001/` only after Task 3 is committed.

**Interfaces:** Official command returns 0 after retained run/report output; the evidence note names every hash, count, terminal outcome, and decision boundary.

- [ ] **Step 1: Preflight exact command and source revision**

Confirm the official directory does not exist or is empty, retain the Task 3 commit SHA, and run exactly:

```text
C:\tmp\redana-batch-python\python.exe scripts/run_f5_quadratic_repair.py --output-dir artifacts/batch-f5-quadratic-repair/batch-f5-quadratic-repair-20260824-001 --run-id batch-f5-quadratic-repair-20260824-001
```

Do not alter the command, rerun identity, source, seed namespace, or output path.

- [ ] **Step 2: Independently recompute retained evidence**

From raw files, verify 1,000 unique `(batch, replication)` identities, finite observed dCor/p-values, 1,000 two-column/1,000-row residual CSVs, 1,000 finite 199-value arrays, record/manifest hashes, both parent hash blocks, p-value guard, all batch medians, null-like count, low-p count, and terminal outcome. Record any warning/exception text verbatim.

- [ ] **Step 3: Write evidence note and commit regardless of outcome**

State the exact outcome and why the governance decision follows. PASS may authorize only a separate owner choice about one matched nonlinear alternative; NARROW/STOP authorizes no tuning. Commit artifacts and note as `docs: record F5 quadratic repair evidence`.

## Self-review

Task 1 implements the sole basis change without altering the existing spline workflow. Task 2 binds that basis to F5-only records and retention. Task 3 applies unchanged rule/provenance via a non-parameterizable CLI. Task 4 supplies the preflight, single official execution, raw recomputation, and permanent outcome record. The plan contains no calibration, retry, general-power, network, or package-work step.
