# Gate 0 Residual-Dependence Simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a disposable, reproducible Python research prototype that executes the approved Gate 0 residual-dependence simulation and produces an owner-facing `PASS`, `STOP`, or `NARROW` evidence packet.

**Architecture:** The prototype lives under `research/gate0/`, explicitly outside a distributable package namespace. Hand-authored fixture generators feed pair-specific five-fold spline residualization; distance correlation and a seeded permutation reference classify only prespecified target and null-control pairs. A runner retains every record, including exceptions, and a report writer emits tables, plots, a manifest, and a gate memo.

**Tech Stack:** Python 3.11+, NumPy, pandas, scikit-learn, dcor, matplotlib, pytest, Ruff.

**Spec:** `outline/initial-phase.md`

## Global Constraints

- Support continuous simulated data only, with exactly six observed variables per fixture.
- Use only the eight frozen fixtures F1–F8 and their prespecified target/control pairs.
- Use pair-specific adjustment sets: neither endpoint may appear in the other endpoint's predictor matrix.
- Use cubic spline features, five-fold cross-fitting, distance correlation, and a permutation reference; do not add learner selection, interactions, forests, kernels, stability selection, graph recovery, or package API work.
- Derive every random seed from fixture, replication, pair, and permutation identity; never from worker or execution order.
- Retain all observations, warnings, exceptions, elapsed times, and configuration values in result artifacts.
- Run a runtime-only smoke test before the substantive run. The smoke test may choose only between the two predeclared computational profiles; it must not alter fixtures, transformations, expected outcomes, or gate semantics.
- A failed gate returns control to the owner. It never authorizes automatic estimator redesign, a new simulation family, or package development.

---

## Planned file structure

| Path | Responsibility |
| --- | --- |
| `pyproject.toml` | Reproducible research-tool dependencies and pytest/Ruff configuration. |
| `research/gate0/config.py` | Frozen statistical and computational profiles, validation, identity-based seed derivation. |
| `research/gate0/fixtures.py` | F1–F8 data-generating mechanisms and immutable fixture metadata. |
| `research/gate0/residuals.py` | Pair-specific cross-fitted additive-spline residualization. |
| `research/gate0/metrics.py` | Distance correlation and deterministic permutation references. |
| `research/gate0/runner.py` | Per-pair execution, exception retention, profile selection, and tidy record writing. |
| `research/gate0/report.py` | Tables, residual-pair figures, manifest, and the owner-facing gate memo. |
| `scripts/run_gate0.py` | Command-line entry point for smoke or substantive runs. |
| `tests/gate0/` | Unit and integration tests for every research component. |
| `artifacts/gate0/<run-id>/` | Generated, immutable run outputs; never treated as source code. |

## Frozen computational profiles and classification rule

Use one of these profiles, selected only by the smoke-test feasibility rule:

| Profile | Source rows | Evaluation rows | Independent replications | Permutations | Use when |
| --- | ---: | ---: | ---: | ---: | --- |
| `full` | 50,000 | 1,000 | 10 | 199 | Projected full run is at most four wall-clock hours and peak memory is at most 4 GiB. |
| `reduced` | 20,000 | 750 | 10 | 99 | `full` fails the feasibility rule and this profile projects within the same limits. |

The smoke run uses F1 only, 5,000 source rows, 500 evaluation rows, one replication, and 19 permutations. It records elapsed time and peak memory. Project runtime scales linearly by the number of evaluated pairs and permutations; select `full` or `reduced` from that projection. If neither profile meets the limits, write a computational `STOP` memo and do not modify the method.

For each evaluated pair in a substantive run, calculate the observed distance correlation and an empirical permutation p-value `(1 + count(null >= observed)) / (B + 1)`. Classify a fixture result as:

- **null-like:** no more than two of ten replications have p-value at or below 0.05, and median observed distance correlation is below 0.05;
- **non-null:** at least eight of ten replications have p-value at or below 0.01, and median observed distance correlation is at least 0.10;
- **ambiguous:** any other result.

Gate outcome: `PASS` requires every target pair to have its specified class and every null-control pair to be null-like. `STOP` applies to any unexpected non-null target/control result or an expected direct-dependence target that is null-like. `NARROW` applies to any remaining ambiguity. The report must preserve the raw statistics; these labels do not replace them.

### Task 1: Establish the disposable research environment and frozen configuration

**Files:**
- Create: `pyproject.toml`
- Create: `research/__init__.py`
- Create: `research/gate0/__init__.py`
- Create: `research/gate0/config.py`
- Create: `tests/gate0/test_config.py`

**Interfaces:**
- Produces `ComputationalProfile`, `Gate0Config`, `FULL_PROFILE`, `REDUCED_PROFILE`, `SMOKE_PROFILE`, and `derive_seed(*parts: str | int) -> int`.
- Consumed by every remaining module.

- [ ] **Step 1: Write the failing configuration tests**

```python
from research.gate0.config import FULL_PROFILE, Gate0Config, derive_seed


def test_seed_depends_on_identity_not_call_order() -> None:
    first = derive_seed("F3", 2, "X1-X2", 17)
    assert first == derive_seed("F3", 2, "X1-X2", 17)
    assert first != derive_seed("F3", 3, "X1-X2", 17)


def test_full_profile_matches_frozen_protocol() -> None:
    assert FULL_PROFILE.source_rows == 50_000
    assert FULL_PROFILE.evaluation_rows == 1_000
    assert FULL_PROFILE.replications == 10
    assert FULL_PROFILE.permutations == 199
    assert Gate0Config(profile=FULL_PROFILE).n_splits == 5
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/gate0/test_config.py -v`

Expected: FAIL because `research.gate0.config` does not exist.

- [ ] **Step 3: Add the minimal project configuration and implementation**

Create `pyproject.toml` with Python `>=3.11`, runtime dependencies `numpy`, `pandas`, `scikit-learn`, `dcor`, and `matplotlib`, plus development dependencies `pytest` and `ruff`. Configure pytest with `testpaths = ["tests"]` and Ruff with line length 100.

Implement immutable dataclasses. `derive_seed` must hash the UTF-8 string formed by joining the identity parts with `"|"` using SHA-256 and convert the first eight bytes to an unsigned integer; never use Python's randomized `hash()`.

- [ ] **Step 4: Run configuration tests and static checks**

Run: `python -m pytest tests/gate0/test_config.py -v`

Expected: PASS.

Run: `python -m ruff check research tests`

Expected: exit code 0.

- [ ] **Step 5: Commit the independently testable setup**

```bash
git add pyproject.toml research tests/gate0/test_config.py
git commit -m "build: add gate 0 research configuration"
```

### Task 2: Implement the eight immutable fixture generators

**Files:**
- Create: `research/gate0/fixtures.py`
- Create: `tests/gate0/test_fixtures.py`

**Interfaces:**
- Consumes `derive_seed`.
- Produces `FixtureDefinition`, `FIXTURES`, and `generate_fixture(fixture_id: str, rows: int, seed: int) -> pandas.DataFrame` with columns `X1` through `X6`.

- [ ] **Step 1: Write failing fixture tests**

```python
from research.gate0.fixtures import FIXTURES, generate_fixture


def test_fixture_registry_is_exactly_the_approved_eight() -> None:
    assert tuple(FIXTURES) == ("F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8")
    assert FIXTURES["F5"].target_pair == ("X1", "X2")
    assert FIXTURES["F7"].expected_target_class == "non-null"


def test_generation_is_deterministic_and_standardized() -> None:
    frame = generate_fixture("F3", rows=2_000, seed=9)
    assert frame.equals(generate_fixture("F3", rows=2_000, seed=9))
    assert list(frame.columns) == ["X1", "X2", "X3", "X4", "X5", "X6"]
    assert frame.mean().abs().max() < 1e-12
    assert (frame.std(ddof=0) - 1).abs().max() < 1e-12
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/gate0/test_fixtures.py -v`

Expected: FAIL because `research.gate0.fixtures` does not exist.

- [ ] **Step 3: Implement each fixture exactly once**

Generate independent standard-normal exogenous variables and independent standard-normal errors. Apply these structural equations before final column-wise centering/scaling:

```text
F1: X1=e1; X2=e2; X3=e3; X4=e4; X5=e5; X6=e6
F2: X1=e1; X2=0.7*X1+e2; X3=e3; X4=e4; X5=e5; X6=e6
F3: X1=e1; X2=0.7*(X1**2-1)+e2; X3=e3; X4=e4; X5=e5; X6=e6
F4: X1=e1; X2=0.7*X1+e2; X3=0.7*X2+e3; X4=e4; X5=e5; X6=e6
F5: X3=e3; X1=0.7*(X3**2-1)+e1; X2=0.7*(X3**2-1)+e2; X4=e4; X5=e5; X6=e6
F6: X1=e1; X2=0.7*(X1**2-1)+e2; X3=0.7*X2+e3; X4=e4; X5=e5; X6=e6
F7: X1=e1; X2=e2; X3=0.7*X1+0.7*X2+e3; X4=e4; X5=e5; X6=e6
F8: X1=e1; X3=0.7*X1+e3; X2=0.7*X1+0.7*X3+e2; X4=e4; X5=e5; X6=e6
```

Set target pairs to F1 `X1/X2`, F2 `X1/X2`, F3 `X1/X2`, F4 `X1/X3`, F5 `X1/X2`, F6 `X1/X3`, F7 `X1/X2`, and F8 `X1/X2`; set every null-control pair to `X4/X5`. Expected target classes are null-like for F1, F4, F5, and F6; non-null for F2, F3, F7, and F8.

- [ ] **Step 4: Run tests and verify the structural fixture boundary**

Run: `python -m pytest tests/gate0/test_fixtures.py -v`

Expected: PASS.

Run: `python -m ruff check research/gate0/fixtures.py tests/gate0/test_fixtures.py`

Expected: exit code 0.

- [ ] **Step 5: Commit the fixture registry**

```bash
git add research/gate0/fixtures.py tests/gate0/test_fixtures.py
git commit -m "feat: add gate 0 simulation fixtures"
```

### Task 3: Add pair-specific cross-fitted spline residualization

**Files:**
- Create: `research/gate0/residuals.py`
- Create: `tests/gate0/test_residuals.py`

**Interfaces:**
- Consumes a six-column fixture frame and `Gate0Config`.
- Produces `predictor_columns(columns: Sequence[str], left: str, right: str) -> tuple[str, ...]` and `cross_fitted_pair_residuals(frame: pandas.DataFrame, left: str, right: str, config: Gate0Config, seed: int) -> pandas.DataFrame` with `left` and `right` residual columns.

- [ ] **Step 1: Write failing residualization tests**

```python
import numpy as np
import pandas as pd

from research.gate0.config import Gate0Config, SMOKE_PROFILE
from research.gate0.residuals import cross_fitted_pair_residuals, predictor_columns


def test_endpoints_are_excluded_from_both_adjustment_designs() -> None:
    assert predictor_columns(("X1", "X2", "X3", "X4"), "X1", "X2") == ("X3", "X4")


def test_cross_fitted_residuals_have_one_value_per_input_row() -> None:
    rng = np.random.default_rng(2)
    frame = pd.DataFrame(rng.normal(size=(100, 6)), columns=[f"X{i}" for i in range(1, 7)])
    residuals = cross_fitted_pair_residuals(frame, "X1", "X2", Gate0Config(SMOKE_PROFILE), seed=4)
    assert residuals.shape == (100, 2)
    assert residuals.columns.tolist() == ["X1", "X2"]
    assert residuals.notna().all().all()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/gate0/test_residuals.py -v`

Expected: FAIL because `research.gate0.residuals` does not exist.

- [ ] **Step 3: Implement a fixed, auditable adjustment model**

For each endpoint independently, form predictors from the four non-endpoint columns only. Use `KFold(n_splits=5, shuffle=True, random_state=seed)` and refit the complete preprocessing/model pipeline on each training fold. The pipeline is:

```python
Pipeline([
    ("spline", SplineTransformer(n_knots=5, degree=3, include_bias=False, knots="quantile")),
    ("scale", StandardScaler()),
    ("ridge", Ridge(alpha=1.0)),
])
```

Predict only the held-out fold and set residuals to `observed - held_out_prediction`. Do not fit a model that includes the opposite endpoint, tune `alpha`, change the spline basis, or reuse in-sample predictions.

- [ ] **Step 4: Run residual tests and the full suite**

Run: `python -m pytest tests/gate0/test_residuals.py -v`

Expected: PASS.

Run: `python -m pytest -v`

Expected: all collected tests PASS.

- [ ] **Step 5: Commit the residualizer**

```bash
git add research/gate0/residuals.py tests/gate0/test_residuals.py
git commit -m "feat: add cross-fitted spline residualization"
```

### Task 4: Measure residual dependence with seeded permutation references

**Files:**
- Create: `research/gate0/metrics.py`
- Create: `tests/gate0/test_metrics.py`

**Interfaces:**
- Consumes residual frames and identity seeds.
- Produces `PermutationResult(observed: float, null_statistics: numpy.ndarray, p_value: float)` and `permutation_distance_correlation(left: numpy.ndarray, right: numpy.ndarray, permutations: int, seed: int) -> PermutationResult`.

- [ ] **Step 1: Write failing metric tests**

```python
import numpy as np

from research.gate0.metrics import permutation_distance_correlation


def test_permutation_result_is_reproducible_and_bounded() -> None:
    rng = np.random.default_rng(7)
    left = rng.normal(size=80)
    right = left + rng.normal(scale=0.1, size=80)
    result = permutation_distance_correlation(left, right, permutations=19, seed=3)
    repeat = permutation_distance_correlation(left, right, permutations=19, seed=3)
    assert result.observed == repeat.observed
    assert np.array_equal(result.null_statistics, repeat.null_statistics)
    assert 1 / 20 <= result.p_value <= 1


def test_dependent_pair_exceeds_its_permutation_median() -> None:
    rng = np.random.default_rng(11)
    left = rng.normal(size=120)
    result = permutation_distance_correlation(left, left**2, permutations=39, seed=5)
    assert result.observed > np.median(result.null_statistics)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/gate0/test_metrics.py -v`

Expected: FAIL because `research.gate0.metrics` does not exist.

- [ ] **Step 3: Implement the dependency statistic without hidden selection**

Use `dcor.distance_correlation` on one-dimensional NumPy arrays. Compute the observed value once. For each permutation index, derive a child identity seed from the supplied seed and the index, permute only the right residual array, and calculate the null value. Use the specified empirical p-value formula and preserve all null statistics in their generated order.

- [ ] **Step 4: Run metric tests and static checks**

Run: `python -m pytest tests/gate0/test_metrics.py -v`

Expected: PASS.

Run: `python -m ruff check research/gate0/metrics.py tests/gate0/test_metrics.py`

Expected: exit code 0.

- [ ] **Step 5: Commit the metric module**

```bash
git add research/gate0/metrics.py tests/gate0/test_metrics.py
git commit -m "feat: add residual distance-correlation references"
```

### Task 5: Orchestrate smoke/profile selection and substantive records

**Files:**
- Create: `research/gate0/runner.py`
- Create: `scripts/run_gate0.py`
- Create: `tests/gate0/test_runner.py`

**Interfaces:**
- Consumes fixture, residual, metric, and configuration interfaces.
- Produces `PairRecord`, `select_profile(smoke: SmokeMeasurement) -> ComputationalProfile | None`, and `run_gate0(mode: Literal["smoke", "substantive"], output_dir: pathlib.Path) -> pandas.DataFrame`.

- [ ] **Step 1: Write failing orchestration tests**

```python
from research.gate0.config import FULL_PROFILE, REDUCED_PROFILE
from research.gate0.runner import SmokeMeasurement, select_profile


def test_profile_selection_uses_only_the_two_predeclared_profiles() -> None:
    assert select_profile(SmokeMeasurement(projected_seconds=14_000, peak_gib=3.0)) == FULL_PROFILE
    assert select_profile(SmokeMeasurement(projected_seconds=14_500, peak_gib=3.0)) == REDUCED_PROFILE
    assert select_profile(SmokeMeasurement(projected_seconds=14_500, peak_gib=4.1)) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/gate0/test_runner.py -v`

Expected: FAIL because `research.gate0.runner` does not exist.

- [ ] **Step 3: Implement record-first execution**

The smoke run evaluates F1 target and null-control pairs only. Measure wall time with `time.perf_counter()` and peak Python allocation with `tracemalloc`; label the latter exactly as `python_allocation_peak_bytes`, not total process memory. Estimate total run time from measured pair/permutation work and the fixed profile dimensions.

For a substantive run, loop through fixture IDs, replications, and each fixture's target/control pair. Derive all seeds by identity. Subsample residual rows without replacement using a derived evaluation seed. Write one `PairRecord` for every attempted pair, with fixture, replication, pair role, expected class, observed statistic, permutation p-value, null statistics path, seed identities, profile, elapsed seconds, warnings, and exception text. Catch exceptions at pair level, record them, then continue; a recorded exception forces the final gate result to `STOP`.

The CLI accepts exactly `--mode smoke` or `--mode substantive`, `--output-dir`, and optional `--run-id`; default run IDs are UTC timestamps. It must refuse a substantive run unless `selected_profile.json` produced by a prior smoke run exists in the output directory.

- [ ] **Step 4: Run orchestration tests and a tiny integration invocation**

Run: `python -m pytest tests/gate0/test_runner.py -v`

Expected: PASS.

Run: `python scripts/run_gate0.py --mode smoke --output-dir artifacts/gate0/test-smoke --run-id smoke-test`

Expected: exit code 0 and `artifacts/gate0/test-smoke/selected_profile.json` exists, or exit code 2 with a computational `STOP` record.

- [ ] **Step 5: Commit the runner and smoke entry point**

```bash
git add research/gate0/runner.py scripts/run_gate0.py tests/gate0/test_runner.py
git commit -m "feat: add gate 0 smoke and run orchestration"
```

### Task 6: Generate evidence artifacts and a non-automatic gate memo

**Files:**
- Create: `research/gate0/report.py`
- Create: `tests/gate0/test_report.py`
- Modify: `research/gate0/runner.py`

**Interfaces:**
- Consumes the tidy `PairRecord` table and generated residual samples.
- Produces `classify_pair(records: pandas.DataFrame) -> str` and `write_gate_report(records: pandas.DataFrame, output_dir: pathlib.Path) -> pathlib.Path`.

- [ ] **Step 1: Write failing report tests**

```python
import pandas as pd

from research.gate0.report import classify_pair


def test_non_null_rule_requires_both_frequency_and_effect_size() -> None:
    records = pd.DataFrame({"p_value": [0.01] * 8 + [0.5, 0.5], "observed": [0.11] * 10})
    assert classify_pair(records) == "non-null"


def test_null_like_rule_rejects_three_small_p_values() -> None:
    records = pd.DataFrame({"p_value": [0.01, 0.02, 0.03] + [0.5] * 7, "observed": [0.02] * 10})
    assert classify_pair(records) == "ambiguous"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/gate0/test_report.py -v`

Expected: FAIL because `research.gate0.report` does not exist.

- [ ] **Step 3: Implement classification and evidence output**

Implement exactly the classification rule in this plan. Write `records.csv`, `manifest.json`, one permutation-distribution plot and one representative residual scatterplot per fixture, plus `gate-memo.md`. The memo must include the profile selected, all fixture expected/observed classes, raw-statistic summary, exceptions/warnings, and a separate F7 collider interpretation stating that an expected non-null result is induced conditional dependence—not a direct causal relationship.

Determine overall status in this order: `STOP` for any exception or unexpected non-null/null-like result; otherwise `NARROW` for any ambiguity; otherwise `PASS`. End the memo with: `Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work.`

- [ ] **Step 4: Run report tests and the complete test suite**

Run: `python -m pytest tests/gate0/test_report.py -v`

Expected: PASS.

Run: `python -m pytest -v`

Expected: all collected tests PASS.

Run: `python -m ruff check research tests scripts`

Expected: exit code 0.

- [ ] **Step 5: Commit evidence generation**

```bash
git add research/gate0/report.py research/gate0/runner.py tests/gate0/test_report.py
git commit -m "feat: write gate 0 evidence reports"
```

### Task 7: Execute only after an explicit pre-run check

**Files:**
- Create: `artifacts/gate0/<run-id>/` through the runner; do not hand-edit results.
- Create: `docs/evidence/gate-0-<run-id>.md` only after reviewing generated `gate-memo.md`.

**Interfaces:**
- Consumes a passing test suite and the CLI from Task 5.
- Produces one immutable artifact directory and one owner-facing evidence pointer.

- [ ] **Step 1: Confirm the implementation boundary before any substantive data are generated**

Run: `python -m pytest -v`

Expected: all collected tests PASS.

Run: `python -m ruff check research tests scripts`

Expected: exit code 0.

Verify manually that the fixture registry is F1–F8 only, `SplineTransformer` has five knots and degree three, `Ridge(alpha=1.0)` is fixed, five-fold cross-fitting is used, and no predictor list contains a pair endpoint.

- [ ] **Step 2: Run the runtime-only smoke test**

Run: `python scripts/run_gate0.py --mode smoke --output-dir artifacts/gate0/<run-id> --run-id <run-id>`

Expected: a selected `full` or `reduced` profile, or a computational `STOP` artifact. Do not edit code or statistical settings after seeing the measurement.

- [ ] **Step 3: If and only if the smoke selects a profile, run the frozen substantive suite**

Run: `python scripts/run_gate0.py --mode substantive --output-dir artifacts/gate0/<run-id> --run-id <run-id>`

Expected: `records.csv`, `manifest.json`, plots, and `gate-memo.md`. A nonzero exit is itself a recorded `STOP`; preserve the partial artifact directory.

- [ ] **Step 4: Review and preserve the gate result**

Read `artifacts/gate0/<run-id>/gate-memo.md` and create `docs/evidence/gate-0-<run-id>.md` containing the artifact path, source revision, selected profile, final status, and the verbatim final owner-decision sentence. Do not begin a follow-on study from the result.

- [ ] **Step 5: Commit source and evidence separately**

```bash
git add research tests scripts pyproject.toml
git commit -m "feat: implement gate 0 residual-dependence study"
git add docs/evidence/gate-0-<run-id>.md artifacts/gate0/<run-id>
git commit -m "docs: record gate 0 simulation evidence"
```

## Self-review

- **Spec coverage:** Tasks 1–2 freeze the data boundary and exact fixtures; Task 3 enforces pair-specific cross-fitting; Task 4 provides distance correlation and permutations; Task 5 preserves records and runtime-only profile selection; Task 6 creates required evidence and termination semantics; Task 7 is the only execution path.
- **Scope:** No task creates a package namespace, graph estimator, visualization for researchers, bootstrap/stability system, nonlinear selector, or broader benchmark.
- **Consistency:** The same eight fixture IDs, six columns, five folds, spline basis, Ridge penalty, two computational profiles, and `PASS`/`STOP`/`NARROW` outcomes are used throughout.
- **No placeholders:** The file paths, equations, command lines, thresholds, required outputs, and error behavior are explicit; `<run-id>` is a runtime identity supplied by the CLI, not an unspecified design value.
