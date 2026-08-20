from pathlib import Path

import pandas as pd

from research.gate0.calibration_report import diagnostic_outcome, write_calibration_report


def _records_for_sizes(*sizes: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for evaluation_rows in sizes:
        for replication in range(30):
            rows.append(
                {
                    "arm": "reference",
                    "fixture_id": "reference",
                    "replication": replication,
                    "evaluation_rows": evaluation_rows,
                    "observed_statistic": 0.02,
                    "permutation_p_value": 0.5,
                    "exception_text": None,
                }
            )
            rows.append(
                {
                    "arm": "fitted",
                    "fixture_id": "F1",
                    "replication": replication,
                    "evaluation_rows": evaluation_rows,
                    "observed_statistic": 0.03,
                    "permutation_p_value": 0.5,
                    "exception_text": None,
                }
            )
    return pd.DataFrame(rows)


def test_permutation_failure_stops_the_diagnostic() -> None:
    """An exception makes the null-reference diagnostic unusable."""

    records = pd.DataFrame(
        {
            "arm": ["reference"],
            "exception_text": ["bad p-values"],
            "observed_statistic": [0.0],
            "permutation_p_value": [0.001],
        }
    )

    assert diagnostic_outcome(records) == "STOP"


def test_reference_baseline_result_requires_owner_calibration_decision() -> None:
    """A high 1,000-row reference baseline remains an owner calibration question."""

    records = pd.DataFrame(
        {
            "arm": ["reference"] * 30,
            "exception_text": [None] * 30,
            "observed_statistic": [0.06] * 30,
            "permutation_p_value": [0.5] * 30,
        }
    )

    assert diagnostic_outcome(records) == "CALIBRATION QUESTION"


def test_reference_p_values_concentrated_near_zero_stop_the_diagnostic() -> None:
    """A broken reference permutation distribution cannot support another diagnosis."""

    records = _records_for_sizes(1_000)
    records.loc[records.arm == "reference", "permutation_p_value"] = 0.01

    assert diagnostic_outcome(records) == "STOP"


def test_persistent_fitted_departure_requires_residualization_decision() -> None:
    """A fitted fixture elevated beyond same-size references flags residualization."""

    records = _records_for_sizes(250, 500)
    records.loc[records.arm == "fitted", "fixture_id"] = "F4"
    records.loc[records.arm == "fitted", "observed_statistic"] = 0.10

    assert diagnostic_outcome(records) == "RESIDUALIZATION QUESTION"


def test_report_writes_summaries_paired_plots_and_owner_memo(tmp_path: Path) -> None:
    """Every supplied evaluation size receives a reference-versus-fitted comparison."""

    memo_path = write_calibration_report(_records_for_sizes(250, 1_000), tmp_path)

    assert memo_path == tmp_path / "calibration-memo.md"
    assert (tmp_path / "calibration-summary.csv").exists()
    assert (tmp_path / "plots" / "evaluation-250-reference-vs-fitted.png").exists()
    assert (tmp_path / "plots" / "evaluation-1000-reference-vs-fitted.png").exists()
    memo = memo_path.read_text(encoding="utf-8")
    assert "No threshold, estimator, or fixture has changed." in memo
    assert memo.rstrip().endswith(
        "Owner decision required; this result does not authorize estimator redesign, a new "
        "simulation family, or package work."
    )
