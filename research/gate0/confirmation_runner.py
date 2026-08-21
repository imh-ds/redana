"""Fresh execution runner for the reference-calibrated confirmation matrix."""

from __future__ import annotations

import json
import subprocess
import time
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from research.gate0.config import FULL_PROFILE, ComputationalProfile, Gate0Config, derive_seed
from research.gate0.confirmation_policy import ConfirmationPolicy
from research.gate0.fixtures import FIXTURES, generate_fixture
from research.gate0.metrics import permutation_distance_correlation
from research.gate0.residuals import cross_fitted_pair_residuals

SEED_NAMESPACE = "reference-confirmation"
CALIBRATION_SOURCE = "artifacts/null-calibration/null-calibration-20260820-001/records.csv"
SEED_COLUMNS = (
    "fixture_seed",
    "residual_seed",
    "evaluation_seed",
    "left_seed",
    "right_seed",
    "permutation_seed",
)


@dataclass(frozen=True)
class ConfirmationConfig:
    """Frozen dimensions for a fresh confirmation run."""

    reference_replications: int = 30
    fixture_replications: int = 10
    source_rows: int = FULL_PROFILE.source_rows
    evaluation_rows: int = FULL_PROFILE.evaluation_rows
    permutations: int = FULL_PROFILE.permutations


@dataclass(frozen=True)
class ConfirmationRecord:
    """One retained reference or fixture-pair attempt."""

    component: str
    fixture_id: str
    pair_role: str | None
    expected_class: str | None
    replication: int
    observed_statistic: float | None
    permutation_p_value: float | None
    null_statistics_path: str | None
    residual_sample_path: str | None
    seed_namespace: str
    fixture_seed: int | None
    residual_seed: int | None
    evaluation_seed: int | None
    left_seed: int | None
    right_seed: int | None
    permutation_seed: int | None
    elapsed_seconds: float
    warnings: str | None
    exception_text: str | None


def run_confirmation(
    output_dir: Path, run_id: str, policy: ConfirmationPolicy, config: ConfirmationConfig
) -> pd.DataFrame:
    """Execute and retain one new reference and complete F1--F8 fixture matrix."""

    if not run_id or not run_id.strip():
        raise ValueError("run_id must be non-empty")
    _initialize_run(output_dir)

    records: list[ConfirmationRecord] = []
    for replication in range(config.reference_replications):
        records.append(_run_reference_cell(output_dir, replication, config))
    for fixture_id in FIXTURES:
        for replication in range(config.fixture_replications):
            records.extend(_run_fixture_replication(output_dir, fixture_id, replication, config))

    frame = _records_frame(records)
    frame.insert(0, "run_id", run_id)
    _write_csv(output_dir / "records.csv", frame)
    _write_json(
        output_dir / "manifest-input.json",
        {
            "policy": asdict(policy),
            "calibration_source": CALIBRATION_SOURCE,
            "calibration_sha256": policy.calibration_sha256,
            "seed_namespace": SEED_NAMESPACE,
            "config": asdict(config),
            "matrix_counts": {
                "reference": config.reference_replications,
                "fixture": len(FIXTURES) * 2 * config.fixture_replications,
            },
            "run_id": run_id,
            "source_revision": _source_revision(),
        },
    )
    _write_json(output_dir / "run_state.json", {"run_id": run_id, "state": "complete"})
    return frame


def _run_reference_cell(
    output_dir: Path, replication: int, config: ConfirmationConfig
) -> ConfirmationRecord:
    left_seed = derive_seed(
        SEED_NAMESPACE, "reference", replication, config.evaluation_rows, "left"
    )
    right_seed = derive_seed(
        SEED_NAMESPACE, "reference", replication, config.evaluation_rows, "right"
    )
    permutation_seed = derive_seed(
        SEED_NAMESPACE, "reference", replication, config.evaluation_rows, "permutation"
    )
    started = time.perf_counter()
    caught: list[warnings.WarningMessage] = []
    null_path: str | None = None
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            left = np.random.default_rng(left_seed).standard_normal(config.evaluation_rows)
            right = np.random.default_rng(right_seed).standard_normal(config.evaluation_rows)
            result = permutation_distance_correlation(
                left, right, config.permutations, permutation_seed
            )
            artifact = output_dir / "reference" / "null_statistics" / f"replication-{replication}.npy"
            _write_null_statistics(artifact, result.null_statistics)
            null_path = artifact.relative_to(output_dir).as_posix()
        return _reference_record(
            replication, left_seed, right_seed, permutation_seed, started, caught, result, null_path
        )
    except Exception as error:  # noqa: BLE001 - preserve each failed cell as evidence.
        return _reference_record(
            replication,
            left_seed,
            right_seed,
            permutation_seed,
            started,
            caught,
            None,
            null_path,
            error,
        )


def _reference_record(
    replication: int,
    left_seed: int,
    right_seed: int,
    permutation_seed: int,
    started: float,
    caught: list[warnings.WarningMessage],
    result: object | None,
    null_path: str | None,
    error: Exception | None = None,
) -> ConfirmationRecord:
    return ConfirmationRecord(
        component="reference",
        fixture_id="reference",
        pair_role=None,
        expected_class=None,
        replication=replication,
        observed_statistic=None if result is None else result.observed,
        permutation_p_value=None if result is None else result.p_value,
        null_statistics_path=null_path,
        residual_sample_path=None,
        seed_namespace=SEED_NAMESPACE,
        fixture_seed=None,
        residual_seed=None,
        evaluation_seed=None,
        left_seed=left_seed,
        right_seed=right_seed,
        permutation_seed=permutation_seed,
        elapsed_seconds=time.perf_counter() - started,
        warnings=_warning_text(caught),
        exception_text=None if error is None else f"{type(error).__name__}: {error}",
    )


def _run_fixture_replication(
    output_dir: Path, fixture_id: str, replication: int, config: ConfirmationConfig
) -> list[ConfirmationRecord]:
    fixture_seed = derive_seed(SEED_NAMESPACE, "fixture", fixture_id, replication, "source")
    started = time.perf_counter()
    setup_warnings: list[warnings.WarningMessage] = []
    try:
        with warnings.catch_warnings(record=True) as setup_warnings:
            warnings.simplefilter("always")
            source = generate_fixture(fixture_id, config.source_rows, fixture_seed)
    except Exception as error:  # noqa: BLE001 - preserve every pair that source failure prevents.
        records = []
        for pair_role, expected_class, _ in _fixture_pairs(fixture_id):
            residual_seed = derive_seed(
                SEED_NAMESPACE, "fixture", fixture_id, replication, pair_role, "residual"
            )
            evaluation_seed = derive_seed(
                SEED_NAMESPACE, "fixture", fixture_id, replication, pair_role, "evaluation"
            )
            permutation_seed = derive_seed(
                SEED_NAMESPACE, "fixture", fixture_id, replication, pair_role, "permutation"
            )
            records.append(
                _fixture_record(
                    fixture_id,
                    pair_role,
                    expected_class,
                    replication,
                    fixture_seed,
                    residual_seed,
                    evaluation_seed,
                    permutation_seed,
                    started,
                    setup_warnings,
                    None,
                    None,
                    None,
                    error,
                )
            )
        return records

    records: list[ConfirmationRecord] = []
    for pair_role, expected_class, pair in _fixture_pairs(fixture_id):
        records.append(
            _run_fixture_cell(
                output_dir,
                fixture_id,
                pair_role,
                expected_class,
                pair,
                replication,
                fixture_seed,
                source,
                config,
                started,
                setup_warnings,
            )
        )
    return records


def _fixture_pairs(fixture_id: str) -> tuple[tuple[str, str, tuple[str, str]], ...]:
    fixture = FIXTURES[fixture_id]
    return (
        ("target", fixture.expected_target_class, fixture.target_pair),
        ("null-control", "null-like", fixture.null_control_pair),
    )


def _run_fixture_cell(
    output_dir: Path,
    fixture_id: str,
    pair_role: str,
    expected_class: str,
    pair: tuple[str, str],
    replication: int,
    fixture_seed: int,
    source: pd.DataFrame,
    config: ConfirmationConfig,
    started: float,
    setup_warnings: list[warnings.WarningMessage],
) -> ConfirmationRecord:
    residual_seed = derive_seed(SEED_NAMESPACE, "fixture", fixture_id, replication, pair_role, "residual")
    evaluation_seed = derive_seed(
        SEED_NAMESPACE, "fixture", fixture_id, replication, pair_role, "evaluation"
    )
    permutation_seed = derive_seed(
        SEED_NAMESPACE, "fixture", fixture_id, replication, pair_role, "permutation"
    )
    caught: list[warnings.WarningMessage] = []
    null_path: str | None = None
    sample_path: str | None = None
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            left, right = pair
            residuals = cross_fitted_pair_residuals(
                source,
                left,
                right,
                Gate0Config(_confirmation_profile(config)),
                _sklearn_seed(residual_seed),
            )
            evaluation_index = np.random.default_rng(evaluation_seed).choice(
                residuals.index.to_numpy(), size=config.evaluation_rows, replace=False
            )
            evaluation = residuals.loc[evaluation_index, [left, right]]
            result = permutation_distance_correlation(
                evaluation[left].to_numpy(),
                evaluation[right].to_numpy(),
                config.permutations,
                permutation_seed,
            )
            artifact_dir = output_dir / "fixtures" / fixture_id / f"replication-{replication}"
            null_artifact = artifact_dir / f"{pair_role}-null-statistics.npy"
            sample_artifact = artifact_dir / f"{pair_role}-residual-sample.csv"
            _write_null_statistics(null_artifact, result.null_statistics)
            null_path = null_artifact.relative_to(output_dir).as_posix()
            _write_residual_sample(sample_artifact, evaluation)
            sample_path = sample_artifact.relative_to(output_dir).as_posix()
        return _fixture_record(
            fixture_id,
            pair_role,
            expected_class,
            replication,
            fixture_seed,
            residual_seed,
            evaluation_seed,
            permutation_seed,
            started,
            [*setup_warnings, *caught],
            result,
            null_path,
            sample_path,
        )
    except Exception as error:  # noqa: BLE001 - preserve failed matrix cells and continue.
        return _fixture_record(
            fixture_id,
            pair_role,
            expected_class,
            replication,
            fixture_seed,
            residual_seed,
            evaluation_seed,
            permutation_seed,
            started,
            [*setup_warnings, *caught],
            None,
            null_path,
            sample_path,
            error,
        )


def _fixture_record(
    fixture_id: str,
    pair_role: str,
    expected_class: str,
    replication: int,
    fixture_seed: int,
    residual_seed: int | None,
    evaluation_seed: int | None,
    permutation_seed: int | None,
    started: float,
    caught: list[warnings.WarningMessage],
    result: object | None,
    null_path: str | None,
    sample_path: str | None,
    error: Exception | None = None,
) -> ConfirmationRecord:
    return ConfirmationRecord(
        component="fixture",
        fixture_id=fixture_id,
        pair_role=pair_role,
        expected_class=expected_class,
        replication=replication,
        observed_statistic=None if result is None else result.observed,
        permutation_p_value=None if result is None else result.p_value,
        null_statistics_path=null_path,
        residual_sample_path=sample_path,
        seed_namespace=SEED_NAMESPACE,
        fixture_seed=fixture_seed,
        residual_seed=residual_seed,
        evaluation_seed=evaluation_seed,
        left_seed=None,
        right_seed=None,
        permutation_seed=permutation_seed,
        elapsed_seconds=time.perf_counter() - started,
        warnings=_warning_text(caught),
        exception_text=None if error is None else f"{type(error).__name__}: {error}",
    )


def _confirmation_profile(config: ConfirmationConfig) -> ComputationalProfile:
    return ComputationalProfile(
        "reference-confirmation",
        config.source_rows,
        config.evaluation_rows,
        config.fixture_replications,
        config.permutations,
    )


def _sklearn_seed(seed: int) -> int:
    return seed % 2**32


def _warning_text(caught: list[warnings.WarningMessage]) -> str:
    return "; ".join(str(item.message) for item in caught)


def _initialize_run(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"run directory is already initialized: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def _records_frame(records: list[ConfirmationRecord]) -> pd.DataFrame:
    frame = pd.DataFrame(asdict(record) for record in records)
    for column in SEED_COLUMNS:
        frame[column] = pd.Series([getattr(record, column) for record in records], dtype="UInt64")
    return frame


def _write_null_statistics(path: Path, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        with temporary.open("wb") as stream:
            np.save(stream, values)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_residual_sample(path: Path, sample: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        sample.to_csv(temporary, index=False)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        frame.to_csv(temporary, index=False)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_json(path: Path, payload: object) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _source_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"
