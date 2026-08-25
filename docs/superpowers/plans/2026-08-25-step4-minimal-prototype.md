# Step 4 Minimal Statistical Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the six components `outline/plan.md` §4 requires for the minimal, reusable residual-dependence prototype, and run one first synthetic validation scenario answering "does the core mechanism work?" -- nothing more.

**Architecture:** A new top-level package `redana/`, sibling to the disposable `research/` tree, holding six small modules: promoted (copied, not imported) cross-fitted residualization and dCor/permutation code, a native-Python EBIC-selected graphical-lasso incumbent network, BH-FDR multiplicity control, precision/recall/F1 scoring, and a thin orchestration entry point that ties them together for one dataset. A single script runs one frozen synthetic scenario (a small network mixing linear and pure-nonlinear edges) end-to-end and reports scoring for both the incumbent network and the residual layer.

**Tech Stack:** Python, NumPy, pandas, scikit-learn, dcor, pytest, Ruff.

**Charter:** `docs/superpowers/specs/2026-08-25-step4-minimal-prototype-charter.md` (approved: promote-by-copy, native Python EBIC-glasso).

## Global Constraints

- Exactly the six components `plan.md` §4 lists, no more: frozen incumbent linear network, pair-specific cross-fitted residualization, an ordinary nonlinear dependence statistic on residual pairs, a permutation/null procedure, BH-FDR multiplicity control, simulation scoring. Do not add stability rendering, edge typology, detectability reporting, mixed-data handling, sophisticated visualization, or functional-form classification -- all explicitly deferred by `plan.md` §4.
- New package `redana/` at the repo root, independent of `research/gate0/`. Do not import from `research.gate0.*` anywhere in `redana/`; copy the two already-validated functions instead (residualization, dCor+permutation), each re-verified by its own tests in the new location.
- This is **not** a Gate 0 study. Do not reuse Gate 0's hash-pinned-calibration/single-official-run/independent-outside-verifier ceremony here -- that machinery existed specifically for Gate 0's frozen-boundary, precommitted-single-cell design. Step 4's own success criterion is simply "does the core mechanism work," validated by ordinary TDD plus one seeded, reproducible synthetic scenario with a short results note.
- Frozen incumbent network: graphical lasso via `sklearn.covariance.graphical_lasso`, over a fixed regularization grid, selected by minimum EBIC with `gamma = 0.5` fixed. Grid and gamma are frozen once implemented -- not tuned against the validation scenario's results.
- Multiplicity control: standard Benjamini-Hochberg FDR over the vector of pairwise permutation p-values for one dataset's `C(p, 2)` pairs.
- Every new module gets focused unit tests before the orchestration layer is built; every promoted function gets a parity test against its Gate 0 original on the same seeded input, proving the copy is faithful.

---

### Task 1: Promote validated residualization and dependence-statistic code

**Files:** Create `redana/__init__.py`, `redana/residuals.py`, `redana/dependence.py`; create `tests/redana/__init__.py`, `tests/redana/test_residuals.py`, `tests/redana/test_dependence.py`.

**Interfaces:** `redana/residuals.py` exposes `predictor_columns(columns, left, right)` and `cross_fitted_pair_residuals(frame, left, right, config, seed)`, copied from `research/gate0/residuals.py` verbatim (same five-fold, spline/Ridge pipeline). `redana/dependence.py` exposes `permutation_distance_correlation(left, right, permutations, seed)` returning the same `(observed, p_value, null_statistics)` result shape as `research/gate0/metrics.py`. Both modules define their own frozen configuration dataclass (do not import `research.gate0.config.Gate0Config`); name it `PrototypeConfig` in `redana/residuals.py` with the same fields (`n_splits`, `spline_knots`, `spline_degree`, `ridge_alpha`).

- [ ] **Step 1: Write failing tests**

For `residuals.py`: test that `predictor_columns` excludes exactly the tested pair; test that `cross_fitted_pair_residuals` returns held-out residuals of the correct shape and that residuals are approximately mean-zero for independent Gaussian inputs at a moderately large sample. Add a **parity test**: build an identical `Gate0Config`/`PrototypeConfig` pair with matching fields, run both `research.gate0.residuals.cross_fitted_pair_residuals` and `redana.residuals.cross_fitted_pair_residuals` on the same seeded synthetic frame, and assert the two residual frames are numerically identical.

For `dependence.py`: test that `permutation_distance_correlation` returns a p-value in `(0, 1]`, a null array of the requested length, and that independent inputs at a large sample produce a large p-value while a strongly dependent pair produces a small one. Add a parity test against `research.gate0.metrics.permutation_distance_correlation` on identical seeded input.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe -m pytest tests/redana/test_residuals.py tests/redana/test_dependence.py -v --basetemp .pytest-step4-promote-red`. Expect import failures for `redana.residuals` and `redana.dependence`.

- [ ] **Step 3: Implement by copying**

Copy the bodies of `predictor_columns`, `cross_fitted_pair_residuals`, and `permutation_distance_correlation` from their Gate 0 originals into the new modules unchanged except for the config dataclass rename and the removal of any Gate 0-specific imports. Do not alter any numeric behavior.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-step4-promote-green`, then Ruff over the four new files; expect clean, including the parity tests passing exactly. Commit as `feat: promote validated residualization and dependence statistic into redana`.

### Task 2: Implement and test BH-FDR multiplicity control

**Files:** Create `redana/fdr.py`, `tests/redana/test_fdr.py`.

**Interfaces:** `benjamini_hochberg(p_values: Sequence[float], alpha: float) -> np.ndarray[bool]` returns a boolean significance mask the same length as the input, applying the standard BH step-up procedure.

- [ ] **Step 1: Write failing tests**

Test against a hand-computed textbook example (a short list of p-values with a known BH-significant subset at a stated alpha). Test the all-null case (large, uniform-ish p-values) yields no significant pairs. Test the all-signal case (all p-values near zero) yields all pairs significant. Test monotonicity: adding more non-significant p-values to a fixed significant set never removes a previously significant entry's status change beyond what BH's shared threshold implies (i.e., match BH's known behavior exactly, not an approximation).

- [ ] **Step 2: Verify RED**

Run the focused suite; expect import failure for `redana.fdr`.

- [ ] **Step 3: Implement**

Standard BH: sort ascending, find the largest `k` with `p_(k) <= (k/m)*alpha`, mark all `p <= p_(k)` significant (or none if no such `k` exists).

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-step4-fdr-green`, then Ruff. Commit as `feat: add BH-FDR multiplicity control to redana`.

### Task 3: Implement and test the frozen incumbent linear network

**Files:** Create `redana/network.py`, `tests/redana/test_network.py`.

**Interfaces:** `fit_incumbent_network(frame: pd.DataFrame, config: NetworkConfig) -> IncumbentNetworkResult`, where `NetworkConfig` freezes the regularization grid and `gamma = 0.5`, and `IncumbentNetworkResult` holds the selected precision matrix, the derived partial-correlation matrix, and a boolean edge-adjacency matrix (nonzero off-diagonal partial correlation).

- [ ] **Step 1: Write failing tests**

Test that a clearly sparse, well-separated synthetic covariance structure (e.g., a small chain or hub graph with strong linear edges and many independent variables) is recovered with high precision/recall by the selected model at a large sample size. Test that fully independent Gaussian columns at a large sample select an empty or near-empty edge set (no rampant false edges from an under-regularized fit). Test that `gamma` and the regularization grid are fixed dataclass defaults, not parameters callers can silently drift by monkeypatching in production code paths.

- [ ] **Step 2: Verify RED**

Run the focused suite; expect import failure for `redana.network`.

- [ ] **Step 3: Implement**

Fit `sklearn.covariance.graphical_lasso` (or `GraphicalLasso`) across the frozen regularization grid on the (already standardized) input frame's covariance; for each fit compute EBIC `= -2*log-likelihood + edges*log(n) + 4*edges*gamma*log(p)` (the standard extended-BIC form used for EBICglasso, `gamma=0.5`); select the minimum-EBIC fit; derive partial correlations from its precision matrix.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-step4-network-green`, then Ruff. Commit as `feat: add frozen EBIC-selected incumbent network to redana`.

### Task 4: Implement and test simulation scoring

**Files:** Create `redana/scoring.py`, `tests/redana/test_scoring.py`.

**Interfaces:** `score_edges(true_edges: set[tuple[str, str]], selected_edges: set[tuple[str, str]]) -> EdgeScore`, where `EdgeScore` holds `precision`, `recall`, `f1`, `true_positive_count`, `false_positive_count`, `false_negative_count`. Pair order within a tuple must not matter (undirected edges).

- [ ] **Step 1: Write failing tests**

Test exact match (precision = recall = f1 = 1.0), no overlap (all zero), partial overlap against a hand-computed expectation, empty selected set (precision undefined -> defined as 0.0, not a division error), empty true set with a non-empty selection (recall undefined -> 0.0), and that `("X1", "X2")` and `("X2", "X1")` are treated as the same edge.

- [ ] **Step 2: Verify RED**

Run the focused suite; expect import failure for `redana.scoring`.

- [ ] **Step 3: Implement**

Normalize every edge tuple to a sorted pair before set operations; compute precision/recall/F1 from the resulting true-positive/false-positive/false-negative counts, guarding the two zero-denominator cases explicitly.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-step4-scoring-green`, then Ruff. Commit as `feat: add edge-set scoring to redana`.

### Task 5: Implement and test the prototype orchestration entry point

**Files:** Create `redana/prototype.py`, `tests/redana/test_prototype.py`.

**Interfaces:** `run_prototype(frame: pd.DataFrame, residual_config: PrototypeConfig, network_config: NetworkConfig, permutations: int, alpha: float, seed: int) -> PrototypeResult`, where `PrototypeResult` holds the incumbent network's edge set (from Task 3), the residual layer's BH-FDR-significant edge set (every unordered pair in `frame`, cross-fitted residualized per Task 1, tested with Task 1's dCor/permutation statistic, multiplicity-controlled per Task 2), and the per-pair observed statistics/p-values for inspection.

- [ ] **Step 1: Write failing tests**

Test on a small (4-6 column) synthetic frame that every unordered pair is tested exactly once, that seeds are deterministically derived per pair (reuse the `derive_seed`-style pattern already proven in Gate 0, reimplemented locally in `redana/` rather than imported), that re-running with the same seed produces identical results, and that the returned incumbent and residual edge sets are independently computed (mock one and confirm the other is unaffected).

- [ ] **Step 2: Verify RED**

Run the focused suite; expect import failure for `redana.prototype`.

- [ ] **Step 3: Implement**

Enumerate `C(p, 2)` pairs from the frame's columns; for each, derive a deterministic seed, compute cross-fitted residuals (Task 1) and the dCor/permutation p-value (Task 1); collect all p-values and apply BH-FDR (Task 2) to get the residual layer's significant pairs; separately fit the incumbent network (Task 3) once on the whole frame.

- [ ] **Step 4: Verify GREEN and commit**

Run focused pytest with basetemp `.pytest-step4-prototype-green`, then Ruff. Commit as `feat: add prototype orchestration entry point to redana`.

### Task 6: Run and record one first synthetic validation scenario

**Files:** Create `scripts/run_step4_validation_scenario.py`; create `tests/redana/test_step4_validation_scenario.py` (a fast smoke test at reduced dimensions, not the full scenario); create `docs/evidence/step4-first-validation-scenario-20260825.md` after running.

**Scenario design:** A single frozen `p = 6` synthetic network at a large sample size (`n = 5000`, chosen so sampling variability is small without requiring Gate 0-style batch replication): two clearly linear edges (e.g., `X1-X2`, `X2-X3`, chain-style, coefficient `0.7`), one pure-nonlinear edge with near-zero linear component (`X4-X5`, quadratic-in-latent-noise construction matching the F5/Candidate-1 shape already validated in Gate 0), and one fully independent pair among the rest (`X6` independent of everything). This mirrors `plan.md` §5's "linear fixture" and "pure nonlinear fixture" expectations in miniature: the incumbent network should recover the two linear edges and miss the nonlinear one; the residual layer should detect the nonlinear edge and add little on the already-linear pairs.

- [ ] **Step 1: Write the scenario generator and a fast smoke test**

Add a small, seeded fixture generator (either inline in the script or as a `redana/scenarios.py` module if reused by the test) producing the `p = 6` frame described above. Write a smoke test at small `n` (e.g. 300) asserting the pipeline runs end-to-end without error and returns well-formed results (correct pair count, valid probabilities, non-empty result object) -- not asserting specific detection outcomes, since small `n` is not expected to be decisive.

- [ ] **Step 2: Verify RED then GREEN**

Run the smoke test; expect an import failure first, then a passing run after the generator and any missing wiring are implemented. Basetemp `.pytest-step4-scenario-green`.

- [ ] **Step 3: Preflight and commit source**

Run the full pytest suite (`--basetemp .pytest-step4-preflight`) and `ruff check research tests scripts redana`; expect full PASS and lint clean. Commit as `feat: add first Step 4 synthetic validation scenario`.

- [ ] **Step 4: Run the scenario once and record results**

Run `PYTHONPATH="C:\tmp\redana-batch-test-deps;." C:\tmp\scova-v4-test\Scripts\python.exe scripts/run_step4_validation_scenario.py` at the full frozen `n = 5000` dimensions. This is not a Gate 0 official run -- no hash-pinning, no independent outside verifier -- but it is still a single deterministic, seeded execution, and its console output (or a small written summary file) should be captured. Write `docs/evidence/step4-first-validation-scenario-20260825.md` recording: the exact scenario definition, the incumbent network's precision/recall/F1 against the two true linear edges, the residual layer's precision/recall/F1 against the one true nonlinear edge, and a plain statement of whether the qualitative expectation (incumbent misses the nonlinear edge, residual layer catches it; both roughly agree on the linear edges) held. Commit the evidence note as `docs: record first Step 4 validation scenario results`.

## Self-review

Tasks 1-6 build exactly the six components `plan.md` §4 requires, in the dependency order each needs (promoted primitives and FDR first, then the two independent estimators, then scoring, then orchestration, then one concrete scenario), reuse already-validated Gate 0 numerics by verified copy rather than reinvention, and explicitly avoid every deferred capability (`plan.md` §4's stability/typology/detectability/mixed-data/visualization/functional-form exclusions). No package, GUI, or broad API is introduced. The final scenario is a smoke test of the mechanism, not a benchmark claim -- Stage I-III (`plan.md` §5-§7) remain untouched and unauthorized by this plan.
