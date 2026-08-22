# F4 Linear Residual-Null Transfer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute one immutable 100 x 10 F4 linear residual-null transfer study at 1,000 rows under the frozen reference rule.

**Architecture:** Mirror the reviewed F5 transfer structure with dedicated F4 runner, report, and CLI modules. The runner uses F4 only and the `(X1, X3)` pair; the report copies the verified calibration selection and uses the unchanged batch policy.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, matplotlib, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-22-f4-linear-residual-null-transfer-design.md`

## Global Constraints

- Existing F4 only; test `(X1, X3)` and adjust for `(X2, X4, X5, X6)`.
- Exactly 100 batches x 10 replications x 1,000 rows; all residual rows; five folds; five-knot cubic splines; Ridge alpha 1; 199 permutations.
- Hash-verify and copy boundary `0.058242447845091264` from the committed calibration directory; never recalibrate.
- Namespace `batch-f4-linear-null-transfer`; retain fixture/residual/permutation UInt64 seeds, 1,000-row residual CSVs, 199-value arrays, warnings, exceptions, elapsed time, manifests, summary, plot, memo, and state.
- Official identity: `batch-f4-linear-null-transfer-20260822-001` at `artifacts/batch-f4-linear-null-transfer/batch-f4-linear-null-transfer-20260822-001`.
- Unchanged outcomes: STOP for incomplete/exception/>67 low p-values; NARROW for <85 null-like batches with p cap passing; PASS otherwise.
- No F5 repeat, recalibration, dependent alternative, other fixture, or package work.

---

### Task 1: Create the isolated F4 runner

**Files:** Create `research/gate0/f4_transfer_runner.py`; create `tests/gate0/test_f4_transfer_runner.py`.

**Interfaces:** Define `F4TransferConfig` with defaults `batches=100`, `replications_per_batch=10`, `rows=1_000`, `permutations=199`, `n_splits=5`, `spline_knots=5`, `spline_degree=3`, `ridge_alpha=1.0`; define `run_f4_transfer(output_dir: Path, run_id: str, config: F4TransferConfig) -> pd.DataFrame`.

- [ ] **Step 1: Write failing runner tests**

Use a 2 x 3 x 100-row test config. Spy on fixture generation and assert exactly six calls of `("F4", 100)`; assert every record has `phase="f4-linear-null-transfer"`, fixture F4, pair `X1/X3`, namespace `batch-f4-linear-null-transfer`, all six identities, 100-row two-column residual CSVs, and existing null arrays.

- [ ] **Step 2: Verify RED**

Run `C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f4_transfer_runner.py -v --basetemp .pytest-f4-runner-red`; expect missing-module import failure.

- [ ] **Step 3: Implement runner**

For each identity derive fixture/residual/permutation seeds from the F4 namespace, generate `generate_fixture("F4", rows, fixture_seed)`, residualize `X1/X3` through `cross_fitted_pair_residuals(frame, "X1", "X3", gate0_config, residual_seed % 2**32)`, apply dCor to all rows, and atomically retain CSV/NPY/records/input manifest. Retain one cell error and continue, and write seed columns as UInt64.

- [ ] **Step 4: Add failure and reuse tests**

Monkeypatch residualization to fail once and require exactly one retained exception while other cells complete. Assert a pre-existing nonempty output directory raises `FileExistsError` without modification.

- [ ] **Step 5: Verify GREEN and commit**

Run focused pytest with `.pytest-f4-runner-green` and Ruff on both new files; expect clean. Commit as `feat: run F4 residual null transfer`.

### Task 2: Create the F4 hash-pinned report

**Files:** Create `research/gate0/f4_transfer_report.py`; create `tests/gate0/test_f4_transfer_report.py`.

**Interfaces:** Define `write_f4_transfer_report(records: pd.DataFrame, output_dir: Path, run_id: str, calibration_dir: Path, config: F4TransferConfig) -> Path`; consume `_verified_calibration`, `summarize_batches`, `check_confirmation`, and `batch_terminal_status`.

- [ ] **Step 1: Write failing report tests**

Build synthetic READY calibration evidence and F4 records. Assert a 85-batch/zero-low-p case copies boundary `0.058242447845091264` and reports PASS. Assert calibration-record tampering refuses by SHA-256; 84 batches gives NARROW; 68 low p-values gives STOP; wrong phase/F4/pair/namespace or missing residual path is rejected.

- [ ] **Step 2: Verify RED**

Run `C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f4_transfer_report.py -v --basetemp .pytest-f4-report-red`; expect missing-module import failure.

- [ ] **Step 3: Implement report**

Verify every F4 identity field and all calibration hashes/READY selection; copy boundary and apply unchanged policy. Write F4 summary, classification plot, manifest, memo, and run state. Memo must state F4 linear residual-null scope and forbid successor work.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with `.pytest-f4-report-green` and Ruff; expect clean. Commit as `feat: report F4 residual null transfer`.

### Task 3: Add frozen CLI, preflight, exact run, and evidence commit

**Files:** Create `scripts/run_f4_linear_residual_null_transfer.py`; modify F4 tests; create `docs/evidence/f4-linear-residual-null-transfer-batch-f4-linear-null-transfer-20260822-001.md` after run.

- [ ] **Step 1: Write failing CLI tests**

Require a tampered calibration to return 2 before creating output. Require default config success in an isolated temporary directory and refusal of a reused output directory. Assert CLI accepts only `--output-dir` and `--run-id`.

- [ ] **Step 2: Verify RED**

Run both F4 focused suites with `.pytest-f4-cli-red`; expect missing CLI import.

- [ ] **Step 3: Implement narrow CLI**

Hard-code the approved calibration directory, verify it before output creation, create `F4TransferConfig()` without overrides, run F4 runner/report, print manifest outcome, and return 2 for refusal exceptions. Expose no fixture, dimension, threshold, seed, or calibration-path override.

- [ ] **Step 4: Preflight and source commit**

Run full pytest with `.pytest-f4-preflight`, then `C:\tmp\scova-v4-test\Scripts\ruff.exe check research tests scripts`; expect full PASS and clean lint. Commit source as `feat: add F4 residual null transfer runner`.

- [ ] **Step 5: Execute exactly once and commit evidence**

Run `C:\tmp\redana-batch-python\python.exe scripts/run_f4_linear_residual_null_transfer.py --output-dir artifacts/batch-f4-linear-null-transfer/batch-f4-linear-null-transfer-20260822-001 --run-id batch-f4-linear-null-transfer-20260822-001`. Inspect before deleting/restarting after harness detachment. Create evidence pointer with all retained paths, hashes, copied boundary, result, and governance; commit artifacts/pointer as `docs: record F4 residual null transfer evidence`.

### Task 4: Independently review F4 evidence

**Files:** Read committed F4 artifacts and evidence pointer.

- [ ] **Step 1: Recompute evidence**

Verify 1,000 identities covering 0..99 x 0..9; F4/X1/X3/phase/namespace fields; 1,000 residual CSVs with 1,000 finite X1/X3 rows; 1,000 finite 199-value arrays; calibration and record hashes; exact seeds; p guards, batch medians, classifications, low-p count, and terminal outcome.

- [ ] **Step 2: Apply governance**

Approve only complete, hash-consistent F4 evidence. A PASS supports the nonlinear-F5 interpretation; a NARROW/STOP supports broader transfer concern. Neither authorizes automatic successor work.

## Self-review

Tasks 1--4 cover fixed F4 identity, frozen residualization/rule, retention/provenance, CLI/preflight/run, and independent evidence review. No threshold/configuration override or placeholder remains.
