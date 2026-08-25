# F1 Independence Null-Transfer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute one immutable 100 x 10 F1 independence null-transfer study at 1,000 rows using the frozen reference boundary and the unmodified general-purpose (spline/Ridge) residualizer.

**Architecture:** A dedicated runner generates F1 only, cross-fits `X1`/`X2` residuals (adjustment set `X3, X4, X5, X6`, all signal-free by construction), and retains all residual samples and dCor arrays. A separate report and narrow CLI copy verified calibration provenance and apply the unchanged null-like batch policy. Both are near-exact copies of the already-reviewed `f6_transfer_runner.py`/`f6_transfer_report.py`, substituting fixture `F1` and pair `(X1, X2)`.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, matplotlib, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-24-f1-independence-null-transfer-design.md`

## Global Constraints

- Existing F1 only (no fixture code changes); pair `(X1, X2)`; adjust for `(X3, X4, X5, X6)` via the existing general-purpose `cross_fitted_pair_residuals` (spline/Ridge) -- not the F5 quadratic-repair basis.
- Exactly 100 batches x 10 replications x 1,000 rows; 199 permutations; five-fold, five-knot cubic-spline/Ridge residualization.
- Copy but never recompute boundary `0.058242447845091264` from `artifacts/batch-null-calibration/batch-null-calibration-20260821-001` after hash verification.
- Use namespace `batch-f1-null-transfer`; retain fixture/residual/permutation UInt64 seeds, 1,000-row residual CSVs, and 199-value null arrays.
- `STOP`: malformed/exception evidence or >67 low p-values; `NARROW`: <85 null-like batches; `PASS`: otherwise.
- Official output: `artifacts/batch-f1-null-transfer/batch-f1-null-transfer-20260824-001`; do not recalibrate, run another fixture, or begin package work regardless of outcome. A NARROW or STOP result is not repaired in this pass.

---

### Task 1: Implement and test the F1 runner

**Files:** Create `research/gate0/f1_transfer_runner.py` and `tests/gate0/test_f1_transfer_runner.py`.

**Interfaces:** `F1TransferConfig` defaults to batches 100, replications 10, rows 1_000, permutations 199, five splits, five knots, degree 3, Ridge alpha 1 (same shape as `F5TransferConfig`/`F6TransferConfig`). `run_f1_transfer(output_dir: Path, run_id: str, config: F1TransferConfig) -> pd.DataFrame` returns rows with F1/pair identity, batch/replication, observed dCor/p-value, residual/null relative paths, three seeds, warnings, exceptions, namespace, and run ID.

- [ ] **Step 1: Write failing tests**

Test a 2 x 3 x 100-row config; spy on `generate_fixture` and assert exactly six calls of `("F1", 100)`, a single output pair `F1/X1/X2`, each residual CSV has 100 rows with columns `X1,X2`, all six `(batch, replication)` identities exist, namespace is `batch-f1-null-transfer`, phase is `f1-null-transfer`, and every successful null-array path exists with shape `(19,)`. Add failure-retention and non-empty-output-refusal tests matching the F6 runner's pattern.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f1_transfer_runner.py -v --basetemp .pytest-f1-runner-red`. Expect import failure for `f1_transfer_runner`.

- [ ] **Step 3: Implement minimal runner**

Copy `f6_transfer_runner.py`'s structure exactly, changing only: namespace `batch-f1-null-transfer`, phase `f1-null-transfer`, fixture id `F1`, pair `("X1", "X2")`, and the `generate_fixture("F1", ...)` call.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-f1-runner-green`, then Ruff over both new files; expect clean. Commit `research/gate0/f1_transfer_runner.py` and its test as `feat: run F1 independence null transfer`.

### Task 2: Implement and test hash-pinned F1 reporting

**Files:** Create `research/gate0/f1_transfer_report.py` and `tests/gate0/test_f1_transfer_report.py`.

**Interfaces:** `write_f1_transfer_report(records: pd.DataFrame, output_dir: Path, run_id: str, calibration_dir: Path, config: F1TransferConfig) -> Path`, built the same way as `write_f6_transfer_report` -- consumes `_verified_calibration`, `summarize_batches`, `check_confirmation`, and `batch_terminal_status`; writes summary, plot, manifest, memo, and complete state.

- [ ] **Step 1: Write failing tests**

Create a synthetic READY calibration, then assert a complete 85-batch F1 frame yields PASS and copies boundary `0.058242447845091264`. Tamper with calibration records and assert a SHA-256 refusal before output. Also test 84 batches gives NARROW, 68 low p-values gives STOP, wrong fixture/pair/phase/namespace is rejected, and a missing residual sample path gives `ValueError`.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f1_transfer_report.py -v --basetemp .pytest-f1-report-red`. Expect import failure for `f1_transfer_report`.

- [ ] **Step 3: Implement report**

Copy `f6_transfer_report.py`'s structure exactly, changing only the fixture/pair/phase/namespace constants and output filenames (`f1-transfer-summary.csv`, `plots/f1-batch-classifications.png`, `f1-transfer-memo.md`). Memo must identify the F1 independence null transfer, name the adjustment set `(X3, X4, X5, X6)`, note it is signal-free by construction, and forbid recalibration, alternate fixtures, and package work.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-f1-report-green`, then Ruff over both new files; expect clean. Commit as `feat: report F1 independence null transfer`.

### Task 3: Add frozen CLI, preflight, execute once, and commit evidence

**Files:** Create `scripts/run_f1_independence_null_transfer.py`; create `tests/gate0/test_f1_transfer_cli.py`; create evidence pointer `docs/evidence/f1-independence-null-transfer-batch-f1-null-transfer-20260824-001.md` after run.

**Interfaces:** CLI accepts only `--output-dir` and non-empty `--run-id`; hard-codes approved calibration directory and `F1TransferConfig()`.

- [ ] **Step 1: Write failing CLI tests**

Assert a tampered calibration causes return code 2 before output creation. Assert default-run success in a temporary directory and a second attempt at the same output returns 2. Assert there are no flags for dimensions, thresholds, fixture IDs, pair names, or calibration path.

- [ ] **Step 2: Verify RED and implement narrow CLI**

Run the focused suite; expect a missing CLI import. Copy `scripts/run_f6_residual_null_transfer.py`'s structure exactly, changing only the fixture-specific imports, config type, runner/report function names, and printed label (`F1 INDEPENDENCE NULL TRANSFER`). Reuse the same frozen calibration hashes (same calibration parent as every prior study).

- [ ] **Step 3: Preflight, commit source, and run exactly once**

Run full pytest with basetemp `.pytest-f1-preflight`, then `ruff check research tests scripts`; expect full PASS and lint clean. Commit new runner/report/CLI/tests as `feat: add F1 independence null transfer runner`. Confirm the official output directory is absent or empty, record the exact commit SHA, then run exactly:

```text
PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_f1_independence_null_transfer.py --output-dir artifacts/batch-f1-null-transfer/batch-f1-null-transfer-20260824-001 --run-id batch-f1-null-transfer-20260824-001
```

Launch exactly once; no retry.

- [ ] **Step 4: Commit immutable evidence**

Create an evidence pointer linking manifest, records, summary, memo, plot, residual samples, arrays, calibration hashes/boundary, result, and governance. Commit artifact tree and pointer as `docs: record F1 independence null transfer evidence`.

### Task 4: Independently review committed F1 evidence

**Files:** Read the committed F1 artifact tree and its evidence pointer.

- [ ] **Step 1: Recompute all evidence from raw files**

Without importing the project runner/report/policy modules: verify exactly 1,000 unique `(batch, replication)` identities covering `0..99 x 0..9`; F1/X1/X2 identity and namespace on every row; 1,000 residual CSVs each with 1,000 X1/X2 rows; 1,000 199-value finite arrays; all hashes and derived seeds; p guards, batch medians, copied-boundary classifications, low-p count, and terminal outcome, reapplied independently.

- [ ] **Step 2: Report governance result**

Approve only complete, hash-consistent, F1-only evidence whose independently recomputed terminal outcome matches the retained manifest.

- If `PASS`: record that the frozen workflow correctly returns null on the simplest possible baseline. This does not itself authorize the next untested structure -- that remains a separate, later owner decision.
- If `NARROW` or `STOP`: record it as the most concerning possible finding in this sequence (a spurious result with no engineered relationship present) and stop for diagnosis; do not design a repair in the same pass.

## Self-review

Tasks 1--4 cover every fixed fixture, residualization, retention,
provenance, rule, CLI, evidence, and independent-review requirement in the
spec, built as a close, deliberately unoriginal copy of the already-reviewed
F6 null-transfer implementation with only the fixture and pair changed. No
placeholders, threshold overrides, or repair-basis work appear.
