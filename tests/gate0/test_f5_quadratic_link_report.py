"""Evidence-report contracts for the F5 quadratic-residual-link alternative."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.gate0 import f5_quadratic_link_report
from research.gate0.f4_link_policy import F4LinkConfig
from research.gate0.f5_quadratic_link_report import write_f5_quadratic_link_report

_BOUNDARY = 0.058242447845091264
_RUN_ID = "f5-quadratic-link-unit"


@pytest.fixture(autouse=True)
def _retain_plot_path_without_a_graphics_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    def write_plot(_summary: pd.DataFrame, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"plot")

    monkeypatch.setattr(
        "research.gate0.f5_quadratic_link_report._plot_detection_batches", write_plot
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _calibration(path: Path) -> Path:
    path.mkdir(parents=True)
    records, runner_input = path / "records.csv", path / "manifest-input.json"
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


def _f5_quadratic_repair_pass(path: Path) -> Path:
    path.mkdir(parents=True)
    records, runner_input = path / "records.csv", path / "manifest-input.json"
    records.write_text("f5 quadratic repair records\n", encoding="utf-8")
    runner_input.write_text(
        '{"basis": "raw-plus-square", "seed_namespace": "batch-f5-quadratic-repair"}\n',
        encoding="utf-8",
    )
    (path / "manifest.json").write_text(
        json.dumps(
            {
                "terminal_outcome": "PASS",
                "fixture_id": "F5",
                "pair": ["X1", "X2"],
                "phase": "f5-quadratic-repair",
                "records": {"sha256": _sha256(records)},
                "manifest_input": {"sha256": _sha256(runner_input)},
                "confirmation_check": {
                    "null_like_batch_count": 90,
                    "low_p_value_count": 44,
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def _freeze_synthetic_parent_hashes(
    monkeypatch: pytest.MonkeyPatch, calibration: Path, f5_quadratic_repair: Path
) -> None:
    monkeypatch.setattr(
        f5_quadratic_link_report,
        "_CALIBRATION_HASHES",
        {
            "records_sha256": _sha256(calibration / "records.csv"),
            "manifest_input_sha256": _sha256(calibration / "manifest-input.json"),
            "manifest_sha256": _sha256(calibration / "manifest.json"),
        },
    )
    monkeypatch.setattr(
        f5_quadratic_link_report,
        "_F5_QUADRATIC_REPAIR_HASHES",
        {
            "records_sha256": _sha256(f5_quadratic_repair / "records.csv"),
            "manifest_input_sha256": _sha256(f5_quadratic_repair / "manifest-input.json"),
            "manifest_sha256": _sha256(f5_quadratic_repair / "manifest.json"),
        },
    )


def _records(*, detected_batches: int = 100, exception: str | None = None) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for batch in range(100):
        for replication in range(10):
            detected = batch < detected_batches
            rows.append(
                {
                    "fixture_id": "F5-quadratic-residual-link",
                    "left": "X1",
                    "right": "X2",
                    "phase": "f5-quadratic-residual-link",
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
                    "seed_namespace": "batch-f5-quadratic-residual-link",
                    "run_id": _RUN_ID,
                    "warnings": None,
                    "exception_text": exception if batch == 0 and replication == 0 else None,
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
                "config": {},
                "fixture_id": "F5-quadratic-residual-link",
                "pair": ["X1", "X2"],
                "phase": "f5-quadratic-residual-link",
                "run_id": _RUN_ID,
                "seed_namespace": "batch-f5-quadratic-residual-link",
                "uses_splines": False,
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


def _prepared_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, records: pd.DataFrame
) -> tuple[Path, Path, Path]:
    output = tmp_path / "link"
    calibration = _calibration(tmp_path / "calibration")
    f5_quadratic_repair = _f5_quadratic_repair_pass(tmp_path / "f5-quadratic-repair")
    _freeze_synthetic_parent_hashes(monkeypatch, calibration, f5_quadratic_repair)
    _write_runner_inputs(output, records)
    return output, calibration, f5_quadratic_repair


def _write_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, records: pd.DataFrame
) -> Path:
    output, calibration, f5_quadratic_repair = _prepared_report(tmp_path, monkeypatch, records)
    return write_f5_quadratic_link_report(
        records, output, _RUN_ID, f5_quadratic_repair, calibration, F4LinkConfig()
    )


def test_complete_link_evidence_passes_and_pins_both_parents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    memo = _write_report(tmp_path, monkeypatch, _records())
    manifest = json.loads((tmp_path / "link" / "manifest.json").read_text(encoding="utf-8"))

    assert "Terminal outcome: **PASS**" in memo.read_text(encoding="utf-8")
    assert manifest["f5_quadratic_repair"]["terminal_outcome"] == "PASS"
    assert manifest["calibration"]["selection"]["boundary"] == _BOUNDARY
    assert manifest["detection_boundary"] == _BOUNDARY
    assert (tmp_path / "link" / "f5-quadratic-link-summary.csv").is_file()
    assert (tmp_path / "link" / "plots" / "f5-quadratic-link-detections.png").is_file()
    assert json.loads((tmp_path / "link" / "run_state.json").read_text(encoding="utf-8")) == {
        "run_id": _RUN_ID,
        "state": "complete",
        "terminal_outcome": "PASS",
    }


@pytest.mark.parametrize("detected_batches, expected", [(84, "NARROW"), (85, "PASS")])
def test_detection_count_applies_the_precommitted_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, detected_batches: int, expected: str
) -> None:
    memo = _write_report(
        tmp_path, monkeypatch, _records(detected_batches=detected_batches)
    )

    assert f"Terminal outcome: **{expected}**" in memo.read_text(encoding="utf-8")


def test_exception_evidence_stops_the_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    records = _records(exception="RuntimeError: retained")
    records.loc[0, ["residual_samples_path", "null_statistics_path"]] = None
    memo = _write_report(tmp_path, monkeypatch, records)

    assert "Terminal outcome: **STOP**" in memo.read_text(encoding="utf-8")


@pytest.mark.parametrize("parent", ["calibration", "f5_quadratic_repair"])
@pytest.mark.parametrize("filename", ["records.csv", "manifest-input.json", "manifest.json"])
def test_tampered_parent_file_is_refused_before_report_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, parent: str, filename: str
) -> None:
    records = _records()
    output, calibration, f5_quadratic_repair = _prepared_report(tmp_path, monkeypatch, records)
    chosen = calibration if parent == "calibration" else f5_quadratic_repair
    (chosen / filename).write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        write_f5_quadratic_link_report(
            records, output, _RUN_ID, f5_quadratic_repair, calibration, F4LinkConfig()
        )

    assert not (output / "manifest.json").exists()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("terminal_outcome", "NARROW", "PASS"),
        ("null_like_batch_count", 89, "90 null-like"),
        ("low_p_value_count", 43, "44 low p-values"),
    ],
)
def test_hash_valid_parent_must_match_recorded_pass_outcome(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    message: str,
) -> None:
    records = _records()
    output = tmp_path / "link"
    calibration = _calibration(tmp_path / "calibration")
    f5_quadratic_repair = _f5_quadratic_repair_pass(tmp_path / "f5-quadratic-repair")
    manifest_path = f5_quadratic_repair / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if field == "terminal_outcome":
        manifest[field] = value
    else:
        manifest["confirmation_check"][field] = value
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    _freeze_synthetic_parent_hashes(monkeypatch, calibration, f5_quadratic_repair)
    _write_runner_inputs(output, records)

    with pytest.raises(ValueError, match=message):
        write_f5_quadratic_link_report(
            records, output, _RUN_ID, f5_quadratic_repair, calibration, F4LinkConfig()
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
def test_wrong_link_identity_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, column: str, value: str, message: str
) -> None:
    records = _records()
    records.loc[0, column] = value
    output, calibration, f5_quadratic_repair = _prepared_report(tmp_path, monkeypatch, records)

    with pytest.raises(ValueError, match=message):
        write_f5_quadratic_link_report(
            records, output, _RUN_ID, f5_quadratic_repair, calibration, F4LinkConfig()
        )


def test_missing_residual_evidence_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    records = _records()
    output, calibration, f5_quadratic_repair = _prepared_report(tmp_path, monkeypatch, records)
    (output / records.loc[0, "residual_samples_path"]).unlink()

    with pytest.raises(ValueError, match="residual sample"):
        write_f5_quadratic_link_report(
            records, output, _RUN_ID, f5_quadratic_repair, calibration, F4LinkConfig()
        )


def test_calibration_boundary_mismatch_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    records = _records()
    output = tmp_path / "link"
    calibration = _calibration(tmp_path / "calibration")
    manifest_path = calibration / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["selection"]["boundary"] = 0.1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    f5_quadratic_repair = _f5_quadratic_repair_pass(tmp_path / "f5-quadratic-repair")
    _freeze_synthetic_parent_hashes(monkeypatch, calibration, f5_quadratic_repair)
    _write_runner_inputs(output, records)

    with pytest.raises(ValueError, match="boundary"):
        write_f5_quadratic_link_report(
            records, output, _RUN_ID, f5_quadratic_repair, calibration, F4LinkConfig()
        )

    assert not (output / "manifest.json").exists()
