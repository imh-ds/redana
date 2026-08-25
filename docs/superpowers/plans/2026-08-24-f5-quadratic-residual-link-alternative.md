# F5 Quadratic-Residual-Link Alternative Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute one immutable Candidate 1 sensitivity study -- the F5 quadratic common-cause null with one planted nonlinear residual link -- at 1,000 rows, using the existing raw-plus-square repair basis, and assess detection.

**Architecture:** A dedicated generator/runner produces only the fixed Candidate 1 DGP and calls the already-implemented `cross_fitted_pair_quadratic_residuals` residualizer unchanged. Detection reuses the existing fixture-agnostic `F4LinkConfig` policy dataclasses unchanged -- no new policy module. A dedicated report applies that policy and pins both the raw-reference calibration and the reviewed F5 quadratic-repair PASS evidence.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, matplotlib, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-24-f5-quadratic-residual-link-alternative-design.md`

## Global Constraints

- Use exactly `Z=X3`, `P=0.7*(Z^2-1)`, `X1=P+e1`, `X2=P+0.7*(e1^2-1)+e2`, plus independent `X4`--`X6`; test `(X1,X2)` adjusting `(X3,X4,X5,X6)` with the existing `cross_fitted_pair_quadratic_residuals` (raw-plus-square basis, no interactions, no splines, no new residualizer code).
- Use 100 batches x 10 replications x 1,000 rows, five shuffled folds, Ridge alpha 1, all held-out residual rows, and 199 permutations -- identical dimensions to the F5 quadratic-repair study.
- Reuse `research/gate0/f4_link_policy.py` (`F4LinkConfig`, `summarize_detection_batches`, `check_detection`, `detection_terminal_status`) unchanged; do not create a second policy module. Detected batch: median dCor > `0.058242447845091264` and >=8/10 p-values <=0.05. PASS >=85 detected batches; NARROW complete but below 85; STOP incomplete/malformed/exception/invalidating-warning evidence, which takes precedence over the batch count.
- Namespace is `batch-f5-quadratic-residual-link`; official run is `batch-f5-quadratic-residual-link-20260824-001` in its specified artifact directory; refuse non-empty output.
- Pin the raw-reference calibration and the reviewed F5 quadratic-repair PASS evidence by exact SHA-256 (values in the spec); do not recalibrate, alter the DGP or coefficient, rerun automatically, or begin package work.

---

### Task 1: Implement the Candidate 1 generator and runner

**Files:** Create `research/gate0/f5_quadratic_link_runner.py`; create `tests/gate0/test_f5_quadratic_link_runner.py`.

**Interfaces:** `generate_f5_quadratic_link_fixture(rows: int, seed: int) -> pd.DataFrame` builds and standardizes the Candidate 1 frame directly (do not route through the shared `FIXTURES` registry in `fixtures.py`, which has no slot for this DGP -- generate `Z=X3`, errors `e1,e2,e4,e5,e6` from one `rng.standard_normal` draw, matching the seeding convention of `generate_f4_link_fixture`). `run_f5_quadratic_link(output_dir: Path, run_id: str, config: F4LinkConfig) -> pd.DataFrame` creates `records.csv` and `manifest-input.json`, reusing `F4LinkConfig` from `research/gate0/f4_link_policy.py` for dimensions.

- [ ] **Step 1: Write failing generator/runner tests**

For a `F4LinkConfig(batches=2, replications_per_batch=3, rows=100, permutations=19)`-shaped config, assert: the generator produces exactly `X1 = P + e1` and `X2 = P + 0.7*(e1**2-1) + e2` with `P = 0.7*(e3**2-1)` and `X3 = e3` before standardization, then standardizes the full frame once; the runner records fixture identity `F5-quadratic-residual-link`, pair `X1`/`X2`, phase `f5-quadratic-residual-link`, namespace `batch-f5-quadratic-residual-link`, all six `(batch, replication)` identities, three UInt64 seed columns, 100-row two-column residual CSVs, and 19-value `.npy` null arrays. Spy on residualization and assert the runner calls `cross_fitted_pair_quadratic_residuals` only, never the spline residualizer. Inject one residualization exception and assert its record is retained while later cells complete. Assert non-empty output is refused without changing the sentinel file.

- [ ] **Step 2: Verify RED**

Run: `C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f5_quadratic_link_runner.py -v --basetemp .pytest-f5-quadratic-link-red`.

Expected: missing `f5_quadratic_link_runner` import.

- [ ] **Step 3: Implement the generator and runner**

Base the runner on the shape of `f4_link_runner.py` and `f5_quadratic_repair_runner.py`: derive `fixture_seed`/`residual_seed`/`permutation_seed` per cell from `derive_seed(_NAMESPACE, batch, replication, component)`; build the frame with one `rng = np.random.default_rng(fixture_seed)` draw of six standard-normal columns; compute `p = 0.7 * (e3**2 - 1)`; set `x1 = p + e1`, `x2 = p + 0.7 * (e1**2 - 1) + e2`; assemble `X3=e3, X4=e4, X5=e5, X6=e6`; standardize once via `(frame - frame.mean()) / frame.std(ddof=0)`; call `cross_fitted_pair_quadratic_residuals(frame, "X1", "X2", gate0_config, residual_seed % (2**32))`; run `permutation_distance_correlation` on the held-out residuals; retain residual CSV and null array atomically exactly as the existing runners do. Do not import or call `cross_fitted_pair_residuals` (the spline residualizer).

- [ ] **Step 4: Verify GREEN and commit**

Run the focused runner tests and `C:\tmp\scova-v4-test\Scripts\ruff.exe check research/gate0/f5_quadratic_link_runner.py tests/gate0/test_f5_quadratic_link_runner.py`; expect clean. Commit as `feat: run F5 quadratic residual-link alternative`.

### Task 2: Implement the hash-pinned detection report

**Files:** Create `research/gate0/f5_quadratic_link_report.py`; create `tests/gate0/test_f5_quadratic_link_report.py`.

**Interfaces:** `write_f5_quadratic_link_report(records: pd.DataFrame, output_dir: Path, run_id: str, f5_quadratic_repair_dir: Path, calibration_dir: Path, config: F4LinkConfig) -> Path` writes summary, plot, manifest, memo, and state, reusing `summarize_detection_batches` / `check_detection` / `detection_terminal_status` from `f4_link_policy.py` unchanged.

- [ ] **Step 1: Write failing report tests**

Build hash-valid synthetic calibration and F5-quadratic-repair-PASS parent directories (`terminal_outcome="PASS"`, `fixture_id="F5"`, `pair=["X1","X2"]`, `phase="f5-quadratic-repair"`, `confirmation_check.null_like_batch_count=90`, `confirmation_check.low_p_value_count=44`). Assert: 85 detected batches with complete evidence yields PASS; 84 yields NARROW; a retained exception or warning yields STOP regardless of count; each manifest embeds both pinned parent hash blocks and the copied boundary; wrong phase/fixture/pair/namespace, a missing residual CSV or null array, and tampered parent evidence all refuse report output before writing anything.

- [ ] **Step 2: Verify RED**

Run: `C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/gate0/test_f5_quadratic_link_report.py -v --basetemp .pytest-f5-quadratic-link-report-red`.

Expected: missing report import.

- [ ] **Step 3: Implement the report**

Follow the shape of `f4_link_report.py`: validate records against the frozen fixture/pair/phase/namespace identity; hash-verify the raw calibration (reuse `_verified_calibration` from `batch_null_report.py`) and the F5-quadratic-repair PASS parent by the exact hashes in the spec, checking `terminal_outcome=="PASS"`, `fixture_id=="F5"`, `pair==["X1","X2"]`, `phase=="f5-quadratic-repair"`, `null_like_batch_count==90`, `low_p_value_count==44`; apply `summarize_detection_batches`/`check_detection`/`detection_terminal_status` unchanged; write summary CSV, plot, manifest (embedding both pinned parent hash blocks, the copied boundary, and `detection_check`), memo (wording that limits a PASS to this one planted nonlinear link under this repair basis), and `run_state.json`.

- [ ] **Step 4: Verify GREEN and commit**

Run focused report tests, all F5-quadratic-repair and F4-link tests, and Ruff on `research` and `tests`; expect clean. Commit as `feat: report F5 quadratic residual-link alternative`.

### Task 3: Add narrow CLI, preflight, exact run, and evidence

**Files:** Create `scripts/run_f5_quadratic_residual_link_alternative.py`; create `tests/gate0/test_f5_quadratic_link_cli.py`; create `docs/evidence/f5-quadratic-residual-link-alternative-batch-f5-quadratic-residual-link-20260824-001.md` after the run.

- [ ] **Step 1: Write failing CLI tests**

Assert altered raw-calibration or F5-quadratic-repair-PASS provenance returns 2 before any output is created; the default CLI succeeds in a temporary output directory and refuses reuse of a non-empty one; only `--output-dir` and `--run-id` are accepted (no DGP, dimension, threshold, coefficient, or parent-path overrides).

- [ ] **Step 2: Verify RED and implement the narrow CLI**

Run the focused suite; expect a missing CLI import. Hard-code both approved parent directories (`artifacts/batch-null-calibration/batch-null-calibration-20260821-001`, `artifacts/batch-f5-quadratic-repair/batch-f5-quadratic-repair-20260824-001`), verify them, use `F4LinkConfig()` defaults only, run the runner then the report, print a single `F5 QUADRATIC RESIDUAL LINK ...` outcome line, and return 2 on any refusal.

- [ ] **Step 3: Preflight, commit source, execute once**

Run full pytest with a unique `.pytest-f5-quadratic-link-preflight` base temp and `C:\tmp\scova-v4-test\Scripts\ruff.exe check research tests scripts`; expect all green/clean. Commit source as `feat: add F5 quadratic residual-link alternative runner`. Confirm the official output directory is absent or empty, then run exactly:

```text
C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_f5_quadratic_residual_link_alternative.py --output-dir artifacts/batch-f5-quadratic-residual-link/batch-f5-quadratic-residual-link-20260824-001 --run-id batch-f5-quadratic-residual-link-20260824-001
```

(Use whichever interpreter/`PYTHONPATH` combination the F5 quadratic-repair run's evidence note recorded as actually available in this environment; record the exact command used, verbatim, in the evidence note.) Do not alter the command, run identity, source, seed namespace, or output path. Launch exactly once; no retry.

- [ ] **Step 4: Commit evidence**

Commit the artifact tree and an evidence note stating the exact outcome, both pinned parent hash blocks, the copied boundary, detected-batch and low-p counts, and the governance limits from the spec's Interpretation section, as `docs: record F5 quadratic residual-link alternative evidence`.

### Task 4: Independently review committed alternative evidence

- [ ] **Step 1: Recompute evidence from raw files**

Without importing the project runner/report/policy modules: parse `records.csv`, manifests, run state, and the batch summary directly; re-derive each seed from the frozen identity string; recompute dCor and the permutation p-value from each retained residual CSV and null array; recompute SHA-256 for current and both parent evidence sets against the pinned values; regroup records by batch and reapply the detection rule (median dCor strictly above `0.058242447845091264`, >=8/10 p-values <=0.05, >=85 detected batches for PASS) independently.

- [ ] **Step 2: Apply governance**

Approve only complete, hash-consistent, exception-free evidence whose independently recomputed terminal outcome matches the retained manifest. Record that a PASS supports detection of this one planted nonlinear residual link under this one repair basis only; it authorizes no automatic package work, no general nonlinear-power claim, and no further simulation family without a separate owner decision.

## Self-review

Task 1 reuses the already-implemented quadratic residualizer and adds only the fixed Candidate 1 generator/runner. Task 2 reuses the existing fixture-agnostic F4 detection policy unchanged and adds only provenance/report wiring pinned to both approved parents. Task 3 supplies a non-parameterizable CLI, preflight, and the single official execution. Task 4 supplies independent raw recomputation and governance. The plan contains no new residualizer, no new detection policy, no calibration, no retry, and no package-work step.
