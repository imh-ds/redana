"""Frozen policy and provenance checks for reference-calibrated confirmation."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from research.gate0.fixtures import FIXTURES

PRACTICAL_NULL_BOUNDARY = 0.07078970914915612
CALIBRATION_RECORDS_SHA256 = "57160bf69892c4047e8a089487d5b894d09243c1a3bcf60164f4daa881369197"


@dataclass(frozen=True)
class ConfirmationPolicy:
    """The approved constants for a single reference-calibrated confirmation."""

    practical_null_boundary: float
    calibration_sha256: str
    calibration_quantile: float = 0.95
    quantile_interpolation: str = "linear"
    fixture_replications: int = 10
    reference_replications: int = 30

    @classmethod
    def frozen(cls) -> ConfirmationPolicy:
        """Return the immutable owner-approved confirmation policy."""

        return cls(PRACTICAL_NULL_BOUNDARY, CALIBRATION_RECORDS_SHA256)


@dataclass(frozen=True)
class ReferenceCheck:
    """The independent reference-arm acceptance outcome."""

    complete: bool
    below_boundary_count: int
    low_p_value_count: int
    practical_boundary_passed: bool
    p_value_passed: bool


def verify_calibration_provenance(path: Path) -> ConfirmationPolicy:
    """Validate the hash and recorded reference quantile before using calibration data."""

    policy = ConfirmationPolicy.frozen()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != policy.calibration_sha256:
        raise ValueError("calibration records SHA-256 does not match the frozen provenance")

    records = pd.read_csv(path)
    required = {"arm", "evaluation_rows", "observed_statistic"}
    if not required.issubset(records.columns):
        raise ValueError("calibration records are missing required reference columns")
    reference = records.loc[
        (records["arm"] == "reference") & (records["evaluation_rows"] == 1_000)
    ]
    statistics = _numeric_column(reference, "observed_statistic")
    if len(reference) != policy.reference_replications or statistics is None:
        raise ValueError("calibration records must contain 30 numeric reference rows at 1,000")

    quantile = statistics.quantile(
        policy.calibration_quantile, interpolation=policy.quantile_interpolation
    )
    if quantile != policy.practical_null_boundary:
        raise ValueError("calibration reference quantile does not match the frozen boundary")
    return policy


def classify_confirmation_pair(records: pd.DataFrame, policy: ConfirmationPolicy) -> str:
    """Classify one complete ten-replication fixture pair under the frozen rules."""

    statistics = _numeric_column(records, "observed_statistic")
    p_values = _numeric_column(records, "permutation_p_value")
    if len(records) != policy.fixture_replications or statistics is None or p_values is None:
        raise ValueError("confirmation pairs require exactly 10 numeric rows")

    if (statistics.median() < policy.practical_null_boundary) and (p_values <= 0.05).sum() <= 2:
        return "null-like"
    if (statistics.median() >= 0.10) and (p_values <= 0.01).sum() >= 8:
        return "non-null"
    return "ambiguous"


def check_reference(records: pd.DataFrame, policy: ConfirmationPolicy) -> ReferenceCheck:
    """Evaluate the complete 30-pair independent reference arm."""

    statistics = _numeric_column(records, "observed_statistic")
    p_values = _numeric_column(records, "permutation_p_value")
    if len(records) != policy.reference_replications or statistics is None or p_values is None:
        return ReferenceCheck(False, 0, 0, False, False)

    below_boundary_count = int((statistics < policy.practical_null_boundary).sum())
    low_p_value_count = int((p_values <= 0.05).sum())
    return ReferenceCheck(
        True,
        below_boundary_count,
        low_p_value_count,
        below_boundary_count >= 27,
        low_p_value_count <= 4,
    )


def confirmation_status(
    reference: ReferenceCheck, fixture_records: pd.DataFrame, policy: ConfirmationPolicy
) -> str:
    """Apply the terminal precedence for the immutable confirmation result."""

    if not reference.complete or not reference.p_value_passed:
        return "STOP"
    if not reference.practical_boundary_passed:
        return "NARROW"
    if _has_retained_exception(fixture_records):
        return "STOP"

    expected_pairs = {
        (fixture_id, "target"): fixture.expected_target_class
        for fixture_id, fixture in FIXTURES.items()
    }
    expected_pairs.update({(fixture_id, "null-control"): "null-like" for fixture_id in FIXTURES})
    required = {"fixture_id", "pair_role"}
    if not required.issubset(fixture_records.columns):
        return "STOP"

    observed_pairs = set(zip(fixture_records["fixture_id"], fixture_records["pair_role"], strict=True))
    if observed_pairs != set(expected_pairs):
        return "STOP"

    has_ambiguity = False
    has_mismatch = False
    for pair, expected_class in expected_pairs.items():
        fixture_id, pair_role = pair
        records = fixture_records.loc[
            (fixture_records["fixture_id"] == fixture_id)
            & (fixture_records["pair_role"] == pair_role)
        ]
        try:
            observed_class = classify_confirmation_pair(records, policy)
        except ValueError:
            return "STOP"
        has_ambiguity |= observed_class == "ambiguous"
        has_mismatch |= observed_class != "ambiguous" and observed_class != expected_class
    if has_ambiguity:
        return "NARROW"
    if has_mismatch:
        return "MIXED / OWNER DECISION"
    return "PASS"


def _numeric_column(records: pd.DataFrame, column: str) -> pd.Series | None:
    """Return one fully finite numeric record column, or ``None`` when malformed."""

    if column not in records.columns:
        return None
    values = pd.to_numeric(records[column], errors="coerce")
    if values.isna().any() or not values.map(math.isfinite).all():
        return None
    return values


def _has_retained_exception(records: pd.DataFrame) -> bool:
    """Treat any retained exception text as malformed confirmation evidence."""

    return "exception_text" in records and records["exception_text"].notna().any()
