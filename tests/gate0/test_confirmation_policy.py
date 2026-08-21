from pathlib import Path

import pandas as pd
import pytest

from research.gate0.confirmation_policy import (
    CALIBRATION_RECORDS_SHA256,
    ConfirmationPolicy,
    ReferenceCheck,
    check_reference,
    classify_confirmation_pair,
    confirmation_status,
    verify_calibration_provenance,
)
from research.gate0.fixtures import FIXTURES


def _pair_records(statistic: float, p_values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "observed_statistic": [statistic] * 10,
            "permutation_p_value": p_values,
            "exception_text": [None] * 10,
        }
    )


def _passing_reference() -> ReferenceCheck:
    return ReferenceCheck(True, 27, 4, True, True)


def _passing_fixture_records() -> pd.DataFrame:
    records: list[pd.DataFrame] = []
    for fixture_id, fixture in FIXTURES.items():
        target = _pair_records(
            0.10 if fixture.expected_target_class == "non-null" else 0.01,
            [0.01] * 8 + [0.5] * 2 if fixture.expected_target_class == "non-null" else [0.5] * 10,
        )
        target["fixture_id"] = fixture_id
        target["pair_role"] = "target"
        records.append(target)

        control = _pair_records(0.01, [0.5] * 10)
        control["fixture_id"] = fixture_id
        control["pair_role"] = "null-control"
        records.append(control)
    return pd.concat(records, ignore_index=True)


def test_policy_freezes_recorded_boundary() -> None:
    path = Path("artifacts/null-calibration/null-calibration-20260820-001/records.csv")

    policy = verify_calibration_provenance(path)

    assert policy.practical_null_boundary == 0.07078970914915612
    assert policy.calibration_sha256 == CALIBRATION_RECORDS_SHA256


def test_policy_rejects_wrong_calibration_hash(tmp_path: Path) -> None:
    path = tmp_path / "records.csv"
    path.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        verify_calibration_provenance(path)


def test_null_like_uses_new_strict_boundary() -> None:
    records = pd.DataFrame(
        {
            "observed_statistic": [0.07078970914915611] * 10,
            "permutation_p_value": [0.05, 0.05] + [0.5] * 8,
        }
    )

    assert classify_confirmation_pair(records, ConfirmationPolicy.frozen()) == "null-like"


def test_boundary_is_strict_and_non_null_is_unchanged() -> None:
    at_boundary = pd.DataFrame(
        {
            "observed_statistic": [0.07078970914915612] * 10,
            "permutation_p_value": [0.5] * 10,
        }
    )
    non_null = pd.DataFrame(
        {
            "observed_statistic": [0.10] * 10,
            "permutation_p_value": [0.01] * 8 + [0.5] * 2,
        }
    )
    policy = ConfirmationPolicy.frozen()

    assert classify_confirmation_pair(at_boundary, policy) == "ambiguous"
    assert classify_confirmation_pair(non_null, policy) == "non-null"


def test_reference_check_requires_27_small_statistics_and_four_low_p_values() -> None:
    records = pd.DataFrame(
        {
            "observed_statistic": [0.01] * 27 + [0.2] * 3,
            "permutation_p_value": [0.5] * 26 + [0.05] * 4,
        }
    )

    check = check_reference(records, ConfirmationPolicy.frozen())

    assert check.complete
    assert check.practical_boundary_passed
    assert check.p_value_passed


def test_reference_boundary_failure_is_narrow() -> None:
    records = pd.DataFrame(
        {
            "observed_statistic": [0.01] * 26 + [0.2] * 4,
            "permutation_p_value": [0.5] * 30,
        }
    )

    status = confirmation_status(
        check_reference(records, ConfirmationPolicy.frozen()),
        _passing_fixture_records(),
        ConfirmationPolicy.frozen(),
    )

    assert status == "NARROW"


def test_reference_p_value_failure_is_stop() -> None:
    records = pd.DataFrame(
        {
            "observed_statistic": [0.01] * 30,
            "permutation_p_value": [0.5] * 25 + [0.05] * 5,
        }
    )

    status = confirmation_status(
        check_reference(records, ConfirmationPolicy.frozen()),
        _passing_fixture_records(),
        ConfirmationPolicy.frozen(),
    )

    assert status == "STOP"


def test_ambiguous_fixture_outranks_definite_mismatch() -> None:
    fixture_records = _passing_fixture_records()
    fixture_records.loc[
        (fixture_records.fixture_id == "F1") & (fixture_records.pair_role == "target"),
        "observed_statistic",
    ] = 0.08
    fixture_records.loc[
        (fixture_records.fixture_id == "F2") & (fixture_records.pair_role == "target"),
        "observed_statistic",
    ] = 0.01
    fixture_records.loc[
        (fixture_records.fixture_id == "F2") & (fixture_records.pair_role == "target"),
        "permutation_p_value",
    ] = 0.5

    assert (
        confirmation_status(_passing_reference(), fixture_records, ConfirmationPolicy.frozen())
        == "NARROW"
    )


def test_definite_fixture_mismatch_requires_owner_decision() -> None:
    fixture_records = _passing_fixture_records()
    fixture_records.loc[
        (fixture_records.fixture_id == "F2") & (fixture_records.pair_role == "target"),
        "observed_statistic",
    ] = 0.01
    fixture_records.loc[
        (fixture_records.fixture_id == "F2") & (fixture_records.pair_role == "target"),
        "permutation_p_value",
    ] = 0.5

    assert (
        confirmation_status(_passing_reference(), fixture_records, ConfirmationPolicy.frozen())
        == "MIXED / OWNER DECISION"
    )


def test_retained_fixture_exception_is_stop() -> None:
    fixture_records = _passing_fixture_records()
    fixture_records.loc[0, "exception_text"] = "RuntimeError: retained failure"

    assert (
        confirmation_status(_passing_reference(), fixture_records, ConfirmationPolicy.frozen())
        == "STOP"
    )


def test_ambiguity_outranks_a_mismatch_that_comes_first() -> None:
    fixture_records = _passing_fixture_records()
    fixture_records.loc[
        (fixture_records.fixture_id == "F2") & (fixture_records.pair_role == "target"),
        "observed_statistic",
    ] = 0.01
    fixture_records.loc[
        (fixture_records.fixture_id == "F2") & (fixture_records.pair_role == "target"),
        "permutation_p_value",
    ] = 0.5
    fixture_records.loc[
        (fixture_records.fixture_id == "F4") & (fixture_records.pair_role == "target"),
        "observed_statistic",
    ] = 0.08

    assert (
        confirmation_status(_passing_reference(), fixture_records, ConfirmationPolicy.frozen())
        == "NARROW"
    )
