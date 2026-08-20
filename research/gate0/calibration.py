"""Frozen null-calibration inputs and the independent reference arm."""

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
from research.gate0.fixtures import FIXTURES, generate_fixture
from research.gate0.metrics import permutation_distance_correlation
from research.gate0.residuals import cross_fitted_pair_residuals

CALIBRATION_FIXTURES = ("F1", "F4", "F5", "F6")
EVALUATION_SIZES = (250, 500, 1_000, 2_000)
SEED_COLUMNS = (
    "fixture_seed",
    "residual_seed",
    "evaluation_seed",
    "left_seed",
    "right_seed",
    "permutation_seed",
)


@dataclass(frozen=True)
class CalibrationConfig:
    """Frozen dimensions for the calibration matrix."""

    replications: int = 30
    source_rows: int = FULL_PROFILE.source_rows
    permutations: int = FULL_PROFILE.permutations
    evaluation_sizes: tuple[int, ...] = EVALUATION_SIZES


@dataclass(frozen=True)
class CalibrationRecord:
    """One attempted calibration calculation, including retained execution metadata."""

    arm: str
    fixture_id: str
    replication: int
    evaluation_rows: int
    observed_statistic: float | None
    permutation_p_value: float | None
    null_statistics_path: str | None
    residual_sample_path: str | None
    fixture_seed: int | None
    residual_seed: int | None
    evaluation_seed: int | None
    left_seed: int | None
    right_seed: int | None
    permutation_seed: int
    elapsed_seconds: float
    warnings: str
    exception_text: str | None


def run_reference_cell(
    *, evaluation_rows: int, replication: int, permutations: int, output_dir: Path | None = None
) -> CalibrationRecord:
    """Run a seeded independent-standard-normal reference calculation."""

    left_seed = derive_seed("calibration", "reference", replication, evaluation_rows, "left")
    right_seed = derive_seed("calibration", "reference", replication, evaluation_rows, "right")
    permutation_seed = derive_seed(
        "calibration", "reference", replication, evaluation_rows, "permutation"
    )
    started = time.perf_counter()
    caught_warnings: list[warnings.WarningMessage] = []
    null_statistics_path: str | None = None

    try:
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            left = np.random.default_rng(left_seed).standard_normal(evaluation_rows)
            right = np.random.default_rng(right_seed).standard_normal(evaluation_rows)
            result = permutation_distance_correlation(left, right, permutations, permutation_seed)
            if output_dir is not None:
                null_path = _reference_null_path(output_dir, replication, evaluation_rows)
                _write_null_statistics(null_path, result.null_statistics)
                null_statistics_path = null_path.relative_to(output_dir).as_posix()
        warning_text = "; ".join(str(item.message) for item in caught_warnings) or ""
        return CalibrationRecord(
            arm="reference",
            fixture_id="reference",
            replication=replication,
            evaluation_rows=evaluation_rows,
            observed_statistic=result.observed,
            permutation_p_value=result.p_value,
            null_statistics_path=null_statistics_path,
            residual_sample_path=None,
            fixture_seed=None,
            residual_seed=None,
            evaluation_seed=None,
            left_seed=left_seed,
            right_seed=right_seed,
            permutation_seed=permutation_seed,
            elapsed_seconds=time.perf_counter() - started,
            warnings=warning_text,
            exception_text=None,
        )
    except Exception as error:  # noqa: BLE001 - failed cells must remain recorded.
        return CalibrationRecord(
            arm="reference",
            fixture_id="reference",
            replication=replication,
            evaluation_rows=evaluation_rows,
            observed_statistic=None,
            permutation_p_value=None,
            null_statistics_path=null_statistics_path,
            residual_sample_path=None,
            fixture_seed=None,
            residual_seed=None,
            evaluation_seed=None,
            left_seed=left_seed,
            right_seed=right_seed,
            permutation_seed=permutation_seed,
            elapsed_seconds=time.perf_counter() - started,
            warnings="; ".join(str(item.message) for item in caught_warnings) or "",
            exception_text=f"{type(error).__name__}: {error}",
        )


def run_fitted_cell(
    *,
    fixture_id: str,
    evaluation_rows: int,
    replication: int,
    source_rows: int = FULL_PROFILE.source_rows,
    permutations: int = FULL_PROFILE.permutations,
) -> CalibrationRecord:
    """Run one fitted-residual calibration cell without retaining artifacts."""

    records = _run_fitted_cells(
        fixture_id=fixture_id,
        replication=replication,
        config=CalibrationConfig(
            replications=1,
            source_rows=source_rows,
            permutations=permutations,
            evaluation_sizes=(evaluation_rows,),
        ),
        output_dir=None,
    )
    return records[0]


def _fitted_seed(fixture_id: str, replication: int, purpose: str, *parts: int) -> int:
    return derive_seed("calibration", "fitted", fixture_id, replication, purpose, *parts)


def _sklearn_seed(identity_seed: int) -> int:
    return identity_seed % 2**32


def _calibration_profile(config: CalibrationConfig, evaluation_rows: int) -> ComputationalProfile:
    return ComputationalProfile(
        "calibration",
        config.source_rows,
        evaluation_rows,
        config.replications,
        config.permutations,
    )


def _reference_null_path(output_dir: Path, replication: int, evaluation_rows: int) -> Path:
    return (
        output_dir
        / "reference"
        / "null_statistics"
        / f"replication-{replication}-evaluation-{evaluation_rows}.npy"
    )


def _write_null_statistics(path: Path, null_statistics: np.ndarray) -> None:
    """Atomically retain one permutation sample without a partial final artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    try:
        with temporary_path.open("wb") as stream:
            np.save(stream, null_statistics)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _write_residual_sample(path: Path, evaluation: pd.DataFrame) -> None:
    """Atomically retain one residual sample without a partial final artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    try:
        evaluation.to_csv(temporary_path, index=False)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _fitted_record(
    *,
    fixture_id: str,
    replication: int,
    evaluation_rows: int,
    fixture_seed: int,
    residual_seed: int,
    evaluation_seed: int,
    permutation_seed: int,
    started: float,
    caught_warnings: list[warnings.WarningMessage],
    result: object | None = None,
    null_statistics_path: str | None = None,
    residual_sample_path: str | None = None,
    exception: Exception | None = None,
) -> CalibrationRecord:
    warning_text = "; ".join(str(item.message) for item in caught_warnings) or ""
    if exception is not None:
        return CalibrationRecord(
            arm="fitted",
            fixture_id=fixture_id,
            replication=replication,
            evaluation_rows=evaluation_rows,
            observed_statistic=None,
            permutation_p_value=None,
            null_statistics_path=null_statistics_path,
            residual_sample_path=residual_sample_path,
            fixture_seed=fixture_seed,
            residual_seed=residual_seed,
            evaluation_seed=evaluation_seed,
            left_seed=None,
            right_seed=None,
            permutation_seed=permutation_seed,
            elapsed_seconds=time.perf_counter() - started,
            warnings=warning_text,
            exception_text=f"{type(exception).__name__}: {exception}",
        )
    assert result is not None
    return CalibrationRecord(
        arm="fitted",
        fixture_id=fixture_id,
        replication=replication,
        evaluation_rows=evaluation_rows,
        observed_statistic=result.observed,
        permutation_p_value=result.p_value,
        null_statistics_path=null_statistics_path,
        residual_sample_path=residual_sample_path,
        fixture_seed=fixture_seed,
        residual_seed=residual_seed,
        evaluation_seed=evaluation_seed,
        left_seed=None,
        right_seed=None,
        permutation_seed=permutation_seed,
        elapsed_seconds=time.perf_counter() - started,
        warnings=warning_text,
        exception_text=None,
    )


def _run_fitted_cells(
    *, fixture_id: str, replication: int, config: CalibrationConfig, output_dir: Path | None
) -> list[CalibrationRecord]:
    fixture = FIXTURES[fixture_id]
    left, right = fixture.target_pair
    fixture_seed = _fitted_seed(fixture_id, replication, "fixture")
    residual_seed = _fitted_seed(fixture_id, replication, "residual")
    started = time.perf_counter()
    records: list[CalibrationRecord] = []

    try:
        with warnings.catch_warnings(record=True) as setup_warnings:
            warnings.simplefilter("always")
            frame = generate_fixture(fixture_id, config.source_rows, fixture_seed)
            residuals = cross_fitted_pair_residuals(
                frame,
                left,
                right,
                Gate0Config(_calibration_profile(config, max(config.evaluation_sizes))),
                _sklearn_seed(residual_seed),
            )
    except Exception as error:  # noqa: BLE001 - failed fitted setup must retain every cell.
        for evaluation_rows in config.evaluation_sizes:
            records.append(
                _fitted_record(
                    fixture_id=fixture_id,
                    replication=replication,
                    evaluation_rows=evaluation_rows,
                    fixture_seed=fixture_seed,
                    residual_seed=residual_seed,
                    evaluation_seed=_fitted_seed(
                        fixture_id, replication, "evaluation", evaluation_rows
                    ),
                    permutation_seed=_fitted_seed(
                        fixture_id, replication, "permutation", evaluation_rows
                    ),
                    started=started,
                    caught_warnings=setup_warnings,
                    exception=error,
                )
            )
        return records

    for evaluation_rows in config.evaluation_sizes:
        evaluation_seed = _fitted_seed(fixture_id, replication, "evaluation", evaluation_rows)
        permutation_seed = _fitted_seed(fixture_id, replication, "permutation", evaluation_rows)
        null_statistics_path = None
        residual_sample_path = None
        cell_warnings: list[warnings.WarningMessage] = []
        try:
            with warnings.catch_warnings(record=True) as cell_warnings:
                warnings.simplefilter("always")
                evaluation_index = np.random.default_rng(evaluation_seed).choice(
                    residuals.index.to_numpy(), size=evaluation_rows, replace=False
                )
                evaluation = residuals.loc[evaluation_index, [left, right]]
                result = permutation_distance_correlation(
                    evaluation[left].to_numpy(),
                    evaluation[right].to_numpy(),
                    config.permutations,
                    permutation_seed,
                )
                if output_dir is not None:
                    artifact_dir = output_dir / "fitted"
                    null_path = (
                        artifact_dir
                        / "null_statistics"
                        / f"{fixture_id}-replication-{replication}-evaluation-{evaluation_rows}.npy"
                    )
                    sample_path = (
                        artifact_dir
                        / "residual_samples"
                        / f"{fixture_id}-replication-{replication}-evaluation-{evaluation_rows}.csv"
                    )
                    _write_null_statistics(null_path, result.null_statistics)
                    null_statistics_path = null_path.relative_to(output_dir).as_posix()
                    _write_residual_sample(sample_path, evaluation)
                    residual_sample_path = sample_path.relative_to(output_dir).as_posix()
            records.append(
                _fitted_record(
                    fixture_id=fixture_id,
                    replication=replication,
                    evaluation_rows=evaluation_rows,
                    fixture_seed=fixture_seed,
                    residual_seed=residual_seed,
                    evaluation_seed=evaluation_seed,
                    permutation_seed=permutation_seed,
                    started=started,
                    caught_warnings=[*setup_warnings, *cell_warnings],
                    result=result,
                    null_statistics_path=null_statistics_path,
                    residual_sample_path=residual_sample_path,
                )
            )
        except Exception as error:  # noqa: BLE001 - every cell must be retained.
            records.append(
                _fitted_record(
                    fixture_id=fixture_id,
                    replication=replication,
                    evaluation_rows=evaluation_rows,
                    fixture_seed=fixture_seed,
                    residual_seed=residual_seed,
                    evaluation_seed=evaluation_seed,
                    permutation_seed=permutation_seed,
                    started=started,
                    caught_warnings=[*setup_warnings, *cell_warnings],
                    null_statistics_path=null_statistics_path,
                    residual_sample_path=residual_sample_path,
                    exception=error,
                )
            )
    return records


def _source_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _initialize_run(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"run directory is already initialized: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def _records_frame(records: list[CalibrationRecord]) -> pd.DataFrame:
    """Build records with nullable seeds preserved as exact unsigned 64-bit values."""

    frame = pd.DataFrame(asdict(record) for record in records)
    for column in SEED_COLUMNS:
        frame[column] = pd.Series(
            [getattr(record, column) for record in records], dtype="UInt64"
        )
    return frame


def run_calibration(output_dir: Path, run_id: str, config: CalibrationConfig) -> pd.DataFrame:
    """Run and persist the frozen fitted-residual and reference calibration arms."""

    if not run_id or not run_id.strip():
        raise ValueError("run_id must be non-empty")
    _initialize_run(output_dir)

    records: list[CalibrationRecord] = []
    for replication in range(config.replications):
        for fixture_id in CALIBRATION_FIXTURES:
            records.extend(
                _run_fitted_cells(
                    fixture_id=fixture_id,
                    replication=replication,
                    config=config,
                    output_dir=output_dir,
                )
            )
        for evaluation_rows in config.evaluation_sizes:
            records.append(
                run_reference_cell(
                    evaluation_rows=evaluation_rows,
                    replication=replication,
                    permutations=config.permutations,
                    output_dir=output_dir,
                )
            )

    frame = _records_frame(records)
    frame.insert(0, "run_id", run_id)
    frame.to_csv(output_dir / "records.csv", index=False)
    _write_json(
        output_dir / "manifest.json",
        {
            "config": asdict(config),
            "run_id": run_id,
            "source_revision": _source_revision(),
        },
    )
    _write_json(output_dir / "run_state.json", {"run_id": run_id, "state": "complete"})
    return frame
