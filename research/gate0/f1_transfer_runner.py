"""Immutable F1 independence null-transfer execution."""

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
from research.gate0.fixtures import generate_fixture
from research.gate0.metrics import permutation_distance_correlation
from research.gate0.residuals import cross_fitted_pair_residuals

_NAMESPACE = "batch-f1-null-transfer"
_PHASE = "f1-null-transfer"
_SEED_COLUMNS = ("fixture_seed", "residual_seed", "permutation_seed")


@dataclass(frozen=True)
class F1TransferConfig:
    """Frozen dimensions and residualization settings for the F1 transfer run."""

    batches: int = 100
    replications_per_batch: int = 10
    rows: int = 1_000
    permutations: int = 199
    n_splits: int = 5
    spline_knots: int = 5
    spline_degree: int = 3
    ridge_alpha: float = 1.0

    def gate0_config(self) -> Gate0Config:
        """Return the matching immutable residualization configuration."""

        return Gate0Config(
            ComputationalProfile("f1-transfer", self.rows, self.rows, 1, self.permutations),
            n_splits=self.n_splits,
            spline_knots=self.spline_knots,
            spline_degree=self.spline_degree,
            ridge_alpha=self.ridge_alpha,
        )


@dataclass(frozen=True)
class F1TransferRecord:
    """One attempted F1 residual dependence calculation."""

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


def run_f1_transfer(
    output_dir: Path, run_id: str, config: F1TransferConfig
) -> pd.DataFrame:
    """Attempt every frozen F1 cell and retain its primary evidence atomically."""

    if not run_id or not run_id.strip():
        raise ValueError("run_id must be non-empty")
    _initialize_output(output_dir)
    gate0_config = config.gate0_config()
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
            "fixture_id": "F1",
            "pair": ["X1", "X2"],
            "phase": _PHASE,
            "run_id": run_id,
            "seed_namespace": _NAMESPACE,
            "source_revision": _source_revision(),
        },
    )
    return frame


def _run_cell(
    batch: int,
    replication: int,
    output_dir: Path,
    run_id: str,
    config: F1TransferConfig,
    gate0_config: Gate0Config,
) -> F1TransferRecord:
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
            frame = generate_fixture("F1", config.rows, fixture_seed)
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
            batch,
            replication,
            run_id,
            fixture_seed,
            residual_seed,
            permutation_seed,
            started,
            caught,
            result.observed,
            result.p_value,
            residual_samples_path,
            null_statistics_path,
        )
    except Exception as error:  # noqa: BLE001 - retain every failed frozen cell.
        return _record(
            batch,
            replication,
            run_id,
            fixture_seed,
            residual_seed,
            permutation_seed,
            started,
            caught,
            None,
            None,
            residual_samples_path,
            null_statistics_path,
            error,
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
) -> F1TransferRecord:
    return F1TransferRecord(
        fixture_id="F1",
        left="X1",
        right="X2",
        phase=_PHASE,
        batch=batch,
        replication=replication,
        observed_statistic=observed_statistic,
        permutation_p_value=permutation_p_value,
        residual_samples_path=residual_samples_path,
        null_statistics_path=null_statistics_path,
        seed_namespace=_NAMESPACE,
        fixture_seed=fixture_seed,
        residual_seed=residual_seed,
        permutation_seed=permutation_seed,
        elapsed_seconds=time.perf_counter() - started,
        warnings="; ".join(str(item.message) for item in caught) or None,
        exception_text=None if error is None else f"{type(error).__name__}: {error}",
        run_id=run_id,
    )


def _initialize_output(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"run directory is already initialized: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def _residual_samples_path(output_dir: Path, batch: int, replication: int) -> Path:
    return output_dir / "residual_samples" / f"batch-{batch}-replication-{replication}.csv"


def _null_statistics_path(output_dir: Path, batch: int, replication: int) -> Path:
    return output_dir / "null_statistics" / f"batch-{batch}-replication-{replication}.npy"


def _records_frame(records: list[F1TransferRecord]) -> pd.DataFrame:
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
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"
