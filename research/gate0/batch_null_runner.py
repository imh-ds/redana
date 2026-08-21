"""Reference-only execution for batch-level null calibration and confirmation."""

from __future__ import annotations

import json
import subprocess
import time
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from research.gate0.batch_null_policy import BatchNullConfig
from research.gate0.config import derive_seed
from research.gate0.metrics import permutation_distance_correlation

Phase = Literal["calibration", "confirmation"]

_NAMESPACE_BY_PHASE: dict[Phase, str] = {
    "calibration": "batch-null-calibration",
    "confirmation": "batch-null-confirmation",
}
_SEED_COLUMNS = ("left_seed", "right_seed", "permutation_seed")


@dataclass(frozen=True)
class BatchNullRecord:
    """One attempted independent-standard-normal reference calculation."""

    phase: str
    batch: int
    replication: int
    observed_statistic: float | None
    permutation_p_value: float | None
    null_statistics_path: str | None
    seed_namespace: str
    left_seed: int | None
    right_seed: int | None
    permutation_seed: int | None
    elapsed_seconds: float
    warnings: str | None
    exception_text: str | None
    run_id: str


def run_batch_phase(
    phase: Phase, output_dir: Path, run_id: str, config: BatchNullConfig
) -> pd.DataFrame:
    """Attempt every independent reference cell and atomically retain its evidence."""

    if phase not in _NAMESPACE_BY_PHASE:
        raise ValueError("phase must be 'calibration' or 'confirmation'")
    if not run_id or not run_id.strip():
        raise ValueError("run_id must be non-empty")
    _initialize_output(output_dir)

    namespace = _NAMESPACE_BY_PHASE[phase]
    records = [
        _run_reference_cell(phase, batch, replication, output_dir, run_id, namespace, config)
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
            "phase": phase,
            "run_id": run_id,
            "seed_namespace": namespace,
            "source_revision": _source_revision(),
        },
    )
    return frame


def _run_reference_cell(
    phase: Phase,
    batch: int,
    replication: int,
    output_dir: Path,
    run_id: str,
    namespace: str,
    config: BatchNullConfig,
) -> BatchNullRecord:
    left_seed = derive_seed(namespace, batch, replication, "left")
    right_seed = derive_seed(namespace, batch, replication, "right")
    permutation_seed = derive_seed(namespace, batch, replication, "permutation")
    started = time.perf_counter()
    caught: list[warnings.WarningMessage] = []
    null_statistics_path: str | None = None
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            left = np.random.default_rng(left_seed).standard_normal(config.evaluation_rows)
            right = np.random.default_rng(right_seed).standard_normal(config.evaluation_rows)
            result = permutation_distance_correlation(
                left, right, config.permutations, permutation_seed
            )
            artifact = _null_statistics_path(output_dir, batch, replication)
            _write_null_statistics(artifact, result.null_statistics)
            null_statistics_path = artifact.relative_to(output_dir).as_posix()
        return _record(
            phase,
            batch,
            replication,
            run_id,
            namespace,
            left_seed,
            right_seed,
            permutation_seed,
            started,
            caught,
            result.observed,
            result.p_value,
            null_statistics_path,
        )
    except Exception as error:  # noqa: BLE001 - retain every failed reference cell.
        return _record(
            phase,
            batch,
            replication,
            run_id,
            namespace,
            left_seed,
            right_seed,
            permutation_seed,
            started,
            caught,
            None,
            None,
            null_statistics_path,
            error,
        )


def _record(
    phase: Phase,
    batch: int,
    replication: int,
    run_id: str,
    namespace: str,
    left_seed: int,
    right_seed: int,
    permutation_seed: int,
    started: float,
    caught: list[warnings.WarningMessage],
    observed_statistic: float | None,
    permutation_p_value: float | None,
    null_statistics_path: str | None,
    error: Exception | None = None,
) -> BatchNullRecord:
    return BatchNullRecord(
        phase=phase,
        batch=batch,
        replication=replication,
        observed_statistic=observed_statistic,
        permutation_p_value=permutation_p_value,
        null_statistics_path=null_statistics_path,
        seed_namespace=namespace,
        left_seed=left_seed,
        right_seed=right_seed,
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


def _null_statistics_path(output_dir: Path, batch: int, replication: int) -> Path:
    return output_dir / "null_statistics" / f"batch-{batch}-replication-{replication}.npy"


def _records_frame(records: list[BatchNullRecord]) -> pd.DataFrame:
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
