"""Immutable F7 collider-detection execution."""

from __future__ import annotations

import json
import subprocess
import time
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from research.gate0.config import ComputationalProfile, Gate0Config, derive_seed
from research.gate0.f4_link_policy import F4LinkConfig
from research.gate0.fixtures import generate_fixture
from research.gate0.metrics import permutation_distance_correlation
from research.gate0.residuals import cross_fitted_pair_residuals

_NAMESPACE = "batch-f7-collider-detection"
_PHASE = "f7-collider-detection"
_FIXTURE = "F7"
_SEED_COLUMNS = ("fixture_seed", "residual_seed", "permutation_seed")


@dataclass(frozen=True)
class F7ColliderDetectionRecord:
    """One attempted F7 collider-detection calculation, retaining failures."""

    fixture_id: str
    left: str
    right: str
    phase: str
    batch: int
    replication: int
    observed_statistic: float | None
    permutation_p_value: float | None
    residual_samples_path: str | None
    null_statistics_path: str | None
    seed_namespace: str
    fixture_seed: int
    residual_seed: int
    permutation_seed: int
    elapsed_seconds: float
    warnings: str | None
    exception_text: str | None
    run_id: str


def run_f7_collider_detection(
    output_dir: Path, run_id: str, config: F4LinkConfig
) -> pd.DataFrame:
    """Attempt every frozen F7 cell and retain its primary evidence atomically."""

    if not run_id or not run_id.strip():
        raise ValueError("run_id must be non-empty")
    _initialize_output(output_dir)
    gate0_config = _gate0_config(config)
    records = [
        _run_cell(batch, replication, output_dir, run_id, config, gate0_config)
        for batch in range(config.batches)
        for replication in range(config.replications_per_batch)
    ]
    frame = _records_frame(records)
    _write_csv(output_dir / "records.csv", frame)
    _write_json(
        output_dir / "manifest-input.json",
        {
            "attempted_records": len(records),
            "config": asdict(config),
            "fixture_id": _FIXTURE,
            "pair": ["X1", "X2"],
            "phase": _PHASE,
            "run_id": run_id,
            "seed_namespace": _NAMESPACE,
            "source_revision": _source_revision(),
        },
    )
    return frame


def _gate0_config(config: F4LinkConfig) -> Gate0Config:
    return Gate0Config(
        ComputationalProfile("f7-collider-detection", config.rows, config.rows, 1, config.permutations),
        n_splits=config.n_splits,
        spline_knots=config.spline_knots,
        spline_degree=config.spline_degree,
        ridge_alpha=config.ridge_alpha,
    )


def _run_cell(
    batch: int,
    replication: int,
    output_dir: Path,
    run_id: str,
    config: F4LinkConfig,
    gate0_config: Gate0Config,
) -> F7ColliderDetectionRecord:
    fixture_seed = derive_seed(_NAMESPACE, batch, replication, "fixture")
    residual_seed = derive_seed(_NAMESPACE, batch, replication, "residual")
    permutation_seed = derive_seed(_NAMESPACE, batch, replication, "permutation")
    started = time.perf_counter()
    caught: list[warnings.WarningMessage] = []
    residual_samples_path: str | None = None
    null_statistics_path: str | None = None
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            frame = generate_fixture(_FIXTURE, config.rows, fixture_seed)
            residuals = cross_fitted_pair_residuals(
                frame, "X1", "X2", gate0_config, residual_seed % (2**32)
            )
            residual_path = _residual_samples_path(output_dir, batch, replication)
            _write_csv(residual_path, residuals)
            residual_samples_path = residual_path.relative_to(output_dir).as_posix()
            result = permutation_distance_correlation(
                residuals["X1"].to_numpy(),
                residuals["X2"].to_numpy(),
                config.permutations,
                permutation_seed,
            )
            null_path = _null_statistics_path(output_dir, batch, replication)
            _write_null_statistics(null_path, result.null_statistics)
            null_statistics_path = null_path.relative_to(output_dir).as_posix()
        return _record(
            batch, replication, run_id, fixture_seed, residual_seed, permutation_seed, started,
            caught, result.observed, result.p_value, residual_samples_path, null_statistics_path,
        )
    except Exception as error:  # noqa: BLE001 - every failed frozen cell is retained.
        return _record(
            batch, replication, run_id, fixture_seed, residual_seed, permutation_seed, started,
            caught, None, None, residual_samples_path, null_statistics_path, error,
        )


def _record(
    batch: int,
    replication: int,
    run_id: str,
    fixture_seed: int,
    residual_seed: int,
    permutation_seed: int,
    started: float,
    caught: list[warnings.WarningMessage],
    observed_statistic: float | None,
    permutation_p_value: float | None,
    residual_samples_path: str | None,
    null_statistics_path: str | None,
    error: Exception | None = None,
) -> F7ColliderDetectionRecord:
    return F7ColliderDetectionRecord(
        fixture_id=_FIXTURE, left="X1", right="X2", phase=_PHASE,
        batch=batch, replication=replication, observed_statistic=observed_statistic,
        permutation_p_value=permutation_p_value, residual_samples_path=residual_samples_path,
        null_statistics_path=null_statistics_path, seed_namespace=_NAMESPACE,
        fixture_seed=fixture_seed, residual_seed=residual_seed, permutation_seed=permutation_seed,
        elapsed_seconds=time.perf_counter() - started,
        warnings="; ".join(str(item.message) for item in caught) or None,
        exception_text=None if error is None else f"{type(error).__name__}: {error}", run_id=run_id,
    )


def _initialize_output(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"run directory is already initialized: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def _residual_samples_path(output_dir: Path, batch: int, replication: int) -> Path:
    return output_dir / "residual_samples" / f"batch-{batch}-replication-{replication}.csv"


def _null_statistics_path(output_dir: Path, batch: int, replication: int) -> Path:
    return output_dir / "null_statistics" / f"batch-{batch}-replication-{replication}.npy"


def _records_frame(records: list[F7ColliderDetectionRecord]) -> pd.DataFrame:
    frame = pd.DataFrame(asdict(record) for record in records)
    for column in _SEED_COLUMNS:
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


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
        ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[2],
        capture_output=True, check=False, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"
