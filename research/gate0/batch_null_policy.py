"""Frozen decision rules for batch-level null calibration."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class BatchNullConfig:
    """Approved dimensions and acceptance thresholds for the reference-only study."""

    batches: int = 100
    replications_per_batch: int = 10
    evaluation_rows: int = 1_000
    permutations: int = 199
    maximum_batch_low_p_values: int = 2
    minimum_calibration_guard_batches: int = 90
    minimum_confirmation_null_like_batches: int = 85
    maximum_confirmation_low_p_values: int = 67


@dataclass(frozen=True)
class BatchSummary:
    """One batch's completeness, p-value guard, and observed dCor median."""

    phase: str
    batch: int
    complete: bool
    exception_free: bool
    p_guard_passed: bool
    median_dcor: float | None


@dataclass(frozen=True)
class CalibrationSelection:
    """The calibration half's frozen boundary, or its terminal stop."""

    status: str
    boundary: float | None
    qualifying_batch_ids: tuple[int, ...]
    guard_passing_batch_count: int
    null_like_batch_count: int


@dataclass(frozen=True)
class ConfirmationCheck:
    """Independent confirmation's count-based decision inputs."""

    complete: bool
    null_like_batch_count: int
    low_p_value_count: int
    batch_rate_passed: bool
    p_value_passed: bool


_REQUIRED_COLUMNS = {
    "phase",
    "batch",
    "replication",
    "observed_statistic",
    "permutation_p_value",
    "exception_text",
}


def summarize_batches(records: pd.DataFrame, config: BatchNullConfig) -> list[BatchSummary]:
    """Summarize exactly the configured zero-indexed batches from retained records."""

    if not _REQUIRED_COLUMNS.issubset(records.columns):
        return [_incomplete_summary("unknown", batch) for batch in range(config.batches)]

    summaries: list[BatchSummary] = []
    expected_replications = set(range(config.replications_per_batch))
    for batch in range(config.batches):
        batch_records = records.loc[records["batch"] == batch]
        phases = batch_records["phase"].dropna().unique()
        phase = str(phases[0]) if len(phases) == 1 else "unknown"
        replication_values = pd.to_numeric(batch_records["replication"], errors="coerce")
        statistics = _finite_numeric(batch_records, "observed_statistic")
        p_values = _finite_numeric(batch_records, "permutation_p_value")
        exception_free = batch_records["exception_text"].isna().all()
        complete = (
            len(batch_records) == config.replications_per_batch
            and len(phases) == 1
            and replication_values.notna().all()
            and (replication_values == replication_values.astype(int)).all()
            and set(replication_values.astype(int)) == expected_replications
            and statistics is not None
            and p_values is not None
            and ((p_values >= 0.0) & (p_values <= 1.0)).all()
            and exception_free
        )
        median = float(statistics.median()) if complete and statistics is not None else None
        low_p_values = int((p_values <= 0.05).sum()) if complete and p_values is not None else 0
        summaries.append(
            BatchSummary(
                phase=phase,
                batch=batch,
                complete=complete,
                exception_free=exception_free,
                p_guard_passed=complete
                and low_p_values <= config.maximum_batch_low_p_values,
                median_dcor=median,
            )
        )
    return summaries


def select_calibration_boundary(
    batches: list[BatchSummary], config: BatchNullConfig
) -> CalibrationSelection:
    """Select the smallest inclusive rank boundary passing the frozen calibration rule."""

    guard_passing = [
        batch for batch in batches if batch.complete and batch.p_guard_passed and batch.median_dcor is not None
    ]
    guard_passing_ids = tuple(batch.batch for batch in guard_passing)
    if (
        len(batches) != config.batches
        or not all(batch.complete for batch in batches)
        or len(guard_passing) < config.minimum_calibration_guard_batches
    ):
        return CalibrationSelection("STOP", None, guard_passing_ids, len(guard_passing), 0)

    ordered = sorted(guard_passing, key=lambda batch: (batch.median_dcor, batch.batch))
    boundary = ordered[config.minimum_calibration_guard_batches - 1].median_dcor
    assert boundary is not None
    null_like_count = sum(
        batch.complete
        and batch.p_guard_passed
        and batch.median_dcor is not None
        and batch.median_dcor <= boundary
        for batch in batches
    )
    return CalibrationSelection(
        "READY", boundary, guard_passing_ids, len(guard_passing), null_like_count
    )


def check_confirmation(
    batches: list[BatchSummary],
    records: pd.DataFrame,
    boundary: float,
    config: BatchNullConfig,
) -> ConfirmationCheck:
    """Check independent confirmation against its copied calibration boundary."""

    if not math.isfinite(boundary) or not _confirmation_records_complete(batches, records, config):
        return ConfirmationCheck(False, 0, 0, False, False)

    null_like_batch_count = sum(
        batch.p_guard_passed and batch.median_dcor is not None and batch.median_dcor <= boundary
        for batch in batches
    )
    p_values = pd.to_numeric(records["permutation_p_value"], errors="coerce")
    low_p_value_count = int((p_values <= 0.05).sum())
    return ConfirmationCheck(
        True,
        null_like_batch_count,
        low_p_value_count,
        null_like_batch_count >= config.minimum_confirmation_null_like_batches,
        low_p_value_count <= config.maximum_confirmation_low_p_values,
    )


def batch_terminal_status(
    selection: CalibrationSelection | None, confirmation: ConfirmationCheck | None
) -> str:
    """Apply terminal precedence: STOP, then NARROW, then PASS."""

    if selection is not None and selection.status == "STOP":
        return "STOP"
    if confirmation is None:
        return "READY" if selection is not None and selection.status == "READY" else "STOP"
    if not confirmation.complete or not confirmation.p_value_passed:
        return "STOP"
    if not confirmation.batch_rate_passed:
        return "NARROW"
    return "PASS"


def _incomplete_summary(phase: str, batch: int) -> BatchSummary:
    return BatchSummary(phase, batch, False, False, False, None)


def _finite_numeric(records: pd.DataFrame, column: str) -> pd.Series | None:
    values = pd.to_numeric(records[column], errors="coerce")
    if values.isna().any() or not values.map(math.isfinite).all():
        return None
    return values


def _confirmation_records_complete(
    batches: list[BatchSummary], records: pd.DataFrame, config: BatchNullConfig
) -> bool:
    expected_records = config.batches * config.replications_per_batch
    return (
        len(records) == expected_records
        and len(batches) == config.batches
        and all(batch.complete for batch in batches)
    )
