import pandas as pd

from research.gate0.batch_null_policy import (
    BatchNullConfig,
    batch_terminal_status,
    check_confirmation,
    select_calibration_boundary,
    summarize_batches,
)


def _records(batch_medians: list[float], *, phase: str = "calibration") -> pd.DataFrame:
    rows = []
    for batch, median in enumerate(batch_medians):
        for replication in range(10):
            rows.append(
                {
                    "phase": phase,
                    "batch": batch,
                    "replication": replication,
                    "observed_statistic": median,
                    "permutation_p_value": 0.5,
                    "exception_text": None,
                }
            )
    return pd.DataFrame(rows)


def test_selection_uses_smallest_inclusive_rank_boundary() -> None:
    batches = summarize_batches(_records([float(index) for index in range(100)]), BatchNullConfig())

    selection = select_calibration_boundary(batches, BatchNullConfig())

    assert selection.boundary == 89.0
    assert selection.null_like_batch_count == 90
    assert selection.status == "READY"


def test_calibration_stops_when_fewer_than_90_batches_pass_p_guard() -> None:
    frame = _records([0.01] * 100)
    frame.loc[frame.batch < 11, "permutation_p_value"] = 0.05

    selection = select_calibration_boundary(summarize_batches(frame, BatchNullConfig()), BatchNullConfig())

    assert selection.status == "STOP"
    assert selection.boundary is None
    assert selection.guard_passing_batch_count == 89


def test_tied_boundary_is_inclusive_and_reproducible() -> None:
    batches = summarize_batches(_records([0.1] * 100), BatchNullConfig())

    selection = select_calibration_boundary(batches, BatchNullConfig())

    assert selection.boundary == 0.1
    assert selection.null_like_batch_count == 100


def test_confirmation_requires_85_batches_and_at_most_67_low_p_values() -> None:
    frame = _records([0.01] * 85 + [0.2] * 15, phase="confirmation")

    check = check_confirmation(
        summarize_batches(frame, BatchNullConfig()), frame, 0.01, BatchNullConfig()
    )

    assert check.complete
    assert check.null_like_batch_count == 85
    assert check.low_p_value_count == 0
    assert check.batch_rate_passed
    assert check.p_value_passed
    assert batch_terminal_status(None, check) == "PASS"


def test_confirmation_is_narrow_with_only_84_null_like_batches() -> None:
    frame = _records([0.01] * 84 + [0.2] * 16, phase="confirmation")

    check = check_confirmation(
        summarize_batches(frame, BatchNullConfig()), frame, 0.01, BatchNullConfig()
    )

    assert not check.batch_rate_passed
    assert check.p_value_passed
    assert batch_terminal_status(None, check) == "NARROW"


def test_confirmation_stops_when_68_p_values_are_low() -> None:
    frame = _records([0.01] * 100, phase="confirmation")
    frame.loc[:67, "permutation_p_value"] = 0.05

    check = check_confirmation(
        summarize_batches(frame, BatchNullConfig()), frame, 0.01, BatchNullConfig()
    )

    assert check.low_p_value_count == 68
    assert not check.p_value_passed
    assert batch_terminal_status(None, check) == "STOP"


def test_malformed_or_exception_data_stops_before_count_results() -> None:
    frame = _records([0.01] * 100, phase="confirmation")
    frame.loc[0, "exception_text"] = "RuntimeError: retained failure"

    check = check_confirmation(
        summarize_batches(frame, BatchNullConfig()), frame, 0.01, BatchNullConfig()
    )

    assert not check.complete
    assert check.null_like_batch_count == 0
    assert check.low_p_value_count == 0
    assert batch_terminal_status(None, check) == "STOP"


def test_noninteger_replication_identifier_makes_its_batch_incomplete() -> None:
    frame = _records([0.01] * 100)
    frame["replication"] = frame["replication"].astype(object)
    frame.loc[0, "replication"] = 0.5

    batches = summarize_batches(frame, BatchNullConfig())

    assert not batches[0].complete
    assert select_calibration_boundary(batches, BatchNullConfig()).status == "STOP"
