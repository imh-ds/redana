from __future__ import annotations

import pandas as pd

from research.gate0.f4_link_policy import (
    F4LinkConfig,
    check_detection,
    detection_terminal_status,
    summarize_detection_batches,
)


def _records(*, detected_batches: int, batches: int = 100) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for batch in range(batches):
        for replication in range(10):
            detected = batch < detected_batches
            rows.append(
                {
                    "phase": "f4-residual-link",
                    "batch": batch,
                    "replication": replication,
                    "observed_statistic": 0.06 if detected else 0.04,
                    "permutation_p_value": 0.01 if detected and replication < 8 else 0.5,
                    "exception_text": None,
                }
            )
    return pd.DataFrame(rows)


def test_detection_requires_eight_low_p_values_and_median_above_boundary() -> None:
    config = F4LinkConfig(batches=2, replications_per_batch=10)
    records = _records(detected_batches=1, batches=2)
    records.loc[records["batch"].eq(1) & records["replication"].lt(7), "permutation_p_value"] = 0.01

    batches = summarize_detection_batches(records, config)

    assert batches[0].detected
    assert batches[0].low_p_value_count == 8
    assert not batches[1].detected
    assert batches[1].low_p_value_count == 7


def test_detection_terminal_policy_passes_at_85_and_narrows_at_84() -> None:
    config = F4LinkConfig()
    boundary = 0.058242447845091264

    passed = check_detection(
        summarize_detection_batches(_records(detected_batches=85), config),
        _records(detected_batches=85),
        boundary,
        config,
    )
    narrowed = check_detection(
        summarize_detection_batches(_records(detected_batches=84), config),
        _records(detected_batches=84),
        boundary,
        config,
    )

    assert passed.detected_batch_count == 85
    assert detection_terminal_status(passed) == "PASS"
    assert narrowed.detected_batch_count == 84
    assert detection_terminal_status(narrowed) == "NARROW"


def test_missing_or_exception_evidence_stops() -> None:
    config = F4LinkConfig()
    records = _records(detected_batches=100)
    records.loc[0, "exception_text"] = "RuntimeError: retained"

    check = check_detection(summarize_detection_batches(records, config), records, 0.01, config)

    assert not check.complete
    assert detection_terminal_status(check) == "STOP"
