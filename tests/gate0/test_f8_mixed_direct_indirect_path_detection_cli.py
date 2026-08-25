"""Command-line contracts for the frozen F8 mixed direct-and-indirect path detection study."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _approved_calibration(path: Path, boundary: float) -> None:
    path.mkdir(parents=True)
    records = path / "records.csv"
    runner_input = path / "manifest-input.json"
    records.write_text("calibration\n", encoding="utf-8")
    runner_input.write_text("{}\n", encoding="utf-8")
    (path / "manifest.json").write_text(
        json.dumps(
            {
                "records": {"sha256": _sha256(records)},
                "manifest_input": {"sha256": _sha256(runner_input)},
                "selection": {"status": "READY", "boundary": boundary},
            }
        ),
        encoding="utf-8",
    )


def test_cli_refuses_altered_calibration_provenance_before_creating_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from scripts import run_f8_mixed_direct_indirect_path_detection as cli

    calibration = tmp_path / "calibration"
    _approved_calibration(calibration, cli._FROZEN_BOUNDARY)
    monkeypatch.setattr(cli, "_CALIBRATION_DIR", calibration)
    (calibration / "records.csv").write_text("altered\n", encoding="utf-8")
    output = tmp_path / "output"

    assert cli.main(["--output-dir", str(output), "--run-id", "unit"]) == 2
    assert not output.exists()
    assert "REFUSED [unit]" in capsys.readouterr().err


def test_cli_uses_only_output_and_run_id_and_refuses_reuse(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from scripts import run_f8_mixed_direct_indirect_path_detection as cli

    calibration = tmp_path / "calibration"
    _approved_calibration(calibration, cli._FROZEN_BOUNDARY)
    monkeypatch.setattr(cli, "_CALIBRATION_DIR", calibration)
    monkeypatch.setattr(cli, "_verify_frozen_calibration", lambda: None)
    calls: dict[str, object] = {}

    def fake_run(output_dir: Path, run_id: str, config: object) -> pd.DataFrame:
        if output_dir.exists() and any(output_dir.iterdir()):
            raise FileExistsError("run directory is already initialized")
        calls.update(output_dir=output_dir, run_id=run_id, config=config)
        output_dir.mkdir(parents=True)
        (output_dir / "records.csv").write_text("records\n", encoding="utf-8")
        return pd.DataFrame({"value": [1]})

    def fake_report(
        records: pd.DataFrame, output_dir: Path, run_id: str, calibration_dir: Path, config: object
    ) -> Path:
        assert len(records) == 1
        assert calibration_dir == calibration
        (output_dir / "manifest.json").write_text('{"terminal_outcome": "PASS"}', encoding="utf-8")
        memo = output_dir / "memo.md"
        memo.write_text("memo\n", encoding="utf-8")
        return memo

    monkeypatch.setattr(cli, "run_f8_mixed_direct_indirect_path_detection", fake_run)
    monkeypatch.setattr(cli, "write_f8_mixed_direct_indirect_path_detection_report", fake_report)
    output = tmp_path / "output"

    assert cli.main(["--output-dir", str(output), "--run-id", "unit"]) == 0
    assert calls["output_dir"] == output
    assert calls["run_id"] == "unit"
    assert type(calls["config"]).__name__ == "F4LinkConfig"
    assert set(vars(cli._parse_args(["--output-dir", str(output), "--run-id", "unit"]))) == {
        "output_dir", "run_id"
    }
    assert cli.main(["--output-dir", str(output), "--run-id", "unit"]) == 2
    assert "REFUSED [unit]" in capsys.readouterr().err


def test_cli_rejects_unknown_flags(tmp_path: Path) -> None:
    from scripts import run_f8_mixed_direct_indirect_path_detection as cli

    with pytest.raises(SystemExit):
        cli._parse_args(
            ["--output-dir", str(tmp_path / "out"), "--run-id", "unit", "--rows", "10"]
        )
