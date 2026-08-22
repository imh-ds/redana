# F5 Residual-Null Transfer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute one immutable 100 x 10 F5 residual-null transfer study at 1,000 rows using the frozen reference boundary.

**Architecture:** A dedicated runner generates F5 only, cross-fits `X1`/`X2` residuals, and retains all residual samples and dCor arrays. A separate report and narrow CLI copy verified calibration provenance and apply unchanged batch policy.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, matplotlib, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-21-f5-residual-null-transfer-design.md`

## Global Constraints

- Existing F5 only; pair `(X1, X2)`; adjust for `(X3, X4, X5, X6)`.
- Exactly 100 batches x 10 replications x 1,000 rows; 199 permutations; five-fold, five-knot cubic-spline/Ridge residualization.
- Copy but never recompute boundary `0.058242447845091264` from `artifacts/batch-null-calibration/batch-null-calibration-20260821-001` after hash verification.
- Use namespace `batch-f5-null-transfer`; retain fixture/residual/permutation UInt64 seeds, 1,000-row residual CSVs, and 199-value null arrays.
- `STOP`: malformed/exception evidence or >67 low p-values; `NARROW`: <85 null-like batches; `PASS`: otherwise.
- Official output: `artifacts/batch-f5-null-transfer/batch-f5-null-transfer-20260821-001`; do not recalibrate, add alternatives, or begin package work.

---

### Task 1: Implement and test the F5 runner

**Files:** Create `research/gate0/f5_transfer_runner.py` and `tests/gate0/test_f5_transfer_runner.py`.

**Interfaces:** `F5TransferConfig` defaults to batches 100, replications 10, rows 1_000, permutations 199, five splits, five knots, degree 3, Ridge alpha 1. `run_f5_transfer(output_dir: Path, run_id: str, config: F5TransferConfig) -> pd.DataFrame` returns rows with F5/pair identity, batch/replication, observed dCor/p-value, residual/null relative paths, three seeds, warnings, exceptions, namespace, and run ID.

- [ ] **Step 1: Write failing tests**

Test a 2 x 3 x 100-row config; spy on `generate_fixture` and assert exactly six calls of `("F5", 100)`, a single output pair `F5/X1/X2`, each residual CSV has 100 rows, all six `(batch, replication)` identities exist, namespace is `batch-f5-null-transfer`, and every successful null-array path exists.

- [ ] **Step 2: Verify RED**

Run `C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f5_transfer_runner.py -v --basetemp .pytest-f5-runner-red`. Expect import failure for `f5_transfer_runner`.

- [ ] **Step 3: Implement minimal runner**

For each `(batch, replication)`, derive fixture/residual/permutation seeds from `batch-f5-null-transfer`; generate `F5`; call `cross_fitted_pair_residuals(frame, "X1", "X2", gate0_config, residual_seed)`; run dCor on all resulting residual rows. Atomically write `residual_samples/batch-{batch}-replication-{replication}.csv`, `null_statistics/batch-{batch}-replication-{replication}.npy`, `records.csv`, and `manifest-input.json`. Preserve a per-cell exception and continue. Use UInt64 seed columns.

- [ ] **Step 4: Add failure/reuse tests**

Monkeypatch residualization to fail on one cell and assert one retained exception while five remaining cells finish. Create a non-empty output directory and assert `run_f5_transfer` raises `FileExistsError` without modifying it.

- [ ] **Step 5: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-f5-runner-green`, then `C:\tmp\scova-v4-test\Scripts\ruff.exe check research/gate0/f5_transfer_runner.py tests/gate0/test_f5_transfer_runner.py`; expect all tests and lint clean. Commit `research/gate0/f5_transfer_runner.py` and its test as `feat: run F5 residual null transfer`.

### Task 2: Implement and test hash-pinned F5 reporting

**Files:** Create `research/gate0/f5_transfer_report.py` and `tests/gate0/test_f5_transfer_report.py`.

**Interfaces:** `write_f5_transfer_report(records: pd.DataFrame, output_dir: Path, run_id: str, calibration_dir: Path, config: F5TransferConfig) -> Path` consumes `_verified_calibration`, `summarize_batches`, `check_confirmation`, and `batch_terminal_status`; writes summary, plot, manifest, memo, and complete state.

- [ ] **Step 1: Write failing tests**

Create a synthetic READY calibration, then assert a complete 85-batch F5 frame yields PASS and copies boundary `0.058242447845091264`. Tamper with calibration records and assert a SHA-256 refusal before output. Also test 84 batches gives NARROW, 68 low p-values gives STOP, and a missing residual sample path gives `ValueError`.

- [ ] **Step 2: Verify RED**

Run `C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f5_transfer_report.py -v --basetemp .pytest-f5-report-red`. Expect import failure for `f5_transfer_report`.

- [ ] **Step 3: Implement report**

Reject records with wrong phase, fixture, pair, run ID, namespace, or residual paths. Verify READY calibration and hashes; copy its selection; calculate the unchanged policy; write `f5-transfer-summary.csv`, `plots/f5-batch-classifications.png`, manifest, `f5-transfer-memo.md`, and run state. Memo must identify the F5 residual-null transfer and forbid recalibration, alternate fixtures, dependent alternatives, and package work.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-f5-report-green`, then Ruff over both new files; expect clean. Commit as `feat: report F5 residual null transfer`.

### Task 3: Add frozen CLI, preflight, execute once, and commit evidence

**Files:** Create `scripts/run_f5_residual_null_transfer.py`; modify the two F5 test files; create evidence pointer `docs/evidence/f5-residual-null-transfer-batch-f5-null-transfer-20260821-001.md` after run.

**Interfaces:** CLI accepts only `--output-dir` and non-empty `--run-id`; hard-codes approved calibration directory and `F5TransferConfig()`.

- [ ] **Step 1: Write failing CLI tests**

Assert a tampered calibration causes return code 2 before output creation. Assert default-run success in a temporary directory and a second attempt at the same output returns 2. Assert there are no flags for dimensions, thresholds, fixture IDs, pair names, calibration path, or namespace.

- [ ] **Step 2: Verify RED**

Run both focused F5 suites with basetemp `.pytest-f5-cli-red`. Expect import failure for `run_f5_residual_null_transfer`.

- [ ] **Step 3: Implement narrow CLI**

Verify the hard-coded calibration directory, run `run_f5_transfer`, then `write_f5_transfer_report`; read outcome from manifest and print it. Catch refusal exceptions and return 2. Do not expose configuration overrides.

- [ ] **Step 4: Preflight, commit source, and run exactly once**

Run full pytest with basetemp `.pytest-f5-preflight`, then `C:\tmp\scova-v4-test\Scripts\ruff.exe check research tests scripts`; expect full PASS and lint clean. Commit new runner/report/CLI/tests as `feat: add F5 residual null transfer runner`. Then run exactly: `C:\tmp\redana-batch-python\python.exe scripts/run_f5_residual_null_transfer.py --output-dir artifacts/batch-f5-null-transfer/batch-f5-null-transfer-20260821-001 --run-id batch-f5-null-transfer-20260821-001`. If the harness detaches, inspect that exact directory before deletion or restart.

- [ ] **Step 5: Commit immutable evidence**

Create an evidence pointer linking manifest, records, summary, memo, plot, residual samples, arrays, calibration hashes/boundary, result, and governance. Commit artifact tree and pointer as `docs: record F5 residual null transfer evidence`.

### Task 4: Independently review committed F5 evidence

**Files:** Read the committed F5 artifact tree and its evidence pointer.

- [ ] **Step 1: Recompute all evidence**

Verify exactly 1,000 unique `(batch, replication)` identities covering `0..99 x 0..9`; F5/X1/X2 identity and namespace on every row; 1,000 residual CSVs each with 1,000 X1/X2 rows; 1,000 199-value finite arrays; all hashes and derived seeds; p guards, batch medians, boundary classifications, low-p count, and outcome.

- [ ] **Step 2: Report governance result**

Approve only complete, hash-consistent, F5-only evidence. A reviewed PASS permits only an owner decision about the matched dependent-residual alternative; no automatic package work.

## Self-review

Tasks 1--4 cover every fixed fixture, residualization, retention, provenance, rule, CLI, evidence, and independent-review requirement in the spec. No placeholders or threshold/configuration overrides appear.
