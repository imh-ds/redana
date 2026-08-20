"""Frozen null-calibration inputs and the independent reference arm."""

from __future__ import annotations

import time
import warnings
from dataclasses import dataclass

import numpy as np

from research.gate0.config import FULL_PROFILE, derive_seed
from research.gate0.metrics import permutation_distance_correlation

CALIBRATION_FIXTURES = ("F1", "F4", "F5", "F6")
EVALUATION_SIZES = (250, 500, 1_000, 2_000)


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
    p_value: float | None
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
    *, evaluation_rows: int, replication: int, permutations: int
) -> CalibrationRecord:
    """Run a seeded independent-standard-normal reference calculation."""

    left_seed = derive_seed("calibration", "reference", replication, evaluation_rows, "left")
    right_seed = derive_seed("calibration", "reference", replication, evaluation_rows, "right")
    permutation_seed = derive_seed(
        "calibration", "reference", replication, evaluation_rows, "permutation"
    )
    started = time.perf_counter()
    caught_warnings: list[warnings.WarningMessage] = []

    try:
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            left = np.random.default_rng(left_seed).standard_normal(evaluation_rows)
            right = np.random.default_rng(right_seed).standard_normal(evaluation_rows)
            result = permutation_distance_correlation(left, right, permutations, permutation_seed)
        warning_text = "; ".join(str(item.message) for item in caught_warnings) or ""
        return CalibrationRecord(
            arm="reference",
            fixture_id="reference",
            replication=replication,
            evaluation_rows=evaluation_rows,
            observed_statistic=result.observed,
            p_value=result.p_value,
            null_statistics_path=None,
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
            p_value=None,
            null_statistics_path=None,
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
    """Reserve the fitted-arm interface for the subsequent calibration task."""

    del fixture_id, evaluation_rows, replication, source_rows, permutations
    raise NotImplementedError("fitted calibration execution has not been implemented")
