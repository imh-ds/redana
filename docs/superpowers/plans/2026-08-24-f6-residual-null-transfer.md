# F6 Residual-Null Transfer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute one immutable 100 x 10 F6 residual-null transfer study at 1,000 rows using the frozen reference boundary and the unmodified general-purpose (spline/Ridge) residualizer.

**Architecture:** A dedicated runner generates F6 only, cross-fits `X1`/`X3` residuals (adjustment set `X2, X4, X5, X6`, derived automatically by excluding both tested endpoints), and retains all residual samples and dCor arrays. A separate report and narrow CLI copy verified calibration provenance and apply the unchanged batch policy. Both are near-exact copies of the already-reviewed `f5_transfer_runner.py`/`f5_transfer_report.py`, substituting fixture `F6` and pair `(X1, X3)`.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, matplotlib, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-24-f6-residual-null-transfer-design.md`

## Global Constraints

- Existing F6 only (no fixture code changes); pair `(X1, X3)`; adjust for `(X2, X4, X5, X6)` via the existing general-purpose `cross_fitted_pair_residuals` (spline/Ridge) -- not the F5 quadratic-repair basis.
- Exactly 100 batches x 10 replications x 1,000 rows; 199 permutations; five-fold, five-knot cubic-spline/Ridge residualization.
- Copy but never recompute boundary `0.058242447845091264` from `artifacts/batch-null-calibration/batch-null-calibration-20260821-001` after hash verification.
- Use namespace `batch-f6-null-transfer`; retain fixture/residual/permutation UInt64 seeds, 1,000-row residual CSVs, and 199-value null arrays.
- `STOP`: malformed/exception evidence or >67 low p-values; `NARROW`: <85 null-like batches; `PASS`: otherwise.
- Official output: `artifacts/batch-f6-null-transfer/batch-f6-null-transfer-20260824-001`; do not recalibrate, add alternatives, run another fixture, or begin package work regardless of outcome.

---

### Task 1: Implement and test the F6 runner

**Files:** Create `research/gate0/f6_transfer_runner.py` and `tests/gate0/test_f6_transfer_runner.py`.

**Interfaces:** `F6TransferConfig` defaults to batches 100, replications 10, rows 1_000, permutations 199, five splits, five knots, degree 3, Ridge alpha 1 (same shape as `F5TransferConfig`). `run_f6_transfer(output_dir: Path, run_id: str, config: F6TransferConfig) -> pd.DataFrame` returns rows with F6/pair identity, batch/replication, observed dCor/p-value, residual/null relative paths, three seeds, warnings, exceptions, namespace, and run ID.

- [ ] **Step 1: Write failing tests**

Test a 2 x 3 x 100-row config; spy on `generate_fixture` and assert exactly six calls of `("F6", 100)`, a single output pair `F6/X1/X3`, each residual CSV has 100 rows with columns `X1,X3`, all six `(batch, replication)` identities exist, namespace is `batch-f6-null-transfer`, phase is `f6-null-transfer`, and every successful null-array path exists with shape `(19,)`.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f6_transfer_runner.py -v --basetemp .pytest-f6-runner-red`. Expect import failure for `f6_transfer_runner`.

- [ ] **Step 3: Implement minimal runner**

Copy `f5_transfer_runner.py` structure exactly, changing only: namespace `batch-f6-null-transfer`, phase `f6-null-transfer`, fixture id `F6`, pair `("X1", "X3")`, and the `generate_fixture("F6", ...)` call. For each `(batch, replication)`, derive fixture/residual/permutation seeds from `batch-f6-null-transfer`; generate `F6`; call `cross_fitted_pair_residuals(frame, "X1", "X3", gate0_config, residual_seed % (2**32))`; run dCor on all resulting residual rows. Atomically write `residual_samples/batch-{batch}-replication-{replication}.csv`, `null_statistics/batch-{batch}-replication-{replication}.npy`, `records.csv`, and `manifest-input.json`. Preserve a per-cell exception and continue. Use UInt64 seed columns.

- [ ] **Step 4: Add failure/reuse tests**

Monkeypatch residualization to fail on one cell and assert one retained exception while five remaining cells finish. Create a non-empty output directory and assert `run_f6_transfer` raises `FileExistsError` without modifying it.

- [ ] **Step 5: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-f6-runner-green`, then Ruff over both new files; expect clean. Commit `research/gate0/f6_transfer_runner.py` and its test as `feat: run F6 residual null transfer`.

### Task 2: Implement and test hash-pinned F6 reporting

**Files:** Create `research/gate0/f6_transfer_report.py` and `tests/gate0/test_f6_transfer_report.py`.

**Interfaces:** `write_f6_transfer_report(records: pd.DataFrame, output_dir: Path, run_id: str, calibration_dir: Path, config: F6TransferConfig) -> Path`, built the same way as `write_f5_transfer_report` -- consumes `_verified_calibration`, `summarize_batches`, `check_confirmation`, and `batch_terminal_status`; writes summary, plot, manifest, memo, and complete state.

- [ ] **Step 1: Write failing tests**

Create a synthetic READY calibration, then assert a complete 85-batch F6 frame yields PASS and copies boundary `0.058242447845091264`. Tamper with calibration records and assert a SHA-256 refusal before output. Also test 84 batches gives NARROW, 68 low p-values gives STOP, and a missing residual sample path gives `ValueError`. Test wrong fixture/pair/phase/namespace is rejected.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f6_transfer_report.py -v --basetemp .pytest-f6-report-red`. Expect import failure for `f6_transfer_report`.

- [ ] **Step 3: Implement report**

Copy `f5_transfer_report.py` structure exactly, changing only the fixture/pair/phase/namespace constants and output filenames (`f6-transfer-summary.csv`, `plots/f6-batch-classifications.png`, `f6-transfer-memo.md`). Reject records with wrong phase, fixture, pair, run ID, namespace, or residual paths. Verify READY calibration and hashes; copy its selection; calculate the unchanged policy. Memo must identify the F6 residual-null transfer, name the adjustment set `(X2, X4, X5, X6)`, and forbid recalibration, alternate fixtures, dependent alternatives, and package work.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-f6-report-green`, then Ruff over both new files; expect clean. Commit as `feat: report F6 residual null transfer`.

### Task 3: Add frozen CLI, preflight, execute once, and commit evidence

**Files:** Create `scripts/run_f6_residual_null_transfer.py`; modify the two F6 test files; create evidence pointer `docs/evidence/f6-residual-null-transfer-batch-f6-null-transfer-20260824-001.md` after run.

**Interfaces:** CLI accepts only `--output-dir` and non-empty `--run-id`; hard-codes approved calibration directory and `F6TransferConfig()`.

- [ ] **Step 1: Write failing CLI tests**

Assert a tampered calibration causes return code 2 before output creation. Assert default-run success in a temporary directory and a second attempt at the same output returns 2. Assert there are no flags for dimensions, thresholds, fixture IDs, pair names, calibration path, or namespace.

- [ ] **Step 2: Verify RED**

Run both focused F6 suites with basetemp `.pytest-f6-cli-red`. Expect import failure for `run_f6_residual_null_transfer`.

- [ ] **Step 3: Implement narrow CLI**

Copy `scripts/run_f5_residual_null_transfer.py` structure exactly, changing only the fixture-specific imports, hard-coded hashes reused unchanged (same calibration parent), config type, runner/report function names, and printed label (`F6 RESIDUAL-NULL TRANSFER`). Verify the hard-coded calibration directory, run `run_f6_transfer`, then `write_f6_transfer_report`; read outcome from manifest and print it. Catch refusal exceptions and return 2. Do not expose configuration overrides.

- [ ] **Step 4: Preflight, commit source, and run exactly once**

Run full pytest with basetemp `.pytest-f6-preflight`, then `ruff check research tests scripts`; expect full PASS and lint clean. Commit new runner/report/CLI/tests as `feat: add F6 residual null transfer runner`. Confirm the official output directory is absent or empty, record the exact commit SHA, then run exactly:

```text
PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_f6_residual_null_transfer.py --output-dir artifacts/batch-f6-null-transfer/batch-f6-null-transfer-20260824-001 --run-id batch-f6-null-transfer-20260824-001
```

Launch exactly once; no retry. If the harness detaches, inspect that exact directory before deletion or restart.

- [ ] **Step 5: Commit immutable evidence**

Create an evidence pointer linking manifest, records, summary, memo, plot, residual samples, arrays, calibration hashes/boundary, result, and governance. Commit artifact tree and pointer as `docs: record F6 residual null transfer evidence`.

### Task 4: Independently review committed F6 evidence

**Files:** Read the committed F6 artifact tree and its evidence pointer.

- [ ] **Step 1: Recompute all evidence from raw files**

Without importing the project runner/report/policy modules: verify exactly 1,000 unique `(batch, replication)` identities covering `0..99 x 0..9`; F6/X1/X3 identity and namespace on every row; 1,000 residual CSVs each with 1,000 X1/X3 rows; 1,000 199-value finite arrays; all hashes and derived seeds; p guards, batch medians, copied-boundary classifications, low-p count, and terminal outcome, reapplied independently.

- [ ] **Step 2: Report governance result**

Approve only complete, hash-consistent, F6-only evidence whose independently recomputed terminal outcome matches the retained manifest.

- If `PASS`: record that the frozen general-purpose residualizer already handles this nonlinear-mediator structure; no F6 repair is needed. This does not itself authorize the next untested structure -- that remains a separate, later owner decision.
- If `NARROW` or `STOP`: record it and stop for diagnosis; do not design a repair in the same pass. A structure-matched F6 repair, if ever pursued, requires its own separate owner-approved design.

## Self-review

Tasks 1--4 cover every fixed fixture, residualization, retention,
provenance, rule, CLI, evidence, and independent-review requirement in the
spec, built as a close, deliberately unoriginal copy of the already-reviewed
F5 null-transfer implementation with only the fixture, pair, and adjustment
set changed. No placeholders, threshold overrides, or repair-basis work
appear -- whether F6 needs a repair is exactly the open question this study
answers, not something assumed in advance.
