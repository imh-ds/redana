"""Evidence-report contracts for the F2 linear direct-edge detection study."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.gate0.f2_linear_direct_edge_detection_report import (
    write_f2_linear_direct_edge_detection_report,
)
from research.gate0.f4_link_policy import F4LinkConfig

_BOUNDARY = 0.058242447845091264
_RUN_ID = "f2-unit"


@pytest.fixture(autouse=True)
def _retain_plot_path_without_a_graphics_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    def write_plot(_summary: pd.DataFrame, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"plot")

    monkeypatch.setattr(
        "research.gate0.f2_linear_direct_edge_detection_report._plot_detection_batches",
        write_plot,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ready_calibration(path: Path) -> Path:
    path.mkdir(parents=True)
    records = path / "records.csv"
    runner_input = path / "manifest-input.json"
    records.write_text("calibration records\n", encoding="utf-8")
    runner_input.write_text('{"fixture_id": "reference"}\n', encoding="utf-8")
    (path / "manifest.json").write_text(
        json.dumps(
            {
                "records": {"sha256": _sha256(records)},
                "manifest_input": {"sha256": _sha256(runner_input)},
                "selection": {"status": "READY", "boundary": _BOUNDARY},
            }
        ),
        encoding="utf-8",
    )
    return path


def _records(*, detected_batches: int = 100, exception: str | None = None) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for batch in range(100):
        for replication in range(10):
            detected = batch < detected_batches
            rows.append(
                {
                    "fixture_id": "F2",
                    "left": "X1",
                    "right": "X2",
                    "phase": "f2-linear-direct-edge-detection",
                    "batch": batch,
                    "replication": replication,
                    "observed_statistic": 0.1 if detected else 0.01,
                    "permutation_p_value": 0.05 if detected and replication < 8 else 0.50,
                    "residual_samples_path": (
                        f"residual_samples/batch-{batch}-replication-{replication}.csv"
                    ),
                    "null_statistics_path": (
                        f"null_statistics/batch-{batch}-replication-{replication}.npy"
                    ),
                    "seed_namespace": "batch-f2-linear-direct-edge-detection",
                    "run_id": _RUN_ID,
                    "warnings": exception if batch == 0 and replication == 0 and exception == "warn" else None,
                    "exception_text": exception if batch == 0 and replication == 0 and exception != "warn" else None,
                }
            )
    return pd.DataFrame(rows)


def _write_runner_inputs(path: Path, records: pd.DataFrame) -> None:
    path.mkdir(parents=True, exist_ok=True)
    records.to_csv(path / "records.csv", index=False)
    (path / "manifest-input.json").write_text(
        json.dumps(
            {
                "config": {},
                "fixture_id": "F2",
                "pair": ["X1", "X2"],
                "phase": "f2-linear-direct-edge-detection",
                "run_id": _RUN_ID,
                "seed_namespace": "batch-f2-linear-direct-edge-detection",
            }
        ),
        encoding="utf-8",
    )
    for row in records.itertuples(index=False):
        if isinstance(row.exception_text, str) and row.exception_text:
            continue
        residual_path = path / row.residual_samples_path
        residual_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"X1": [0.0], "X2": [0.0]}).to_csv(residual_path, index=False)
        null_path = path / row.null_statistics_path
        null_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(null_path, np.array([0.01]))


def _write_report(tmp_path: Path, records: pd.DataFrame) -> Path:
    output = tmp_path / "detection"
    _write_runner_inputs(output, records)
    return write_f2_linear_direct_edge_detection_report(
        records, output, _RUN_ID, _ready_calibration(tmp_path / "calibration"), F4LinkConfig()
    )


def test_complete_detection_evidence_passes_and_copies_boundary(tmp_path: Path) -> None:
    memo = _write_report(tmp_path, _records())
    manifest = json.loads((tmp_path / "detection" / "manifest.json").read_text(encoding="utf-8"))

    assert "Terminal outcome: **PASS**" in memo.read_text(encoding="utf-8")
    assert manifest["calibration"]["selection"]["boundary"] == _BOUNDARY
    assert manifest["detection_boundary"] == _BOUNDARY
    assert (tmp_path / "detection" / "f2-linear-direct-edge-detection-summary.csv").is_file()
    assert (tmp_path / "detection" / "plots" / "f2-linear-direct-edge-detections.png").is_file()


@pytest.mark.parametrize("detected_batches, expected", [(84, "NARROW"), (85, "PASS")])
def test_detection_count_applies_the_precommitted_outcome(
    tmp_path: Path, detected_batches: int, expected: str
) -> None:
    memo = _write_report(tmp_path, _records(detected_batches=detected_batches))

    assert f"Terminal outcome: **{expected}**" in memo.read_text(encoding="utf-8")


def test_exception_evidence_stops_the_report(tmp_path: Path) -> None:
    records = _records(exception="RuntimeError: retained")
    records.loc[0, ["residual_samples_path", "null_statistics_path"]] = None
    memo = _write_report(tmp_path, records)

    assert "Terminal outcome: **STOP**" in memo.read_text(encoding="utf-8")


def test_warning_evidence_stops_the_report(tmp_path: Path) -> None:
    records = _records(exception="warn")
    records.loc[0, "warnings"] = "UserWarning: something noted"
    memo = _write_report(tmp_path, records)

    assert "Terminal outcome: **STOP**" in memo.read_text(encoding="utf-8")


def test_tampered_calibration_records_are_refused_before_report_output(tmp_path: Path) -> None:
    output = tmp_path / "detection"
    records = _records()
    _write_runner_inputs(output, records)
    calibration = _ready_calibration(tmp_path / "calibration")
    (calibration / "records.csv").write_text("tampered", encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        write_f2_linear_direct_edge_detection_report(
            records, output, _RUN_ID, calibration, F4LinkConfig()
        )

    assert not (output / "manifest.json").exists()


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("fixture_id", "F5", "fixture"),
        ("phase", "wrong", "phase"),
        ("left", "X2", "pair"),
        ("seed_namespace", "wrong", "seed namespace"),
    ],
)
def test_wrong_detection_identity_is_rejected(
    tmp_path: Path, column: str, value: str, message: str
) -> None:
    records = _records()
    records.loc[0, column] = value
    output = tmp_path / "detection"
    _write_runner_inputs(output, records)

    with pytest.raises(ValueError, match=message):
        write_f2_linear_direct_edge_detection_report(
            records, output, _RUN_ID, _ready_calibration(tmp_path / "calibration"), F4LinkConfig()
        )


def test_missing_residual_evidence_is_rejected(tmp_path: Path) -> None:
    records = _records()
    output = tmp_path / "detection"
    _write_runner_inputs(output, records)
    (output / records.loc[0, "residual_samples_path"]).unlink()

    with pytest.raises(ValueError, match="residual sample"):
        write_f2_linear_direct_edge_detection_report(
            records, output, _RUN_ID, _ready_calibration(tmp_path / "calibration"), F4LinkConfig()
        )
