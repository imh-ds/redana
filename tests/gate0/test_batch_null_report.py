"""Evidence-report contracts for the batch-level null-calibration study."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from research.gate0.batch_null_policy import BatchNullConfig
from research.gate0.batch_null_report import (
    write_calibration_report,
    write_confirmation_report,
)
from research.gate0.config import OWNER_DECISION_SENTENCE


@pytest.fixture(autouse=True)
def _retain_plot_paths_without_a_graphics_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep report-contract tests independent of the available matplotlib installation."""

    def write_plot(_summary: pd.DataFrame, path: Path, *_args: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"plot")

    monkeypatch.setattr("research.gate0.batch_null_report._plot_batch_medians", write_plot)
    monkeypatch.setattr("research.gate0.batch_null_report._plot_batch_classes", write_plot)


def _records(
    *,
    phase: str,
    run_id: str,
    null_like_batches: int = 100,
    low_p_values: int = 0,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for batch in range(100):
        for replication in range(10):
            index = batch * 10 + replication
            rows.append(
                {
                    "phase": phase,
                    "batch": batch,
                    "replication": replication,
                    "observed_statistic": 0.01 if batch < null_like_batches else 0.20,
                    "permutation_p_value": 0.05 if index < low_p_values else 0.50,
                    "exception_text": None,
                    "warnings": None,
                    "null_statistics_path": f"null_statistics/batch-{batch}-{replication}.npy",
                    "run_id": run_id,
                    "seed_namespace": f"batch-null-{phase}",
                }
            )
    return pd.DataFrame(rows)


def _write_runner_inputs(path: Path, records: pd.DataFrame) -> None:
    path.mkdir(parents=True, exist_ok=True)
    records.to_csv(path / "records.csv", index=False)
    (path / "manifest-input.json").write_text(
        json.dumps(
            {
                "config": {
                    "batches": 100,
                    "replications_per_batch": 10,
                    "evaluation_rows": 1_000,
                    "permutations": 199,
                },
                "seed_namespace": records["seed_namespace"].iloc[0],
                "source_revision": "test-revision",
            }
        ),
        encoding="utf-8",
    )


def _ready_calibration(path: Path) -> Path:
    records = _records(phase="calibration", run_id="calibration-unit")
    _write_runner_inputs(path, records)
    write_calibration_report(records, path, "calibration-unit", BatchNullConfig())
    return path


def test_calibration_report_records_selected_boundary_and_rank(tmp_path: Path) -> None:
    """A changed rank selection must be visible in the frozen calibration evidence."""

    records = _records(phase="calibration", run_id="calibration-unit")
    _write_runner_inputs(tmp_path, records)

    memo = write_calibration_report(records, tmp_path, "calibration-unit", BatchNullConfig())

    text = memo.read_text(encoding="utf-8")
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert "90 of 100" in text
    assert "Selected boundary" in text
    assert manifest["selection"]["null_like_batch_count"] >= 90
    assert manifest["records"]["sha256"]
    assert manifest["manifest_input"]["sha256"]


def test_confirmation_report_rejects_changed_calibration_manifest(tmp_path: Path) -> None:
    """A replaced calibration manifest cannot be used to authorize confirmation."""

    calibration = _ready_calibration(tmp_path / "calibration")
    (calibration / "manifest.json").write_text("{}", encoding="utf-8")
    confirmation = _records(phase="confirmation", run_id="confirmation-unit")
    _write_runner_inputs(tmp_path / "confirmation", confirmation)

    with pytest.raises(ValueError, match="SHA-256"):
        write_confirmation_report(
            confirmation,
            tmp_path / "confirmation",
            "confirmation-unit",
            calibration,
            BatchNullConfig(),
        )


def test_confirmation_report_rejects_changed_calibration_records(tmp_path: Path) -> None:
    """A changed calibration record file cannot be paired with its old manifest hash."""

    calibration = _ready_calibration(tmp_path / "calibration")
    (calibration / "records.csv").write_text("tampered", encoding="utf-8")
    confirmation = _records(phase="confirmation", run_id="confirmation-unit")
    _write_runner_inputs(tmp_path / "confirmation", confirmation)

    with pytest.raises(ValueError, match="SHA-256"):
        write_confirmation_report(
            confirmation,
            tmp_path / "confirmation",
            "confirmation-unit",
            calibration,
            BatchNullConfig(),
        )


def test_confirmation_report_copies_pinned_calibration_selection(tmp_path: Path) -> None:
    """Confirmation must carry the selected boundary and exact calibration hashes forward."""

    calibration = _ready_calibration(tmp_path / "calibration")
    confirmation = _records(phase="confirmation", run_id="confirmation-unit")
    _write_runner_inputs(tmp_path / "confirmation", confirmation)

    write_confirmation_report(
        confirmation,
        tmp_path / "confirmation",
        "confirmation-unit",
        calibration,
        BatchNullConfig(),
    )

    calibration_manifest = json.loads((calibration / "manifest.json").read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "confirmation" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["calibration"]["selection"] == calibration_manifest["selection"]
    assert manifest["calibration"]["records_sha256"] == calibration_manifest["records"]["sha256"]
    assert manifest["calibration"]["manifest_sha256"]


def test_confirmation_report_is_narrow_at_84_batches(tmp_path: Path) -> None:
    """Fewer than 85 boundary-passing batches remains NARROW, not PASS."""

    calibration = _ready_calibration(tmp_path / "calibration")
    confirmation = _records(
        phase="confirmation", run_id="confirmation-unit", null_like_batches=84
    )
    _write_runner_inputs(tmp_path / "confirmation", confirmation)

    memo = write_confirmation_report(
        confirmation,
        tmp_path / "confirmation",
        "confirmation-unit",
        calibration,
        BatchNullConfig(),
    )

    assert "Terminal outcome: **NARROW**" in memo.read_text(encoding="utf-8")


def test_confirmation_report_stops_for_68_low_p_values(tmp_path: Path) -> None:
    """The high low-p-value count has STOP precedence over the batch-rate result."""

    calibration = _ready_calibration(tmp_path / "calibration")
    confirmation = _records(
        phase="confirmation", run_id="confirmation-unit", low_p_values=68
    )
    _write_runner_inputs(tmp_path / "confirmation", confirmation)

    memo = write_confirmation_report(
        confirmation,
        tmp_path / "confirmation",
        "confirmation-unit",
        calibration,
        BatchNullConfig(),
    )

    assert "Terminal outcome: **STOP**" in memo.read_text(encoding="utf-8")


def test_stop_calibration_blocks_confirmation(tmp_path: Path) -> None:
    """A calibration that fails its p-value guard cannot supply a confirmation boundary."""

    calibration_records = _records(phase="calibration", run_id="calibration-stop", low_p_values=300)
    calibration = tmp_path / "calibration"
    _write_runner_inputs(calibration, calibration_records)
    write_calibration_report(calibration_records, calibration, "calibration-stop", BatchNullConfig())
    confirmation = _records(phase="confirmation", run_id="confirmation-unit")
    _write_runner_inputs(tmp_path / "confirmation", confirmation)

    with pytest.raises(ValueError, match="READY"):
        write_confirmation_report(
            confirmation,
            tmp_path / "confirmation",
            "confirmation-unit",
            calibration,
            BatchNullConfig(),
        )


def test_report_requires_matching_record_run_id(tmp_path: Path) -> None:
    """A report cannot make a mixed or mismatched run look like one immutable artifact."""

    records = _records(phase="calibration", run_id="records")
    _write_runner_inputs(tmp_path, records)

    with pytest.raises(ValueError, match="does not match"):
        write_calibration_report(records, tmp_path, "argument", BatchNullConfig())


def test_memos_end_with_owner_governance_sentence(tmp_path: Path) -> None:
    """Evidence reports must not authorize F1--F8 or automatic successor work."""

    calibration = _ready_calibration(tmp_path / "calibration")
    confirmation = _records(phase="confirmation", run_id="confirmation-unit")
    _write_runner_inputs(tmp_path / "confirmation", confirmation)
    memo = write_confirmation_report(
        confirmation,
        tmp_path / "confirmation",
        "confirmation-unit",
        calibration,
        BatchNullConfig(),
    )

    text = memo.read_text(encoding="utf-8")
    assert "does not run F1--F8" in text
    assert text.rstrip().endswith(OWNER_DECISION_SENTENCE)
