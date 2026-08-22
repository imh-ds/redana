# F4 Residual-Link Alternative Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute one immutable F4-plus-residual-link sensitivity study at 1,000 rows and assess clear residual-dependence detection.

**Architecture:** A dedicated generator/runner produces only the fixed F4 residual-link DGP and retains each residual sample/dCor array. A dedicated report applies the precommitted detection policy and pins the reviewed F4-null and raw-reference calibration provenance.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, matplotlib, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-22-f4-residual-link-alternative-design.md`

## Global Constraints

- Use exactly `X1=e1`, `X2=.7*X1+e2`, `X3=.7*X2+.7*e1+e3`, plus independent X4--X6; test X1/X3 adjusting X2/X4/X5/X6.
- Use 100 x 10 x 1,000 rows, five folds, five-knot cubic spline/Ridge alpha 1, all residual rows, and 199 permutations.
- Namespace is `batch-f4-residual-link`; official run is `batch-f4-residual-link-20260822-001` in its specified artifact directory.
- Detected batch: median dCor > `.058242447845091264` and >=8/10 p-values <=.05. PASS >=85 detected batches; NARROW complete but below 85; STOP incomplete/malformed/exception/invalidating-warning evidence.
- Pin reviewed F4-null and raw-reference calibration hashes; do not recalibrate, alter signal or residualizer, rerun automatically, or begin package work.

---

### Task 1: Implement the residual-link runner and policy

**Files:** Create `research/gate0/f4_link_runner.py`, `research/gate0/f4_link_policy.py`, `tests/gate0/test_f4_link_runner.py`, and `tests/gate0/test_f4_link_policy.py`.

**Interfaces:** `F4LinkConfig` defaults to frozen dimensions; `run_f4_link(output_dir: Path, run_id: str, config: F4LinkConfig) -> pd.DataFrame`; `summarize_detection_batches(records, config)`, `check_detection(batches, records, boundary, config)`, and `detection_terminal_status(check) -> str`.

- [ ] **Step 1: Write failing policy/runner tests**

Test a 2x3x100-row config. Assert generator creates the exact equations and F4-link identity; runner records phase `f4-residual-link`, pair X1/X3, namespace, all identities, residual CSVs, arrays, and UInt64 seeds. Assert a synthetic batch with 8/10 low p-values and median above boundary is detected; 7/10 is not; 85 detected batches passes; 84 narrows; missing/exception evidence stops.

- [ ] **Step 2: Verify RED**

Run `C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f4_link_policy.py tests/gate0/test_f4_link_runner.py -v --basetemp .pytest-f4-link-red`; expect missing-module imports.

- [ ] **Step 3: Implement minimal policy and runner**

Generate each frame from three derived seeds/normal errors, standardize exactly once, cross-fit residuals, run dCor on all rows, atomically retain `residual_samples/batch-{b}-replication-{r}.csv` and `null_statistics/batch-{b}-replication-{r}.npy`, retain a per-cell exception and continue, then write records/input manifest. Use distinct fixture/residual/permutation seeds and deterministic UInt64 storage.

- [ ] **Step 4: Add failure/reuse tests**

Inject one residualization failure and require retention/continuation. Assert nonempty output refusal without modification.

- [ ] **Step 5: Verify GREEN and commit**

Run focused tests with `.pytest-f4-link-green` and Ruff on all four new files; expect clean. Commit as `feat: run F4 residual link alternative`.

### Task 2: Implement hash-pinned detection report

**Files:** Create `research/gate0/f4_link_report.py` and `tests/gate0/test_f4_link_report.py`.

**Interfaces:** `write_f4_link_report(records: pd.DataFrame, output_dir: Path, run_id: str, f4_null_dir: Path, calibration_dir: Path, config: F4LinkConfig) -> Path` writes summary, plot, manifest, memo, and state.

- [ ] **Step 1: Write failing report tests**

Create synthetic hash-valid F4-null and calibration evidence. Assert report pins both; 85 detected batches yields PASS; 84 yields NARROW; an exception yields STOP; tampering either parent records file refuses before report output. Reject wrong DGP identity/phase/pair/namespace/missing residual sample.

- [ ] **Step 2: Verify RED**

Run `C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f4_link_report.py -v --basetemp .pytest-f4-link-report-red`; expect missing module.

- [ ] **Step 3: Implement report and verify GREEN**

Validate parent manifests/hashes and F4-link records; copy boundary as effect threshold; compute detection policy; write manifest/memo explicitly limiting claim to one clear residual link. Run focused tests and Ruff; commit as `feat: report F4 residual link alternative`.

### Task 3: Add narrow CLI, preflight, exact run, and evidence

**Files:** Create `scripts/run_f4_residual_link_alternative.py`; modify F4-link tests; create `docs/evidence/f4-residual-link-alternative-batch-f4-residual-link-20260822-001.md` after run.

- [ ] **Step 1: Write failing CLI tests**

Assert altered F4-null or calibration provenance returns 2 before output creation; default CLI succeeds in a temporary output and refuses its reuse. Assert only `--output-dir` and `--run-id` exist.

- [ ] **Step 2: Verify RED and implement narrow CLI**

Run focused F4-link suites; expect missing CLI import. Hard-code both approved parent directories, verify them, use `F4LinkConfig()` only, run runner/report, print outcome, and return 2 on refusal. Expose no DGP, dimension, threshold, or path overrides.

- [ ] **Step 3: Preflight, commit source, execute once**

Run full pytest with `.pytest-f4-link-preflight` and `C:\tmp\scova-v4-test\Scripts\ruff.exe check research tests scripts`; expect PASS/clean. Commit source as `feat: add F4 residual link alternative runner`. Run exactly `C:\tmp\redana-batch-python\python.exe scripts/run_f4_residual_link_alternative.py --output-dir artifacts/batch-f4-residual-link/batch-f4-residual-link-20260822-001 --run-id batch-f4-residual-link-20260822-001`. Inspect before deletion/restart after detachment.

- [ ] **Step 4: Commit evidence**

Commit artifact tree and evidence pointer with all paths, parent hashes, boundary, detection counts/outcome, and governance as `docs: record F4 residual link alternative evidence`.

### Task 4: Independently review committed alternative evidence

- [ ] **Step 1: Recompute evidence**

Verify 1,000 identities, equations/DGP identity, X1/X3 phase/namespace, residual samples, arrays, seeds, parent hashes, batch detections, and terminal result.

- [ ] **Step 2: Apply governance**

Approve only complete, hash-consistent evidence. PASS supports detection of this one clear link; no automatic package work or power claims.

## Self-review

Tasks 1--4 cover fixed signal generation, detection policy, provenance, CLI/preflight/exact run, evidence, and independent review. No post-result tuning or unspecified configuration appears.
