# Null-Calibration Diagnostic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure whether Gate 0’s ambiguous known-null results arise from distance correlation’s finite-sample baseline or from fitted residualization, without changing any Gate 0 estimator or decision threshold.

**Architecture:** Add a separate calibration runner and report namespace beside the Gate 0 prototype. It has an independent standard-normal reference arm and a fitted-residual arm for F1/F4/F5/F6; both reuse the frozen distance-correlation and permutation implementation. The report describes the evidence as `CALIBRATION QUESTION`, `RESIDUALIZATION QUESTION`, `STOP`, or `MIXED / OWNER DECISION`, never as a new Gate 0 result.

**Tech Stack:** Python 3.12, NumPy, pandas, scikit-learn, dcor, matplotlib, pytest, Ruff.

**Spec:** `outline/null-calibration-diagnostic.md`

## Global Constraints

- Reuse the Gate 0 adjustment model, five folds, distance correlation, 199 permutations, and empirical p-value unchanged.
- Use exactly F1, F4, F5, and F6 in the fitted-residual arm; do not add fixtures, estimators, or graph-recovery metrics.
- Use 30 identity-seeded replications and evaluation subsample sizes 250, 500, 1,000, and 2,000.
- Generate `50,000` source rows for every fitted-residual replication.
- The independent standard-normal reference arm is the exact statistic baseline; do not use exogenous errors as universal conditional-residual oracles.
- Retain every record, permutation array, warning, exception, seed identity, and runtime.
- No result may change a threshold, estimator, fixture, or package scope automatically. The output always returns control to the owner.

---

## Planned file structure

| Path | Responsibility |
| --- | --- |
| `research/gate0/calibration.py` | Frozen matrix definition, reference/fitted execution, identity seeds, and tidy records. |
| `research/gate0/calibration_report.py` | Aggregate summaries, paired reference-versus-fitted plots, and owner-facing diagnostic memo. |
| `scripts/run_null_calibration.py` | Immutable run-directory CLI. |
| `tests/gate0/test_calibration.py` | Matrix, reference, fitted-residual, and failure-retention tests. |
| `tests/gate0/test_calibration_report.py` | Memo/category/reporting tests. |
| `artifacts/null-calibration/<run-id>/` | Immutable diagnostic records, arrays, figures, manifest, and memo. |

### Task 1: Freeze the calibration matrix and reference arm

**Files:**
- Create: `research/gate0/calibration.py`
- Create: `tests/gate0/test_calibration.py`

**Interfaces:**
- Produces `CalibrationConfig`, `CalibrationRecord`, `CALIBRATION_FIXTURES`, `EVALUATION_SIZES`, `run_reference_cell(...)`, and `run_fitted_cell(...)`.
- Consumes `derive_seed`, `FULL_PROFILE`, `generate_fixture`, `cross_fitted_pair_residuals`, and `permutation_distance_correlation`.

- [ ] **Step 1: Write failing tests for the frozen matrix and reference statistic**

```python
from research.gate0.calibration import CALIBRATION_FIXTURES, EVALUATION_SIZES, run_reference_cell


def test_calibration_matrix_is_frozen() -> None:
    assert CALIBRATION_FIXTURES == ("F1", "F4", "F5", "F6")
    assert EVALUATION_SIZES == (250, 500, 1_000, 2_000)


def test_reference_cell_is_identity_seeded_and_uses_independent_normals() -> None:
    first = run_reference_cell(evaluation_rows=250, replication=3, permutations=19)
    second = run_reference_cell(evaluation_rows=250, replication=3, permutations=19)
    assert first.observed_statistic == second.observed_statistic
    assert first.arm == "reference"
    assert first.fixture_id == "reference"
    assert first.exception_text is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\\Scripts\\python.exe -m pytest tests/gate0/test_calibration.py -v --basetemp .pytest-calibration-red`

Expected: FAIL because `research.gate0.calibration` does not exist.

- [ ] **Step 3: Implement the frozen data model and reference execution**

Define `CalibrationConfig(replications=30, source_rows=50_000, permutations=199, evaluation_sizes=(250, 500, 1_000, 2_000))`. Define `CalibrationRecord` with arm, fixture ID, replication, evaluation rows, observed statistic, p-value, null-statistics path, residual-sample path, all identity seeds, elapsed seconds, warnings, and exception text.

`run_reference_cell` must draw two independent standard-normal arrays of exactly `evaluation_rows`, derive distinct identity seeds for left/right/permutation, and call `permutation_distance_correlation` unchanged. It must not invoke fixtures or residualization.

- [ ] **Step 4: Run focused tests and Ruff**

Run: `.venv\\Scripts\\python.exe -m pytest tests/gate0/test_calibration.py -v --basetemp .pytest-calibration-green`

Expected: PASS.

Run: `.venv\\Scripts\\ruff.exe check research/gate0/calibration.py tests/gate0/test_calibration.py`

Expected: exit code 0.

- [ ] **Step 5: Commit**

```bash
git add research/gate0/calibration.py tests/gate0/test_calibration.py
git commit -m "feat: add null calibration reference arm"
```

### Task 2: Add the fitted-residual arm and record-first persistence

**Files:**
- Modify: `research/gate0/calibration.py`
- Modify: `tests/gate0/test_calibration.py`

**Interfaces:**
- Consumes the Task 1 record model and existing Gate 0 fixture/residual/metric functions.
- Produces `run_calibration(output_dir: Path, run_id: str, config: CalibrationConfig) -> pandas.DataFrame`.

- [ ] **Step 1: Write failing fitted-arm and failure-retention tests**

```python
from pathlib import Path

from research.gate0.calibration import CalibrationConfig, run_calibration


def test_fitted_arm_records_only_the_four_approved_null_fixtures(tmp_path: Path) -> None:
    frame = run_calibration(
        tmp_path, "unit", CalibrationConfig(replications=1, evaluation_sizes=(250,), permutations=19)
    )
    assert set(frame.loc[frame.arm == "fitted", "fixture_id"]) == {"F1", "F4", "F5", "F6"}
    assert set(frame.loc[frame.arm == "reference", "fixture_id"]) == {"reference"}


def test_calibration_retains_a_fitted_arm_exception(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("research.gate0.calibration.generate_fixture", lambda *args: (_ for _ in ()).throw(RuntimeError("fixture failed")))
    frame = run_calibration(tmp_path, "failure", CalibrationConfig(replications=1, evaluation_sizes=(250,), permutations=19))
    assert frame.loc[frame.arm == "fitted", "exception_text"].notna().all()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\\Scripts\\python.exe -m pytest tests/gate0/test_calibration.py -v --basetemp .pytest-calibration-fitted-red`

Expected: FAIL because `run_calibration` does not exist.

- [ ] **Step 3: Implement fitted execution and immutable artifacts**

For each fixture, replication, and evaluation size, derive one fixture/replication dataset seed; fit the unchanged pair-specific residualization once per fixture/replication; draw an identity-seeded evaluation subsample for each size; calculate the unchanged permutation statistic; and write the null array and residual-pair sample under `fitted/`.

Run the reference cell once per replication/evaluation-size under `reference/`. Catch exceptions at cell level, write a record with the captured warnings, and continue. Refuse a nonempty run directory and persist `records.csv`, a manifest with the frozen configuration and source revision, and `run_state.json` only after every cell is attempted.

- [ ] **Step 4: Run focused tests, full suite, and Ruff**

Run: `.venv\\Scripts\\python.exe -m pytest tests/gate0/test_calibration.py -v --basetemp .pytest-calibration-fitted-green`

Expected: PASS.

Run: `.venv\\Scripts\\python.exe -m pytest -v --basetemp .pytest-calibration-full`

Expected: all tests PASS.

Run: `.venv\\Scripts\\ruff.exe check research tests scripts`

Expected: exit code 0.

- [ ] **Step 5: Commit**

```bash
git add research/gate0/calibration.py tests/gate0/test_calibration.py
git commit -m "feat: add fitted null calibration arm"
```

### Task 3: Report the diagnostic without changing Gate 0 semantics

**Files:**
- Create: `research/gate0/calibration_report.py`
- Create: `tests/gate0/test_calibration_report.py`
- Modify: `research/gate0/calibration.py`

**Interfaces:**
- Consumes the Task 2 records and artifact paths.
- Produces `diagnostic_outcome(records: pandas.DataFrame) -> str` and `write_calibration_report(records: pandas.DataFrame, output_dir: Path) -> Path`.

- [ ] **Step 1: Write failing report tests**

```python
import pandas as pd

from research.gate0.calibration_report import diagnostic_outcome


def test_permutation_failure_stops_the_diagnostic() -> None:
    records = pd.DataFrame({"arm": ["reference"], "exception_text": ["bad p-values"], "observed_statistic": [0.0], "permutation_p_value": [0.001]})
    assert diagnostic_outcome(records) == "STOP"


def test_reference_baseline_result_requires_owner_calibration_decision() -> None:
    records = pd.DataFrame({"arm": ["reference"] * 30, "exception_text": [None] * 30, "observed_statistic": [0.06] * 30, "permutation_p_value": [0.5] * 30})
    assert diagnostic_outcome(records) == "CALIBRATION QUESTION"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\\Scripts\\python.exe -m pytest tests/gate0/test_calibration_report.py -v --basetemp .pytest-calibration-report-red`

Expected: FAIL because `research.gate0.calibration_report` does not exist.

- [ ] **Step 3: Implement descriptive outcomes and evidence**

Write distribution summaries by arm/fixture/evaluation size: count, median, 5th/95th observed-statistic percentiles, p-value quantiles, and the unchanged Gate 0 null-like/non-null/ambiguous shares. Produce paired reference-versus-fitted plots at every evaluation size.

Determine outcomes in priority order: `STOP` for exceptions or reference p-values materially concentrated near zero; `CALIBRATION QUESTION` when reference at 1,000 rows frequently exceeds the unchanged 0.05 effect-size clause while p-values are not concentrated near zero; `RESIDUALIZATION QUESTION` when a fitted fixture persistently departs from its same-size reference distribution; otherwise `MIXED / OWNER DECISION`. The memo must state that no threshold, estimator, or fixture has changed and end with the owner-decision sentence from the approved protocol.

- [ ] **Step 4: Run report tests and verification**

Run: `.venv\\Scripts\\python.exe -m pytest tests/gate0/test_calibration_report.py -v --basetemp .pytest-calibration-report-green`

Expected: PASS.

Run: `.venv\\Scripts\\python.exe -m pytest -v --basetemp .pytest-calibration-report-full`

Expected: all tests PASS.

Run: `.venv\\Scripts\\ruff.exe check research tests scripts`

Expected: exit code 0.

- [ ] **Step 5: Commit**

```bash
git add research/gate0/calibration.py research/gate0/calibration_report.py tests/gate0/test_calibration_report.py
git commit -m "feat: report null calibration evidence"
```

### Task 4: Add the immutable CLI and execute only after preflight

**Files:**
- Create: `scripts/run_null_calibration.py`
- Modify: `tests/gate0/test_calibration.py`
- Create: `docs/evidence/null-calibration-<run-id>.md` after the completed run.

**Interfaces:**
- Consumes `run_calibration` and `write_calibration_report`.
- Produces one immutable artifact directory and one owner-facing evidence pointer.

- [ ] **Step 1: Write a failing CLI lifecycle test**

```python
def test_calibration_cli_refuses_to_overwrite_completed_run(tmp_path: Path) -> None:
    output = tmp_path / "run"
    first = run_cli("--output-dir", str(output), "--run-id", "calibration-unit")
    second = run_cli("--output-dir", str(output), "--run-id", "calibration-unit")
    assert first.returncode == 0
    assert second.returncode != 0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv\\Scripts\\python.exe -m pytest tests/gate0/test_calibration.py -v --basetemp .pytest-calibration-cli-red`

Expected: FAIL because the CLI does not exist.

- [ ] **Step 3: Implement the CLI and pre-run controls**

Accept only `--output-dir` and nonempty `--run-id`; reject nonempty output directories. On success, write raw records, manifest, figures, and `calibration-memo.md`; emit the final diagnostic outcome. Do not create a Gate 0 `PASS`/`STOP` report or call the package-facing CLI.

- [ ] **Step 4: Verify and run the approved diagnostic**

Run: `.venv\\Scripts\\python.exe -m pytest -v --basetemp .pytest-calibration-preflight`

Expected: all tests PASS.

Run: `.venv\\Scripts\\ruff.exe check research tests scripts`

Expected: exit code 0.

Run: `.venv\\Scripts\\python.exe scripts/run_null_calibration.py --output-dir artifacts/null-calibration/<run-id> --run-id <run-id>`

Expected: one immutable artifact directory and `calibration-memo.md`; retain it for owner review regardless of outcome.

- [ ] **Step 5: Commit source and evidence separately**

```bash
git add research tests scripts
git commit -m "feat: add null calibration diagnostic runner"
git add artifacts/null-calibration/<run-id> docs/evidence/null-calibration-<run-id>.md
git commit -m "docs: record null calibration evidence"
```

## Self-review

- **Spec coverage:** Tasks 1–2 implement the frozen reference/fitted matrix and complete record retention; Task 3 implements the four owner-facing outcomes without threshold changes; Task 4 enforces immutable execution and preserves evidence.
- **Scope:** No task changes the Gate 0 cutoff, residualizer, dependence statistic, fixture equations, estimator, or package API.
- **Consistency:** Every task uses the same four fixtures, 30 replications, four evaluation sizes, 50,000 source rows, and 199 permutations.
- **No placeholders:** All runtime values, paths, interfaces, data arms, and decision outcomes are stated; `<run-id>` is the required immutable execution identity supplied by the CLI.
