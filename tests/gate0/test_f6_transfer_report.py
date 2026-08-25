"""Evidence-report contracts for the frozen F6 residual-null transfer."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pytest

from research.gate0.f6_transfer_report import write_f6_transfer_report

_BOUNDARY = 0.058242447845091264
_RUN_ID = "f6-unit"


@dataclass(frozen=True)
class _TransferConfig:
    batches: int = 100
    replications_per_batch: int = 10
    rows: int = 1_000
    permutations: int = 199


@pytest.fixture(autouse=True)
def _retain_plot_path_without_a_graphics_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    def write_plot(_summary: pd.DataFrame, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"plot")

    monkeypatch.setattr("research.gate0.f6_transfer_report._plot_batch_classes", write_plot)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ready_calibration(path: Path) -> Path:
    path.mkdir(parents=True)
    records = path / "records.csv"
    runner_input = path / "manifest-input.json"
    records.write_text("calibration records\n", encoding="utf-8")
    runner_input.write_text('{"fixture_id": "reference"}\n', encoding="utf-8")
    manifest = {
        "records": {"sha256": _sha256(records)},
        "manifest_input": {"sha256": _sha256(runner_input)},
        "selection": {
            "status": "READY",
            "boundary": _BOUNDARY,
            "qualifying_batch_ids": list(range(100)),
            "guard_passing_batch_count": 100,
            "null_like_batch_count": 100,
        },
    }
    (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _records(*, null_like_batches: int = 100, low_p_values: int = 0) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for batch in range(100):
        for replication in range(10):
            index = batch * 10 + replication
            rows.append(
                {
                    "fixture_id": "F6",
                    "left": "X1",
                    "right": "X3",
                    "phase": "f6-null-transfer",
                    "batch": batch,
                    "replication": replication,
                    "observed_statistic": 0.01 if batch < null_like_batches else 0.20,
                    "permutation_p_value": 0.05 if index < low_p_values else 0.50,
                    "residual_samples_path": f"residual_samples/batch-{batch}-replication-{replication}.csv",
                    "null_statistics_path": f"null_statistics/batch-{batch}-replication-{replication}.npy",
                    "seed_namespace": "batch-f6-null-transfer",
                    "run_id": _RUN_ID,
                    "warnings": None,
                    "exception_text": None,
                }
            )
    return pd.DataFrame(rows)


def _write_runner_inputs(path: Path, records: pd.DataFrame) -> None:
    path.mkdir(parents=True, exist_ok=True)
    records.to_csv(path / "records.csv", index=False)
    (path / "manifest-input.json").write_text(
        json.dumps({"config": {}, "seed_namespace": "batch-f6-null-transfer"}), encoding="utf-8"
    )
    for relative_path in records["residual_samples_path"]:
        target = path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"X1": [0.0], "X3": [0.0]}).to_csv(target, index=False)


def _write_report(tmp_path: Path, records: pd.DataFrame) -> Path:
    output = tmp_path / "transfer"
    _write_runner_inputs(output, records)
    return write_f6_transfer_report(
        records, output, _RUN_ID, _ready_calibration(tmp_path / "calibration"), _TransferConfig()
    )


def test_complete_f6_frame_passes_and_copies_frozen_boundary(tmp_path: Path) -> None:
    """A complete F6-only frame applies the unchanged confirmation policy."""

    memo = _write_report(tmp_path, _records())
    manifest = json.loads((tmp_path / "transfer" / "manifest.json").read_text(encoding="utf-8"))

    assert "Terminal outcome: **PASS**" in memo.read_text(encoding="utf-8")
    assert manifest["calibration"]["selection"]["boundary"] == _BOUNDARY
    assert (tmp_path / "transfer" / "f6-transfer-summary.csv").is_file()
    assert (tmp_path / "transfer" / "plots" / "f6-batch-classifications.png").is_file()


def test_tampered_calibration_records_are_refused_before_report_output(tmp_path: Path) -> None:
    """A changed pinned calibration record file cannot authorize this transfer report."""

    output = tmp_path / "transfer"
    records = _records()
    _write_runner_inputs(output, records)
    calibration = _ready_calibration(tmp_path / "calibration")
    (calibration / "records.csv").write_text("tampered", encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        write_f6_transfer_report(records, output, _RUN_ID, calibration, _TransferConfig())

    assert not (output / "manifest.json").exists()


def test_84_null_like_batches_are_narrow(tmp_path: Path) -> None:
    """The frozen policy leaves a complete 84-batch transfer NARROW."""

    memo = _write_report(tmp_path, _records(null_like_batches=84))

    assert "Terminal outcome: **NARROW**" in memo.read_text(encoding="utf-8")


def test_68_low_p_values_stop_the_transfer(tmp_path: Path) -> None:
    """The frozen low-p cap has STOP precedence."""

    memo = _write_report(tmp_path, _records(low_p_values=68))

    assert "Terminal outcome: **STOP**" in memo.read_text(encoding="utf-8")


def test_missing_residual_sample_path_is_rejected(tmp_path: Path) -> None:
    """Every successful F6 record must point to a retained residual sample."""

    records = _records()
    output = tmp_path / "transfer"
    _write_runner_inputs(output, records)
    (output / records.loc[0, "residual_samples_path"]).unlink()

    with pytest.raises(ValueError, match="residual sample"):
        write_f6_transfer_report(
            records, output, _RUN_ID, _ready_calibration(tmp_path / "calibration"), _TransferConfig()
        )


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("fixture_id", "F5", "fixture F6"),
        ("left", "X2", "fixture F6"),
        ("phase", "wrong", "F6 residual-null transfer records"),
        ("seed_namespace", "wrong", "seed namespace"),
    ],
)
def test_wrong_transfer_identity_is_rejected(
    tmp_path: Path, column: str, value: str, message: str
) -> None:
    """An identity mismatch must not be summarized as F6 transfer evidence."""

    records = _records()
    records.loc[0, column] = value
    output = tmp_path / "transfer"
    _write_runner_inputs(output, records)

    with pytest.raises(ValueError, match=message):
        write_f6_transfer_report(
            records, output, _RUN_ID, _ready_calibration(tmp_path / "calibration"), _TransferConfig()
        )
