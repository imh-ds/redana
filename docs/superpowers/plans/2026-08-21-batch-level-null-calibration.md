# Batch-Level Null Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Calibrate and independently confirm a 90% batch-level practical-null dCor rule using only fresh known-independent reference data.

**Architecture:** Build pure batch policy and provenance functions first, then a reference-only batch runner and evidence report. Execute the 100-batch calibration half under an immutable CLI and review its evidence before the independent 100-batch confirmation CLI reads the pinned calibration manifest, records, and selected boundary.

**Tech Stack:** Python 3.12, NumPy, pandas, dcor, matplotlib, pytest, Ruff.

**Spec:** docs/superpowers/specs/2026-08-21-batch-level-null-calibration-design.md

## Global Constraints

- Reference-only study: do not run F1--F8, fixture generation, residualization, cross-fitting, or fitted adjustment.
- Every reference replication is two independent standard-normal vectors with 1,000 rows, dCor, 199 permutations, and existing empirical p-value formula.
- Calibration and confirmation each contain exactly 100 batches of 10 reference replications.
- Batch p-value guard is at most 2 of 10 p-values <= 0.05.
- Calibration stops when fewer than 90 batches pass that guard; otherwise select the smallest observed guard-passing batch median that makes at least 90 of all 100 calibration batches null-like using inclusive median <= boundary.
- Confirmation uses the copied, frozen calibration boundary; PASS requires at least 85 of 100 null-like batches and at most 67 of 1,000 p-values <= 0.05.
- Seed namespaces are exactly batch-null-calibration and batch-null-confirmation, with no shared seed identities.
- Retain all records, arrays, exact nullable seeds, warnings, exceptions, runtimes, configuration, source revision, selection metadata, and artifact hashes.
- Nonempty output directories are refused. Earlier Gate 0, null-calibration, and reference-confirmation artifacts remain immutable.
- No result automatically changes a threshold, estimator, fixture, simulation family, package scope, roadmap, or launches F1--F8.

## Planned File Structure

| Path | Responsibility |
| --- | --- |
| research/gate0/batch_null_policy.py | Batch guard, rank-based selection, confirmation checks, and terminal statuses. |
| research/gate0/batch_null_runner.py | Fresh reference execution, exact records, atomic arrays, and immutable lifecycle. |
| research/gate0/batch_null_report.py | Calibration/confirmation manifests, summaries, figures, and owner memos. |
| scripts/run_batch_null_calibration.py | Calibration-half CLI only. |
| scripts/run_batch_null_confirmation.py | Confirmation-half CLI only, verifying frozen calibration evidence. |
| tests/gate0/test_batch_null_policy.py | Selection, thresholds, and precedence tests. |
| tests/gate0/test_batch_null_runner.py | Matrix, namespace, retention, and lifecycle tests. |
| tests/gate0/test_batch_null_report.py | Manifest/memo and calibration-to-confirmation provenance tests. |

### Task 1: Implement frozen batch policy and calibration selection

**Files:**

- Create: research/gate0/batch_null_policy.py
- Create: tests/gate0/test_batch_null_policy.py

**Interfaces:**

- Produces BatchNullConfig, BatchSummary, CalibrationSelection, ConfirmationCheck, summarize_batches(records: pd.DataFrame, config: BatchNullConfig) -> list[BatchSummary], select_calibration_boundary(batches: list[BatchSummary], config: BatchNullConfig) -> CalibrationSelection, check_confirmation(batches: list[BatchSummary], records: pd.DataFrame, boundary: float, config: BatchNullConfig) -> ConfirmationCheck, and batch_terminal_status(selection: CalibrationSelection | None, confirmation: ConfirmationCheck | None) -> str.
- Consumes record frames with phase, batch, replication, observed_statistic, permutation_p_value, and exception_text.

- [ ] **Step 1: Write failing selection tests**

~~~python
def _records(batch_medians: list[float], *, phase: str = "calibration") -> pd.DataFrame:
    rows = []
    for batch, median in enumerate(batch_medians):
        for replication in range(10):
            rows.append({"phase": phase, "batch": batch, "replication": replication,
                         "observed_statistic": median, "permutation_p_value": 0.5,
                         "exception_text": None})
    return pd.DataFrame(rows)


def test_selection_uses_smallest_inclusive_rank_boundary() -> None:
    batches = summarize_batches(_records([float(index) for index in range(100)]), BatchNullConfig())
    selection = select_calibration_boundary(batches, BatchNullConfig())
    assert selection.boundary == 89.0
    assert selection.null_like_batch_count == 90
    assert selection.status == "READY"


def test_calibration_stops_when_fewer_than_90_batches_pass_p_guard() -> None:
    frame = _records([0.01] * 100)
    frame.loc[frame.batch < 11, "permutation_p_value"] = 0.05
    selection = select_calibration_boundary(summarize_batches(frame, BatchNullConfig()), BatchNullConfig())
    assert selection.status == "STOP"
~~~

- [ ] **Step 2: Verify RED**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_batch_null_policy.py -v --basetemp .pytest-batch-policy-red

Expected: import failure because batch_null_policy does not exist.

- [ ] **Step 3: Implement pure policy**

~~~python
@dataclass(frozen=True)
class BatchNullConfig:
    batches: int = 100
    replications_per_batch: int = 10
    evaluation_rows: int = 1_000
    permutations: int = 199
    maximum_batch_low_p_values: int = 2
    minimum_calibration_guard_batches: int = 90
    minimum_confirmation_null_like_batches: int = 85
    maximum_confirmation_low_p_values: int = 67


@dataclass(frozen=True)
class BatchSummary:
    phase: str
    batch: int
    complete: bool
    exception_free: bool
    p_guard_passed: bool
    median_dcor: float | None


@dataclass(frozen=True)
class CalibrationSelection:
    status: str
    boundary: float | None
    qualifying_batch_ids: tuple[int, ...]
    guard_passing_batch_count: int
    null_like_batch_count: int


@dataclass(frozen=True)
class ConfirmationCheck:
    complete: bool
    null_like_batch_count: int
    low_p_value_count: int
    batch_rate_passed: bool
    p_value_passed: bool
~~~

summarize_batches requires exactly 100 complete ten-record batches numbered 0 through 99. A retained exception, missing value, duplicate, or missing batch makes the relevant result incomplete. select_calibration_boundary filters to p-guard-passing complete batches, returns STOP below 90, otherwise uses the 90th ordered median among the guard-passing batches and inclusive comparison. check_confirmation applies the copied boundary, requires 85 batches and at most 67 low p-values. Status precedence is STOP, then NARROW, then PASS.

- [ ] **Step 4: Add tie, p-value, and terminal tests**

~~~python
def test_tied_boundary_is_inclusive_and_reproducible() -> None:
    batches = summarize_batches(_records([0.1] * 100), BatchNullConfig())
    selection = select_calibration_boundary(batches, BatchNullConfig())
    assert selection.boundary == 0.1
    assert selection.null_like_batch_count == 100


def test_confirmation_requires_85_batches_and_at_most_67_low_p_values() -> None:
    frame = _records([0.01] * 85 + [0.2] * 15, phase="confirmation")
    check = check_confirmation(summarize_batches(frame, BatchNullConfig()), frame, 0.01, BatchNullConfig())
    assert check.batch_rate_passed and check.p_value_passed
~~~

Also test 84 null-like batches returns NARROW, 68 low p-values returns STOP, and malformed/exception data returns STOP before any count result.

- [ ] **Step 5: Verify Task 1**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_batch_null_policy.py -v --basetemp .pytest-batch-policy-green

Expected: PASS.

Run: .venv\Scripts\ruff.exe check research/gate0/batch_null_policy.py tests/gate0/test_batch_null_policy.py

Expected: exit code 0.

- [ ] **Step 6: Commit Task 1**

~~~bash
git add research/gate0/batch_null_policy.py tests/gate0/test_batch_null_policy.py
git commit -m "feat: add batch null calibration policy"
~~~

### Task 2: Execute and retain reference-only batches

**Files:**

- Create: research/gate0/batch_null_runner.py
- Create: tests/gate0/test_batch_null_runner.py

**Interfaces:**

- Consumes BatchNullConfig, derive_seed, and permutation_distance_correlation.
- Produces BatchNullRecord and run_batch_phase(phase: Literal["calibration", "confirmation"], output_dir: Path, run_id: str, config: BatchNullConfig) -> pd.DataFrame.

- [ ] **Step 1: Write failing matrix and isolation tests**

~~~python
def test_small_phase_contains_each_batch_and_replication_once(tmp_path: Path) -> None:
    config = BatchNullConfig(batches=2, replications_per_batch=3, evaluation_rows=100, permutations=19)
    frame = run_batch_phase("calibration", tmp_path, "unit", config)
    assert len(frame) == 6
    assert set(frame[["batch", "replication"]].itertuples(index=False, name=None)) == {
        (batch, replication) for batch in range(2) for replication in range(3)
    }
    assert frame.seed_namespace.eq("batch-null-calibration").all()


def test_reference_runner_never_calls_fixture_or_residualization(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("research.gate0.batch_null_runner.generate_fixture", lambda *args: (_ for _ in ()).throw(AssertionError()))
    monkeypatch.setattr("research.gate0.batch_null_runner.cross_fitted_pair_residuals", lambda *args: (_ for _ in ()).throw(AssertionError()))
    frame = run_batch_phase("calibration", tmp_path, "isolated", _small_config())
    assert frame.exception_text.isna().all()
~~~

- [ ] **Step 2: Verify RED**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_batch_null_runner.py -v --basetemp .pytest-batch-runner-red

Expected: import failure because batch_null_runner does not exist.

- [ ] **Step 3: Implement runner and exact records**

~~~python
@dataclass(frozen=True)
class BatchNullRecord:
    phase: str
    batch: int
    replication: int
    observed_statistic: float | None
    permutation_p_value: float | None
    null_statistics_path: str | None
    seed_namespace: str
    left_seed: int | None
    right_seed: int | None
    permutation_seed: int | None
    elapsed_seconds: float
    warnings: str | None
    exception_text: str | None
    run_id: str
~~~

Use derive_seed(seed_namespace, batch, replication, role) for distinct left, right, and permutation identities. Draw exactly evaluation_rows values for each independent normal vector. Persist each 199-value permutation array atomically. Capture warnings and exceptions per record; continue after a record failure. Serialize every seed as exact UInt64. Require an initially empty output and persist records.csv plus manifest-input.json only after every required record is attempted.

- [ ] **Step 4: Add retention and lifecycle tests**

~~~python
def test_runner_retains_every_successful_permutation_array(tmp_path: Path) -> None:
    frame = run_batch_phase("confirmation", tmp_path, "arrays", _small_config())
    assert frame.null_statistics_path.notna().all()
    for relative_path in frame.null_statistics_path:
        assert (tmp_path / relative_path).exists()


def test_runner_refuses_nonempty_output(tmp_path: Path) -> None:
    output = tmp_path / "taken"
    output.mkdir()
    (output / "existing.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError, match="initialized"):
        run_batch_phase("calibration", output, "taken", _small_config())
~~~

Also test a forced metric exception is retained, not raised; nullable >2**53 seed values round-trip exactly; and calibration and confirmation seed sets have no intersection for equal batch/replication indices.

- [ ] **Step 5: Verify Task 2**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_batch_null_runner.py -v --basetemp .pytest-batch-runner-green

Expected: PASS.

Run: .venv\Scripts\python.exe -m pytest -v --basetemp .pytest-batch-runner-full

Expected: all tests PASS.

Run: .venv\Scripts\ruff.exe check research tests scripts

Expected: exit code 0.

- [ ] **Step 6: Commit Task 2**

~~~bash
git add research/gate0/batch_null_runner.py tests/gate0/test_batch_null_runner.py
git commit -m "feat: run batch null reference phases"
~~~


### Task 3: Write hash-pinned manifests and owner-facing reports

**Files:**

- Create: research/gate0/batch_null_report.py
- Create: tests/gate0/test_batch_null_report.py

**Interfaces:**

- Consumes BatchNullConfig, CalibrationSelection, ConfirmationCheck, and batch records.
- Produces write_calibration_report(records: pd.DataFrame, output_dir: Path, run_id: str, config: BatchNullConfig) -> Path and write_confirmation_report(records: pd.DataFrame, output_dir: Path, run_id: str, calibration_dir: Path, config: BatchNullConfig) -> Path.

- [ ] **Step 1: Write failing provenance/report tests**

~~~python
def test_calibration_report_records_selected_boundary_and_rank(tmp_path: Path) -> None:
    memo = write_calibration_report(_calibration_records(), tmp_path, "calibration-unit", BatchNullConfig())
    text = memo.read_text(encoding="utf-8")
    assert "90 of 100" in text
    assert "Selected boundary" in text
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["selection"]["null_like_batch_count"] >= 90


def test_confirmation_report_rejects_changed_calibration_manifest(tmp_path: Path) -> None:
    calibration = _write_calibration_artifacts(tmp_path / "calibration")
    (calibration / "manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256"):
        write_confirmation_report(_confirmation_records(), tmp_path / "confirmation", "confirmation-unit", calibration, BatchNullConfig())
~~~

- [ ] **Step 2: Verify RED**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_batch_null_report.py -v --basetemp .pytest-batch-report-red

Expected: import failure because batch_null_report does not exist.

- [ ] **Step 3: Implement report and provenance contract**

Calibration report must call pure policy selection, write batch-summary.csv, calibration-memo.md, manifest.json, run_state.json, and a batch-median plot. Its manifest includes configuration, exact seed namespace, selection status, boundary, rank/qualifying batch IDs, guard count, record count, source revision, and SHA-256 hashes of records and manifest input.

Confirmation report must verify the calibration directory’s manifest and records hashes, require its READY selection/boundary, copy boundary plus calibration paths/hashes/selection metadata, and never recompute the selection. It writes confirmation-summary.csv, confirmation-memo.md, manifest.json, run_state.json, and a batch classification plot. Both memos list warnings/exceptions, terminal status, and end exactly with OWNER_DECISION_SENTENCE.

- [ ] **Step 4: Add outcome and governance tests**

~~~python
def test_confirmation_report_is_narrow_at_84_batches(tmp_path: Path) -> None:
    calibration = _write_calibration_artifacts(tmp_path / "calibration")
    memo = write_confirmation_report(_confirmation_records(null_like_batches=84), tmp_path / "confirmation", "confirmation-unit", calibration, BatchNullConfig())
    assert "Terminal outcome: **NARROW**" in memo.read_text(encoding="utf-8")


def test_confirmation_report_stops_for_68_low_p_values(tmp_path: Path) -> None:
    calibration = _write_calibration_artifacts(tmp_path / "calibration")
    memo = write_confirmation_report(_confirmation_records(low_p_values=68), tmp_path / "confirmation", "stop-unit", calibration, BatchNullConfig())
    assert "Terminal outcome: **STOP**" in memo.read_text(encoding="utf-8")
~~~

Also test STOP calibration blocks confirmation, all memos include no-F1--F8 governance language, and report run IDs match record run IDs.

- [ ] **Step 5: Verify Task 3**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_batch_null_report.py -v --basetemp .pytest-batch-report-green

Expected: PASS.

Run: .venv\Scripts\python.exe -m pytest -v --basetemp .pytest-batch-report-full

Expected: all tests PASS.

Run: .venv\Scripts\ruff.exe check research tests scripts

Expected: exit code 0.

- [ ] **Step 6: Commit Task 3**

~~~bash
git add research/gate0/batch_null_report.py tests/gate0/test_batch_null_report.py
git commit -m "feat: report batch null calibration evidence"
~~~

### Task 4: Add calibration CLI and run only the calibration half

**Files:**

- Create: scripts/run_batch_null_calibration.py
- Modify: tests/gate0/test_batch_null_runner.py
- Create after run: docs/evidence/batch-null-calibration-batch-null-calibration-20260821-001.md

**Interfaces:**

- Consumes BatchNullConfig, run_batch_phase, and write_calibration_report.
- Produces one immutable calibration artifact tree with a frozen boundary or STOP result.

- [ ] **Step 1: Write failing lifecycle test**

~~~python
def test_calibration_cli_refuses_completed_directory(tmp_path: Path) -> None:
    output = tmp_path / "calibration"
    first = run_cli("--output-dir", str(output), "--run-id", "batch-calibration-unit")
    second = run_cli("--output-dir", str(output), "--run-id", "batch-calibration-unit")
    assert first.returncode == 0
    assert second.returncode != 0
~~~

- [ ] **Step 2: Verify RED**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_batch_null_runner.py -v --basetemp .pytest-batch-calibration-cli-red

Expected: failure because run_batch_null_calibration.py does not exist.

- [ ] **Step 3: Implement narrow calibration CLI**

Accept only output-dir and nonempty run-id. Use BatchNullConfig() with no overrides, run only phase calibration, write calibration report, and print READY or STOP. Do not import fixture, residual, Gate 0, null-calibration, or confirmation CLI modules.

- [ ] **Step 4: Preflight, source commit, and exact one calibration run**

Run: .venv\Scripts\python.exe -m pytest -v --basetemp .pytest-batch-calibration-preflight

Expected: all tests PASS.

Run: .venv\Scripts\ruff.exe check research tests scripts

Expected: exit code 0.

~~~bash
git add research tests scripts
git commit -m "feat: add batch null calibration runner"
~~~

Run exactly:

~~~bash
.venv\Scripts\python.exe scripts/run_batch_null_calibration.py --output-dir artifacts/batch-null-calibration/batch-null-calibration-20260821-001 --run-id batch-null-calibration-20260821-001
~~~

Retain evidence whether READY or STOP. Do not run confirmation from this task.

- [ ] **Step 5: Commit calibration evidence**

Create docs/evidence/batch-null-calibration-batch-null-calibration-20260821-001.md linking manifest, records, summary, memo, figures, boundary/STOP, and governance.

~~~bash
git add artifacts/batch-null-calibration/batch-null-calibration-20260821-001 docs/evidence/batch-null-calibration-batch-null-calibration-20260821-001.md
git commit -m "docs: record batch null calibration evidence"
~~~

### Task 5: Independently review calibration, then add confirmation CLI and run it only if READY

**Files:**

- Create: scripts/run_batch_null_confirmation.py
- Modify: tests/gate0/test_batch_null_report.py
- Create after approved READY calibration run: docs/evidence/batch-null-confirmation-batch-null-confirmation-20260821-001.md

**Interfaces:**

- Consumes BatchNullConfig, run_batch_phase, and write_confirmation_report.
- Requires a reviewed READY calibration directory and its pinned manifest/record hashes.
- Produces one independent immutable confirmation artifact tree.

- [ ] **Step 1: Read and independently review the committed calibration evidence**

Check the calibration memo, manifest, records count, selection count, boundary, arrays, source revision, exact seed fields, and output state. If calibration is STOP or review finds a defect, do not create confirmation CLI/evidence or execute confirmation; return to owner.

- [ ] **Step 2: Write failing calibration-provenance CLI test**

~~~python
def test_confirmation_cli_rejects_tampered_calibration_evidence(tmp_path: Path) -> None:
    calibration = _write_ready_calibration(tmp_path / "calibration")
    (calibration / "records.csv").write_text("tampered", encoding="utf-8")
    result = run_confirmation_cli("--calibration-dir", str(calibration), "--output-dir", str(tmp_path / "confirmation"), "--run-id", "batch-confirmation-unit")
    assert result.returncode != 0
~~~

- [ ] **Step 3: Implement confirmation CLI only after READY calibration**

Accept only calibration-dir, output-dir, and nonempty run-id. Verify calibration report provenance before output creation. Use BatchNullConfig() without overrides, run only phase confirmation, and write confirmation report. Refuse a STOP calibration, changed manifest/records, nonempty output, or a calibration directory outside the named batch-null-calibration artifact root.

- [ ] **Step 4: Preflight, source commit, and one independent confirmation run**

Run: .venv\Scripts\python.exe -m pytest -v --basetemp .pytest-batch-confirmation-preflight

Expected: all tests PASS.

Run: .venv\Scripts\ruff.exe check research tests scripts

Expected: exit code 0.

~~~bash
git add research tests scripts
git commit -m "feat: add batch null confirmation runner"
~~~

If and only if Task 4 evidence is READY and its independent review is clean, run exactly:

~~~bash
.venv\Scripts\python.exe scripts/run_batch_null_confirmation.py --calibration-dir artifacts/batch-null-calibration/batch-null-calibration-20260821-001 --output-dir artifacts/batch-null-confirmation/batch-null-confirmation-20260821-001 --run-id batch-null-confirmation-20260821-001
~~~

Retain result for PASS, NARROW, or STOP. Do not run F1--F8 or revise the boundary.

- [ ] **Step 5: Commit confirmation evidence**

Create docs/evidence/batch-null-confirmation-batch-null-confirmation-20260821-001.md linking both calibration and confirmation evidence, copied boundary/hash metadata, terminal status, and the no-automatic-successor statement.

~~~bash
git add artifacts/batch-null-confirmation/batch-null-confirmation-20260821-001 docs/evidence/batch-null-confirmation-batch-null-confirmation-20260821-001.md
git commit -m "docs: record batch null confirmation evidence"
~~~

## Self-review

- **Spec coverage:** Task 1 defines exact batch-level selection/checking. Task 2 generates complete independent-reference evidence. Task 3 binds calibration to confirmation by hashes and reports all governance. Task 4 executes calibration only. Task 5 requires a reviewed READY calibration before independent confirmation.
- **Scope:** The plan excludes F1--F8 and every fitted/residual path, does not modify prior evidence, and prohibits automatic successor work.
- **Type consistency:** BatchNullConfig/BatchSummary/CalibrationSelection/ConfirmationCheck are defined in Task 1; BatchNullRecord/run_batch_phase in Task 2; report writers in Task 3; Task 4 and Task 5 consume only those interfaces.
- **No placeholders:** Counts, thresholds, seed namespaces, paths, outcomes, and approved run identities are explicit.
