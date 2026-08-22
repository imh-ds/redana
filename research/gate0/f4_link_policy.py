"""Frozen detection rules for the F4 residual-link alternative."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class F4LinkConfig:
    """Approved dimensions and detection thresholds for the clear-link study."""

    batches: int = 100
    replications_per_batch: int = 10
    rows: int = 1_000
    permutations: int = 199
    n_splits: int = 5
    spline_knots: int = 5
    spline_degree: int = 3
    ridge_alpha: float = 1.0
    detection_boundary: float = 0.058242447845091264
    minimum_low_p_values_per_detected_batch: int = 8
    minimum_detected_batches: int = 85


@dataclass(frozen=True)
class DetectionBatch:
    """One batch's retained evidence and fixed detection classification."""

    batch: int
    complete: bool
    exception_free: bool
    median_dcor: float | None
    low_p_value_count: int
    detected: bool


@dataclass(frozen=True)
class DetectionCheck:
    """Study-level evidence completeness and fixed detection count."""

    complete: bool
    detected_batch_count: int
    batch_rate_passed: bool


_REQUIRED_COLUMNS = {
    "phase",
    "batch",
    "replication",
    "observed_statistic",
    "permutation_p_value",
    "exception_text",
}


def summarize_detection_batches(
    records: pd.DataFrame, config: F4LinkConfig
) -> list[DetectionBatch]:
    """Summarize every configured batch under the frozen alternative rule."""

    if not _REQUIRED_COLUMNS.issubset(records.columns):
        return [_incomplete_batch(batch) for batch in range(config.batches)]

    expected_replications = set(range(config.replications_per_batch))
    summaries: list[DetectionBatch] = []
    for batch in range(config.batches):
        cells = records.loc[records["batch"] == batch]
        replications = pd.to_numeric(cells["replication"], errors="coerce")
        statistics = _finite_numeric(cells, "observed_statistic")
        p_values = _finite_numeric(cells, "permutation_p_value")
        exception_free = cells["exception_text"].isna().all()
        complete = (
            len(cells) == config.replications_per_batch
            and replications.notna().all()
            and (replications == replications.astype(int)).all()
            and set(replications.astype(int)) == expected_replications
            and statistics is not None
            and p_values is not None
            and ((p_values >= 0.0) & (p_values <= 1.0)).all()
            and exception_free
        )
        median_dcor = float(statistics.median()) if complete and statistics is not None else None
        low_p_value_count = int((p_values <= 0.05).sum()) if complete and p_values is not None else 0
        summaries.append(
            DetectionBatch(
                batch=batch,
                complete=complete,
                exception_free=exception_free,
                median_dcor=median_dcor,
                low_p_value_count=low_p_value_count,
                detected=bool(
                    complete
                    and median_dcor is not None
                    and median_dcor > config.detection_boundary
                    and low_p_value_count >= config.minimum_low_p_values_per_detected_batch
                ),
            )
        )
    return summaries


def check_detection(
    batches: list[DetectionBatch],
    records: pd.DataFrame,
    boundary: float,
    config: F4LinkConfig,
) -> DetectionCheck:
    """Apply the precommitted boundary and count rule to retained evidence."""

    complete = (
        math.isfinite(boundary)
        and boundary == config.detection_boundary
        and len(records) == config.batches * config.replications_per_batch
        and len(batches) == config.batches
        and all(batch.complete for batch in batches)
    )
    if not complete:
        return DetectionCheck(False, 0, False)
    detected_batch_count = sum(
        batch.detected and batch.median_dcor is not None and batch.median_dcor > boundary
        for batch in batches
    )
    return DetectionCheck(
        True,
        detected_batch_count,
        detected_batch_count >= config.minimum_detected_batches,
    )


def detection_terminal_status(check: DetectionCheck) -> str:
    """Apply terminal precedence for the fixed alternative study."""

    if not check.complete:
        return "STOP"
    if not check.batch_rate_passed:
        return "NARROW"
    return "PASS"


def _incomplete_batch(batch: int) -> DetectionBatch:
    return DetectionBatch(batch, False, False, None, 0, False)


def _finite_numeric(records: pd.DataFrame, column: str) -> pd.Series | None:
    values = pd.to_numeric(records[column], errors="coerce")
    if values.isna().any() or not values.map(math.isfinite).all():
        return None
    return values
