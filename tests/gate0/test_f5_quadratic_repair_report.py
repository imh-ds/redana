"""Evidence-report contracts for the frozen F5 quadratic repair."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.gate0 import f5_quadratic_repair_report
from research.gate0.f5_quadratic_repair_report import (
    write_f5_quadratic_repair_report,
)
from research.gate0.f5_quadratic_repair_runner import F5QuadraticRepairConfig

_BOUNDARY = 0.058242447845091264
_RUN_ID = "f5-quadratic-unit"


@pytest.fixture(autouse=True)
def _retain_plot_path_without_a_graphics_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    def write_plot(_summary: pd.DataFrame, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"plot")

    monkeypatch.setattr(
        "research.gate0.f5_quadratic_repair_report._plot_batch_classes", write_plot
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _calibration(path: Path) -> Path:
    path.mkdir(parents=True)
    records = path / "records.csv"
    runner_input = path / "manifest-input.json"
    records.write_text("raw calibration records\n", encoding="utf-8")
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


def _f5_stop(path: Path) -> Path:
    path.mkdir(parents=True)
    records = path / "records.csv"
    runner_input = path / "manifest-input.json"
    records.write_text("original F5 STOP records\n", encoding="utf-8")
    runner_input.write_text(
        '{"seed_namespace": "batch-f5-null-transfer"}\n', encoding="utf-8"
    )
    (path / "manifest.json").write_text(
        json.dumps(
            {
                "terminal_outcome": "STOP",
                "fixture_id": "F5",
                "pair": ["X1", "X2"],
                "phase": "f5-null-transfer",
                "records": {"sha256": _sha256(records)},
                "manifest_input": {"sha256": _sha256(runner_input)},
                "confirmation_check": {
                    "null_like_batch_count": 74,
                    "low_p_value_count": 81,
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def _freeze_synthetic_parent_hashes(
    monkeypatch: pytest.MonkeyPatch, calibration: Path, f5_stop: Path
) -> None:
    monkeypatch.setattr(
        f5_quadratic_repair_report,
        "_CALIBRATION_HASHES",
        {
            "records_sha256": _sha256(calibration / "records.csv"),
            "manifest_input_sha256": _sha256(calibration / "manifest-input.json"),
            "manifest_sha256": _sha256(calibration / "manifest.json"),
        },
    )
    monkeypatch.setattr(
        f5_quadratic_repair_report,
        "_F5_STOP_HASHES",
        {
            "records_sha256": _sha256(f5_stop / "records.csv"),
            "manifest_input_sha256": _sha256(f5_stop / "manifest-input.json"),
            "manifest_sha256": _sha256(f5_stop / "manifest.json"),
        },
    )


def _records(
    *, null_like_batches: int = 100, low_p_values: int = 0
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for batch in range(100):
        for replication in range(10):
            index = batch * 10 + replication
            rows.append(
                {
                    "fixture_id": "F5",
                    "left": "X1",
                    "right": "X2",
                    "phase": "f5-quadratic-repair",
                    "batch": batch,
                    "replication": replication,
                    "observed_statistic": 0.01 if batch < null_like_batches else 0.20,
                    "permutation_p_value": 0.05 if index < low_p_values else 0.50,
                    "residual_samples_path": "residual_samples/retained.csv",
                    "null_statistics_path": "null_statistics/retained.npy",
                    "seed_namespace": "batch-f5-quadratic-repair",
                    "fixture_seed": index + 1,
                    "residual_seed": index + 2,
                    "permutation_seed": index + 3,
                    "elapsed_seconds": 0.01,
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
        json.dumps(
            {
                "basis": "raw-plus-square",
                "config": {
                    "batches": 100,
                    "replications_per_batch": 10,
                    "rows": 1_000,
                    "permutations": 199,
                    "n_splits": 5,
                    "ridge_alpha": 1.0,
                },
                "fixture_id": "F5",
                "pair": ["X1", "X2"],
                "phase": "f5-quadratic-repair",
                "run_id": _RUN_ID,
                "seed_namespace": "batch-f5-quadratic-repair",
                "source_revision": "source-test-sha",
                "uses_splines": False,
            }
        ),
        encoding="utf-8",
    )
    residual_path = path / "residual_samples" / "retained.csv"
    residual_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"X1": [0.0], "X2": [0.0]}).to_csv(residual_path, index=False)
    null_path = path / "null_statistics" / "retained.npy"
    null_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(null_path, np.array([0.01]))


def _prepared_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    records: pd.DataFrame,
) -> tuple[Path, Path, Path]:
    output = tmp_path / "repair"
    calibration = _calibration(tmp_path / "calibration")
    f5_stop = _f5_stop(tmp_path / "f5-stop")
    _freeze_synthetic_parent_hashes(monkeypatch, calibration, f5_stop)
    _write_runner_inputs(output, records)
    return output, calibration, f5_stop


def _write_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, records: pd.DataFrame
) -> Path:
    output, calibration, f5_stop = _prepared_report(tmp_path, monkeypatch, records)
    return write_f5_quadratic_repair_report(
        records,
        output,
        _RUN_ID,
        calibration,
        f5_stop,
        F5QuadraticRepairConfig(),
    )


def test_85_null_like_batches_pass_and_pin_basis_and_both_parents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A wrong boundary, basis, parent hash, or PASS scope must fail this contract."""

    memo = _write_report(tmp_path, monkeypatch, _records(null_like_batches=85))
    output = tmp_path / "repair"
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["terminal_outcome"] == "PASS"
    assert manifest["copied_boundary"] == _BOUNDARY
    assert manifest["basis"] == {"name": "raw-plus-square", "uses_splines": False}
    assert manifest["calibration"]["manifest_sha256"] == _sha256(
        tmp_path / "calibration" / "manifest.json"
    )
    assert manifest["f5_stop"]["manifest_sha256"] == _sha256(
        tmp_path / "f5-stop" / "manifest.json"
    )
    assert manifest["f5_stop"]["terminal_outcome"] == "STOP"
    assert manifest["confirmation_check"]["null_like_batch_count"] == 85
    assert (output / "f5-quadratic-repair-summary.csv").is_file()
    assert (output / "plots" / "f5-quadratic-batch-classifications.png").is_file()
    assert json.loads((output / "run_state.json").read_text(encoding="utf-8")) == {
        "run_id": _RUN_ID,
        "state": "complete",
        "terminal_outcome": "PASS",
    }
    assert (
        "A PASS supports only that this explicit raw-plus-square basis repairs the "
        "prescribed F5 quadratic null under this frozen 1,000-row procedure."
        in memo.read_text(encoding="utf-8")
    )


@pytest.mark.parametrize(
    ("null_like_batches", "low_p_values", "expected"),
    [(84, 0, "NARROW"), (100, 68, "STOP")],
)
def test_frozen_counts_apply_terminal_precedence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    null_like_batches: int,
    low_p_values: int,
    expected: str,
) -> None:
    """Changing either frozen count branch must change the retained outcome."""

    memo = _write_report(
        tmp_path,
        monkeypatch,
        _records(null_like_batches=null_like_batches, low_p_values=low_p_values),
    )

    assert f"Terminal outcome: **{expected}**" in memo.read_text(encoding="utf-8")


def test_retained_exception_stops_without_requiring_missing_cell_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Treating a retained cell exception as NARROW or PASS must fail this test."""

    records = _records()
    records.loc[0, ["observed_statistic", "permutation_p_value"]] = None
    records.loc[0, ["residual_samples_path", "null_statistics_path"]] = None
    records.loc[0, "exception_text"] = "RuntimeError: retained failure"

    memo = _write_report(tmp_path, monkeypatch, records)

    assert "Terminal outcome: **STOP**" in memo.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("phase", "wrong", "phase"),
        ("fixture_id", "F4", "fixture"),
        ("left", "X2", "pair"),
        ("seed_namespace", "wrong", "seed namespace"),
    ],
)
def test_wrong_repair_identity_is_refused_before_report_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    column: str,
    value: str,
    message: str,
) -> None:
    """An identity mismatch must not be summarized as repair evidence."""

    records = _records()
    records.loc[0, column] = value
    output, calibration, f5_stop = _prepared_report(tmp_path, monkeypatch, records)

    with pytest.raises(ValueError, match=message):
        write_f5_quadratic_repair_report(
            records,
            output,
            _RUN_ID,
            calibration,
            f5_stop,
            F5QuadraticRepairConfig(),
        )

    assert not (output / "manifest.json").exists()


@pytest.mark.parametrize(
    ("column", "message"),
    [
        ("residual_samples_path", "residual sample"),
        ("null_statistics_path", "null array"),
    ],
)
def test_missing_success_evidence_is_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    column: str,
    message: str,
) -> None:
    """A successful cell without either retained evidence type must be refused."""

    records = _records()
    output, calibration, f5_stop = _prepared_report(tmp_path, monkeypatch, records)
    (output / records.loc[0, column]).unlink()

    with pytest.raises(ValueError, match=message):
        write_f5_quadratic_repair_report(
            records,
            output,
            _RUN_ID,
            calibration,
            f5_stop,
            F5QuadraticRepairConfig(),
        )

    assert not (output / "manifest.json").exists()


@pytest.mark.parametrize("parent", ["calibration", "f5_stop"])
@pytest.mark.parametrize("filename", ["records.csv", "manifest-input.json", "manifest.json"])
def test_tampered_parent_file_is_refused_before_report_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    parent: str,
    filename: str,
) -> None:
    """Changing any of the six pinned parent files must prevent report creation."""

    records = _records()
    output, calibration, f5_stop = _prepared_report(tmp_path, monkeypatch, records)
    chosen = calibration if parent == "calibration" else f5_stop
    (chosen / filename).write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        write_f5_quadratic_repair_report(
            records,
            output,
            _RUN_ID,
            calibration,
            f5_stop,
            F5QuadraticRepairConfig(),
        )

    assert not (output / "manifest.json").exists()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("terminal_outcome", "PASS", "STOP"),
        ("null_like_batch_count", 75, "74 null-like"),
        ("low_p_value_count", 80, "81 low p-values"),
    ],
)
def test_hash_valid_f5_parent_must_match_recorded_stop_outcome(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    message: str,
) -> None:
    """A hash-valid but semantically different F5 comparator must be refused."""

    records = _records()
    output = tmp_path / "repair"
    calibration = _calibration(tmp_path / "calibration")
    f5_stop = _f5_stop(tmp_path / "f5-stop")
    manifest_path = f5_stop / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if field == "terminal_outcome":
        manifest[field] = value
    else:
        manifest["confirmation_check"][field] = value
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    _freeze_synthetic_parent_hashes(monkeypatch, calibration, f5_stop)
    _write_runner_inputs(output, records)

    with pytest.raises(ValueError, match=message):
        write_f5_quadratic_repair_report(
            records,
            output,
            _RUN_ID,
            calibration,
            f5_stop,
            F5QuadraticRepairConfig(),
        )

    assert not (output / "manifest.json").exists()
