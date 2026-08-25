# F7 Collider Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute one immutable 100 x 10 F7 collider-detection study at 1,000 rows, using the unmodified general-purpose residualizer and the unmodified fixture-agnostic F4 detection policy.

**Architecture:** A dedicated runner generates F7 only, cross-fits `X1`/`X2` residuals (adjustment set `X3, X4, X5, X6`, derived automatically), and retains all residual samples and dCor arrays -- built the same way as `f6_transfer_runner.py`. A dedicated report applies the unmodified `F4LinkConfig` detection policy (reused from `research/gate0/f4_link_policy.py`, already used for the F4 residual-link alternative and Candidate 1) and pins only the single raw-reference calibration parent -- there is no second "null" parent to match, since F7 is a standalone canonical structure.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, matplotlib, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-24-f7-collider-detection-design.md`

## Global Constraints

- Existing F7 only (no fixture code changes); pair `(X1, X2)`; adjust for `(X3, X4, X5, X6)` via the existing general-purpose `cross_fitted_pair_residuals` (spline/Ridge) -- not the F5 quadratic-repair basis.
- Exactly 100 batches x 10 replications x 1,000 rows; 199 permutations; five-fold, five-knot cubic-spline/Ridge residualization.
- Copy but never recompute boundary `0.058242447845091264` from `artifacts/batch-null-calibration/batch-null-calibration-20260821-001` after hash verification.
- Reuse `research/gate0/f4_link_policy.py` (`F4LinkConfig`, `summarize_detection_batches`, `check_detection`, `detection_terminal_status`) unchanged -- do not create a new policy module. Detected batch: median dCor > boundary and >=8/10 p-values <=0.05. PASS >=85 detected batches; NARROW complete but below 85; STOP incomplete/malformed/exception/invalidating-warning evidence.
- Use namespace `batch-f7-collider-detection`; retain fixture/residual/permutation UInt64 seeds, 1,000-row residual CSVs, and 199-value null arrays.
- Official output: `artifacts/batch-f7-collider-detection/batch-f7-collider-detection-20260824-001`; do not recalibrate, run another fixture, or begin package work regardless of outcome.

---

### Task 1: Implement and test the F7 runner

**Files:** Create `research/gate0/f7_collider_detection_runner.py` and `tests/gate0/test_f7_collider_detection_runner.py`.

**Interfaces:** `F7ColliderDetectionConfig` -- reuse the shape of `F4LinkConfig` (batches 100, replications 10, rows 1_000, permutations 199, five splits, five knots, degree 3, Ridge alpha 1, detection boundary/thresholds) by importing `F4LinkConfig` directly rather than duplicating it, exactly as Candidate 1's runner did. `run_f7_collider_detection(output_dir: Path, run_id: str, config: F4LinkConfig) -> pd.DataFrame` returns rows with F7/pair identity, batch/replication, observed dCor/p-value, residual/null relative paths, three seeds, warnings, exceptions, namespace, and run ID.

- [ ] **Step 1: Write failing tests**

Test a 2 x 3 x 100-row `F4LinkConfig` config; spy on `generate_fixture` and assert exactly six calls of `("F7", 100)`, a single output pair `F7/X1/X2`, each residual CSV has 100 rows with columns `X1,X2`, all six `(batch, replication)` identities exist, namespace is `batch-f7-collider-detection`, phase is `f7-collider-detection`, and every successful null-array path exists with shape `(19,)`. Add failure-retention and non-empty-output-refusal tests matching the F6 runner's pattern.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f7_collider_detection_runner.py -v --basetemp .pytest-f7-runner-red`. Expect import failure for `f7_collider_detection_runner`.

- [ ] **Step 3: Implement minimal runner**

Copy `f6_transfer_runner.py`'s structure, changing namespace `batch-f7-collider-detection`, phase `f7-collider-detection`, fixture id `F7`, pair `("X1", "X2")`, the `generate_fixture("F7", ...)` call, and importing `F4LinkConfig` for dimensions instead of defining a new config dataclass.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-f7-runner-green`, then Ruff over both new files; expect clean. Commit as `feat: run F7 collider detection`.

### Task 2: Implement and test hash-pinned F7 reporting

**Files:** Create `research/gate0/f7_collider_detection_report.py` and `tests/gate0/test_f7_collider_detection_report.py`.

**Interfaces:** `write_f7_collider_detection_report(records: pd.DataFrame, output_dir: Path, run_id: str, calibration_dir: Path, config: F4LinkConfig) -> Path`, built the same way as `f4_link_report.py`'s detection-policy application but pinning only the single calibration parent (no second matched-null parent), the way `f6_transfer_report.py` pins only calibration. Reuses `summarize_detection_batches`, `check_detection`, and `detection_terminal_status` from `f4_link_policy.py` unchanged, and `_verified_calibration` from `batch_null_report.py`.

- [ ] **Step 1: Write failing tests**

Create a synthetic READY calibration. Assert: 85 detected batches with complete evidence yields PASS and copies boundary `0.058242447845091264`; 84 yields NARROW; a retained exception or warning yields STOP regardless of count; tampered calibration records are refused with a SHA-256 message before any output; wrong fixture/pair/phase/namespace is rejected; a missing residual sample or null array is rejected.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f7_collider_detection_report.py -v --basetemp .pytest-f7-report-red`. Expect import failure for `f7_collider_detection_report`.

- [ ] **Step 3: Implement report**

Follow the shape of `f4_link_report.py`'s detection-policy application (validate identity, verify calibration, apply `summarize_detection_batches`/`check_detection`/`detection_terminal_status`, apply the STOP-on-warning-or-exception override) combined with `f6_transfer_report.py`'s single-parent provenance pinning (no second parent). Write `f7-collider-detection-summary.csv`, `plots/f7-collider-detections.png`, manifest, `f7-collider-detection-memo.md`, and run state. Memo must identify the collider structure and its expected-detection rationale, and forbid recalibration, alternate fixtures, and package work.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-f7-report-green`, then Ruff over both new files; expect clean. Commit as `feat: report F7 collider detection`.

### Task 3: Add frozen CLI, preflight, execute once, and commit evidence

**Files:** Create `scripts/run_f7_collider_detection.py`; create `tests/gate0/test_f7_collider_detection_cli.py`; create evidence pointer `docs/evidence/f7-collider-detection-batch-f7-collider-detection-20260824-001.md` after run.

**Interfaces:** CLI accepts only `--output-dir` and non-empty `--run-id`; hard-codes the approved calibration directory (with hash pins, matching every prior narrow CLI in this project) and `F4LinkConfig()`.

- [ ] **Step 1: Write failing CLI tests**

Assert a tampered calibration causes return code 2 before output creation. Assert default-run success in a temporary directory and a second attempt at the same output returns 2. Assert there are no flags for dimensions, thresholds, fixture IDs, pair names, or calibration path.

- [ ] **Step 2: Verify RED and implement narrow CLI**

Run the focused suite; expect a missing CLI import. Hard-code the approved calibration directory and its frozen hashes/boundary, verify it, use `F4LinkConfig()` defaults only, run the runner then the report, print a single `F7 COLLIDER DETECTION ...` outcome line, and return 2 on any refusal.

- [ ] **Step 3: Preflight, commit source, and run exactly once**

Run full pytest with basetemp `.pytest-f7-preflight`, then `ruff check research tests scripts`; expect full PASS and lint clean. Commit new runner/report/CLI/tests as `feat: add F7 collider detection runner`. Confirm the official output directory is absent or empty, record the exact commit SHA, then run exactly:

```text
PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_f7_collider_detection.py --output-dir artifacts/batch-f7-collider-detection/batch-f7-collider-detection-20260824-001 --run-id batch-f7-collider-detection-20260824-001
```

Launch exactly once; no retry.

- [ ] **Step 4: Commit immutable evidence**

Create an evidence note stating the exact outcome, calibration hashes/boundary, detection counts, and governance limits from the spec's Interpretation section. Commit artifact tree and note as `docs: record F7 collider detection evidence`.

### Task 4: Independently review committed F7 evidence

**Files:** Read the committed F7 artifact tree and its evidence note.

- [ ] **Step 1: Recompute all evidence from raw files**

Without importing the project runner/report/policy modules: verify exactly 1,000 unique `(batch, replication)` identities covering `0..99 x 0..9`; F7/X1/X2 identity and namespace on every row; 1,000 residual CSVs each with 1,000 X1/X2 rows; 1,000 199-value finite arrays; all hashes and derived seeds; observed dCor and permutation p-values recomputed directly from retained residuals and null arrays; detected-batch count and terminal outcome, reapplied independently using the detection rule (median dCor strictly above `0.058242447845091264`, >=8/10 p-values <=0.05, >=85 detected batches for PASS).

- [ ] **Step 2: Report governance result**

Approve only complete, hash-consistent evidence whose independently recomputed terminal outcome matches the retained manifest.

- If `PASS`: record that the frozen workflow correctly detects this collider-induced dependence. This does not itself authorize the next untested structure -- that remains a separate, later owner decision.
- If `NARROW` or `STOP`: record it and stop for diagnosis; do not design a follow-up in the same pass.

## Self-review

Tasks 1--4 cover every fixed fixture, residualization, retention, provenance, rule, CLI, evidence, and independent-review requirement in the spec, reusing the already-reviewed F4 detection policy and F6 runner/report shapes unchanged rather than inventing new machinery. No placeholders, threshold overrides, or repair-basis work appear.
