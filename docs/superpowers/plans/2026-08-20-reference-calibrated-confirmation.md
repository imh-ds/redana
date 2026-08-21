# Reference-Calibrated Confirmation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Run one independently seeded, reference-calibrated confirmation of the Gate 0 residual-dependence diagnostic at 1,000 evaluation rows.

**Architecture:** Add separate confirmation policy, runner, report, and CLI modules. They reuse the existing fixture generator, pair-specific residualizer, and permutation dCor primitives, but use a new seed namespace and immutable lifecycle. They never edit completed evidence.

**Tech Stack:** Python 3.12, NumPy, pandas, scikit-learn, dcor, matplotlib, pytest, Ruff.

**Spec:** docs/superpowers/specs/2026-08-20-reference-calibrated-confirmation-design.md

## Global Constraints

- Preserve F1--F8 equations, 50,000 source rows, pair-specific endpoint exclusion, five-fold cubic-spline/StandardScaler/Ridge(alpha=1.0) adjustment, dCor, 199 permutations, and empirical p-values.
- Use only 1,000-row residual pairs.
- Freeze practical-null boundary 0.07078970914915612, identified by calibration SHA-256 57160bf69892c4047e8a089487d5b894d09243c1a3bcf60164f4daa881369197 and pandas linear 0.95 quantile.
- null-like: exactly 10 records, at most 2 p-values <= 0.05, and median dCor < 0.07078970914915612.
- non-null remains: at least 8 p-values <= 0.01 and median dCor >= 0.10.
- Reference arm: exactly 30 fresh standard-normal pairs; at least 27 dCor values below boundary and at most 4 p-values <= 0.05.
- Use new reference-confirmation seed namespace; retain every record, exact seed, permutation array, applicable residual sample, warning, exception, runtime, source revision, and frozen configuration.
- Reject nonempty outputs and never touch existing Gate 0 or calibration artifact directories.
- No outcome changes a threshold, estimator, fixture, simulation family, package scope, or roadmap automatically.

## Planned File Structure

| Path | Responsibility |
| --- | --- |
| research/gate0/confirmation_policy.py | Calibration provenance, revised classifier, reference check, and terminal precedence. |
| research/gate0/confirmation_runner.py | Fresh execution, seeds, exact records, and immutable lifecycle. |
| research/gate0/confirmation_report.py | Summaries, manifest, figures, and owner memo. |
| scripts/run_reference_confirmation.py | Narrow immutable confirmation CLI. |
| tests/gate0/test_confirmation_policy.py | Policy/provenance tests. |
| tests/gate0/test_confirmation_runner.py | Runner, retention, and lifecycle tests. |
| tests/gate0/test_confirmation_report.py | Reporting and terminal-outcome tests. |

### Task 1: Freeze calibration provenance and decision policy

**Files:**

- Create: research/gate0/confirmation_policy.py
- Create: tests/gate0/test_confirmation_policy.py

**Interfaces:**

- Produces ConfirmationPolicy, ReferenceCheck, verify_calibration_provenance(path: Path) -> ConfirmationPolicy, classify_confirmation_pair(records: pd.DataFrame, policy: ConfirmationPolicy) -> str, check_reference(records: pd.DataFrame, policy: ConfirmationPolicy) -> ReferenceCheck, and confirmation_status(reference: ReferenceCheck, fixture_records: pd.DataFrame, policy: ConfirmationPolicy) -> str.
- Consumes calibration records.csv only as a pinned provenance input and FIXTURES only for expected pair classes.

- [ ] **Step 1: Write failing provenance and boundary tests**

~~~python
def test_policy_freezes_recorded_boundary() -> None:
    path = Path("artifacts/null-calibration/null-calibration-20260820-001/records.csv")
    policy = verify_calibration_provenance(path)
    assert policy.practical_null_boundary == 0.07078970914915612
    assert policy.calibration_sha256 == CALIBRATION_RECORDS_SHA256


def test_policy_rejects_wrong_calibration_hash(tmp_path: Path) -> None:
    path = tmp_path / "records.csv"
    path.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256"):
        verify_calibration_provenance(path)


def test_null_like_uses_new_strict_boundary() -> None:
    records = pd.DataFrame({"observed_statistic": [0.07078970914915611] * 10,
                            "permutation_p_value": [0.05, 0.05] + [0.5] * 8})
    assert classify_confirmation_pair(records, ConfirmationPolicy.frozen()) == "null-like"
~~~

- [ ] **Step 2: Verify the test file is red**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_confirmation_policy.py -v --basetemp .pytest-confirm-policy-red

Expected: import failure because confirmation_policy does not exist.

- [ ] **Step 3: Implement the pure policy layer**

~~~python
PRACTICAL_NULL_BOUNDARY = 0.07078970914915612
CALIBRATION_RECORDS_SHA256 = "57160bf69892c4047e8a089487d5b894d09243c1a3bcf60164f4daa881369197"


@dataclass(frozen=True)
class ConfirmationPolicy:
    practical_null_boundary: float
    calibration_sha256: str
    calibration_quantile: float = 0.95
    quantile_interpolation: str = "linear"
    fixture_replications: int = 10
    reference_replications: int = 30

    @classmethod
    def frozen(cls) -> "ConfirmationPolicy": ...


@dataclass(frozen=True)
class ReferenceCheck:
    complete: bool
    below_boundary_count: int
    low_p_value_count: int
    practical_boundary_passed: bool
    p_value_passed: bool
~~~

verify_calibration_provenance hashes file bytes before parsing, requires exactly 30 reference rows at evaluation_rows == 1_000, recomputes pandas linear 0.95 quantile, and rejects any mismatch. The classifier requires exactly 10 numeric rows. Terminal precedence: malformed/exception data or failed reference p-value condition gives STOP; failed reference boundary or ambiguity gives NARROW; definite fixture mismatch after a passing reference gives MIXED / OWNER DECISION; otherwise PASS.

- [ ] **Step 4: Add rule and precedence cases**

~~~python
def test_boundary_is_strict_and_non_null_is_unchanged() -> None:
    at_boundary = pd.DataFrame({"observed_statistic": [0.07078970914915612] * 10,
                                "permutation_p_value": [0.5] * 10})
    non_null = pd.DataFrame({"observed_statistic": [0.10] * 10,
                             "permutation_p_value": [0.01] * 8 + [0.5] * 2})
    policy = ConfirmationPolicy.frozen()
    assert classify_confirmation_pair(at_boundary, policy) == "ambiguous"
    assert classify_confirmation_pair(non_null, policy) == "non-null"


def test_reference_check_requires_27_small_statistics_and_four_low_p_values() -> None:
    records = pd.DataFrame({"observed_statistic": [0.01] * 27 + [0.2] * 3,
                            "permutation_p_value": [0.5] * 26 + [0.05] * 4})
    check = check_reference(records, ConfirmationPolicy.frozen())
    assert check.practical_boundary_passed and check.p_value_passed
~~~

Also test 26 below-boundary values gives NARROW, five low reference p-values gives STOP, an ambiguous fixture outranks a definite mismatch as NARROW, and a definite mismatch alone gives MIXED / OWNER DECISION.

- [ ] **Step 5: Verify focused tests and lint**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_confirmation_policy.py -v --basetemp .pytest-confirm-policy-green

Expected: PASS.

Run: .venv\Scripts\ruff.exe check research/gate0/confirmation_policy.py tests/gate0/test_confirmation_policy.py

Expected: exit code 0.

- [ ] **Step 6: Commit Task 1**

~~~bash
git add research/gate0/confirmation_policy.py tests/gate0/test_confirmation_policy.py
git commit -m "feat: freeze reference confirmation policy"
~~~

### Task 2: Execute fresh reference and fixture matrices

**Files:**

- Create: research/gate0/confirmation_runner.py
- Create: tests/gate0/test_confirmation_runner.py

**Interfaces:**

- Consumes ConfirmationPolicy, FIXTURES, FULL_PROFILE, derive_seed, generate_fixture, cross_fitted_pair_residuals, and permutation_distance_correlation.
- Produces ConfirmationConfig, ConfirmationRecord, and run_confirmation(output_dir: Path, run_id: str, policy: ConfirmationPolicy, config: ConfirmationConfig) -> pd.DataFrame.

- [ ] **Step 1: Write failing matrix and seed-isolation tests**

~~~python
def test_confirmation_runs_reference_and_full_fixture_matrix(tmp_path: Path) -> None:
    config = ConfirmationConfig(reference_replications=1, fixture_replications=1,
                                source_rows=500, evaluation_rows=100, permutations=19)
    frame = run_confirmation(tmp_path, "unit", ConfirmationPolicy.frozen(), config)
    assert len(frame.loc[frame.component == "reference"]) == 1
    assert len(frame.loc[frame.component == "fixture"]) == 16
    assert set(frame.loc[frame.component == "fixture", "fixture_id"]) == {f"F{i}" for i in range(1, 9)}


def test_confirmation_uses_a_new_seed_namespace(tmp_path: Path) -> None:
    frame = run_confirmation(tmp_path, "seeds", ConfirmationPolicy.frozen(), _small_config())
    assert frame["seed_namespace"].eq("reference-confirmation").all()
~~~

- [ ] **Step 2: Verify the test file is red**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_confirmation_runner.py -v --basetemp .pytest-confirm-runner-red

Expected: import failure because confirmation_runner does not exist.

- [ ] **Step 3: Implement record-first execution**

~~~python
@dataclass(frozen=True)
class ConfirmationConfig:
    reference_replications: int = 30
    fixture_replications: int = 10
    source_rows: int = 50_000
    evaluation_rows: int = 1_000
    permutations: int = 199


@dataclass(frozen=True)
class ConfirmationRecord:
    component: str
    fixture_id: str
    pair_role: str | None
    expected_class: str | None
    replication: int
    observed_statistic: float | None
    permutation_p_value: float | None
    null_statistics_path: str | None
    residual_sample_path: str | None
    seed_namespace: str
    fixture_seed: int | None
    residual_seed: int | None
    evaluation_seed: int | None
    left_seed: int | None
    right_seed: int | None
    permutation_seed: int | None
    elapsed_seconds: float
    warnings: str | None
    exception_text: str | None
~~~

Use derive_seed("reference-confirmation", ...) for every identity. The reference arm draws independent standard-normal arrays and never invokes fixtures or residualization. Each fixture replication generates source data once, then executes target and null-control pairs using existing residualizer and metric. Atomically persist permutation arrays and fixture residual samples. Catch exceptions per cell and continue. Serialize nullable seeds as exact UInt64 columns, never floats. Initialize only empty outputs and, after all attempts, write records.csv, run_state.json, and a manifest-input payload that includes policy, calibration source/hash, seed namespace, configuration, matrix counts, and source revision.

- [ ] **Step 4: Add retention and lifecycle tests**

~~~python
def test_confirmation_retains_reference_arrays_and_fixture_samples(tmp_path: Path) -> None:
    frame = run_confirmation(tmp_path, "artifacts", ConfirmationPolicy.frozen(), _small_config())
    assert frame.loc[frame.component == "reference", "null_statistics_path"].notna().all()
    assert frame.loc[frame.component == "fixture", "null_statistics_path"].notna().all()
    assert frame.loc[frame.component == "fixture", "residual_sample_path"].notna().all()


def test_confirmation_refuses_nonempty_output(tmp_path: Path) -> None:
    output = tmp_path / "taken"
    output.mkdir()
    (output / "existing.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError, match="initialized"):
        run_confirmation(output, "taken", ConfirmationPolicy.frozen(), _small_config())
~~~

Also test a fixture-cell exception is retained without aborting the matrix and that a persisted CSV round-trips non-null seeds above 2**53 exactly.

- [ ] **Step 5: Verify Task 2**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_confirmation_runner.py -v --basetemp .pytest-confirm-runner-green

Expected: PASS.

Run: .venv\Scripts\python.exe -m pytest -v --basetemp .pytest-confirm-runner-full

Expected: all tests PASS.

Run: .venv\Scripts\ruff.exe check research tests scripts

Expected: exit code 0.

- [ ] **Step 6: Commit Task 2**

~~~bash
git add research/gate0/confirmation_runner.py tests/gate0/test_confirmation_runner.py
git commit -m "feat: run reference calibrated confirmation"
~~~


### Task 3: Report confirmation outcomes and provenance

**Files:**

- Create: research/gate0/confirmation_report.py
- Create: tests/gate0/test_confirmation_report.py

**Interfaces:**

- Consumes ConfirmationPolicy, ReferenceCheck, check_reference, confirmation_status, and confirmation record frames.
- Produces write_confirmation_report(records: pd.DataFrame, output_dir: Path, run_id: str, policy: ConfirmationPolicy) -> Path.

- [ ] **Step 1: Write failing reporting tests**

~~~python
def test_confirmation_memo_records_frozen_boundary_and_governance(tmp_path: Path) -> None:
    memo = write_confirmation_report(_passing_records(), tmp_path, "unit", ConfirmationPolicy.frozen())
    text = memo.read_text(encoding="utf-8")
    assert "0.07078970914915612" in text
    assert "57160bf69892c4047e8a089487d5b894d09243c1a3bcf60164f4daa881369197" in text
    assert text.rstrip().endswith(OWNER_DECISION_SENTENCE)


def test_reference_p_value_failure_is_stop(tmp_path: Path) -> None:
    records = _passing_records()
    records.loc[records.component == "reference", "permutation_p_value"] = 0.05
    memo = write_confirmation_report(records, tmp_path, "stop", ConfirmationPolicy.frozen())
    assert "Terminal outcome: **STOP**" in memo.read_text(encoding="utf-8")
~~~

The _passing_records helper must create exactly 30 complete reference rows and 160 complete fixture rows with expected classes, valid retained artifact paths, statistics below/above the required boundaries, and p-values satisfying both class rules.

- [ ] **Step 2: Verify the test file is red**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_confirmation_report.py -v --basetemp .pytest-confirm-report-red

Expected: import failure because confirmation_report does not exist.

- [ ] **Step 3: Implement report and manifest**

write_confirmation_report must reject mixed run IDs, call the pure policy functions, and write confirmation-summary.csv, manifest.json, plots/reference-dcor.png, plots/fixture-classifications.png, confirmation-memo.md, and terminal run_state.json after it receives all records. The summary includes reference count, below-boundary count, low-p-value count, reference dCor/p-value quantiles, every fixture/pair expected and observed class, warnings, exceptions, and retained artifact paths.

The manifest and memo must include calibration relative path and SHA-256, linear quantile method, exact boundary, reference thresholds and counts, unchanged non-null rule, configuration, seed namespace, source revision, terminal result, and the exact OWNER_DECISION_SENTENCE as the final memo line.

- [ ] **Step 4: Add terminal and output tests**

~~~python
def test_reference_count_failure_is_narrow(tmp_path: Path) -> None:
    records = _passing_records()
    records.loc[records.component == "reference", "observed_statistic"] = 0.2
    memo = write_confirmation_report(records, tmp_path, "narrow", ConfirmationPolicy.frozen())
    assert "Terminal outcome: **NARROW**" in memo.read_text(encoding="utf-8")


def test_report_writes_summary_manifest_and_reference_plot(tmp_path: Path) -> None:
    write_confirmation_report(_passing_records(), tmp_path, "artifacts", ConfirmationPolicy.frozen())
    assert (tmp_path / "confirmation-summary.csv").exists()
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "plots" / "reference-dcor.png").exists()
~~~

Also test a definite fixture mismatch after a passing reference is MIXED / OWNER DECISION, an ambiguous fixture is NARROW, and malformed/incomplete records are STOP.

- [ ] **Step 5: Verify Task 3**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_confirmation_report.py -v --basetemp .pytest-confirm-report-green

Expected: PASS.

Run: .venv\Scripts\python.exe -m pytest -v --basetemp .pytest-confirm-report-full

Expected: all tests PASS.

Run: .venv\Scripts\ruff.exe check research tests scripts

Expected: exit code 0.

- [ ] **Step 6: Commit Task 3**

~~~bash
git add research/gate0/confirmation_report.py tests/gate0/test_confirmation_report.py
git commit -m "feat: report reference confirmation evidence"
~~~

### Task 4: Add immutable CLI and execute the approved confirmation

**Files:**

- Create: scripts/run_reference_confirmation.py
- Modify: tests/gate0/test_confirmation_runner.py
- Create after run: docs/evidence/reference-confirmation-reference-confirmation-20260820-001.md

**Interfaces:**

- Consumes ConfirmationPolicy.frozen, verify_calibration_provenance, run_confirmation, and write_confirmation_report.
- Produces one immutable artifact tree and one owner-facing evidence pointer.

- [ ] **Step 1: Write failing CLI lifecycle test**

~~~python
def test_confirmation_cli_refuses_completed_run(tmp_path: Path) -> None:
    output = tmp_path / "confirmation"
    first = run_cli("--output-dir", str(output), "--run-id", "confirmation-unit")
    second = run_cli("--output-dir", str(output), "--run-id", "confirmation-unit")
    assert first.returncode == 0
    assert second.returncode != 0
~~~

- [ ] **Step 2: Verify the lifecycle test is red**

Run: .venv\Scripts\python.exe -m pytest tests/gate0/test_confirmation_runner.py -v --basetemp .pytest-confirm-cli-red

Expected: failure because run_reference_confirmation.py does not exist.

- [ ] **Step 3: Implement narrow CLI**

Accept only --output-dir and nonempty --run-id. Resolve the pinned calibration records relative to repository root, verify provenance before creating output, reject nonempty outputs, execute ConfirmationConfig() without overrides, write report, and print terminal outcome. Do not call run_gate0, run_calibration, or earlier CLIs; do not write to earlier evidence directories.

- [ ] **Step 4: Fresh preflight and source commit**

Run: .venv\Scripts\python.exe -m pytest -v --basetemp .pytest-reference-confirmation-preflight

Expected: all tests PASS.

Run: .venv\Scripts\ruff.exe check research tests scripts

Expected: exit code 0.

~~~bash
git add research tests scripts
git commit -m "feat: add reference confirmation runner"
~~~

- [ ] **Step 5: Execute exactly one approved fresh run**

Run exactly:

~~~bash
.venv\Scripts\python.exe scripts/run_reference_confirmation.py --output-dir artifacts/reference-confirmation/reference-confirmation-20260820-001 --run-id reference-confirmation-20260820-001
~~~

Retain this output for PASS, STOP, NARROW, or MIXED / OWNER DECISION. Do not rerun it or change rules from its result.

- [ ] **Step 6: Record evidence separately**

Create docs/evidence/reference-confirmation-reference-confirmation-20260820-001.md. It must link memo, manifest, records, summary, and figures; state terminal outcome; state it is confirmation under frozen conditions only; and say it changes no estimator, fixture, threshold, scope, or roadmap automatically.

~~~bash
git add artifacts/reference-confirmation/reference-confirmation-20260820-001 docs/evidence/reference-confirmation-reference-confirmation-20260820-001.md
git commit -m "docs: record reference confirmation evidence"
~~~

## Self-review

- **Spec coverage:** Task 1 pins calibration provenance, classification, reference checks, and status precedence. Task 2 creates the fresh 30-reference plus 160-fixture-record matrix with complete retention. Task 3 provides required summary, provenance, figures, memo, and governance. Task 4 supplies narrow CLI, fresh preflight, one run, and separate evidence commit.
- **Scope:** No task edits completed Gate 0/calibration artifacts or their frozen procedures. This is a new confirmation path only.
- **Type consistency:** Task 1 defines ConfirmationPolicy and ReferenceCheck; Task 2 defines ConfirmationConfig, ConfirmationRecord, and run_confirmation; Task 3 defines write_confirmation_report; Task 4 consumes these interfaces.
- **No placeholders:** All runtime values, paths, accepted outcomes, source provenance, and approved run identity are explicit.

