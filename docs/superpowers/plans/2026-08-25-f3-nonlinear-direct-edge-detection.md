# F3 Nonlinear Direct-Edge Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute one immutable 100 x 10 F3 nonlinear direct-edge detection study at 1,000 rows, using the unmodified general-purpose residualizer and the unmodified fixture-agnostic F4 detection policy.

**Architecture:** A dedicated runner generates F3 only, cross-fits `X1`/`X2` residuals (adjustment set `X3, X4, X5, X6`, all signal-free by construction), and retains all residual samples and dCor arrays -- built the same way as `f7_collider_detection_runner.py`. A dedicated report applies the unmodified `F4LinkConfig` detection policy and pins only the single raw-reference calibration parent, built the same way as `f7_collider_detection_report.py`.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, matplotlib, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-25-f3-nonlinear-direct-edge-detection-design.md`

## Global Constraints

- Existing F3 only (no fixture code changes); pair `(X1, X2)`; adjust for `(X3, X4, X5, X6)` via the existing general-purpose `cross_fitted_pair_residuals` (spline/Ridge) -- not the F5 quadratic-repair basis.
- Exactly 100 batches x 10 replications x 1,000 rows; 199 permutations; five-fold, five-knot cubic-spline/Ridge residualization.
- Copy but never recompute boundary `0.058242447845091264` from `artifacts/batch-null-calibration/batch-null-calibration-20260821-001` after hash verification.
- Reuse `research/gate0/f4_link_policy.py` (`F4LinkConfig`, `summarize_detection_batches`, `check_detection`, `detection_terminal_status`) unchanged -- do not create a new policy module. Detected batch: median dCor > boundary and >=8/10 p-values <=0.05. PASS >=85 detected batches; NARROW complete but below 85; STOP incomplete/malformed/exception/invalidating-warning evidence.
- Use namespace `batch-f3-nonlinear-direct-edge-detection`; retain fixture/residual/permutation UInt64 seeds, 1,000-row residual CSVs, and 199-value null arrays.
- Official output: `artifacts/batch-f3-nonlinear-direct-edge-detection/batch-f3-nonlinear-direct-edge-detection-20260825-001`; do not recalibrate, run another fixture, or begin package work regardless of outcome.

---

### Task 1: Implement and test the F3 runner

**Files:** Create `research/gate0/f3_nonlinear_direct_edge_detection_runner.py` and `tests/gate0/test_f3_nonlinear_direct_edge_detection_runner.py`.

**Interfaces:** Reuse `F4LinkConfig` directly for dimensions (do not duplicate it), exactly as the F7 runner did. `run_f3_nonlinear_direct_edge_detection(output_dir: Path, run_id: str, config: F4LinkConfig) -> pd.DataFrame` returns rows with F3/pair identity, batch/replication, observed dCor/p-value, residual/null relative paths, three seeds, warnings, exceptions, namespace, and run ID.

- [ ] **Step 1: Write failing tests**

Test a 2 x 3 x 100-row `F4LinkConfig` config; spy on `generate_fixture` and assert exactly six calls of `("F3", 100)`, a single output pair `F3/X1/X2`, each residual CSV has 100 rows with columns `X1,X2`, all six `(batch, replication)` identities exist, namespace is `batch-f3-nonlinear-direct-edge-detection`, phase is `f3-nonlinear-direct-edge-detection`, and every successful null-array path exists with shape `(19,)`. Add failure-retention and non-empty-output-refusal tests matching the F7 runner's pattern.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f3_nonlinear_direct_edge_detection_runner.py -v --basetemp .pytest-f3-runner-red`. Expect import failure for `f3_nonlinear_direct_edge_detection_runner`.

- [ ] **Step 3: Implement minimal runner**

Copy `f7_collider_detection_runner.py`'s structure exactly, changing namespace `batch-f3-nonlinear-direct-edge-detection`, phase `f3-nonlinear-direct-edge-detection`, fixture id `F3`, pair `("X1", "X2")`, and the `generate_fixture("F3", ...)` call.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-f3-runner-green`, then Ruff over both new files; expect clean. Commit as `feat: run F3 nonlinear direct-edge detection`.

### Task 2: Implement and test hash-pinned F3 reporting

**Files:** Create `research/gate0/f3_nonlinear_direct_edge_detection_report.py` and `tests/gate0/test_f3_nonlinear_direct_edge_detection_report.py`.

**Interfaces:** `write_f3_nonlinear_direct_edge_detection_report(records: pd.DataFrame, output_dir: Path, run_id: str, calibration_dir: Path, config: F4LinkConfig) -> Path`, built the same way as `write_f7_collider_detection_report` -- reuses `summarize_detection_batches`, `check_detection`, and `detection_terminal_status` from `f4_link_policy.py` unchanged, and `_verified_calibration` from `batch_null_report.py`, pinning only the single calibration parent.

- [ ] **Step 1: Write failing tests**

Create a synthetic READY calibration. Assert: 85 detected batches with complete evidence yields PASS and copies boundary `0.058242447845091264`; 84 yields NARROW; a retained exception or warning yields STOP regardless of count; tampered calibration records are refused with a SHA-256 message before any output; wrong fixture/pair/phase/namespace is rejected; a missing residual sample or null array is rejected.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f3_nonlinear_direct_edge_detection_report.py -v --basetemp .pytest-f3-report-red`. Expect import failure for `f3_nonlinear_direct_edge_detection_report`.

- [ ] **Step 3: Implement report**

Copy `f7_collider_detection_report.py`'s structure exactly, changing only the fixture/pair/phase/namespace constants and output filenames (`f3-nonlinear-direct-edge-detection-summary.csv`, `plots/f3-nonlinear-direct-edge-detections.png`, `f3-nonlinear-direct-edge-detection-memo.md`). Memo must identify the F3 structure and its rationale as the complement to F5's STOP, and forbid recalibration, alternate fixtures, and package work.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-f3-report-green`, then Ruff over both new files; expect clean. Commit as `feat: report F3 nonlinear direct-edge detection`.

### Task 3: Add frozen CLI, preflight, execute once, and commit evidence

**Files:** Create `scripts/run_f3_nonlinear_direct_edge_detection.py`; create `tests/gate0/test_f3_nonlinear_direct_edge_detection_cli.py`; create evidence pointer `docs/evidence/f3-nonlinear-direct-edge-detection-batch-f3-nonlinear-direct-edge-detection-20260825-001.md` after run.

**Interfaces:** CLI accepts only `--output-dir` and non-empty `--run-id`; hard-codes the approved calibration directory (with hash pins, matching every prior narrow CLI in this project) and `F4LinkConfig()`.

- [ ] **Step 1: Write failing CLI tests**

Assert a tampered calibration causes return code 2 before output creation. Assert default-run success in a temporary directory and a second attempt at the same output returns 2. Assert there are no flags for dimensions, thresholds, fixture IDs, pair names, or calibration path.

- [ ] **Step 2: Verify RED and implement narrow CLI**

Run the focused suite; expect a missing CLI import. Copy `scripts/run_f7_collider_detection.py`'s structure exactly, changing only the fixture-specific imports, config type, runner/report function names, and printed label (`F3 NONLINEAR DIRECT-EDGE DETECTION`). Reuse the same frozen calibration hashes.

- [ ] **Step 3: Preflight, commit source, and run exactly once**

Run full pytest with basetemp `.pytest-f3-preflight`, then `ruff check research tests scripts`; expect full PASS and lint clean. Commit new runner/report/CLI/tests as `feat: add F3 nonlinear direct-edge detection runner`. Confirm the official output directory is absent or empty, record the exact commit SHA, then run exactly:

```text
PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_f3_nonlinear_direct_edge_detection.py --output-dir artifacts/batch-f3-nonlinear-direct-edge-detection/batch-f3-nonlinear-direct-edge-detection-20260825-001 --run-id batch-f3-nonlinear-direct-edge-detection-20260825-001
```

Launch exactly once; no retry.

- [ ] **Step 4: Commit immutable evidence**

Create an evidence note stating the exact outcome, calibration hashes/boundary, detection counts, and governance limits from the spec's Interpretation section. Commit artifact tree and note as `docs: record F3 nonlinear direct-edge detection evidence`.

### Task 4: Independently review committed F3 evidence

**Files:** Read the committed F3 artifact tree and its evidence note.

- [ ] **Step 1: Recompute all evidence from raw files**

Without importing the project runner/report/policy modules: verify exactly 1,000 unique `(batch, replication)` identities covering `0..99 x 0..9`; F3/X1/X2 identity and namespace on every row; 1,000 residual CSVs each with 1,000 X1/X2 rows; 1,000 199-value finite arrays; all hashes and derived seeds; observed dCor and permutation p-values recomputed directly from retained residuals and null arrays; detected-batch count and terminal outcome, reapplied independently using the detection rule.

- [ ] **Step 2: Report governance result**

Approve only complete, hash-consistent evidence whose independently recomputed terminal outcome matches the retained manifest.

- If `PASS`: record that the unrepaired general-purpose workflow correctly detects raw nonlinear dependence absent adjustment complications, confirming F5's STOP was an adjustment-specific limitation. This does not itself authorize the next untested structure.
- If `NARROW` or `STOP`: record it as a more fundamental limitation than F5's STOP and stop for diagnosis; do not design a follow-up in the same pass.

## Self-review

Tasks 1--4 cover every fixed fixture, residualization, retention, provenance, rule, CLI, evidence, and independent-review requirement in the spec, reusing the already-reviewed F4 detection policy and F7 runner/report shapes unchanged rather than inventing new machinery. No placeholders, threshold overrides, or repair-basis work appear.
